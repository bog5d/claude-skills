# Telegram 通道诊断（Hermes 侧）

波总本机 Hermes gateway 的 Telegram 通道诊断要点。适用：手机遥控 bot 不响应、cron 投递失败、轮询周期性断连。

## 快速体检清单

```bash
# 1. bot 是否存活（走 Clash 代理调 getMe；直连会被墙）
TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" ~/.hermes/.env | cut -d= -f2-)
curl -s --max-time 10 -x http://127.0.0.1:7897 "https://api.telegram.org/bot${TOKEN}/getMe"

# 2. 出站测试（发送到波总 home channel）
curl -s --max-time 12 -x http://127.0.0.1:7897 "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d "chat_id=8447296166" -d "text=测试"

# 3. 轮询状态（gateway 日志）
tail -50 ~/.hermes/logs/gateway.log | grep '\[Telegram\]'

# 4. 授权白名单（pairing store 优先于 env allowlist）
cat ~/.hermes/pairing/telegram-approved.json
```

## 关键机制

### 1. 代理解析顺序（telegram_network.py / gateway/platforms/base.py）

`resolve_proxy_url()` 检查顺序：
1. `TELEGRAM_PROXY` 环境变量（最高优先）
2. `HTTPS_PROXY` / `HTTP_PROXY` / `ALL_PROXY`（及小写）
3. macOS 系统代理（`scutil --proxy` 自动检测）

注意：**gateway 通过 launchd 启动时没有 shell 代理环境变量**，靠第 3 步系统代理检测兜底。若 Clash 系统代理开着（127.0.0.1:7897），理论上能检测到。轮询周期性 `httpx.ConnectError`（每 2-4 小时一次、自动恢复）通常是 Clash 节点切换/抖动，不是配置错误——先看 `scutil --proxy` 是否 Enable=1 且端口正确，再决定是否显式设 `TELEGRAM_PROXY`。

### 2. 授权：TELEGRAM_ALLOWED_USERS 是 env allowlist，pairing store 是 UNION 优先路径

- 症状排查时发现 `.env` 里 `TELEGRAM_ALLOWED_USERS=501` —— **501 是 macOS UID，不是 Telegram ID**，看着像配置错误
- 但 `authz_mixin.py::_is_user_authorized` 检查顺序：平台 allow-all flag → env allowlist → **DM pairing store**（`~/.hermes/pairing/telegram-approved.json`）→ 全局 allow-all → deny
- 波总 `8447296166` 已在 pairing store 批准 → **即使 env allowlist 是错的也不影响**。不要看到 501 就改 .env 重启 gateway
- 真正的授权故障特征：日志有拒绝记录，或 pairing store 无该用户

### 3. 入站无消息 ≠ 通道坏

- 判断通道是否活着看 **gateway.log 的 [Telegram] 轮询记录**（有 restarted/conflict 都是活着）
- 8 月后无入站消息，通常是波总没发（旅行/用 desktop），不是 bot 挂了
- 出站（cron 投递 `delivered to telegram:8447296166`）正常 = 通道 OK

### 4. 测试陷阱

- **不要手动调 getUpdates**：会和 gateway 轮询冲突，日志出现 `Telegram polling conflict`，虽然会自动恢复，但会短暂干扰
- 验证出站用 sendMessage（无副作用），不要用 getUpdates
- curl 必须带 `--max-time`，直连 api.telegram.org 被墙会卡满；用 `-x http://127.0.0.1:7897` 走 Clash

## 波总环境速查

- default profile bot：`macHermes（副官）` @cosy_udbe_bot
- home channel / 波总 Telegram ID：`8447296166`（中本 笨笨）
- pairing store 路径：`~/.hermes/pairing/telegram-approved.json`
- 各 profile 有独立 bot：her-m2 / finance / english-tutor 各自 `.env` 有 TELEGRAM_BOT_TOKEN
