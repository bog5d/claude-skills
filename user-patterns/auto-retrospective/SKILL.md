---
name: auto-retrospective
description: 对话结束自动复盘——提取可复用经验存入 agentmemory。受 erocore Hypergraph Memory OS 启发。
triggers:
  - "复盘"
  - "retrospective"
  - "经验沉淀"
  - "记住这次"
  - "学到了什么"
  - conversation_end_hook
---

# 自动复盘引擎 (Auto-Retrospective)

受 **erocore (Hypergraph Memory OS)** 启发——每次有意义的对话结束后，自动提取三类结构化经验，存入 agentmemory 供跨会话召回。

## 核心原则

- **被动触发**：在对话自然结束时执行（用户说"好的/谢谢/搞定/就这样"等收尾词后）
- **三类经验**：
  - 🟢 PATTERN — 成功的模式、有效的策略、新学的技能
  - 🔴 LESSON — 失败的教训、要避免的坑、已知限制
  - 🔵 DISCOVERY — 新发现的事实、环境变化、配置变更
- **LLM 驱动总结**：不是简单截取原文，而是用 LLM 提炼为可复用的结构化知识
- **跨会话召回**：存入 agentmemory，下次对话自动注入 context

## 执行时机

当用户在对话末尾使用以下任一收尾词时，自动触发复盘：
- "好的" "ok" "谢谢" "搞定" "就这样" "没问题" "可以了" "done" "thanks"
- 或用户明确说"复盘一下" / "总结一下"

## 复盘流程

### Step 1: 回顾本轮对话

用 `session_search` 回顾本轮对话的关键节点：
- 用户初衷是什么
- 你做了什么关键操作
- 结果如何
- 遇到了什么坑

### Step 2: 提取经验（LLM 分析）

基于回顾内容，提取以下三类经验：

**PATTERN（成功模式）**：
- 这次解决方法的通用模式是什么
- 有什么可以复用在类似问题上的
- 例："macOS launchd 的 HardResourceLimits 不支持 RSS 限制 → 用 system-watchdog 监控替代"

**LESSON（教训/坑）**：
- 踩了什么坑
- 什么方法不 work
- 需要避免什么
- 例："default profile 的 PID 文件在 ~/.hermes/gateway.pid 而不是 profiles/default/"

**DISCOVERY（新发现）**：
- 发现了什么新事实
- 环境有什么变化
- 用户的什么新偏好
- 例："API Gateway 已重构为 gateway 内嵌平台，旧 plist 已废弃"

### Step 3: 结构化存储

对每条经验：

1. 用 `memory` 工具存入长期记忆（简短，< 200 字）
2. 同时用 `mcp_agentmemory_memory_save` 存入 agentmemory（带 concepts 标签）
   ```
   type: pattern|lesson|discovery
   concepts: 逗号分隔的关键词
   files: 涉及的文件路径
   ```

### Step 4: 告知用户

简洁汇报：
> 🧠 复盘完成：提取了 2 PATTERN + 1 LESSON + 1 DISCOVERY

## 反模式（不要做的）

- ❌ 不要每条对话都复盘——只在有实质性内容时
- ❌ 不要复盘纯闲聊
- ❌ 不要存入超过 500 字的经验（会被截断）
- ❌ 不要存入临时状态（如"这次用了 PID 12345"）
- ❌ 不要替换用户已有的重要记忆

## 与现有系统集成

- **memory 工具**：存入长期记忆（注入每轮 prompt）
- **agentmemory MCP**：存入结构化记忆（语义检索）
- **session_search**：回顾历史对话
- **mem0_conclude**：存入用户偏好类经验
- **skill_manage**：发现可复用工作流时，主动创建/更新 skill

## 外部参考

- `references/everos-integration.md` — EverOS (EverMind-AI) 集成评估：MCP 直连 vs Docker 自部署 vs Cloud API
