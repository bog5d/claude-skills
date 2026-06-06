---
name: cursor-acp-integration
description: Integrate Cursor CLI as a subagent backend via the Agent Client Protocol (ACP). Cursor's ACP server runs via `cursor-agent --acp --stdio`, providing access to Cursor's full agent runtime including hooks, MCP servers, subagents, and team settings.
version: 1.1.0
author: Hermes Agent
tags:
  - cursor
  - acp
  - agent-client-protocol
  - subagent
related_skills:
  - delegated-subagent
  - native-mcp
---

# Cursor ACP Integration

Cursor CLI (`cursor agent`) exposes an **Agent Client Protocol (ACP)** server via stdio, enabling Hermes Agent (or any ACP-compatible host) to delegate work to Cursor's agent runtime. This is similar to how Claude Code's ACP (`code --acp --stdio`) works but with Cursor's additional capabilities.

## When to Use

Use this when you need to:
- Delegate complex coding tasks to Cursor's agent while staying in Hermes
- Leverage Cursor's **hooks system**, **MCP server config**, **subagent spawning**, or **team settings**
- Run Cursor-style agents without opening the Cursor IDE
- Compare results between Cursor agent and Claude Code agent on the same task

## Prerequisites

- **cursor-agent CLI** installed via Homebrew: `brew install --cask cursor-cli`
- ⚠️ **CRITICAL: Binary Name** — The brew cask installs the binary as `cursor-agent`, NOT `cursor`. Always use `cursor-agent --acp --stdio`. `cursor agent --acp --stdio` will fail.
- **Cursor Pro account** with a valid API token
- `cursor-agent --acp --stdio` must work (verify via delegate_task, not CLI piping)

## Installation & Setup

### 1. Check cursor CLI version

```bash
cursor --version  # Should show something like "2026.04.17-787b533"
```

The ACP server is bundled in `cursor agent` subcommand. It's in the main brew cask.

### 2. Authenticate (Pro account required)

```bash
cursor auth login           # Interactive browser login
# OR, if you have a token:
cursor auth token <YOUR_CURSOR_TOKEN>
```

Token is stored at `~/Library/Application Support/Cursor/User/auth.json`.

### 3. Verify ACP server works

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"0.14.1","capabilities":{},"clientInfo":{"name":"hermes","version":"1.0"}}}' | cursor agent --acp --stdio 2>/dev/null | head -c 2000
```

You should get a JSON-RPC response back with capabilities.

## Architecture

### ACP Module Layout (inside cursor-agent bundle)

The ACP modules are in `/opt/homebrew/Caskroom/cursor-cli/<version>/dist-package/7414.index.js`:

| Module | File | Purpose |
|--------|------|---------|
| **runAcp()** | `src/acp/run.ts` | Entry point; creates ACP server, wraps stdin/stdout in WebStreams, registers the CursorAcpAgent |
| **CursorAcpAgent** | `src/acp/cursor-acp-agent.ts` | Implements AcpAgent interface; handles client metadata (hostClientName, hostClientVersion), initializes shared services |
| **AgentSession** | `src/acp/agent-session.ts` | Core session handler; receives prompts, streams tool calls, handles interaction queries (web search/fetch approval, plan creation, questions) |
| **SharedServices** | `src/acp/shared-services.ts` | Initializes all agent services: model manager, agent client (gRPC to Cursor backend), MCP lease, permissions, hooks executor, team settings, codebase references |
| **SessionResources** | `src/acp/session-resources.ts` | Builds the full resource tree: terminal executor, MCP (from ACP client's mcpServers config), subagents, hooks pipeline, AI code tracker, background work registry |
| **ConfigStore** | `src/acp/config-store.ts` | Persists ACP host registrations (list of known ACP clients) |
| **AcpStorage** | `src/acp/acp-storage.ts` | Session persistence: meta.json + store.db per session |
| **Streams** | `src/acp/streams.ts` | Node.js stream → WebStream adapter for ACP transport |
| **Types** | `src/acp/types.ts` | Tool kind mapping (34 tool types), custom RPC method names (cursor/ask_question, cursor/create_plan, cursor/task, cursor/generate_image) |

### Communication Flow

```
ACP Host (Hermes)
  │  stdin/stdout (JSON-RPC over WebStreams)
  ▼
Cursor ACP Server
  │  1. onInitialize() receives client metadata (name, version)
  │  2. initSharedServices() creates:
  │     - ModelManager (fetches available models from Cursor backend)
  │     - AgentClient (gRPC connection to api2.cursor.com)
  │     - MCPLease (loads MCP servers from ACP client's config)
  │     - PermissionsProvider (allowlist-based approval)
  │     - HookExecutor (team hooks pipeline)
  │     - SubagentsService (client-side subagent spawning)
  │
  │  Per prompt:
  │  3. handlePrompt() → processPrompt()
  │     - Parses prompt content (text, images, resource_links, resources)
  │     - Handles slash commands (/copy-request-id, /custom-commands)
  │     - Sends UserMessageAction via gRPC AgentClient.run()
  │     - Streams back text deltas, tool calls, thinking deltas
  │
  ▼
Cursor Backend (gRPC)
  api2.cursor.com (or configurable endpoint)
```

### Protocol Details

- **Transport**: JSON-RPC 2.0 over stdin/stdout WebStreams
- **SDK**: `@agentclientprotocol/sdk@0.14.1` (npm)
- **Auth**: Cursor Pro API token passed via header injection (`x-cursor-client-type: acp`, `x-cursor-host-app-name`, `x-cursor-host-app-version`)
- **Session persistence**: SQLite DB (`store.db`) per session, with `meta.json` for metadata (cwd, title)

### RPC Methods Used

| Method | Direction | Purpose |
|--------|-----------|---------|
| `initialize` / `initialized` | Client → Server | ACP handshake |
| `sessionCreate` | Client → Server | Create new agent session |
| `prompt` | Client → Server | Send user message + context |
| `sessionUpdate` | Server → Client | Stream results (text, tool calls, thinking) |
| `extMethod("cursor/create_plan")` | Client → Server | Create execution plan tool |
| `extMethod("cursor/ask_question")` | Client → Server | Interactive question tool |
| `extMethod("cursor/task")` | Client → Server | Subagent delegation |
| `requestPermission` | Server → Client | Approval UI (allow-once/allow-always/reject) |

### Tool Types (34 mapped in types.ts)

| Kind | Tool Examples |
|------|---------------|
| `execute` | shell, computer_use, writeShellStdin |
| `edit` | edit, applyAgentDiff |
| `search` | grep, glob, semSearch, webSearch, ls |
| `read` | read, readTodos, readLints, readMcpResource |
| `fetch` | webFetch, fetch |
| `think` | askQuestion, reflect |
| `other` | mcp, updateTodos, createPlan, task, truncate, generateImage, reportBugfixResults |

## Caller Obligations (Hermes-side rules)

When delegating to Cursor via ACP, the calling agent MUST:

1. **Visual differentiation** — prefix cursor output with `🔴 [Cursor 执行中]` / `🔴 [Cursor 输出]` / `🔴 [Cursor 完成]`. When falling back to native, prefix with `🟢 [Hermes 原生]`.
2. **Model priority** — Cursor Pro users auto-get Claude Opus → Sonnet → GPT-4 → default via server-side smart routing. No manual `--model` flag needed (ACP doesn't support it).
3. **Graceful degradation** — if Cursor ACP fails 3 times, fall back to Hermes native subagent and annotate `⚠️ 已降级为 Hermes 原生执行`.

## Integration with Hermes

### Using ACP Subagent Transport

In Hermes config, add cursor as an ACP provider:

```python
# In delegate_task, use acp_command parameter:
result = delegate_task(
    goal="Refactor the login module",
    context="~/projects/myapp",
    acp_command="cursor",   # Spawns `cursor agent --acp --stdio`
    acp_args=["--acp", "--stdio"]
)
```

### Important Paths

- **Cursor config**: `~/Library/Application Support/Cursor/User/`
- **ACP sessions**: `~/Library/Application Support/Cursor/acp-sessions/`
- **Auth info**: `~/Library/Application Support/Cursor/User/auth.json`
- **MCP config**: `~/.cursor/mcp.json` (per-project) or global settings

### MCP Server Propagation

ACP clients can pass MCP server config via `sessionCreate.mcpServers`. The CursorAcpAgent parses these and loads them into the agent's MCP lease. The parser supports:
- **Stdio servers** (command + args + env)
- **HTTP/SSE servers** (url + headers)
- **Legacy format** (using `transport.case` / `stdio` / `http` nested objects)

## Troubleshooting

### "cursor: command not found"
Install with: `brew install --cask cursor-cli`

### "cursor agent: unknown command"
Only the brew cask version (2026.04+) includes the `agent` subcommand. Older versions or App Store versions may not have it.

### ACP server fails to start
- Check auth: `cursor auth status`
- Ensure Cursor Pro subscription is active
- Run with `--debug` flag for verbose logs: `cursor agent --acp --stdio --debug`

### Permission requests blocked
ACP sessions will prompt for web search/fetch permissions. In test/automated mode, ensure the approval handler responds.

### gRPC connection errors
Cursor's agent runs via gRPC to `api2.cursor.com`. If behind a corporate proxy, configure endpoint with `--endpoint` flag.

## Comparison with Other ACP Agents

| Feature | Cursor Agent | Claude Code |
|---------|-------------|-------------|
| ACP Protocol | Yes (v0.14.1) | Yes |
| Stdio Transport | Yes | Yes |
| MCP Servers | Yes (via client config) | Manual |
| Team Hooks | Yes | No |
| Subagent Spawning | Yes (client-side) | No |
| Custom RPC Methods | cursor/create_plan, cursor/ask_question, cursor/task, cursor/generate_image | code/ extensions |
| Offline Mode | No (requires gRPC backend) | Partial |
| Model Flexibility | Configurable via backend | Claude only |
