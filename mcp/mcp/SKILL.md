---
name: mcp
description: Complete MCP ecosystem — native client configuration, mcporter CLI, ACP subagent integration (Cursor, Claude Code), MCP server mode, and application-specific MCP integrations.
---

# MCP（Model Context Protocol）集成

## 1. 原生 MCP 客户端（Built-in）

Hermes 内置 MCP 客户端，启动时自动连接服务器、发现工具、注册为第一类工具。

### 配置（config.yaml）
```yaml
mcp_servers:
  server_name:
    command: "npx"              # stdio 传输
    args: ["-y", "pkg-name"]
    env:
      API_KEY: "value"
    timeout: 120
    
  # 或 HTTP 传输
  remote:
    url: "https://server.example.com/mcp"
    headers:
      Authorization: "Bearer ..."
```

### 工具命名
`mcp_{server_name}_{tool_name}` — 连字符/点替换为下划线。

### 安全
- 环境变量过滤：仅传递 PATH、HOME、USER 等安全变量
- 凭据脱敏：错误消息中自动隐藏 API keys、tokens
- Sampling 支持：MCP 服务器可请求 LLM 补全

### 故障排查
| 症状 | 原因 | 修复 |
|------|------|------|
| "MCP SDK not available" | `pip install mcp` 未安装 | `pip install mcp` |
| 工具未出现 | YAML 缩进错误 / 名字不对 | 检查 `mcp_{server}_{tool}` 命名 |
| 连接不断断开 | 服务器不稳定 | 增加 timeout，检查网络 |

## 2. Mcporter CLI（ad-hoc 调用）

`mcporter` 命令行工具用于临时调用 MCP 服务器工具，无需配置。

### 常用命令
```bash
mcporter list                    # 列出已配置服务器
mcporter call <server.tool> key=value   # 调用工具
mcporter auth <server>          # OAuth 认证
mcporter config list            # 查看配置
```

### 临时连接
```bash
mcporter list --http-url https://some-server.com --name my_server
mcporter list --stdio "npx -y pkg-name" --name fs
```

## 3. ACP 子代理集成

### Cursor ACP
```python
delegate_task(
    goal="Refactor the login module",
    acp_command="cursor",
    acp_args=["--acp", "--stdio"]
)
```
- 二进制名：`cursor-agent`（brew cask 安装后）
- 认证：`cursor auth login` 或 `cursor auth token <TOKEN>`
- 验证：`cursor-agent --acp --stdio` 应返回 JSON-RPC 握手响应

### Claude Code ACP
```python
delegate_task(
    goal="Review PR #123",
    acp_command="claude"
)
```

### 调用规则
1. 视觉区分：Cursor 输出前缀 `🔴`，Hermes 原生前缀 `🟢`
2. 优雅降级：Cursor ACP 失败 3 次后回退到 Hermes 原生子代理
3. Cursor Pro 用户自动获得 Claude Opus → Sonnet → GPT-4 智能路由

## 4. MCP Server 模式

暴露 Hermes 工具给外部 MCP 客户端（Claude Desktop、Cursor、Copilot）。

### 注册清单
1. 创建 `tools/mcp_server.py`
2. 添加到 `model_tools.py` `_modules` 列表
3. 添加到 `toolsets.py` `_HERMES_CORE_TOOLS`
4. 验证：`import model_tools; print(registry.get_toolset_for_tool("mcp_server_start"))`

### FastMCP API 陷阱
- ❌ 不接受 `version` 参数
- ❌ 不接受 `Tool` 对象作为第一个参数
- ✅ 用 `server.tool(name="...", description="...")(handler)`

## 5. 应用特定 MCP

### TouchDesigner（twozero MCP）
- 端口：localhost:40404
- 36 个原生工具
- 安装：拖入 twozero.tox → 启用 MCP → 重启 Hermes
- 关键：永远不要猜参数名，先调用 `td_get_par_info`

### CLI-Anything
- 结构化 CLI 访问桌面 GUI 应用（LibreOffice, GIMP, Blender 等 80+）
- 替换 `macos-computer-use` 截图-点击模式
- macOS 需要 Python ≥ 3.12（homebrew），PEP 668 需要 `--break-system-packages`

## 支持文件
- `references/mcp-troubleshooting.md` — 连接故障排查
- `references/acp-comparison.md` — ACP 代理对比