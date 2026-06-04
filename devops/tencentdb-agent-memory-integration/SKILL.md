---
name: tencentdb-agent-memory-integration
description: "TencentDB Agent Memory 四层记忆系统与 Hermes 集成——安装、配置、启动、共存架构。Phase 1-3 完整 SOP。"
category: devops
---

# TencentDB Agent Memory × Hermes 集成

## 架构

```
┌─────────────────────────────────────────────────┐
│                 Hermes Agent (Python)             │
│  ┌───────────────────────────────────────────┐   │
│  │  MemoryManager                            │   │
│  │  └─ memory_tencentdb provider (HTTP client)│   │
│  │       │ POST /recall, /capture, /search    │   │
│  └───────┼───────────────────────────────────┘   │
│          │                                        │
└──────────┼────────────────────────────────────────┘
           │  HTTP (127.0.0.1:8420)
┌──────────┼────────────────────────────────────────┐
│  TDAI Memory Gateway (Node.js)                    │
│  ┌───────┴───────────────────────────────────┐   │
│  │  L0 原始对话 → SQLite + JSONL              │   │
│  │  L1 原子事实 → LLM 提取 + BM25 索引        │   │
│  │  L2 场景聚类 → Markdown 文件               │   │
│  │  L3 用户画像 → persona.md                  │   │
│  │  Offload   → Mermaid 任务状态图 (可选)     │   │
│  └───────────────────────────────────────────┘   │
│  Storage: SQLite + sqlite-vec (~/.memory-tencentdb/)│
└───────────────────────────────────────────────────┘

与其他记忆系统共存：
  Agent Memory  → 「从对话中提取什么」(L1-L3 提取管道)
  EverOS        → 「怎么检索和关联」(混合检索)
  Mem0          → 「语义精排」(Rerank)
  Memory 工具   → 保持不变 (MEMORY.md 快速注入)
  Skills        → 「程序性记忆」不变
```

## 快速恢复 (Disaster Recovery)

如果 Gateway 挂了：

```bash
# 1. 检查进程
curl -s http://localhost:8420/health || echo "DOWN"

# 2. 重启
export $(grep -v '^#' ~/.hermes/.env | xargs)
cd ~/.memory-tencentdb
TD...://api.deepseek.com/v1" \
TD...chat" \
node --import tsx/esm \
  node_modules/@tencentdb-agent-memory/memory-tencentdb/src/gateway/server.ts &

# 3. 验证
sleep 10 && curl -s http://localhost:8420/health
```

## 安装记录

### 已部署组件

| 组件 | 位置 | 状态 |
|------|------|------|
| npm 包 | `~/.memory-tencentdb/` | ✅ |
| Hermes 插件 | `~/.hermes/hermes-agent/plugins/memory/memory_tencentdb/` (symlink) | ✅ |
| Gateway 进程 | `localhost:8420` | ✅ |
| launchd 服务 | `~/Library/LaunchAgents/ai.tdai.memory-gateway.plist` | ✅ |
| 启动脚本 | `~/.hermes/scripts/tdai-gateway.sh` | ✅ |
| 环境变量 | `~/.memory-tencentdb/tdai-gateway.env` | ✅ |
| Gateway 配置 | `~/.memory-tencentdb/tdai-gateway.yaml` | ✅ |
| 数据目录 | `~/.memory-tencentdb/memory-tdai/` | ✅ |

### Hermes config.yaml 关键配置

```yaml
memory:
  provider: memory_tencentdb   # ← 从 mem0 切换
  memory_enabled: true
  user_profile_enabled: true
```

### 使用的 API

- **LLM**: DeepSeek API (deepseek-chat)
- **Embedding**: 未配置 (纯 BM25 关键词检索)
- **成本**: 预估 ¥1-3/月 (L1/L2/L3 提取)

## 坑与经验

1. **TDAI_LLM_* vs MEMORY_TENCENTDB_LLM_***：Gateway 本身读 `TDAI_LLM_*` 环境变量。Hermes 插件读 `MEMORY_TENCENTDB_LLM_*`。两者需要同时设置或在启动脚本中映射。

2. **Standalone Gateway ≠ OpenClaw Plugin**：Standalone 模式只支持 capture/recall/search；offload (Mermaid) 是 OpenClaw 插件功能。在 Hermes 中通过 `offload.enabled: true` 在 config 中开启（效果受限）。

3. **Docker 不是必需的**：原生 Node.js + npm 在本机直接跑，零 Docker 依赖。

4. **config.yaml 修改受网关保护**：必须用 `hermes config set` 而非直接文件写入。

5. **launchd 环境**：wrapper 脚本需同时 source `.hermes/.env` 和 `tdai-gateway.env`，因为 launchd 不继承用户 shell 环境。

6. **数据持久性**：Gateway 重启后数据不丢失（SQLite 存储在 `~/.memory-tencentdb/memory-tdai/`）。

7. **同 session 多 capture 触发管道**：默认每 5 轮触发一次 L1 提取（`everyNConversations: 5`），warmup 模式会加速初始提取。

## 测试验证

```bash
# 健康检查
curl http://localhost:8420/health

# Capture 对话
curl -X POST http://localhost:8420/capture \
  -H "Content-Type: application/json" \
  -d '{"session_key":"test","user_content":"...","assistant_content":"..."}'

# Recall 记忆 (跨 session 生效)
curl -X POST http://localhost:8420/recall \
  -H "Content-Type: application/json" \
  -d '{"query":"用户偏好","session_key":"any-session"}'
```
