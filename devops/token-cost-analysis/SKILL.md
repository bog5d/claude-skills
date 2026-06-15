---
name: token-cost-analysis
version: 1.0
author: Hermes
tags: [token, cost, billing, deepseek, flash, pro, optimization, debugging]
description: 诊断 API token 用量异常、分析账单、定位 token 消耗来源、优化模型路由。适用于 token 费用突增、Flash 用量异常、缓存命中率低等问题。
created: 2026-06-14
updated: 2026-06-14
---

# Token 用量分析与优化

当用户报告"token 烧得快"、"账单高了"、"这个模型用量怎么这么大"时使用。

## 核心原则

**不要凭感觉判断 token 消耗。必须看账单数据。**

## Phase 1: 读取账单

获取 token 账单 CSV（通常来自 DeepSeek 控制台或 API 提供商的用量导出）：

```bash
# 用户发送 CSV 文件后，直接读取
read_file path=/path/to/token-bill.csv
```

CSV 典型列：`type`, `utc_date`, `model`, `api_key_name`, `api_key`, `price`, `amount`

## Phase 2: 数据聚合分析

用 Python 做关键聚合：

```python
import csv
from collections import defaultdict

rows = []
with open('bill.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# 1. 按日期+模型聚合输出 token
by_date_model = defaultdict(lambda: defaultdict(int))
for r in rows:
    if r['type'] == 'output_tokens' and r['amount']:
        by_date_model[r['utc_date']][r['model']] += int(float(r['amount']))

# 2. 按 key 聚合
by_key = defaultdict(lambda: {'output': 0, 'requests': 0})
for r in rows:
    if r['type'] == 'output_tokens':
        by_key[r['api_key_name']]['output'] += float(r['amount']) if r['amount'] else 0
    elif r['type'] == 'request_count':
        by_key[r['api_key_name']]['requests'] += int(float(r['amount']))

# 3. 按日期聚合总成本
by_date_cost = defaultdict(float)
for r in rows:
    if r['type'] == 'amount' and r['amount']:
        by_date_cost[r['utc_date']] += float(r['amount'])
```

## Phase 3: 定位异常

### 关键信号

| 信号 | 含义 | 行动 |
|------|------|------|
| 某模型某天用量突增 3x+ | 行为变化，非正常增长 | 查当天 cron/agent 日志 |
| Flash 占比突然升高 | 路由变化或 fallback 触发 | 检查 delegation.model 配置 |
| 单请求输出 token 暴增 | 子任务/压缩输出过长 | 检查 subagent 输出长度 |
| cache_miss 比例高 | prompt 变化大，无法缓存 | 检查 system prompt 是否动态变化 |
| 某 key 用量远超其他 | 该 key 被大量使用 | 查哪些组件在用这个 key |

### 排除路径

**不是 subagent** — `delegate_tool.py` 中 `effective_model = model or parent_agent.model`，parent 是 v4-pro 则 subagent 也走 pro。

**不是 advisor cron** — 明确配置 `model: deepseek-v4-pro`，日志全是 v4-pro。

**不是 context compression** — 压缩用的是独立模型（如 agnes-2.0-flash），走不同的 API endpoint，不消耗主 key。

### 常见根因

1. **`delegation.model: ''` 空字符串** — config.yaml 中 `delegation.model` 为空时，可能触发 credential pool 的自动路由到 Flash
2. **credential pool 自动路由** — 当 Pro 遇到 rate-limit 时自动 fallback 到 Flash
3. **cron job 新增/变更** — 新加的 cron job 可能用了不同的模型或产生了大量子任务
4. **subagent 输出过长** — 每个子任务输出 2000+ tokens（正常 200-500）

## Phase 4: 验证与修复

### 验证

```bash
# 查 agent log 中特定日期的活动
grep "2026-06-08" ~/.hermes/logs/agent.log | grep -c "API call"

# 查 Flash 相关记录
grep "v4-flash" ~/.hermes/logs/agent.log

# 查 delegation 配置
grep -A5 "delegation:" ~/.hermes/config.yaml

# 查 advisor cron 模型
grep "advisor" ~/.hermes/cron/jobs.json 2>/dev/null
```

### 修复

**方案 A：强制 subagent 走 Pro**

```yaml
# config.yaml
delegation:
  model: 'deepseek-v4-pro'  # 不再是空字符串
```

**方案 B：加 subagent 输出长度 guard**

在 `delegate_tool.py` 的 `_build_child_agent` 中加：
```python
# Guard: 单次 subagent 输出超过 80K tokens 时警告
if max_iterations > 50:
    logger.warning("Subagent max_iterations=%d may produce excessive output", max_iterations)
```

**方案 C：Flash 只用于简短任务**

在 subagent 路由逻辑中加复杂度判断——简单任务用 Flash，复杂任务用 Pro。

## 用户沟通要点

- **压缩没有浪费 token** — 压缩前的 token 数（如 319K）是原始值，压缩后只剩 ~5K，节省了 98.5%。用户看到"数字很大"是压缩前的值，实际被压缩掉了。
- **Flash 不是"本身贵"** — 输出 token 单价是 Pro 的 1/3，但如果每个请求输出量是 Pro 的 5-7 倍且 cache_miss 率高，总成本反而更高。
- **不是泄露** — key 专用、调用模式正常、cache_hit 比例合理，就是行为变化导致的。

## Token 优化技术

当 token 用量已经确认很高时，除了分析根因，还可以部署 **headroom proxy** 作为前置压缩层。

### headroom proxy — 前置上下文压缩

headroom（[github.com/chopratejas/headroom](https://github.com/chopratejas/headroom)）在 LLM 请求进入模型前先压缩上下文，60-95% token 削减，准确率不变（GSM8K ±0, TruthfulQA +0.030）。

**部署方式**: 作为独立代理运行在 8787 端口，Hermes gateway 配置 provider 的 `base_url` 指向它即可。

**完整集成流程**: 见 `headroom-proxy-integration` skill。

**关键点**:
- 默认 backend 是 Anthropic，DashScope/Agnes AI 等 OpenAI 兼容 API 必须用 `--backend litellm-openai --openai-api-url <upstream>`
- 通过 launchd 持久化管理，macOS 重启自动恢复
- 四个 profile 共享同一个 headroom 实例，token 节省是指数级的

### 深度缓存优化

| 方法 | 场景 | 节省幅度 |
|------|------|---------|
| headroom 压缩 | 长上下文场景 | 60-95% token 削减 |
| DeepSeek 前缀缓存 | 稳定 system prompt | 20-40% 成本 |
| 模型路由降级 | 简单任务走 Flash | 3x 单价优势 |
| 输出长度 guard | 控制 subagent 输出 | 减少无意义 token |

## 参考

| 文件 | 说明 |
|------|------|
| `references/token-bill-diagnosis.md` | 完整诊断案例：2026-06-14 副官 token 异常（Flash 用量从 1% 飙到 78%） |
| `references/v4-flash-spike-investigation.md` | V4-Flash 用量异常的根因（`delegation.model: ''` 空字符串 bug）+ 一键修复命令 + 预防规则 |