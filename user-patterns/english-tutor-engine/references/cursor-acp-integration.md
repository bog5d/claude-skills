# Cursor ACP Integration — 开发路由

## 发现日期
2026-06-06（副官确认：2026-04-25 首次跑通）

## Cursor CLI ACP 调用方式

```python
delegate_task(
    goal="开发任务描述",
    acp_command="cursor-agent",
    acp_args=["--acp", "--stdio"]
)
```

## 调用链

```
Hermes (delegate_task)
  → cursor-agent --acp --stdio (子进程)
  → ACP JSON-RPC (stdio transport)
  → api2.cursor.com (gRPC)
  → Cursor 写代码 → 结果回传 Hermes
```

## 关键文件

| 文件 | 路径 |
|------|------|
| cursor-agent binary | `/opt/homebrew/bin/cursor-agent` (symlink → Homebrew Cask) |
| cursor-agent package | `/opt/homebrew/Caskroom/cursor-cli/2026.04.17-787b533/dist-package/` |
| cursor-agent node | `dist-package/node` (Node.js v24.5.0) |
| cursor-agent index.js | `dist-package/index.js` (webpack bundle, ~7.6MB) |
| Hermes ACP adapter | `/Users/mac/.hermes/hermes-agent/acp_adapter/` |
| Copilot ACP plugin | `/Users/mac/.hermes/hermes-agent/plugins/model-providers/copilot-acp/` |

## 当前状态

- **cursor-agent 已安装** ✅
- **Node.js 运行时正常** ✅
- **api2.cursor.com 可达** ✅ (HTTP 200)
- **ACP 模式无响应** ❌ — 2026-06-06 测试时 `--acp --stdio` 不产生任何输出，疑似 CLI auth token 过期

## 修复方法（推测）

```bash
# 在 Mac 终端刷新 CLI 认证
cursor login
# 或
cursor agent login
```

Cursor IDE 的登录状态和 CLI 的 auth token 不共享。CLI 需要独立认证。

## Aider 桥接（备选）

```bash
# 路径
/Users/mac/aider_workspace/bridge_cmd.py

# 调用
python3 /Users/mac/aider_workspace/bridge_cmd.py "开发任务描述"

# 实际执行
python3 -m aider --model deepseek/deepseek-chat --yes --message "【仓颉计划指令】任务:..."
```

已验证可运行（2026-06-06），输出写入 `aider_run.log`。

## 三线开发路由对比

| 路线 | 适合 | 调用方式 | 状态 |
|------|------|------|:--:|
| Aider bridge | Python 管线/SM-2 | terminal 调 bridge_cmd.py | ✅ |
| Cursor ACP | 全栈（含 HTML 预览）| delegate_task(acp_command="cursor-agent") | ⚠️ 待修复 auth |
| Copilot ACP | 全栈 | delegate_task(acp_command="copilot") | ❌ CLI 未安装 |
