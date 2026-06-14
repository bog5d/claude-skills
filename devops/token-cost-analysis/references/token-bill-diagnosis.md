# Token Bill Diagnosis Case — 副官 Flash 异常 (2026-06-14)

## 事件概述

6/1-6/7 日均 token 账单 ¥7-13。6/8 起突增到 ¥45-106/天（8-12倍）。根因：`to-hermes副官llm使用` key 的 v4-flash 用量从 1%/天 飙升到 78%/天。

## 数据事实

### 按日期输出 token 变化

| 日期 | 总输出 | Flash 输出 | Flash 占比 | Pro 输出 |
|------|--------|-----------|-----------|---------|
| 6/1 | 417,266 | 10,903 | 3% | 406,363 |
| 6/7 | 542,477 | 641 | 0% | 541,836 |
| **6/8** | **2,016,978** | **1,375,209** | **68%** | **641,769** |
| 6/9 | 4,136,431 | 3,534,631 | 85% | 601,800 |
| 6/10 | 3,273,955 | 2,657,769 | 81% | 616,186 |
| 6/11 | 3,468,577 | 3,023,257 | 87% | 445,320 |
| 6/14 | 3,214,814 | 2,389,321 | 74% | 825,493 |

### Flash 请求分析（副官 key）

| 日期 | Flash 请求数 | 每请求平均输出 | 缓存未命中 |
|------|------------|--------------|-----------|
| 6/7 | 4 | 78 | 500 |
| 6/8 | 613 | 2,205 | 6,172,372 |
| 6/9 | 1,663 | 2,124 | 18,346,260 |
| 6/14 | 1,018 | 2,347 | 11,581,678 |

Pro 每请求平均输出：250-600 tokens（正常对话范围）
Flash 每请求平均输出：2,000-2,400 tokens（**6倍**）

### 按 key 用量分布

| API Key | Flash 输出 token | Flash 请求数 | 占比 |
|---------|-----------------|------------|------|
| `to-hermes副官llm使用` | 19,525,157 | 8,875 | **95%** |
| `to-ai融资教练` | 74,505 | 75 | 0.4% |
| 其他 | 37,497 | 89 | 0.2% |

## 排查过程

### 排除路径

1. **不是 subagent** — `delegate_tool.py` 中 `effective_model = model or parent_agent.model`，parent 是 v4-pro
2. **不是 advisor cron** — 明确配置 `model: deepseek-v4-pro`，日志全是 v4-pro
3. **不是 context compression** — 压缩用的是 `agnes-2.0-flash` 走 `apihub.agnes-ai.com`，不同 key
4. **不是泄露** — key 专用、6/8 前用量极低、cache_hit 比例正常

### 定位

config.yaml 中 `delegation.model: ''`（空字符串）。当 credential pool 或 gateway 处理空字符串时可能触发自动路由。6/8 左右的行为变化（可能是 cron 配置变更或任务复杂度增加）触发了 Flash 大量调用。

### 验证方法

```bash
# 1. 确认 subagent 不走 Flash
grep "effective_model" ~/hermes/hermes-agent/tools/delegate_tool.py

# 2. 确认 advisor cron 用 Pro
grep -A5 "advisor" ~/hermes/hermes-agent/cron/ 2>/dev/null

# 3. 查 agent log 中 Flash 记录（通常无记录，因为是 gateway 层路由）
grep "v4-flash" ~/hermes/logs/agent.log

# 4. 确认 delegation 配置
grep -A5 "delegation:" ~/hermes/config.yaml
```

## 修复

```yaml
# config.yaml
delegation:
  model: 'deepseek-v4-pro'  # 不再是空字符串
```

改完后重启 gateway：
```bash
launchctl kickstart -k gui/501/ai.hermes.gateway
```

## 关键教训

- `model: ''` 空字符串在 Python `or` 中是 falsy，但在 credential pool 路由逻辑中可能被解释为"未指定→走默认"，而默认路径可能路由到 Flash
- token 账单分析必须聚合到 key + 日期 + 模型三个维度才能看到真实图景
- 单看"总量变大"没有用，必须分解看是哪个模型、哪个 key、哪天的变化
