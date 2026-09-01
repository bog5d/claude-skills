# 2026-09-01 Cursor/CLI agent 无法上网 — 完整诊断记录

## 用户报告
"本机无法上网，尤其是 cursor 各种 agent。无人值守全部搞好。"

## 分层诊断结果

| 层 | 检查 | 结果 |
|----|------|------|
| L1 本地网络 | ping 网关 / 百度直连 | ✅ 0% 丢包，百度 200 (0.16s) |
| L2 系统代理 | scutil --proxy | ✅ HTTP/HTTPS/SOCKS 全 127.0.0.1:7897 |
| L3 Cursor 配置 | settings.json + 日志 | ❌ Cursor 用残留端口 7890 |
| L3 CLI agents | env \| grep proxy | ❌ 终端零代理变量，直连被墙 |
| L4 机场 | Google/GitHub/X vs OpenAI | ⚠️ 前三个通，AI 三个全超时 |

## 根因 A：Cursor 缓存旧代理端口

Cursor 日志（`~/Library/Application Support/Cursor/logs/<ts>/`）：
```
Error fetching user privacy mode: [internal] Failed to establish a socket connection
to proxies: PROXY 127.0.0.1:7890
```
- Clash 实际监听 7897（`lsof -nP -iTCP:7897 -sTCP:LISTEN` 确认）
- `verge.yaml` 里 `verge_mixed_port: 7890` 是 UI 元数据残留（运行时 `clash-verge.yaml` 是 7897）
- Cursor 的 `state.vscdb` / storage 缓存了旧端口，settings.json 无显式代理

**修复**（已执行）：
1. 备份 `settings.json` → 写入：
   ```json
   {"window.autoDetectColorScheme": false,
    "http.proxy": "http://127.0.0.1:7897",
    "http.proxyStrictSSL": false,
    "http.proxySupport": "override"}
   ```
2. 优雅重启：`osascript -e 'tell application "Cursor" to quit'` → 等 5s → `open -a Cursor`
3. 验证：重启后 Cursor 新日志目录不再有 7890 错误 ✅

## 根因 B：CLI agents 无代理环境变量

- `codex`、`claude`、`aider`、`cursor-agent` 都只读环境变量，不读 macOS 系统代理
- 实测直连 `api2.cursor.sh` / `api.openai.com` → 000 timeout（被墙）
- `~/.zshrc` 原本零代理配置

**修复**（已执行）：`~/.zshrc` 追加完整代理块（见 SKILL.md L3-B），备份 `.bak-hermes-proxy`。新终端生效。

## 残留：机场 IP 池被 AI 厂商封

修复 L3 后仍超时：Google/GitHub/X/DeepSeek 走代理全通，但以下三个超时：
```
❌ api2.cursor.sh     ❌ api.openai.com     ❌ api.anthropic.com
```
- 结论：hellobog 机场全部 3 个节点（BWG-CN2-Reality / CDN-Backup / VIP-Reality-救命节点）出口 IP 被 AI 厂商 TCP 层封锁
- 2026-07-29 同机场是 403 (cf-mitigated)，2026-09-01 恶化到 000 timeout
- 配置层面无解 → 需要换订阅/机场
- 待办（用户决策）：更新订阅拿新 IP / 换机场 / 先不管（DeepSeek、GitHub、Telegram 正常）

## 工具教训

- terminal 前台 curl 卡满超时会被系统 BLOCK（"Command timed out without user response"）→ 用 `execute_code` + subprocess 带 `--max-time`，或单条短超时
- unix socket 读 Clash API：`curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/proxies` 可用，但返回体可能有 HTTP 噪音，python 从第一个 `{` 截取再 json.loads
- Clash API 切换组节点：PUT `/proxies/<urlencoded组名>` body `{"name": "节点名"}`；URLTest 组可能自动回切，属正常
- `pgrep -x Cursor` 主进程 PID 单一；`ps aux | grep [C]ursor` 有大量 Helper 进程（extension-host / mcp-process），不要全杀
