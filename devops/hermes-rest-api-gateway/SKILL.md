---
name: hermes-rest-api-gateway
description: 为 Hermes Agent 创建 REST API 网关，用 HTTP + Bearer Token 暴露工具给外部程序/AI智能体调用。非 MCP 协议，是标准 REST 接口。
---

# Hermes REST API Gateway

## ⭐ 首选方案：内置 api_server（已生产可用）

Hermes 内置的 `api_server` 平台是生产级的 REST API，**无需写代码，已随 gateway 启动**。优先级远高于下面的自定义方案。

### 配置

`config.yaml` 中 `platforms.api_server` 段，`.env` 中 `API_SERVER_KEY=<token>`。默认端口 8642。

### 已验证端点（2026-06-09）

| 端点 | 方法 | 鉴权 | 说明 |
|------|:--:|:--:|------|
| `/health` | GET | ❌ 无需 | 健康检查，返回 `{"status":"ok"}` |
| `/v1/capabilities` | GET | ✅ Bearer | 功能清单（chat/streaming/runs/tools） |
| `/v1/models` | GET | ✅ Bearer | 可用模型列表 |
| `/api/sessions` | GET | ✅ Bearer | 列出所有会话 |
| `/api/sessions` | POST | ✅ Bearer | 创建新会话，body: `{"title":"..."}` |
| `/api/sessions/{id}` | GET | ✅ Bearer | 获取会话详情 |
| `/api/sessions/{id}/chat` | POST | ✅ Bearer | 发送消息，body: `{"message":"..."}` |
| `/api/sessions/{id}/chat/stream` | POST | ✅ Bearer | SSE 流式对话 |

### 验证流程

```bash
# 健康检查（无需鉴权）
curl http://127.0.0.1:8642/health

# 创建会话
curl -X POST http://127.0.0.1:8642/api/sessions \
  -H "Authorization: Bearer <API_SERVER_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"title":"test"}'

# 对话
curl -X POST http://127.0.0.1:8642/api/sessions/<session_id>/chat \
  -H "Authorization: Bearer <API_SERVER_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"message":"今天星期几"}'
```

返回格式：`{"object":"hermes.session.chat.completion","session_id":"...","message":{"role":"assistant","content":"..."},"usage":{...}}`

### 多 profile 端口冲突

多 gateway 环境默认都尝试绑定 8642。对于纯 Telegram bot（不需要 REST API），禁用：
- ❌ `enabled: false` **不够** — gateway 仍会初始化 adapter 并持续报错重连
- ✅ 从 config.yaml `platforms:` 段**整块删除** `api_server:` 配置，然后 bootout+bootstrap 重启

### 微信 AI 等外部集成

微信 AI "开发模式" → 小程序云函数 → HTTP POST → 本 API。需要公网可达（ngrok/cloudflare tunnel/或部署到公网服务器）。

---

## 是什么（自定义方案说明）

以下内容描述 `tools/hermes_api.py` 自定义实现——仅在内置 api_server 不可用或不满足需求时使用。

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

### 6. 代码热更新陷阱（2026-05-17验证）
**importlib.reload 对已启动的 HTTP server 无效！** 因为 HTTPServer 已经持有了旧的 Handler 类引用。必须：
```bash
lsof -ti:18765 | xargs kill -9
# 然后重新启动整个 Python 进程
```

### 7. 公网穿透方案对比
| 方案 | 是否需要账号 | 稳定性 | 当前状态 |
|------|------------|--------|---------|
| ngrok | 需要（免费注册） | 高 | 无 authtoken |
| cloudflared quick tunnel | 不需要 | 低（频繁500） | 已试，不可用 |
| bore-cli | 不需要 | 中 | 未安装 |

推荐：注册 ngrok 免费账号 → `ngrok config add-authtoken` → `ngrok http 18765`

### 8. AnyGen 接入反馈（2026-05-17）
另一个 AI 智能体对网关的评估：
- 架构方向正确，接口设计合理
- **阻塞点**：localhost 不可达（对方在远程沙箱）
- **建议补充**：
  - `GET /tools/{name}` 返回完整参数 schema
  - 统一错误码（TOOL_NOT_FOUND / MISSING_PARAMETER / UNAUTHORIZED）
  - 统一返回格式 `{"success":bool, "tool":"...", "data":..., "error":{...}, "duration_ms":N, "request_id":"..."}`
  - OpenAPI 3.0 规范文档
- **协作模式建议**：Hermes 做执行层，对方做理解与编排层

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

## macOS 开机自启配置（launchd）

Gateway 通过 login item 自动启动，但 API 服务器需要单独配置 launchd 才能在停电/重启后自动恢复。

### 创建 plist
`~/Library/LaunchAgents/com.hermes.api-gateway.plist`：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" ...>
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hermes.api-gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/mac/.hermes/hermes-agent/venv/bin/python3</string>
        <string>-c</string>
        <string>import model_tools; from tools.hermes_api import _start_server; _start_server(port=18765); import time,threading,signal; stop=threading.Event(); signal.signal(signal.SIGTERM,lambda*a:stop.set()); [time.sleep(5) while not stop.is_set()]</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/mac/.hermes/hermes-agent</string>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key>
    <string>/Users/mac/.hermes/logs/api-gateway.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/mac/.hermes/logs/api-gateway-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>HERMES_HOME</key><string>/Users/mac/.hermes</string>
        <key>HOME</key><string>/Users/mac</string>
    </dict>
</dict>
</plist>
```

### 加载
```bash
launchctl bootout gui/$(id -u)/com.hermes.api-gateway 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hermes.api-gateway.plist
launchctl list | grep hermes.api
```

### 验证自启
重启 Mac 后检查：`curl http://localhost:18765/health`

## ngrok 公网穿透完整流程

### 注册
去 ngrok.com → Sign Up（GitHub/Google/邮箱，30秒）

### 配置 authtoken（从 Dashboard 复制）
```bash
ngrok config add-authtoken <你的token>
ngrok http 18765
```

### 常见问题：端口绑定冲突
```
ERR_NGROK_334: endpoint 'xxx.ngrok-free.dev' is already online
```
原因：之前的 ngrok 进程残留或同一个 endpoint 被其他地方占用。
解决：
```bash
pkill -f ngrok
sleep 2
ngrok http 18765
```

### 验证公网可访问
```bash
curl https://xxx.ngrok-free.dev/health
```

## v2 增强功能（2026-05-18）

基于 AnyGen 等外部 AI 的反馈，网关 v2 增加了：
- `GET /tools` — 全量工具清单含完整参数 schema
- `GET /tools/{name}` — 单个工具详情（参数、必填项、类型）
- `GET /openapi.json` — OpenAPI 3.0 规范文档
- 统一返回格式：`{"success":bool, "tool":"...", "data":..., "duration_ms":N, "request_id":"..."}`
- 统一错误码：`TOOL_NOT_FOUND` / `MISSING_PARAMETER` / `UNAUTHORIZED` / `EXECUTION_FAILED`
- API Key 固定存储在 `~/.hermes/api_key.txt`，权限 0600，不会变化
