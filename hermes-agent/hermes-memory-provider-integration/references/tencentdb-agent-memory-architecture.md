# TencentDB Agent Memory 架构详解

> 来源：GitHub TencentCloud/TencentDB-Agent-Memory (Apache 2.0)，实测于 2026-06-04

## 四层记忆架构

```
L3 用户画像 (Persona)
  ↑ 可追溯
L2 场景聚类 (Scene Blocks)
  ↑ 可追溯
L1 原子事实 (Atomic Facts)
  ↑ 可追溯
L0 原始对话 (Raw Conversations)
```

### L0 — 原始对话
- SQLite + JSONL 全量存储
- 兜底层，随时可回查原始消息

### L1 — 原子事实
- LLM 自动从对话提取独立事实节点
- 打标签、去重（向量相似度）
- 每条保留 source 引用（指向 L0）

### L2 — 场景聚类
- 相关原子事实按场景聚合
- 生成 Markdown 文件（人可直接读）
- 例：`编程语言偏好-Rust-TypeScript.md`

### L3 — 用户画像
- 基于 L0-L2 生成稳定用户画像
- 包含：核心原型、长期偏好、决策逻辑、沟通策略、深层洞察
- 完整追溯链：L3 画像 → L2 场景 → L1 事实 → L0 对话

## 短期记忆：Mermaid 符号压缩

- 工具日志卸载到外部文件 (`refs/*.md`)
- Mermaid 语法编码任务状态图（token 密度极高）
- `node_id` 按需回查原始日志
- 实测：token 省 50%+，任务完成率升 23%

## 检索：BM25 + Embedding 双路 RRF

- BM25（jieba 中文分词）→ 精确命中
- Embedding（sqlite-vec 本地向量）→ 语义匹配
- RRF (Reciprocal Rank Fusion) 融合排序
- 无需外部 Embedding 服务即可运行（keyword-only 模式）

## 与 Hermes 现有记忆栈对比

| 能力 | Agent Memory | 我们现有 | 差距判断 |
|------|-------------|---------|---------|
| 原始对话留存 | ✅ SQLite 全量 | ✅ SessionDB FTS5 | 持平 |
| 原子事实自动提取 | ✅ LLM 提取+打标签 | ⚠️ 三层记忆 skill 骨架，LLM 提取基础 | 明显差距 |
| 场景/主题聚类 | ✅ 按场景聚合，Markdown | ❌ 没有 | 核心缺失 |
| 用户画像自动生成 | ✅ 全自动 L0-L3 推导 | ⚠️ 手动 USER_PROFILE.md | 有差距 |
| 追溯链 | ✅ L3→L2→L1→L0 | ❌ 没有 | 核心缺失 |
| 短期记忆压缩 | ✅ Mermaid 图 | ⚠️ StagedArchiver token 截断 | 代际差距 |
| 双路检索+RRF | ✅ BM25+Embedding | ⚠️ EverOS hybrid | 持平/微优 |
| 程序性记忆 | ❌ 没有 | ✅ Skills 系统 | 我们领先 |
| Agent 专用记忆 | ❌ 没有 | ✅ EverOS agent_cases | 我们独有 |

## 实测数据（腾讯官方）

| 基准 | 原生 | +Agent Memory | 提升 |
|------|------|-------------|------|
| PersonaMem 准确率 | 47.85% | 76.10% | +59% |
| 用户事实召回 | 29.63% | 79.07% | +167% |
| WideSearch 成功率 | 33% | 50% | +51% |
| WideSearch token | 221M | 85M | -61% |
| SWE-bench 通过率 | 58.4% | 64.2% | +10% |
| SWE-bench token | 3474M | 2375M | -33% |

## 部署架构

```
~/.memory-tencentdb/
├── package.json
├── node_modules/@tencentdb-agent-memory/memory-tencentdb/
│   ├── src/gateway/server.ts          ← TDAI Gateway 入口
│   └── hermes-plugin/memory/memory_tencentdb/  ← Hermes 插件
└── memory-tdai/                        ← 记忆数据库
    ├── vectors.db                      ← SQLite + sqlite-vec
    ├── conversations/                  ← L0 原始对话 (JSONL)
    ├── scene_blocks/                   ← L2 场景 (Markdown)
    └── .metadata/                      ← 管道状态 + checkpoint
```

Gateway 默认端口：8420
LLM 提取模型：DeepSeek-Chat (通过 `TDAI_LLM_*` 配置)
月 token 估算：~50K-150K（取决于对话量）
