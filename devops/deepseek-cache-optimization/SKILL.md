---
name: deepseek-cache-optimization
description: DeepSeek 前缀缓存优化——稳定化 system prompt 前缀，最大化缓存命中率，降低 API 成本。受 DeepSeek-Reasonix 启发。
triggers:
  - "prefix cache"
  - "prefix-cache"
  - "缓存优化"
  - "cache hit"
  - "降低 API 成本"
  - "token 节省"
---

# DeepSeek 前缀缓存优化

受 **DeepSeek-Reasonix** 启发——通过稳定化 system prompt 前缀，使 DeepSeek API 的自动前缀缓存命中率从 ~30% 提升到 99%。

## 背景

DeepSeek API 自动缓存请求前缀。当前缀不变时：
- **缓存命中**：prompt_tokens 按 10% 计费（90% off）
- **缓存未命中**：prompt_tokens 全价

Hermes 的 system prompt 分三层（见 `agent/system_prompt.py`）：
```
stable   — identity, tool guidance, skills prompt       ← 极少变化（理想缓存区）
context  — context files, system_message                ← 少量变化
volatile — memory snapshot, user profile, timestamp     ← 每次变化（缓存断裂点）
```

## 优化策略

### 策略 1: 固定 skills 加载顺序

Skills 在 system prompt 中的列出顺序必须稳定。如果每次顺序不同，前缀缓存失效。

**规则**：Skills 始终按**字母序**排列，避免随机/时间序排列。

验证方法：
```bash
grep -c "skills" ~/.hermes/profiles/her-m2/logs/agent.log | tail -1
```

### 策略 2: Memory 注入位置后移

Memory 内容（记忆条目、USER.md）应该放在 system prompt **末尾**而非开头。
因为 memory 每次对话都可能变化，放在开头会打断整个前缀缓存。

**当前架构已经这样做了**——volatile tier 在最后。不要改。

### 策略 3: 对话间保持 skills 集合稳定

避免频繁创建/删除/更新 skills 文件——每次变化都会改变 system prompt 的 stable tier，
导致缓存全部失效。

**规则**：
- 新增 skill → 缓存失效一次（可接受）
- 每小时超过 3 次 skill 变更 → 缓存基本作废

### 策略 4: 监控缓存命中率

运行监控脚本：
```bash
python3 ~/.hermes/profiles/her-m2/bin/cache_monitor.py [profile_name]
```

输出示例：
```json
{
  "total_requests": 45,
  "estimated_cache_hits": 42,
  "estimated_cache_misses": 3,
  "cache_hit_rate": 93.3,
  "estimated_savings_pct": 46.7
}
```

### 策略 5: 上下文文件（AGENTS.md）缓存

如果在项目目录下有 `AGENTS.md` 或 `.cursorrules`，它们被注入到 context tier。
确保这些文件的内容在对话间保持稳定。

## 诊断

### 为什么缓存 miss？

常见原因（按可能性排序）：
1. ❌ Skills 列表顺序变了 → 固定字母序
2. ❌ Memory 内容变更 → 正常且不可避免（memory 在 volatile tier）
3. ❌ 换了 model → 不同 model 独立缓存
4. ❌ System prompt 格式变化 → 排查 agent/system_prompt.py 是否有更新
5. ❌ API key 换了 → 不同 key 独立缓存

### 测量实际命中率

DeepSeek API 在响应中**不显式标注**缓存命中，但可以反向推断：
- Token 账单中 prompt_tokens 按 10% 计费 = 缓存命中
- Token 账单中 prompt_tokens 全价 = 缓存未命中

## 与 system-watchdog 集成

system-watchdog 已有 5 分钟巡检，建议在其中加入缓存健康检查：
- 如果 24h 缓存命中率 < 50% → 告警
- 如果 skills 有 10+ 变更 → 告警

## 副官系统 (Adjutant) 缓存优化

Hermes 的副官系统 (`~/.hermes/adjutant/`) 是**独立的 DeepSeek 消费者**——它有自己的 API key (`to-hermes副官llm使用`)、自己的代码路径 (`perception.py → advisor.py → executor.py`)，与 Hermes 主对话的 `agent/system_prompt.py` 完全隔离。

**仅优化 Hermes 主对话而不动副官 = 只砍了一半的账单。**

### 副官缓存失效根因

副官的 `advisor.py` 每次调用时，上下文是 `status.json + 所有任务 + diary` 的动态拼装。任务增删/时间变化导致前缀不同 → 缓存命中→失效→命中→失效 反复横跳。即使命中率 83%，miss 的绝对金额依然惊人（miss 单价 ¥3/M vs hit ¥0.025/M，差 120 倍）。

### 优化策略

1. **固定 advisor.py 的 system prompt 前缀**：将不变部分（AGENTS.md、任务格式说明）提到最前，可变部分（status.json 内容）放到末尾
2. **批量处理而非实时**：将 advisor/executor 改为批量模式——攒 1 小时的 status.json 快照，一次 LLM 调完，而非每次 git push 触发
3. **no_agent 降级**：对纯数据任务（Zombie 检测、冲突检测、同步状态检查），用 `no_agent=true` 的 cron script 替代 LLM 调用

## 从账单 CSV 诊断缓存健康

DeepSeek 的用量账单（`amount-YYYY-M.csv`）包含 `input_cache_hit_tokens` 和 `input_cache_miss_tokens` 两个字段，可以直接计算实际缓存命中率和费用占比。

### 诊断脚本

```python
import csv

with open('amount-2026-6.csv', 'r', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

# 按天汇总
from collections import defaultdict
daily = defaultdict(lambda: {'hit': 0, 'miss': 0, 'cost_hit': 0, 'cost_miss': 0})

for r in rows:
    day = r['utc_date']
    amt = int(r['amount']) if r['amount'].strip() else 0
    price = float(r['price']) if r['price'].strip() else 0
    if r['type'] == 'input_cache_hit_tokens':
        daily[day]['hit'] += amt
        daily[day]['cost_hit'] += amt * price
    elif r['type'] == 'input_cache_miss_tokens':
        daily[day]['miss'] += amt
        daily[day]['cost_miss'] += amt * price

for day in sorted(daily):
    d = daily[day]
    total = d['hit'] + d['miss']
    rate = d['hit'] / total * 100 if total > 0 else 0
    miss_pct = d['cost_miss'] / (d['cost_hit'] + d['cost_miss']) * 100 if (d['cost_hit'] + d['cost_miss']) > 0 else 0
    print(f"{day}: hit_rate={rate:.1f}% miss_cost_pct={miss_pct:.0f}% ¥{d['cost_miss']:.2f}")
```

### 健康阈值

| 指标 | 🟢 健康 | 🟡 警告 | 🔴 危险 |
|------|---------|---------|---------|
| 缓存命中率 | >95% | 85-95% | <85% |
| Miss费用占比 | <20% | 20-50% | >50% |
| 单日总费用 | <¥5 | ¥5-20 | >¥20 |

**注意**：即使命中率 86%（看起来不低），miss 的 120 倍价格意味着 miss 费用占比可达 70%+。不要被命中率迷惑——看费用占比。

## 已知限制

- DeepSeek 不公开缓存的具体行为（存活时间、大小限制）
- 估算基于请求模式推断，非精确测量
- 缓存可能在不同 DC / 不同时间有不同行为
- 副官系统是独立消费者——缓存优化必须分别应用到每个 DeepSeek 调用入口
