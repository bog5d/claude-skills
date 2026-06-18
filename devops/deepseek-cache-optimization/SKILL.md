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

### 策略 6: 外部脚本的 system/user 双消息模式

如果你在维护**直接调 DeepSeek API 的脚本**（不在 Hermes 的 system_prompt.py 体系内），典型症状是只发一个 `user` 消息——前缀缓存基本作废。

**修复模式**：
1. 抽取脚本中永不变化的部分 → 定义为 `SYSTEM_PREFIX` 常量（200+ 字符，放角色定义、职责说明、输出格式要求）
2. 将 API 调用从 `[{"role": "user", "content": ...}]` 改为 `[{"role": "system", "content": SYSTEM_PREFIX}, {"role": "user", "content": ...}]`
3. ⚠️ **不要在 SYSTEM_PREFIX 中放日期、文件路径、任务列表等动态内容**——任何变化都会让缓存锚点断裂

**验证命令**：搜索代码库中所有直接调 API 的地方
```bash
rg -n 'deepseek|openai|chat\.completions|/v1/chat' /path/to/project/
```

## 诊断

### 🔍 第一步：审计「谁在调 LLM」

**铁律**：永远不要信任任何来源（诊断报告、记忆、之前的你自己）关于"X 调用 LLM"的结论。用 grep 验证。

```bash
# 对目标项目做全量审计
rg -n 'deepseek|openai|chat\.completions|/v1/chat|llm' /path/to/target/repo/
# 如果结果为空 → 这个项目不直接调 LLM，优化方向不在 API 层
# 如果有结果 → 只改这些文件，不要动其他文件
```

**常见误判**：
- 编排脚本（如 `perception.py`）只是串联其他脚本，不自己调 LLM
- 规则引擎（如 `advisor.py`）只是 if/else + JSON 输出，不调 LLM
- 错误归因会导致在错误的文件上浪费时间，而真正的消费者没被优化

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

Hermes 的副官系统 (`~/.hermes/adjutant/`) 是**独立的 DeepSeek 消费者**，与 Hermes 主对话的 `agent/system_prompt.py` 完全隔离。**仅优化 Hermes 主对话而不动副官 = 只砍了一半的账单。**

### ⚠️ 先验证再优化——不要相信诊断报告

**铁律**：任何诊断报告、记忆条目甚至你自己的推测中声称"X 脚本调用 LLM"的结论，都必须在动手修改前**用 grep 验证**。本次会话就是教训——初始诊断报告称 `advisor.py` 和 `perception.py` 调用 DeepSeek，但实际上：

- `advisor.py` — 纯规则引擎，125 行，零 LLM 调用
- `executor.py` — 纯规则引擎，65 行，零 LLM 调用
- `perception.py` — 纯编排引擎，818 行，零直接 LLM 调用
- **`night_shift.py` — 唯一的 LLM 消费者**，通过 `llm_fill()` 直接请求 `api.deepseek.com/v1/chat/completions`

**审计命令**（永远先跑这行）：
```bash
rg -n 'deepseek|openai|chat\.completions|llm' ~/.hermes/adjutant/repo/hermes-adjutant/scripts/
```

### 副官 LLM 架构

- `scripts/night_shift.py`：唯一直接调 DeepSeek 的脚本。使用 `DEEPSEEK_API_KEY` 从 `.env` 加载。`llm_fill()` 组装 prompt → POST `https://api.deepseek.com/v1/chat/completions` → 解析返回
- `scripts/perception.py`：编排脚本（git pull + 调 advisor/executor + synclog_agent_llm），不自己调 LLM
- `scripts/advisor.py`、`scripts/executor.py`：纯规则引擎（if-else 逻辑 + JSON 输出）

### 副官缓存优化（针对 night_shift.py）

#### 技术：稳定前缀 + system/user 双消息模式

`night_shift.py` 的原始实现将所有内容拼成单个 `user` role 消息——DeepSeek 没有 system 消息做缓存锚点，前缀缓存命中率极低。

**修改方案**：注入一个固定不变的 `SYSTEM_PREFIX` 作为 system role 消息，动态内容放在 user role 消息中。

```python
# 在 night_shift.py 顶部定义（永不变化 = 每次调用缓存命中）
SYSTEM_PREFIX = """你是 Hermes 副官系统的夜间摘要生成器（Night Shift）。

你的职责：
1. 分析当天的任务状态变化（status.json）
2. 识别需关注的风险项（超期任务、冲突、僵尸任务）
3. 生成结构化的每日摘要报告

输出格式：Markdown，含状态表格和风险清单。
上下文中的任务 ID 和文件名仅作参考，不会改变你的职责定义。
"""

# 在 llm_fill() 中：system 消息在前（缓存锚点），user 消息在后（动态内容）
def llm_fill(prompt_text):
    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM_PREFIX},   # ← 缓存锚点
                {"role": "user", "content": prompt_text},       # ← 动态内容
            ],
        },
    )
```

**为什么 system 消息是好的缓存锚点**：DeepSeek 的前缀缓存从 messages[0] 开始匹配。system 消息固定不变 → 每次请求的前 200+ tokens 相同 → 缓存命中。user 消息（动态任务列表）在 system 之后，不破坏前缀。

#### 同样规则适用于任何直接调 DeepSeek API 的脚本

如果你在项目中发现类似 `llm_fill()` 的函数（只有一个 user 消息），套用相同模式：
1. 抽取固定文本到 `SYSTEM_PREFIX` 常量
2. 改为 `[system, user]` 双消息格式
3. 确保 system 消息的内容永远不变（不要塞日期、不要塞动态状态）

### 非 LLM 脚本的降级策略（用于 cron 优化）

对于 `advisor.py`、`executor.py` 这类纯规则引擎脚本，它们在 cron 中通过 Hermes agent 运行时仍然消耗 token（Hermes agent 本身会调 LLM）。两种降级方案：

1. **`no_agent: true`**：如果 cron job 只是跑脚本、收集输出，不需要 AI 推理 → 在 cronjob 设置中启用 `no_agent=true`，完全跳过 LLM
2. **直接 cron/launchd**：如果脚本不需要 Hermes 环境，直接用系统 cron 或 launchd 调度，绕过 Hermes 的 agent 循环

### 参考

- **`references/adjutant-night-shift-pattern.md`** — night_shift.py 的完整优化实录，含修改前后的代码对比和验证命令

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
