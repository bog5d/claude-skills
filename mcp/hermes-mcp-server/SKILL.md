---
name: hermes-mcp-server
description: Add MCP Server mode to Hermes — expose Hermes tools to external AI clients via Model Context Protocol
---

# Hermes MCP Server Implementation

## When to use
Adding or fixing MCP Server functionality — exposing Hermes's internal tools (61+) to external MCP clients (Claude Desktop, Cursor, Copilot).

## What exists
- `tools/mcp_tool.py` (2457 lines): MCP **Client** mode — Hermes calls external MCP servers
- `tools/mcp_server.py` (360 lines): MCP **Server** mode — external AIs call Hermes tools

## FastMCP API Quirks (pitfalls discovered 2026-05-17)

### 1. No `version` parameter
```python
# WRONG
server = FastMCP(name="Hermes", version="1.0.0")

# CORRECT
server = FastMCP(name="Hermes", instructions="Description string")
```

### 2. Tool registration pattern
```python
# WRONG — Tool object as first arg
server.tool(mcp_tool_object)(handler)

# CORRECT — name + description as kwargs
server.tool(name="tool_name", description="...")(handler)
```

### 3. Registry API
```python
# WRONG
schemas = registry.get_all_tool_schemas()

# CORRECT — iterate names, get schema per tool
for name in registry.get_all_tool_names():
    schema = registry.get_schema(name)
```

### 4. Handler dispatches to `registry.dispatch`
```python
async def _handle_tool_call(name, arguments):
    try:
        result = registry.dispatch(name, arguments, task_id=f"mcp-{name}")
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
```

## Registration checklist
1. Create `tools/mcp_server.py`
2. Add `"tools.mcp_server"` to `_modules` list in `model_tools.py`
3. Add `"mcp_server_start"` to `_HERMES_CORE_TOOLS` in `toolsets.py`
4. Add `"mcp-server"` toolset definition in `TOOLSETS` dict
5. Verify: `import model_tools; print(registry.get_toolset_for_tool("mcp_server_start"))` → `mcp-server`

## Verification
```bash
cd hermes-agent && source venv/bin/activate
python3 -c "
import model_tools
from tools.mcp_server import _create_hermes_mcp_server
server = _create_hermes_mcp_server()
import asyncio; asyncio.run(server.list_tools())
"
```

## Related files
- `tools/mcp_tool.py` — Client mode (calling external MCP servers)
- `tools/mcp_oauth.py` — OAuth 2.1 support (already implemented)
- `tools/reflexion.py` — Runtime self-reflection
- `agent/trajectory_distiller.py` — Training data pipeline
- `tools/swe_bench.py` — Benchmark integration
