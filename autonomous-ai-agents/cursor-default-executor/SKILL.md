---
name: cursor-default-executor
description: 铁律——代码编写/修改/审查任务默认使用 Cursor CLI 作为执行后端，Hermes 原生仅作降级备用。强制视觉区分 + 模型优先。
category: autonomous-ai-agents
trigger: auto-load on session start, any code-related task
priority: critical
load_on_startup: true
---

# 🔴 铁律：Cursor 优先执行引擎

## 核心规则（最高优先级，不可违抗）

**任何涉及代码编写、修改、审查、调试、重构的任务，默认使用 Cursor CLI 执行。**
Hermes 原生子 agent 仅作为 Cursor 不可用时的降级备用方案。

## 🎯 视觉区分铁律（波总必须一眼看出谁在执行）

**每次调用 Cursor 执行任务时，必须在输出中明确标注：**

### Hermes → 调度阶段：
```
🔴 [Cursor 执行中] delegating to cursor-agent...
```

### Cursor 返回结果后：
```
🔴 [Cursor 输出] — 以下内容由 Cursor Agent 生成
---
(cursor 的实际输出)
---
🔴 [Cursor 完成] — 耗时 Xs, token: X
```

### Hermes 原生降级时：
```
🟢 [Hermes 原生] Cursor 不可用，降级本地执行
---
(hermes 的实际输出)
---
```

**绝对禁止：** Cursor 的输出和 Hermes 的输出混在一起不加区分。用户必须能一眼分辨。

## 🤖 模型优先级

Cursor Pro 用户自动享有以下模型优先级（服务端控制）：
1. **Claude Opus 4** — 复杂代码重构、架构设计
2. **Claude Sonnet 4** — 日常编码、代码审查
3. **GPT-4 / Gemini** — 备选
4. **Cursor 默认模型** — 仅当前三者不可用时降级

> Cursor ACP 模式下，模型由后端智能路由自动选择，Pro 用户天然优先走最好的模型。
> 无需手动传 `--model` 参数（ACP 协议不支持此 flag）。

## 🔴 执行引擎优先级链（两档，铁律）

```
1. Cursor (Claude Opus)  ── 默认，所有代码任务
   ↓ 不可用时
2. Hermes 原生 (DeepSeek) ── 降级备用
   ↓ 特定场景手动指定
3. Aider (DeepSeek)  ── 仅超大repo重构需repo-map索引时，手动调用
```

**Aider 不作为自动降级层。** 原因：Aider 底层也是 DeepSeek，与 Hermes 原生同模型，但工具链更窄（只有代码编辑），且多一层桥接开销。仅在需要 repo-map 索引的特定场景手动调用。

Aider 调用方式（手动）：
```bash
python3 ~/aider_workspace/bridge_cmd.py "任务描述" --cwd /path/to/project
```

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

## 录音/长内容处理调度（2026-08-11 波总约定）

**波总发来录音/长口述/会议转写需要处理时，Hermes 作为总调度，优先派遣 Cursor CLI 执行全部完成动作**（转写提炼、副官拆解、同步仓库）。

原因（波总明确）：Cursor 订阅月额度大量未用完，直接调 DeepSeek 计费。用 Cursor CLI 测试论证可行性。

### 处理流程
1. 收到录音/长内容 → 标注 `🔴 [Cursor 执行中] delegating to cursor-agent...`
2. `delegate_task(goal="处理录音: 原始稿→清洗稿→副官拆解→同步仓库", acp_command="cursor-agent", acp_args=["--acp", "--stdio"])`
3. 传入仓库路径：`~/AI_Workspaces/Cangjie_OBS_Notes`（先读 交接手记/START_HERE.md）
4. Cursor 完成 → 标注 `🔴 [Cursor 输出]` + 耗时
5. Hermes 收到后**必须验证**：检查 source_id 是否生成、台账是否更新、validate_repo.py 是否通过、git push 是否成功（子代理自报不可信，主代理验证侧效应）
6. 若 Cursor 不可用/失败 → 降级 Hermes 原生，标注 `🟢 [Hermes 原生]`

### 调度注意事项
- Cursor 输出是"完成动作"（写文件、git push），Hermes 负责校验和汇报
- 录音文件位置与处理权限需在 goal 中写明绝对路径
- 处理回执按仓库协议：写入了什么、存疑什么、下一步

## 跨 AI 同步

此铁律已写入：
- `~/.hermes/skills/autonomous-ai-agents/cursor-default-executor/SKILL.md`（本文件）
- Hermes 持久化 memory
- Adjutant 仓库 `AGENTS.md`（供 Claude/Cursor/Copilot 等其他 AI 读取）
- 所有 profile 通过 `sync_skills_cross_profile.sh` 自动同步
