# Telegram 手机遥控通道诊断（2026-08-10 实测）

用户通过手机 Telegram 遥控 Hermes 长期记忆/人脉 agent 时的完整诊断链路。所有结论均实测验证。

## 诊断速查表

| 检查项 | 命令/方法 | 预期 |
|---|---|---|
| Bot 存活 | `curl -x http://127.0.0.1:7897 .../getMe`（走代理） | `ok:true` + username |
| 出站（我→手机） | python urllib 走代理 sendMessage | ok:true + message_id |
| 入站（手机→我） | 日志搜 `inbound message: platform=telegram` | 应有近期记录 |
| 授权 | `~/.hermes/pairing/telegram-approved.json` | 波总 ID 8447296166 在册 |
| 代理 | `resolve_proxy_url("TELEGRAM_PROXY")` | 返回 `http://127.0.0.1:7897` |
| 轮询 | 日志搜 `\[Telegram\]` | 周期抖动会自恢复 |

## 关键知识点

### 1. 授权是 pairing store 优先（env allowlist 是坑）

- 检查顺序：per-platform allow-all → env allowlist → **DM pairing 白名单** → global allow-all → deny。
- `pairing/telegram-approved.json` 里已批准的用户**绕过** `TELEGRAM_ALLOWED_USERS`。
- 陷阱：`TELEGRAM_ALLOWED_USERS=501` 是 macOS UID（`id -u mac`），不是 Telegram ID（9~10 位）。pairing 已批准时 501 不影响使用，但配对丢失会锁死所有人——是定时炸弹。

### 2. 代理解析顺序（Hermes 原生支持）

`resolve_proxy_url(platform_env_var)` 检查顺序：
1. `TELEGRAM_PROXY`（最高优先，支持 http/https/socks5）
2. `HTTPS_PROXY` / `HTTP_PROXY` / `ALL_PROXY`（大小写变体）
3. macOS 系统代理 `scutil --proxy` 自动检测

macOS 系统代理开着（Clash 7897）时，即使 launchd plist 无代理环境变量，轮询也会自动走系统代理——`ps eww <pid> | grep -i proxy` 为空 ≠ 没走代理。

配置入口：config.yaml `telegram.proxy_url`（adapter 启动时写入 `TELEGRAM_PROXY` env）。

### 3. 轮询周期性抖动（每 2~4 小时一次）≠ 故障

- 日志特征：`polling degraded (heartbeat probe)` → `network error (attempt 1/10)` → `restarted after network error (attempt 1)`，间隔 2~4 小时，自动恢复。
- 根因：Clash `AI服务` 组是 url-test 类型，节点切换瞬间切断长轮询连接。**不是根本性故障**，不要误判 bot 死了。

### 4. ⚠️ 陷阱：不要手动调 getUpdates 测试（会打断轮询）

- Telegram 只允许一个 getUpdates 长轮询会话。手动 `curl .../getUpdates` 会与 gateway 轮询冲突：
  ```
  Telegram polling conflict (1/5) — previous session still held open on Telegram's servers.
  Error: Conflict: terminated by other getUpdates request
  ```
- gateway 会自动恢复（等待 20s + 重试），但造成短暂中断。
- 正确验证出站：用 `sendMessage`（不影响轮询）；验证入站：让用户回一条消息 + 看日志。

### 5. curl 走 Clash 代理会卡住超时 → 用 python urllib

实测：`curl -x http://127.0.0.1:7897 api.telegram.org` 有时挂起（terminal 超时被 BLOCKED）。改用 python urllib 带严格 timeout 更可靠：

```python
import urllib.request, urllib.parse, json
proxy = "http://127.0.0.1:7897"
url = f"https://api.telegram.org/bot{token}/sendMessage"
data = urllib.parse.urlencode({"chat_id": "8447296166", "text": "测试"}).encode()
opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
req = urllib.request.Request(url, data=data)
with opener.open(req, timeout=10) as resp:
    d = json.loads(resp.read().decode())
    print(d.get('ok'), d.get('result', {}).get('message_id'))
```

## 手机遥控完整验证流程

1. `getMe` 走代理 → bot 存活
2. 检查 pairing store → 波总已授权
3. `sendMessage` 走代理 → 手机收到测试消息（出站 OK）
4. 让用户手机回一条 → 日志出现 `inbound message: platform=telegram user=中本 笨笨`（入站 OK）
5. 若长时间无入站记录：要么用户没发，要么轮询断了；看 gateway.log 最近的 `[Telegram]` 时间戳判断

## 关联

- Clash 侧规则：`DOMAIN-SUFFIX,telegram.org,AI服务`（url-test 组），节点切换导致抖动
- 人脉/记忆 agent 场景：用户通过 Telegram 遥控时先跑本表诊断，别一上来就怀疑仓库或授权
