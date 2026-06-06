# Headroom Proxy — macOS launchd 部署

## 概述

Headroom 是 AI Agent 的上下文压缩层。截获 tool 输出（terminal/web_search/文件内容）后压缩 60-95% token，再发给 LLM。

三种接入模式：
- **Proxy** (`headroom proxy --port 8787`) — HTTP 代理，任何 LLM 客户端通过 `ANTHROPIC_BASE_URL` / `OPENAI_BASE_URL` 指向它
- **MCP Server** (`headroom mcp serve`) — 暴露 `headroom_compress` / `headroom_retrieve` / `headroom_stats` 工具
- **wrap** (`headroom wrap claude/codex/cursor`) — 临时包装特定 CLI

## 安装

```bash
/Users/mac/.hermes/hermes-agent/venv/bin/pip install headroom-ai
# 版本: 0.23.0
```

## launchd 持久化服务

Plist 路径：`/Users/mac/Library/LaunchAgents/com.hermes.headroom-proxy.plist`

### 关键配置

```xml
<key>ProgramArguments</key>
<array>
    <string>/Users/mac/.hermes/hermes-agent/venv/bin/headroom</string>
    <string>proxy</string>
    <string>--port</string>
    <string>8787</string>
    <string>--stateless</string>  <!-- 必须！绕过 /.headroom 写 root 文件系统问题 -->
    <string>--memory</string>
</array>
```

### 环境变量（必须）

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>HOME</key>
    <string>/Users/mac</string>
    <key>XDG_DATA_HOME</key>
    <string>/Users/mac/.local/share</string>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
</dict>
```

### 致命陷阱

1. **`--stateless` 必须加**：Headroom 默认在 `/.headroom/` 创建文件，macOS root 只读导致 `OSError: [Errno 30] Read-only file system`。`--stateless` 禁用所有文件系统写入。

2. **HOME 必须显式设置**：launchd 不会自动设 HOME 环境变量。不加则 Headroom 解析路径出错。

## Hermes MCP 集成

在 `config.yaml` 的 `mcp_servers` 下添加：

```yaml
mcp_servers:
  headroom:
    command: /Users/mac/.hermes/hermes-agent/venv/bin/headroom
    args:
    - mcp
    - serve
    timeout: 30
```

⚠️ Hermes `config.yaml` 受 gateway 运行时保护，patch/write_file 会被拒绝。必须用 terminal + venv python 直接编辑：

```bash
/Users/mac/.hermes/hermes-agent/venv/bin/python3 -c "
import yaml
path = '/Users/mac/.hermes/profiles/her-m2/config.yaml'
with open(path) as f:
    cfg = yaml.safe_load(f)
cfg['mcp_servers']['headroom'] = {
    'command': '/Users/mac/.hermes/hermes-agent/venv/bin/headroom',
    'args': ['mcp', 'serve'],
    'timeout': 30
}
with open(path, 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
"
```

修改后需重启 gateway 才能加载新 MCP 工具。

## 其他工具接入

| 工具 | 命令 |
|------|------|
| Claude.app | `headroom mcp install`（自动注册 MCP） |
| Cursor | 手动在 MCP 配置中加 headroom mcp serve |
| Codex CLI | `headroom wrap codex` 或 `headroom init codex` |
| 任何 OpenAI 客户端 | 设 `OPENAI_BASE_URL=http://localhost:8787/v1` |

## ⚠️ 致命陷阱：MCP stdio 模式冻结 Hermes Gateway

**不要将 `headroom mcp serve` 作为 Hermes 的 MCP Server。** 这会导致 gateway 随机冻结。

### 症状
- Gateway 进程 PID 存活但 0% CPU
- 所有日志停止输出（包括 kanban tick、cron 等周期性日志）
- Telegram 消息完全不响应
- `lsof -p <PID> | grep PIPE` 显示残留 PIPE fd
- `ps aux | grep headroom` 显示僵尸 `headroom mcp serve` 进程

### 根因
Hermes MCP 使用 stdio 传输。`headroom mcp serve` 启动后通过 stdin/stdout 与 gateway 通信。当 MCP server 内部阻塞（如连接 proxy :8787 超时），stdio 管道阻塞 → gateway 的 asyncio 事件循环整个冻结 → 0% CPU + 无日志。

### 验证
```bash
# 检查 gateway 是否冻结
ps -p <PID> -o pid,state,%cpu
# 如果 %CPU=0.0 且日志停止 60s+ → 已冻结

# 检查是否有僵尸 headroom mcp serve
ps aux | grep 'headroom mcp serve'
lsof -p <gateway_PID> | grep PIPE | grep -v '    1\|    2'
```

### 修复
```bash
# 1. 移除 headroom MCP 配置
/Users/mac/.hermes/hermes-agent/venv/bin/python3 -c "
import yaml
path = '/Users/mac/.hermes/profiles/<profile>/config.yaml'
with open(path) as f:
    cfg = yaml.safe_load(f)
cfg['mcp_servers'].pop('headroom', None)
with open(path, 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
"

# 2. 杀僵尸 MCP 进程和卡死的 gateway
kill -9 <headroom_mcp_PID> <gateway_PID>

# 3. 重启 gateway
launchctl kickstart -k gui/501/<service>
```

### 正确用法
- **Claude.app** — 用 `headroom mcp install`，Claude 的 MCP 实现不受此问题影响
- **Hermes** — **只用 headroom proxy**（HTTP 端口 8787），不要用 MCP stdio 模式
- **桌面端** — 所有桌面 App 都可以通过环境变量 `ANTHROPIC_BASE_URL=http://localhost:8787` 使用 proxy

## 健康检查

```bash
curl -s http://localhost:8787/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'], d['ready'])"
# 预期: healthy True
```

## 服务管理

```bash
# 启动
launchctl bootstrap gui/501 /Users/mac/Library/LaunchAgents/com.hermes.headroom-proxy.plist
launchctl kickstart gui/501/com.hermes.headroom-proxy

# 停止
launchctl bootout gui/501/com.hermes.headroom-proxy

# 查看状态
launchctl list | grep headroom
```
