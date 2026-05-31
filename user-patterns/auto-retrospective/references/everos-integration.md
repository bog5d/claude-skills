# EverOS (EverMind-AI) 集成评估

> 原名 "erocore"，实际项目名为 **EverOS**，由陈天桥/盛大集团全资孵化的 EverMind-AI 团队开源。

## 基本信息

| 字段 | 值 |
|------|-----|
| GitHub | `EverMind-AI/EverOS` — 4,985⭐ 531 fork |
| 协议 | Apache 2.0 |
| 语言 | Python |
| 核心组件 | EverCore（记忆OS）+ HyperMem（超图记忆架构，ACL 2026） |
| Docker | `docker compose up -d` → 需要 PostgreSQL + Redis + 向量 DB |
| REST API | `localhost:1995/health` |
| MCP Server | `uvx evermemos-mcp@latest` (PyPI: `evermemos-mcp`) |

## 三条集成路径

### A: MCP Server（推荐 — 一行配置）

Hermes 原生支持 MCP。在 `config.yaml` 添加：

```yaml
mcp_servers:
  evermemos:
    type: stdio
    command: uvx
    args: [evermemos-mcp@latest]
    env:
      EVERMEMOS_API_KEY: <从 evermind.ai 申请>
```

获得两个新工具：
- `remember` — 存入长期记忆
- `briefing` — 跨会话召回（基准 60/60 recall, P95<2s, 零幻觉归属）

### B: Docker 自部署

```bash
cd EverOS/methods/EverCore
docker compose up -d
uv sync
cp env.template .env  # 设置 LLM_API_KEY + VECTORIZE_API_KEY
uv run python src/run.py
curl http://localhost:1995/health
```

### C: Cloud API

申请 API key → 直接用 MCP server 或 REST API

## 与 Hermes 现有记忆系统对比

| 维度 | EverOS MCP | Hermes 自建 |
|------|-----------|------------|
| 架构 | Hypergraph 图记忆 | agentmemory 向量 + memory 文本 |
| 部署 | 外部 MCP server (uvx) | 零依赖 |
| 跨会话召回 | 语义超图关联 | agentmemory 语义检索 |
| 基准 | 60/60 recall | 未基准测试 |
| 成本 | API key 或自部署 | 免费 |

## 推荐策略

两条并行，互为补充：
- EverOS → 深度语义关联 + 跨时间线推理
- auto-retrospective → 轻量即时沉淀（零外部依赖）

## 来源

原始视频分析报告中的 erocore 条目实际指向此项目。
