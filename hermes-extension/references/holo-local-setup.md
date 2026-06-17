# Holo-Local 本地模型 Telegram 集成

**日期**: 2026-06-17
**场景**: Mac 本地跑了 llama-server，需要让 Telegram bot 也能对话

## 环境

- **模型**: mradermacher/Holo-3.1-4B-GGUF (Q4_K_M quantization)
- **服务端**: llama-server 监听 http://127.0.0.1:8080
- **管理方式**: launchd agent `ai.holo.local.llama`
- **启动脚本**: `~/hermes/scripts/start-holo-local-llama.sh`
- **API 端点**: `http://127.0.0.1:8080/v1/chat/completions`

## 验证步骤

```bash
# 1. 确认进程在跑
ps aux | grep llama-server

# 2. 确认 launchd 状态
launchctl list | grep holo

# 3. 测试 API 响应
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Holo-3.1-4B.Q4_K_M.gguf",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

## Telegram 集成步骤

1. 从 @BotFather 创建新 bot，获取 token
2. 在 holo-local profile 的 config.yaml 中添加 Telegram bot 配置
3. 绑定 bot 到 holo-local profile
4. 重启 gateway

**注意**：holo-local profile 不会自动出现在 Telegram gateway 的 bot 列表中，需要手动添加 bot token 和 profile 绑定。
