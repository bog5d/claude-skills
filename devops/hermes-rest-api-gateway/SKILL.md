---
name: hermes-rest-api-gateway
description: 为 Hermes Agent 创建 REST API 网关，用 HTTP + Bearer Token 暴露工具给外部程序/AI智能体调用。非 MCP 协议，是标准 REST 接口。
---

# Hermes REST API Gateway

## 是什么

把 Hermes Agent 的全部工具暴露为标准 HTTP REST 接口。外部程序（包括其他 AI 智能体如 AnyGen/Coze/Manus）通过 `POST /call` + `Bearer Token` 即可调用 Hermes 工具。

**与 MCP Server 的区别：** MCP Server 是 stdio/SSE 协议，只有 MCP 兼容客户端能用。REST API 是标准 HTTP，任何能发 HTTP 请求的东西都能用。

## 创建步骤

### 1. 创建 `tools/hermes_api.py`

使用 Python 标准库 `http.server.HTTPServer`，不需要额外依赖。

核心结构：
```python
class HermesAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):   # /tools, /health
    def do_POST(self):  # /call — 鉴权后dispatch到registry
    def do_OPTIONS(self):  # CORS

def _load_api_key():    # 从 ~/.hermes/api_key.txt 读或自动生成
def _check_auth():      # Bearer Token 验证
def _start_server():    # HTTP server in daemon thread
```

### 2. 注册到系统（三处）

- `model_tools.py` `_modules` 列表：`"tools.hermes_api"`
- `toolsets.py` `_HERMES_CORE_TOOLS`：`"hermes_api_start", "hermes_api_stop", "hermes_api_key"`
- `toolsets.py` `TOOLSETS`：新增 `"api-gateway"` 工具集定义

### 3. 鉴权方式

API Key 格式：`hm-sk-` + 48位随机hex
存储位置：`~/.hermes/api_key.txt`（权限 0600）
请求头：`Authorization: Bearer <key>`

## ⚠️ 常见踩坑

### 1. 端口冲突
`OSError: [Errno 48] Address already in use`

先用 `lsof -i :8765` 查占用，换一个端口。默认 8765 常被占用，用 18765 等高位端口。

### 2. Daemon 线程无法保活
**错误做法：** `threading.Thread(target=server.serve_forever, daemon=True)`
Python 进程退出后 daemon 线程自动被杀，server 立刻死。

**正确做法：** 在背景进程的主线程中用 keep-alive 循环：
```python
stop = threading.Event()
signal.signal(signal.SIGTERM, lambda *a: stop.set())
while not stop.is_set():
    time.sleep(5)
```
然后用 `terminal(background=true)` 启动整个进程。

### 3. API Key 文件权限
创建 key 文件后必须 `os.chmod(path, 0o600)`，否则其他用户可读。

### 4. CORS 头
外部 AI 平台（如 Coze 的 Webhook）可能从浏览器发请求，需要加：
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
```

### 5. `registry.dispatch` vs `registry.get_handler`
dispatch 会自动处理 JSON 包装和错误，get_handler 返回原始函数。API 层用 dispatch 更安全。

## 验证方式

```bash
# 健康检查
curl http://localhost:PORT/health

# 工具列表
curl http://localhost:PORT/

# 调用工具
curl -X POST http://localhost:PORT/call \
  -H "Authorization: Bearer <KEY>" \
  -H "Content-Type: application/json" \
  -d '{"tool":"read_file","args":{"path":"/tmp/test.txt"}}'
```

## 给其他 AI 智能体用的配置方式

把两个信息给对方：
1. **endpoint**: `http://YOUR_IP:PORT`
2. **API Key**: `hm-sk-xxxxxxxx`

对方在"自定义工具/Custom Tool/Webhook"中配置 POST 请求，JSON body 格式：
```json
{"tool": "工具名", "args": {"参数": "值"}, "task_id": "可选"}
```
