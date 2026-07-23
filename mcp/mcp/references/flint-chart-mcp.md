# Flint Chart MCP — Quick Reference

## Installation

```bash
npm install -g flint-chart-mcp
npx flint-chart-mcp --help  # verify
```

- **Package name**: `flint-chart-mcp` (NOT `@microsoft/flint-chart-mcp` — the `@microsoft` scoped name returns 404)
- **Version tested**: 0.3.0

## Hermes Config

```yaml
mcp_servers:
  flint-chart:
    command: npx
    args: ["-y", "flint-chart-mcp"]
    timeout: 60
```

## API Format Pitfalls

### Parameters use camelCase, NOT snake_case

| ✅ Correct (camelCase) | ❌ Wrong (snake_case) |
|---|---|
| `chartType` | `chart_type` |
| `encodings` | `encoding` |
| `xAxis`, `yAxis` | `x_axis`, `y_axis` |

### Chart types are Title Case strings

```
"Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot",
"Area Chart", "Boxplot", "Heatmap", "Violin Plot"
```

NOT `"bar"`, `"line"`, `"pie"`, etc.

### Chart spec is passed directly, NOT wrapped

```json
// ✅ Correct
{"chartType": "Bar Chart", "encodings": {"xAxis": "category", "yAxis": "value"}}

// ❌ Wrong — don't wrap in {"spec": ...}
{"spec": {"chartType": "Bar Chart", ...}}
```

## Backend Support Matrix

| Chart Type | Vega-Lite | ECharts | Chart.js |
|---|---|---|---|
| Bar Chart | ✅ | ✅ | ✅ |
| Line Chart | ✅ | ✅ | ✅ |
| Pie Chart | ✅ | ✅ | ✅ |
| Scatter Plot | ✅ | ✅ | ✅ |
| Area Chart | ✅ | ✅ | ✅ |
| Boxplot | ✅ | ✅ | ✅ |
| Heatmap | ✅ | ✅ | ❌ |
| Violin Plot | ✅ | ✅ | ✅ |

**Chart.js has 20 types**, no Heatmap. Vega-Lite: 34 types, ECharts: 37 types.

## Tools

| Tool | Key Params | Returns |
|---|---|---|
| `validate_chart` | `chart_spec` | validation result |
| `compile_chart` | `chart_spec`, `backend` | JSON spec for target backend |
| `render_chart` | `chart_spec`, `data`, `backend`, `format` | base64 image (PNG) or text (SVG) |
| `create_chart_view` | `chart_spec`, `data` | HTML with interactive chart |
| `list_chart_types` | — | array of supported types |

## render_chart Output

- `format: "png"` → returns base64 image content (type: `image`)
- `format: "svg"` → returns raw SVG text (type: `text`)
- `scale` parameter (default 1): set to 2 for retina displays

## Testing via stdio (Python)

```python
import subprocess, json

def mcp_call(server_args, method, params=None):
    """Call an MCP tool via stdio subprocess."""
    proc = subprocess.Popen(
        server_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True
    )
    # Initialize
    init = {"jsonrpc": "2.0", "id": 0, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}
    proc.stdin.write(json.dumps(init) + "\n")
    proc.stdin.flush()
    proc.stdout.readline()  # consume init response
    # Send actual request
    req = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params:
        req["params"] = params
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    resp = json.loads(proc.stdout.readline())
    proc.terminate()
    return resp["result"]

# Usage
tools = mcp_call(["npx", "-y", "flint-chart-mcp"], "tools/list")
chart = mcp_call(["npx", "-y", "flint-chart-mcp"], "tools/call", {
    "name": "render_chart",
    "arguments": {
        "chart_spec": {"chartType": "Bar Chart", "encodings": {"xAxis": "x", "yAxis": "y"}},
        "data": [{"x": "A", "y": 10}, {"x": "B", "y": 20}],
        "backend": "vega-lite"
    }
})
```

## Error Patterns

| Error | Cause | Fix |
|---|---|---|
| `Unknown Chart.js chart type: Heatmap` | Chart.js backend doesn't support Heatmap | Use vega-lite or echarts |
| Empty/short compile output | Wrong `chartType` case | Use Title Case ("Bar Chart" not "bar") |
| 404 npm install | Using `@microsoft/flint-chart-mcp` | Use `flint-chart-mcp` |
