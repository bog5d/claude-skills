# Profile .env 重建指南

## 何时需要

Profile 的 `.env` 文件被意外覆盖、删除或损坏时。

## 重建步骤

### 1. 基底复制

```bash
cp /Users/mac/.hermes/.env /Users/mac/.hermes/profiles/<profile>/.env
```

全局 `.env` 通常已包含：
- `DEEPSEEK_API_KEY`
- `EVEROS_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `API_SERVER_KEY`
- `TELEGRAM_ALLOWED_USERS`

### 2. 追加 Profile 特定 Key

```bash
# GITHUB_TOKEN（如果 profile 需要 git 操作）
echo 'GITHUB_TOKEN=*** >> /Users/mac/.hermes/profiles/<profile>/.env

# SUDO_PASSWORD（如果需要 sudo）
echo 'SUDO_PASSWORD=*** >> /Users/mac/.hermes/profiles/<profile>/.env
```

### 3. 验证

```bash
# 列出所有 key
grep -o '^[A-Z_]*=' /Users/mac/.hermes/profiles/<profile>/.env | sort

# ⚠️ 关键：确认 Telegram bot 不和其他 profile 冲突
# 所有 gateway 共用同一 TELEGRAM_BOT_TOKEN 会导致 polling conflict（见 Mode Q）。
# 用此脚本确认每个 profile 使用独立 bot（token 从文件读，不在代码中明文出现）：

python3 /Users/mac/.hermes/profiles/english-tutor/skills/devops/hermes-service-troubleshooting/references/check-bot-tokens.py

# 预期：三个 profile 的 @username 必须全部不同，且无 FAIL
```

### 4. 重启 Gateway

```bash
pkill -f "<profile>.*gateway" 2>/dev/null
bash -c 'ulimit -n 4096 && hermes --profile <profile> gateway run --replace'
```

### 5. 确认平台连接

```bash
sleep 10 && tail -15 <profile>/logs/gateway.log | grep -E 'connected|failed'
```

预期输出应包含：
```
✓ api_server connected
✓ telegram connected
Gateway running with 2 platform(s)
```

## 关键 Pitfall

- Profile `.env` **不会** fallback 到全局 `.env`。每个 key 必须显式存在于 profile `.env` 中
- Telegram Bot Token **必须唯一** — 两个 profile 共用同一 token 会导致 polling conflict
- **不要**用 `write_file` 覆盖 `.env`（已知 argument corruption bug #15236）
- 如果 profile 之前有独立的 Telegram bot（非全局 @cosy_udbe_bot），需从历史记录找回原始 token
