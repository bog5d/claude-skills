---
name: macos-network-proxy-troubleshooting
title: macOS 网络/代理分层排查（AI 工作站）
description: "Use when 本机无法上网、Cursor/CLI agent 连不上、AI 站点超时。分层排查代理与封禁。"
version: 1.0.0
author: Hermes curator
license: MIT
metadata:
  hermes:
    tags: [network, proxy, clash, cursor, troubleshooting, macos]
    related_skills: [clash-verge-management, hermes-service-troubleshooting]
trigger: "User reports '无法上网'、'Cursor 连不上'、'agent 全部失败'、'ChatGPT/Claude 打不开'、'bot 没反应'"
---

# macOS 网络/代理分层排查（AI 工作站）

## When to Use

- 用户报告"无法上网"、"Cursor/各种 agent 连不上"、"AI 站点打不开/超时"、"bot 没反应"
- 需要区分：本地网络断、代理配置错、还是机场 IP 被 AI 厂商封禁

## 核心原则

**先分层，再动手。** 每次"上不了网"都按下面 4 层从底向上实测，用 curl 给出证据，不要一上来就重启 Clash/gateway。

```
L1 本地网络  → 网关 ping + 百度直连
L2 系统代理  → scutil --proxy + 代理连 Google
L3 应用配置  → Electron 缓存端口 / CLI 环境变量
L4 机场 IP  → AI 厂商封禁（403 或 000）
```

## L1+L2：快速摸底（30 秒）

```bash
# 本地网络
ping -c 2 -W 2 192.168.1.1          # 网关（看路由表实际网关）
curl -s -o /dev/null -w '%{http_code} %{time_total}s' --connect-timeout 5 https://www.baidu.com

# 系统代理状态（Clash Verge 通常 127.0.0.1:7897）
scutil --proxy | grep -E 'Enable|Port|Proxy'

# 代理连通性（走 Clash 混合端口）
curl -s -o /dev/null -w '%{http_code} %{time_total}s' --connect-timeout 8 -x http://127.0.0.1:7897 https://www.google.com
```

**判读**：
- 百度 200 + 网关通 → L1 OK
- scutil 显示 7897 + Google 走代理 200 → L2 OK，问题在 L3/L4

## L3：应用层——两个高频根因

### A. Electron 应用（Cursor/VSCode）缓存了旧代理端口

- 症状：Cursor 日志 `Failed to establish a socket connection to proxies: PROXY 127.0.0.1:7890`，但 Clash 在 7897
- 根因：`clash-verge.yaml`（运行时）与 `verge.yaml`（UI 元数据 `verge_mixed_port`）端口不一致，应用缓存了旧值
- 修复：
  1. 确认实际监听：`lsof -nP -iTCP:7897 -sTCP:LISTEN` 或 netstat
  2. 给应用写显式代理覆盖缓存：Cursor `~/Library/Application Support/Cursor/User/settings.json` 加
     `"http.proxy": "http://127.0.0.1:7897"`, `"http.proxyStrictSSL": false`, `"http.proxySupport": "override"`
  3. 优雅重启应用（`osascript -e 'tell application "Cursor" to quit'`，等 5 秒，`open -a Cursor`）
  4. 修正 `verge.yaml` 的 `verge_mixed_port` 与运行时一致，防 UI 回写错误端口
- 改配置前先备份（`.bak-时间戳`）

### B. CLI agents（codex/claude/aider/cursor-agent）不读 macOS 系统代理

- 症状：终端里各种 agent 直连被墙（000 timeout），但浏览器正常
- 根因：CLI 工具只读环境变量，不读 `scutil --proxy`。系统代理只管 GUI 应用
- 修复：`~/.zshrc` 追加（NO_PROXY 必须带本地段，否则本地服务全挂）：
  ```bash
  export https_proxy="http://127.0.0.1:7897"
  export http_proxy="http://127.0.0.1:7897"
  export all_proxy="socks5://127.0.0.1:7897"
  export HTTPS_PROXY="http://127.0.0.1:7897"
  export HTTP_PROXY="http://127.0.0.1:7897"
  export ALL_PROXY="socks5://127.0.0.1:7897"
  export NO_PROXY="localhost,127.0.0.1,::1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,100.64.0.0/10,*.local"
  export no_proxy="$NO_PROXY"
  ```
- 新终端生效；已开终端重开

## L4：机场 IP 被 AI 厂商封禁

**快速判别**：Google/GitHub/X/DeepSeek 走代理都通，唯独 openai.com / anthropic.com / cursor.sh 超时 → 机场 IP 池被 AI 厂商封，**配置层面无解**。

- `403 (cf-mitigated: challenge)` = WAF 挑战拦截（连接能建立）
- `000 / connect timeout` = TCP 层封锁（连接建立不了）——比 403 更深，且会随时间恶化（hellobog 2026-07-29 是 403，2026-09-01 变 000）
- 同订阅商所有节点共享 IP 声誉，全被封（BWG/VIP/CDN 三个节点一个跑不掉）
- 解法（三选一）：浏览器过 CF 验证（临时）→ 更新订阅拿新 IP → 换机场
- 排查时不要循环 curl 同一域名（长超时会卡住工具调用），用 `--max-time` 控制，或改用 python urllib + ProxyHandler 严格超时

## Telegram bot 不响应（Hermes 侧）

见 `references/telegram-channel-diagnostics.md`（含 bot 存活检测、代理解析顺序、TELEGRAM_ALLOWED_USERS 陷阱、getUpdates 冲突警告）。

## 完整案例

见 `references/2026-09-01-cursor-cli-proxy-fix.md`（Cursor 7890 端口缓存 + CLI 无代理 + hellobog 机场被封的完整诊断与修复记录）。

## Pitfalls

- 排查顺序永远 L1→L4，用 curl 实测每一层，证据驱动，别一上来就重启服务
- curl 直连被墙域名会卡满超时（默认无上限）——所有连通性测试必须带 `--connect-timeout` 和 `--max-time`
- `execute_code` 里 subprocess 调 curl 带超时比 terminal 前台更可控（terminal 里卡住会被系统拦成 BLOCKED）
- 改任何配置前备份；Electron 应用改 settings.json 后必须重启才生效
- 代理环境变量必须带 NO_PROXY 本地段，否则 Hermes API server (127.0.0.1:8642)、Ollama (11434)、dashboard (9119) 全部走代理连不上自己
