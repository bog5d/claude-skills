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

## 副官记忆注入开销（2026-06-17 新增）

**现象**：副官 cron job 消耗 98.5% 总费用，日均 ¥27/天，月预估 ¥570+。

**根因拆解**：

1. **Cron 无状态** — 每次 cron 触发是全新 session，没有"上次聊了什么"的记忆，必须重新注入全部上下文
2. **Skills 全家桶加载** — 25 个 SKILL.md 全文注入（~82MB 目录，实际加载 500KB+）
3. **Episodic Memory 搜索** — EverOS/tencentdb 每次搜索返回几十到上百条对话摘要
4. **AGENTS.md + 任务文件** — 副岗说明书 + status.json + diary + prep 全部读取
5. **高频触发** — 感知引擎每 5 分钟跑一次（`perception.py --once`），每天 ~288 次，每月 ~8,640 次

**对比 her-m2**：her-m2 只在用户主动发消息时触发，注入量相同但频率低几个数量级。

**优化方向**：
- 副官切 v4-flash（同样的任务不需要顶级推理能力，便宜 3 倍）
- 减少 skill 加载（副官实际只用 3-4 个 skill，不必全加载）
- 压缩 episodic memory 搜索范围（只搜最近 N 天）
- 降低感知引擎频率（5 分钟 → 15-30 分钟）

**诊断命令**：
```bash
# 看 cron jobs 里哪些是 LLM-driven（no_agent: false）
python3 -c "
import json
with open('/Users/mac/.hermes/cron/jobs.json') as f:
    jobs = json.load(f)['jobs']
for j in jobs:
    if not j.get('no_agent', True):
        print(f\"{j['name']}: enabled={j['enabled']}, profile={j.get('profile')}, runs={j.get('repeat',{}).get('completed',0)}\")
"
# 看 skill 总大小
du -sh ~/.hermes/skills/
# 看 AGENTS.md 大小
wc -c ~/.hermes/adjutant/repo/hermes-adjutant/AGENTS.md
```

## 2026-06-17 案例：全 profile 模型统一降级为 Agnes + DeepSeek v4-flash

**场景**：副官 cron 消耗 98.5% 费用，用户要求全面降本。

**操作**：
1. 暂停低价值 cron（感知引擎、健康巡检、财务周报等 4 个）
2. 确认 default 已是 agnes-2.0-flash + v4-flash fallback
3. 逐个修改 finance / english-tutor / holo-local profile 的 fallback 从 v4-pro → v4-flash
4. holo-local 原本无 fallback，新增 deepseek-v4-flash

**验证命令**：
```bash
for p in default her-m2 finance english-tutor holo-local; do
  echo "=== $p ==="
  grep -A3 'default:' ~/.hermes/profiles/$p/config.yaml 2>/dev/null || echo "no config"
done
```

**结果**：所有 profile 统一 agnes-2.0-flash（免费）→ deepseek-v4-flash（降级）路由。

## 2026-06-19 案例：Copilot ACP 死循环重试 + 多源账单脱节

**现象**：DeepSeek 控制台报余额 ¥29 预警，近三天日均 ¥67。token_ledger 只显示 agnes 费用（¥0），账单和内部日志对不上。

**根因**：
1. **Copilot ACP 无限重试**：Cursor/Trae 通过 `copilot-acp` provider 调用 `api.deepseek.com/v1` 的 `deepseek-v4-pro`，每次 90 秒超时后重试 3 轮，每轮都扣钱。6/18 一天跑了 233 次 v4-pro 调用，187 万 input tokens。
2. **官方 DeepSeek 直连也在烧钱**：`provider=deepseek base_url=https://api.deepseek.com/v1` 报 HTTP 402 欠费。
3. **token_ledger 不完整**：它只记录 Hermes 自己跑的 agnes/cron 请求，不记录 copilot-acp 和外部 CLI 直调 DeepSeek 的账单。

**诊断命令**：
```bash
# 1. 看 token_ledger 里 v4-pro 的调用源（区分 cron vs telegram vs copilot-acp）
grep 'deepseek-v4-pro' ~/.hermes/logs/token_ledger.jsonl | python3 -c "
import sys, json
from collections import defaultdict
sources = defaultdict(int)
for line in sys.stdin:
    entry = json.loads(line.strip())
    sources[entry.get('source','?').split(':')[2][:15]] += 1
for s, c in sorted(sources.items(), key=lambda x:-x[1]): print(f'{s}: {c}')
"

# 2. 看 gateway.error.log 里的超时重试循环（最大嫌疑信号）
grep -c 'copilot-acp.*timed out\|API call failed.*attempt 3/3' ~/.hermes/logs/gateway.error.log

# 3. 看是否有无限 90s 超时重试（每次重试 = 一次 API 计费）
grep 'copilot-acp.*TimeoutError.*deepseek-v4-pro' ~/.hermes/logs/gateway.error.log | wc -l

# 4. 对比 DeepSeek 控制台账单 vs token_ledger（脱节验证）
#    如果账单 ¥67/天但 token_ledger 只有 ¥0 → 有外部调用不走 Hermes
```

**修复**：
- 禁用/停用 copilot-acp provider（如果不需要 Cursor 通过 Hermes 调度 DeepSeek）
- 暂停副官记忆仓同步（每 5 分钟的高频 cron）
- 检查 DeepSeek 官方 key 余额，隔离 billing key

## 参考

| 文件 | 说明 |
|------|------|
| `references/token-bill-diagnosis.md` | 完整诊断案例：2026-06-14 副官 token 异常（Flash 用量从 1% 飙到 78%） |
| `references/v4-flash-spike-investigation.md` | V4-Flash 用量异常的根因（`delegation.model: ''` 空字符串 bug）+ 一键修复命令 + 预防规则 |
| `references/subagent-memory-injection-overhead.md` | 2026-06-17 案例：副官记忆注入开销机制拆解（cron 无状态 + 25 skills 全加载 + episodic memory 搜索 = 98.5% 费用） |
| `references/all-profile-model-switch.md` | 全 profile 模型统一降级为 Agnes + v4-flash 的操作记录 |
| `references/copilot-acp-retry-loop.md` | 2026-06-19 案例：Copilot ACP 死循环重试导致费用暴涨的诊断全流程 |