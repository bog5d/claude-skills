# TencentDB Agent Memory — 评估与集成分析

> 评估日期：2026-06-04 | 项目 GitHub：https://github.com/TencentCloud/TencentDB-Agent-Memory

## 概览

腾讯云数据库团队开源，Apache 2.0，两个月 4600+ Star。核心能力：**四层渐进式记忆架构 + Mermaid 短期记忆压缩 + BM25/Embedding 双路 RRF 检索**。

## 四层架构

```
L3 用户画像 ←── 可追溯
L2 场景聚类 ←── 可追溯（Markdown，人可读）  
L1 原子事实 ←── 可追溯（自动提取+打标签）
L0 原始对话（SQLite 全量保留）
```

## 两个杀手级差异化能力

### 1. 短期记忆压缩：Mermaid 任务状态图
- 把长任务日志卸载到外部文件
- 用 Mermaid 语法画紧凑的任务状态图塞进上下文
- Token 消耗降 50%+，任务完成率升 23%
- **对比我们的 StagedArchiver**：token 暴力截断 vs 结构化压缩，代际差距

### 2. 双路检索 + RRF 融合排序
- Embedding 模糊匹配 + BM25 精确命中 → RRF 融合
- 语义相关的不会漏，精确匹配的不会丢

## 基准测试数据

| 指标 | 原生 OpenClaw | 接入 Agent Memory | 提升 |
|------|-------------|------------------|------|
| 总准确率 | 47.85% | 76.10% | +59% |
| 用户事实召回 | 29.63% | 79.07% | +167% |
| 偏好跟踪 | 66.67% | 83.45% | +25% |
| 个性化推荐 | 46.67% | 76.36% | +64% |
| WideSearch 成功率 | 33% | 50% | Token 省 61% |
| SWE-bench 通过率 | 58.4% | 64.2% | Token 省 33% |

## vs 我们现有记忆栈

| 能力 | 我们 | Agent Memory | 差距 |
|------|------|-------------|------|
| 原始对话留存 | Session FTS5 ✅ | SQLite 全量 ✅ | 持平 |
| 原子事实提取 | 三层记忆骨架（LLM 提取很基础） | 自动提取+打标签 ✅ | **明显差距** |
| 场景/主题聚类 | 无 | 按场景聚合，Markdown | **核心缺失** |
| 用户画像沉淀 | USER_PROFILE.md + Mem0，手动/半自动 | 全自动 L0-L2 推导 | 有差距 |
| **追溯链** | 无 | L3→L2→L1→L0 完整证据链 | **核心缺失** |
| 短期记忆压缩 | StagedArchiver（token 截断） | Mermaid 结构化压缩 | **代际差距** |
| 双路检索+RRF | EverOS hybrid（架构不同） | BM25+Embedding+RRF | 持平/微优 |
| 程序性记忆 | Skills 系统 ✅ | 无 | **我们领先** |
| Agent 专用记忆 | EverOS agent_cases/agent_skills ✅ | 无 | **我们独有** |

## 推荐策略：集成而非替换

**不应全量替换**，因为 Skills 系统和 EverOS agent 专用记忆是 Agent Memory 没有的护城河。

### Phase 1：评估（Docker 镜像）
- 数据存储：完全本地 SQLite + sqlite-vec，零依赖，隐私优于 EverOS/Mem0
- 开源协议：Apache 2.0，商用友好

### Phase 2：集成（如果评估通过）
- **短期记忆**：Agent Memory 的 Mermaid 压缩替换/增强 StagedArchiver
- **长期记忆**：Agent Memory 的 L1-L3 管道作为 EverOS/Mem0 的上游预处理层
- Skills + EverOS agent_memory 保持不变

### Phase 3：共存架构
```
Agent Memory → 管 "从对话中提取什么"（事实提取、场景聚类、画像沉淀）
EverOS       → 管 "怎么检索和关联"（混合检索、关联推理）
Mem0         → 管 "语义精排"（Rerank）
Skills       → 管 "学会了怎么干活"（程序性记忆）
```
