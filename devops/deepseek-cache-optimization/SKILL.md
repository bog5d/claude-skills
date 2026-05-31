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

## 已知限制

- DeepSeek 不公开缓存的具体行为（存活时间、大小限制）
- 估算基于请求模式推断，非精确测量
- 缓存可能在不同 DC / 不同时间有不同行为
