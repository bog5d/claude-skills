# Pipeline 路由自检：LLM 角色最小化

## 问题背景

2026-06-18 真实事故：LLM 连续多轮手写判分，`session_pipeline.py`（925行完整流水线）一次都没被调用。

## 系统架构（正确姿势）

```
「来一局」→ fast_vocab_round.py → relay stdout 原样
「答题」  → session_pipeline.py  → relay _formatted 原样
LLM 角色 → 仅 JSON 格式纠错 + pipeline 报错时诊断（≤15%）
```

## LLM 自检清单

每当我发现自己要做以下事情，立即停止并输出「⚠️ 路由异常，需要调用脚本」：

| 手写行为 | 正确做法 |
|---------|---------|
| 手写 Round 1/3、全局限 27 词 | fast_vocab_round.py 默认 12 词 6→6 |
| 手写 📝 填空 | 脚本不输出填空，不手写 |
| 手写 ✅/❌ 判分 | session_pipeline.py 的 _formatted 已含 |
| 手写五层讲解 | session_pipeline.py 自动生成 |
| 手写 📊 全局总结 | session_pipeline.py 的 _formatted 已含 |
| 手写 🎯 升级判定 | engine_upgrade_sample_descent.py |

## session_pipeline.py 调用方式

```bash
python3 /Users/mac/.hermes/profiles/english-tutor/state/session_pipeline.py <round_number> '<json_answers>'
```

输入：`<round_number>` 是 1/2/3，`<json_answers>` 格式：
```json
{"1": "稳定的", "2": "可持续的", "3": "替代", "4": "机构", "5": "赌博", "6": "积累"}
```

输出：JSON 对象，含 `_formatted` 字段（Telegram-ready markdown）。LLM 直接 relay `_formatted`，不修改不补充。

## 降级模型说明

降级计数器 `_failed_sample_count` 由 `session_pipeline.py` → `gamification_v2.update_after_session()` 自动更新。LLM 手动判分不会递增此计数器，导致降级永不触发。

## 恢复步骤（当发现绕开过 pipeline 后）

1. 运行 `python3 bin/engine_upgrade_sample_descent.py` 检查段位一致性
2. 如有 sub_rank 显示 bug（青铜青铜I），手动修复 `state/gamification.json`
3. 手动设置 `_failed_sample_count` 为 0（重置降级计数）
4. 后续所有答题严格走 pipeline
