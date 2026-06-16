# 副官记忆注入开销机制拆解

**日期**：2026-06-17
**问题**：副官 cron job 消耗 98.5% 总费用

## 注入层解剖

每次副官 cron 触发（无状态 session），系统注入以下上下文：

| 层 | 内容 | 大小 |
|----|------|------|
| ① AGENTS.md | 副官系统操作手册 | 9KB (~2,300 tokens) |
| ② 25个 Skills | 全部 SKILL.md 全文 | ~500KB+ (~125K tokens) |
| ③ Episodic Memory | EverOS/tencentdb 搜索结果 | 每次 30-100 条 (~50K tokens) |
| ④ MEMORY.md | 持久记忆（偏好/凭证/状态） | ~5KB (~1,250 tokens) |
| ⑤ 任务文件 | status.json + diary + prep | ~10KB (~2,500 tokens) |
| **合计** | | **~200K tokens/次** |

## 触发频率

- 感知引擎：每 5 分钟 `perception.py --once`
- 每天 ~288 次 × 30 天 = 8,640 次/月
- 每次 ~200K tokens × 0.000006 元/tokens(v4-pro) = ¥1.2/次
- 月预估 ¥10,368（实际更低因 cache hit 高，但纯 output token 仍昂贵）

## 实际费用

- 6 月 1-14 日：¥375.41（日均 ¥26.81）
- 副官 key `to-hermes副官llm使用`：¥369.97（98.5%）
- v4-pro output：8,729,778 tokens
- cache hit 比例高（数十亿级），但每次 cache miss 的 input 本身就贵

## 跨 profile 差异

| Profile | 触发方式 | 频率 | 主要费用 |
|---------|---------|------|---------|
| her-m2 | 用户主动触发 | 按需 | 低 |
| default（副官） | cron 每5分钟 | 8,640次/月 | 98.5% |

## 优化方案

1. **模型降级**：副官 cron 切 v4-flash，3x 单价优势
2. **Skill 白名单**：cron job 只加载需要的 3-4 个 skill，不加载 25 个
3. **Memory 搜索裁剪**：限制只搜最近 7 天的 episodic memory
4. **降低频率**：感知引擎 5min → 15-30min

## 诊断命令

```bash
# 列出所有 LLM-driven cron jobs
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
