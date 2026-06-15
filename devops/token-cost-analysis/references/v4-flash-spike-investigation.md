# V4-Flash 用量异常激增 — 根因与修复

**事件**：2026-06-14 发现副官 token 账单从 ¥7-13/天突增到 ¥45-106/天（8-12倍）。
**根因**：`config.yaml` 中 `delegation.model: ''`（空字符串），DeepSeek credential pool 将其解释为"未指定"，自动路由到 v4-flash。
**证据**：Flash 占比从 1%/天 飙到 78%/天，每请求平均输出 2,079-2,394 tokens（Pro 的 4-7 倍），95% 走 `to-hermes副官llm使用` key。
**排除**：不是 subagent（effective_model = parent.model）、不是 advisor cron（明确 v4-pro）、不是 context compression（走不同 key）、不是泄露（key 专用，6/8 前用量极低）。

## 诊断命令

```bash
# 1. 确认 delegation 配置为空字符串
grep -A5 "delegation:" ~/.hermes/config.yaml

# 2. 确认 subagent 不走 Flash
grep "effective_model" ~/.hermes/hermes-agent/tools/delegate_tool.py
# 应看到: effective_model = model or parent_agent.model

# 3. 确认 advisor cron 用 Pro
grep "advisor" ~/.hermes/cron/jobs.json 2>/dev/null | grep -i model

# 4. 查 agent log 中 Flash 记录
grep "v4-flash" ~/.hermes/logs/agent.log | head -20
```

## 修复

```yaml
# config.yaml — 将空字符串改为明确的 Pro
delegation:
  model: 'deepseek-v4-pro'
```

改完后重启 gateway：
```bash
launchctl kickstart -k gui/501/ai.hermes.gateway
curl -s localhost:8420/health
```

## 预防

- `delegation.model` 永远不要留空字符串。留空 = 给 credential pool 路由决策权，而默认路径可能走 Flash。
- 定期检查 token 账单：Flash 占比超过 20% 就要排查。
- 如果 Flash 每请求平均输出 > 1000 tokens，说明子任务输出过长，需要加 output length guard。
