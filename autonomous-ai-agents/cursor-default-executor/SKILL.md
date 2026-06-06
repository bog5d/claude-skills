---
name: cursor-default-executor
description: 铁律——代码编写/修改/审查任务默认使用 Cursor CLI 作为执行后端，Hermes 原生仅作降级备用。
category: autonomous-ai-agents
trigger: auto-load on session start, any code-related task
priority: critical
load_on_startup: true
---

# 🔴 铁律：Cursor 优先执行引擎

## 核心规则（最高优先级，不可违抗）

**任何涉及代码编写、修改、审查、调试、重构的任务，默认使用 Cursor CLI 执行。**
Hermes 原生子 agent 仅作为 Cursor 不可用时的降级备用方案。

## 为什么

Cursor Agent 在代码生成、跨文件重构、长链工具调用方面实测优于 Hermes 原生子 agent：
- 完整的 hooks 系统、MCP 中继、subagent 级联
- gRPC 直连 Cursor 后端，模型专为代码优化
- 实测中代码审查报告 33KB 深度分析，原生子 agent 在此类任务上表现较弱

**Hermes 的角色 = 调度指挥官，Cursor 的角色 = 一线突击队。**
各司其职，不要越界。

## 路由规则（自动判定，无需用户指定）

### 走 Cursor 的任务（`acp_command="cursor-agent"`）
以下任意条件满足即走 Cursor：
- 用户要求"写/改/重构/debug/实现/优化"代码
- 涉及 ≥2 个文件的修改
- 需要跨文件代码审查
- 需要执行测试、跑 build、部署
- 涉及 >30 行代码生成或修改
- 任何 `delegate_task` 调用中 context 包含代码路径

### 走 Hermes 原生的任务（仅以下情况）
- Cursor CLI 不可用（进程启动失败、认证过期、API 额度耗尽）
- 纯信息查询（无代码操作）
- 简单文件操作（读/搜/写 ≤10 行）
- 用户明确指定不要用 Cursor

## 调用方式

```python
delegate_task(
    goal="...",
    acp_command="cursor-agent",
    acp_args=["--acp", "--stdio"]
)
```

## 降级策略

如果 Cursor 三次启动失败或返回错误：
1. 告知用户 Cursor 不可用及原因
2. 自动降级为 Hermes 原生子 agent
3. 在结果中标注"⚠️ 已降级为 Hermes 原生执行"

## 例外

- 用户说"不要用cursor"或"你自己做" → 跳过此规则
- 用户在对话中明确切换执行引擎 → 尊重选择
- Cursor 额度耗尽 → 告知用户，降级 Hermes

---

## 跨 AI 同步

此铁律已写入：
- `~/.hermes/skills/autonomous-ai-agents/cursor-default-executor/SKILL.md`（本文件）
- Hermes 持久化 memory
- Adjutant 仓库 `AGENTS.md`（供 Claude/Cursor/Copilot 等其他 AI 读取）
- 所有 profile 通过 `sync_skills_cross_profile.sh` 自动同步
