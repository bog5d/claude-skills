---
name: hermes-gateway-monitoring
description: 为 Hermes Gateway 部署零 AI 消耗的系统监控——启动通知、关闭预告、崩溃告警、定时状态报告。纯 Bash + Python + Telegram Bot API + Launchd。
---

# Hermes Gateway 监控系统 v2

## 触发条件
- 用户问"怎么监控 gateway 状态"、"重启了不知道"、"系统像黑盒"
- 需要部署 gateway 启动通知 / 关闭预告 / 定时状态报告
- 新增 profile 需要监控覆盖
- 用户想让监控报告增加维度（模型、错误分类、Provider 健康等）

## 核心原则

> **零 AI 消耗，零内存负担。** Bash 调度 + Python 报告生成 + `curl` 调用 Telegram Bot API。绝不经过任何 LLM。

## 架构

```
监控系统
├── hermes-monitor.sh      ← 入口脚本（命令路由 + 通知发送）
├── monitor_report.py      ← 报告生成引擎（Python，含 YAML/JSON/ps/curl）
├── Launchd plist           ← 定时状态报告（默认 4 小时）
└── 命令行入口               ← startup / shutdown / crash / report / status / watch
```

## 报告维度（v2 新增）

| 维度 | 来源 | 说明 |
|------|------|------|
| 🧠 模型信息 | `config.yaml` | 主模型 + provider + fallback |
| 📊 会话数 | `sessions/*.json` 文件计数 | 每个 profile 存了多少会话 |
| 💾 磁盘占用 | `du -sh logs/ sessions/` | 分开统计 |
| ⚠️ 错误分类 | `gateway.error.log` (最近1h) | API/连接/工具/超时/基础设施/其他 6类 |
| 🌐 Provider 连通性 | `curl <base_url>/models` | 实时检测每个 API provider 是否可达 |

## 部署步骤

### 1. 部署脚本

**入口脚本**：`~/.hermes/profiles/<profile>/bin/hermes-monitor.sh`
参考：`references/hermes-monitor.sh`（完整脚本）

**报告引擎**：`~/.hermes/profiles/<profile>/bin/monitor_report.py`
参考：`references/monitor_report.py`

**关键配置点**：
- 所有路径 **必须用绝对路径**（Hermes 运行时会重写 `$HOME`）
- `VENV_PYTHON` 指向 hermes-agent 的 venv python（确保能 `import yaml`）
- `TELEGRAM_BOT_TOKEN`: 从 profile 的 `.env` 读取
- `CHAT_ID`: 从 profile 的 `channel_directory.json` 自动发现

### 2. 创建 Launchd 定时任务

plist 位置：`~/Library/LaunchAgents/com.hermes.monitor.plist`

```xml
<key>ProgramArguments</key>
<array>
    <string>/bin/bash</string>
    <string>/Users/mac/.hermes/profiles/her-m2/bin/hermes-monitor.sh</string>
    <string>report</string>
</array>
<key>StartInterval</key>
<integer>14400</integer>  <!-- 4小时 -->
<key>RunAtLoad</key>
<true/>
```

加载：`launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hermes.monitor.plist`

### 3. 集成到 gateway 启动流程

创建 `start-gateway.sh` wrapper，在 gateway 启动前后发送通知：

```bash
MONITOR_SCRIPT="${HOME}/.hermes/profiles/her-m2/bin/hermes-monitor.sh"
"$MONITOR_SCRIPT" startup "$PROFILE_NAME" &   # 启动通知（异步）
trap '"$MONITOR_SCRIPT" shutdown "$PROFILE_NAME" 30' EXIT  # 关闭预告
exec python3 -m hermes_cli.main --profile "$PROFILE_NAME" gateway run --replace
```

## 命令参考

| 命令 | 用途 | Telegram 通知 |
|------|------|:---:|
| `status` | 控制台输出状态报告 | 否 |
| `report` | 发送完整状态报告 | ✅ |
| `startup <profile> [pid]` | 发送启动通知 | ✅ |
| `shutdown <profile> [delay]` | 发送关闭预告 | ✅ |
| `crash <profile>` | 发送崩溃告警 | ✅ |
| `watch` | 持续监控进程变化 | 变化时 ✅ |

## 已知坑位

### 1. Default profile 的 PID 文件位置特殊
- her-m2 / english-tutor 的 PID 文件：`~/.hermes/profiles/<name>/gateway.pid`
- **default profile 的 PID 文件**：`~/.hermes/gateway.pid`（根级别，不在 `profiles/default/` 下）
- 如果不处理这个特殊路径，default gateway 永远被报告为"停止"

### 2. 不要用 `launchctl list` 的 exit code 判断运行状态
- `launchctl list` 显示的 exit code 是 **上一次退出时的状态**，不是当前状态
- 例如 exit code -9 只表示上次被 SIGKILL，但当前进程可能已经重启且正常运行
- **正确做法**：用 `kill -0 <PID>` 或 `ps -p <PID>` 验证进程是否存活

### 3. PID 文件是 JSON 格式
`gateway.pid` 不是纯数字，而是 JSON：`{"pid": 98717, "kind": "hermes-gateway", ...}`
→ 必须用 `python3 -c "import json; ..."` 解析，不能用 `cat | grep`

### 4. Bash 生成复杂报告容易出 bug
当报告内容包含换行符、管道符(`|`)等时，bash 的字段分隔解析极易出错。
→ **v2 方案**：用 Python 脚本 `monitor_report.py` 生成报告，bash 只负责调度和发送

### 5. `$HOME` 被重写
Hermes gateway 运行时会改变 `$HOME` 环境变量，导致相对路径错误。
→ **全部使用绝对路径**：`/Users/mac/.hermes/...`

### 6. Telegram API 发送消息的格式
- 使用 `parse_mode=Markdown`，特殊字符需转义
- `_` 和 `*` 在消息中会被 Markdown 解析，wrap 内容用反引号

### 7. ⚠️ 不要用 HardResourceLimits → RSS（macOS 不支持）
macOS launchd 的 `HardResourceLimits` **不支持** `RSS` 键。加了会导致 `launchctl bootstrap` 报 `Input/output error` 且进程无法启动。
→ **替代方案**：system-watchdog 每 5 分钟检查 gateway RSS，超过 500MB 发送 Telegram 告警。

### 8. ⚠️ 不要用 pkill 杀 gateway（命令行不含 profile 名）
her-m2 和 default gateway 的命令行是 `hermes_cli.main gateway run --replace`，**不含 profile 名称**。
`pkill -f "hermes.*gateway"` 会误杀所有 gateway，包括正在对话的。
→ **正确做法**：从 PID 文件读取 PID，用 `os.kill(pid, 9)` 精确杀。

## 测试方法

```bash
# 1. 直接看报告（不发 Telegram）
/Users/mac/.hermes/hermes-agent/venv/bin/python3 \
  /Users/mac/.hermes/profiles/her-m2/bin/monitor_report.py

# 2. 通过 bash 入口
bash ~/.hermes/profiles/her-m2/bin/hermes-monitor.sh status

# 3. 发送测试报告到 Telegram
bash ~/.hermes/profiles/her-m2/bin/hermes-monitor.sh report
```

## v3 防线架构（2026-05-30）

七层自动防线，全部 launchd 托管 + KeepAlive=true：

| 层 | 组件 | 巡检 | 职责 | 文件 |
|---|------|------|------|------|
| 1 | **defibrillator v2** | 10s | PID 检测 → 单 gateway 复活(launchd) → 3×Token 广播 | `defibrillator_v2.py` |
| 2 | **network-watchdog** | 30s | Clash→DNS→TCP→HTTPS 四级检测 + Clash 重启 + DNS 刷新 | `network-watchdog.py` |
| 3 | **system-watchdog** | 5min | Swap/Disk/Zombie/RSS 阈值告警 + >50MB 日志自动截断 | `system-watchdog.py` |
| 4 | **DNS 冗余** | 2h | 多路 DNS + Telegram 种子 IP 缓存 + Clash DoH 白名单 | `dns-redundancy.py` |
| 5 | **launchd KeepAlive** | 即时 | 7 服务无条件保活，崩溃秒级重启 | 7 个 plist |
| 6 | **skills sync** | 30min | 三端 192 skills 同步 + GitHub push | cron `skills-sync-三端` |

关键文件路径:
- `~/.hermes/profiles/her-m2/bin/defibrillator_v2.py`
- `~/.hermes/profiles/her-m2/bin/network-watchdog.py`
- `~/.hermes/profiles/her-m2/bin/system-watchdog.py`
- `~/.hermes/profiles/her-m2/bin/dns-redundancy.py`
- `~/Library/LaunchAgents/com.hermes.defibrillator.plist`
- `~/Library/LaunchAgents/com.hermes.network-watchdog.plist`
- `~/Library/LaunchAgents/com.hermes.system-watchdog.plist`
- `~/Library/LaunchAgents/ai.hermes.gateway*.plist` (KeepAlive=true + 1GB RSS)

部署命令（一次性）:
```bash
# 加载所有 watchdog
for plist in defibrillator network-watchdog system-watchdog; do
    launchctl bootstrap gui/501 ~/Library/LaunchAgents/com.hermes.$plist.plist
    launchctl kickstart gui/501/com.hermes.$plist
done
```

## 与现有技能的互补

- `hermes-service-troubleshooting`：被动诊断 gateway 异常
- `hermes-gateway-monitoring`（本技能）：主动监控 + 事件通知

两者配合：监控发出告警 → 诊断接手排查。
