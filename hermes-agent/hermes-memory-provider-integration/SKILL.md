---
name: hermes-memory-provider-integration
description: "为 Hermes Agent 评估、安装、配置外部记忆 Provider（如 TencentDB Agent Memory、Mem0、Honcho 等）。涵盖原生安装、Docker 部署、端到端验证、与现有记忆栈共存策略。"
category: hermes-agent
---

# Hermes Memory Provider 集成

## 触发条件

- 用户提到要评估/集成某个外部记忆系统
- 需要对比不同 memory provider 方案
- 为 Hermes 添加新的 `plugins/memory/<name>/` provider
- 排查 memory provider 不可用问题

## 架构总览

```
Hermes Agent (Python)
  └─ MemoryManager
       └─ plugins/memory/<provider>/    ← 要集成的目标
            ├─ __init__.py + plugin.yaml
            └─ (可能是 HTTP client 连外部 Gateway，或本地 SDK)

外部 Gateway/Sidecar (可选)
  → 记忆提取 LLM 调用
  → 存储后端 (SQLite / VectorDB)
  → 召回 API
```

## 安装流程（以 TencentDB Agent Memory 为例）

### Step 1：安装 Gateway（如果 provider 有独立 sidecar）

TencentDB Agent Memory 的 Hermes 插件是薄 HTTP client，实际记忆处理在 Node.js Gateway 中运行。

```bash
# 安装 npm 包
mkdir -p ~/.memory-tencentdb
cd ~/.memory-tencentdb
echo '{"name":"tdai-memory","version":"1.0.0","type":"module","private":true}' > package.json
npm install @tencentdb-agent-memory/memory-tencentdb@latest tsx
```

> ⚠️ npm install 可能超时（大包），但可能已部分完成。检查 `node_modules/@tencentdb-agent-memory/memory-tencentdb/src/gateway/server.ts` 是否存在。

### Step 2：Symlink 插件到 Hermes

```bash
ln -sf ~/.memory-tencentdb/node_modules/@tencentdb-agent-memory/memory-tencentdb/hermes-plugin/memory/memory_tencentdb \
       ~/.hermes/hermes-agent/plugins/memory/memory_tencentdb
```

> 目录名必须是 `memory_tencentdb`（下划线），不能是 `memory-tencentdb`（连字符）。

### Step 3：验证插件被发现

```bash
# 必须用 Hermes venv 的 Python（系统 Python 可能有类型注解兼容性问题）
~/.hermes/hermes-agent/venv/bin/python3 -c '
from plugins.memory import discover_memory_providers
providers = discover_memory_providers()
[print(f"{n}: available={a}") for n, _, a in providers]
'
```

- 刚安装时：`available=False`（Gateway 未运行）
- Gateway 启动后：`available=True`

### Step 4：启动 Gateway

Gateway 是独立进程，需要 LLM API key 来做 L1/L2/L3 提取。

**关键坑：环境变量命名。**
- Hermes 插件 README 说用 `MEMORY_TENCENTDB_LLM_*`
- 实际 Gateway 独立运行时读的是 `TDAI_LLM_*`
- Hermes 插件会在启动 Gateway 子进程时做变量映射，但手动启动需要直接用 `TDAI_LLM_*`

```bash
TDAI_LLM_API_KEY="sk-..." \
TDAI_LLM_BASE_URL="https://api.deepseek.com/v1" \
TDAI_LLM_MODEL="deepseek-chat" \
node --import tsx/esm \
  ~/.memory-tencentdb/node_modules/@tencentdb-agent-memory/memory-tencentdb/src/gateway/server.ts
```

端口默认 8420，数据目录默认 `~/.memory-tencentdb/memory-tdai/`。

验证：
```bash
curl http://localhost:8420/health
# → {"status":"ok","stores":{"vectorStore":true,...}}
```

### Step 5：端到端验证

```bash
# Capture 对话
curl -s -X POST http://localhost:8420/capture \
  -H "Content-Type: application/json" \
  -d '{"session_key":"test-001","user_content":"我用Rust和TypeScript","assistant_content":"了解"}'

# 至少 5 轮触发 L1 提取（pipeline.everyNConversations=5）

# 结束 session 触发 flush
curl -s -X POST http://localhost:8420/session/end \
  -H "Content-Type: application/json" \
  -d '{"session_key":"test-001"}'

# 等 15-30 秒（L1 提取是异步的），然后召回
curl -s -X POST http://localhost:8420/recall \
  -H "Content-Type: application/json" \
  -d '{"query":"用户用什么语言","session_key":"cross-test"}'
```

验证要点：
- `memory_count > 0` — L1 原子事实已提取
- context 含 `<user-persona>` — L3 画像已生成
- context 含 `<scene-navigation>` — L2 场景簇已聚合
- 用不同 `session_key` 召回仍成功 — 跨 session 持久化

## 与现有记忆栈共存

Hermes 可以同时运行多个 memory provider，不互斥：

```
Agent Memory    → 上游提取（自动从对话提取事实/场景/画像）
EverOS          → 语义检索 + Agent 专用记忆
Mem0            → 语义精排
Skills          → 程序性记忆
Memory Tool     → 每轮注入的快速事实
```

**推荐策略**：Agent Memory 作为「提取层」，产生的结构化记忆可以喂给 EverOS 做检索，L3 画像可替代手动维护的 USER_PROFILE.md。

## Docker 方案（备选）

```bash
# 从源码构建
cd /tmp/TencentDB-Agent-Memory/docker/opensource
docker build -f Dockerfile.hermes -t hermes-memory .

# 运行
docker run -d --name hermes-memory \
  -p 8420:8420 \
  -e MODEL_API_KEY="sk-..." \
  -e MODEL_BASE_URL="https://api.deepseek.com/v1" \
  hermes-memory
```

> macOS 上 Docker Desktop 启动可能很慢（VM 初始化 1-2 分钟），原生安装通常更快。

## Pitfalls

1. **环境变量命名不一致**：Gateway 独立运行时用 `TDAI_LLM_*`，Hermes 插件文档说的是 `MEMORY_TENCENTDB_LLM_*`。手动启动 Gateway 必须用前者。
2. **Python 版本**：`discover_memory_providers()` 需要 Python 3.10+（类型联合语法 `str | object`）。用 Hermes venv 的 Python，不要用系统 Python。
3. **L1 提取是异步的**：capture 调用成功 ≠ 记忆立即可召回。需等待 15-30 秒或检查 `~/.memory-tencentdb/memory-tdai/.metadata/recall_checkpoint.json` 中的 `total_memories_extracted`。
4. **npm install 超时**：大包安装可能 120s 超时，但可能已部分完成。检查关键文件 `src/gateway/server.ts` 是否存在。
5. **目录名用下划线**：`memory_tencentdb` 不是 `memory-tencentdb`。连字符形式只是 config 别名。
6. **不要用 Docker 当首选**：macOS 上 Docker Desktop 启动不可靠（VM 初始化慢、socket 路径问题）。原生 npm 安装更稳定。

## 参考文件

- `references/tencentdb-agent-memory-architecture.md` — 四层记忆架构详解、与 Hermes 现有记忆栈的对比分析、实测 benchmark 数据、部署架构图
