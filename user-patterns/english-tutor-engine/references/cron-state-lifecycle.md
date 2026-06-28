# Cron 推送 vs 实时答题 — State 生命周期问题

## 问题

每日词汇挑战 cron job（no_agent 模式）运行 `fast_vocab_round.py`，该脚本：
1. 生成 `state/vocab_escalating.json`（含 round_words + wanted_list）
2. 输出挑战消息给用户
3. cron 结束后 state 文件被清理/归档

用户几小时后看到消息并回答时，`session_pipeline.py` 找不到 state 文件，报错：
```
"route_error": true,
"message": "没有待判分题目。请先发送「来一局」生成新题。"
```

## 临时应对

```bash
# 1. 重新生成当前题局
python3 /Users/mac/.hermes/profiles/english-tutor/bin/fast_vocab_round.py

# 2. 用户答新题（词表变了，旧答案不匹配）
# 3. 调用 pipeline 判分
python3 /Users/mac/.hermes/profiles/english-tutor/state/session_pipeline.py 1 '{"word1":"答案",...}'
```

## 推荐修复方向

### A) Cron 只发提醒，不出题
Cron 消息仅提示「该刷词了」，用户主动说「来一局」触发 real-time 出题。这样 state 文件在用户响应时实时存在。代价是延迟增加一次 terminal 调用。

### B) Cron 保留 state 文件
修改 `fast_vocab_round.py`：在 no_agent cron 模式下，发完消息后不清理 `vocab_escalating.json`，保留到当天结束或用户首次交互后再归档。

### C) Cron 输出完整 state 供 LLM 重建
Cron 输出中包含 JSON 格式的完整 state 信息，LLM 可从对话中重建 state 文件后调用 pipeline。较复杂且依赖 LLM 正确解析。

## 必检清单

每次用户提交答案前：
- [ ] `state/vocab_escalating.json` 存在？
- [ ] 不存在 → 先 run `fast_vocab_round.py` 再 pipeline
- [ ] 存在 → 对比 round_words 与用户答案的键是否匹配
