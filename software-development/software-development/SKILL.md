---
name: software-development
description: Complete software development workflow — planning, execution, code review, TDD, debugging, subagent delegation, and project triage. Covers the full lifecycle from idea to verified implementation.
---

# 软件开发全流程

## 1. 规划与计划

### writing-plans — 实施计划
将需求拆解为 2-5 分钟的 bite-sized 任务，包含完整文件路径、代码示例、验证命令。
原则：DRY, YAGNI, TDD, 频繁提交。

### plan — 纯规划模式
写入 `.hermes/plans/` 下的 markdown 计划，不执行。用于需要规划但不立即实现的场景。

### prototype — 多变体方案生成
针对需求生成 3+ 差异化方案（A/B/C），启动预览，等待选型。

### spike — 可行性验证实验
Throwaway 实验验证想法可行性。流程：分解 → 研究 → 构建 → 判决（VALIDATED/PARTIAL/INVALIDATED）。

### phase-planning-workflow — 阶段规划
代码扫描 + 行业趋势研究 + 能力差距分析 → 可执行周计划。适用于里程碑后决定下一步方向。

## 2. 执行与审查

### subagent-driven-development — 子代理驱动开发
通过 `delegate_task` 分发子代理执行计划，每任务两轮审查（规格合规 + 代码质量）。
铁律：每个任务用新鲜子代理，规格审查先于质量审查。

### requesting-code-review — 预提交代码审查
安全扫描 + 质量门禁 + 独立审查子代理 + 自动修复循环（最多 2 次）。
铁律：不要让实现者自己审查自己的工作。

### test-driven-development — 测试驱动开发
RED-GREEN-REFACTOR 循环。铁律：没有失败测试的生产代码 = 不存在。
步骤：写失败测试 → 验证失败 → 最小实现 → 验证通过 → 重构。

### converge-bare-exceptions — 消除裸异常
系统性替换 `except Exception` 为具体异常类型。
操作：grep 审计 → 上下文分析 → 操作→异常映射 → 批量替换 → 测试验证。

## 3. 调试

### systematic-debugging — 四阶段根因调试
铁律：没有根因调查就不许修复。
四阶段：①根因调查 ②模式分析 ③假设测试 ④实施修复。
3 次修复失败 = 架构问题，停止并讨论。

### debugging-hermes-tui-commands — TUI 命令调试
Hermes 斜杠命令跨三层（Python 注册 → Gateway JSON-RPC → Ink 前端）的调试流程。
排查：命令在 TUI 出现但不在自动补全 / CLI 正常 TUI 不正常 / 配置持久化但 UI 不实时更新。

## 4. 项目理解

### codebase-triaging-protocol — 陌生代码库评估协议
六步：确认最新 → 三路并行采集（README/AGENTS/CHANGELOG）→ 架构理解 → 现状评估 → 结构化输出 → 等待确认。
铁律：不能跳步，不能分析完直接开干。

### handoff — 工作交接协议
会话结束前生成 handoff.md，记录项目结构、已完成决策、遗留问题、下一步指令。
任何 AI 读完即可无缝接盘。

## 5. 任务编排

### task-graph-dag — DAG 任务图
多步并行任务编排系统。支持：拓扑排序、循环检测、并行执行、超时控制、重试、跨步骤数据传递。

## 6. 自改进

### self-improvement-mechism
对话完成后自动反思：提取成功/失败模式、生成错误指纹、存储经验到语义记忆、检测技能候选。
触发条件：≥3 次工具调用。技能候选：≥8 次调用。

## 7. 调试工具

### python-debugpy — Python 远程调试
通过 debugpy 附加 Python REPL 进行交互式调试。

### node-inspect-debugger — Node.js 远程调试
通过 --inspect + Chrome DevTools Protocol 调试 Node.js。

## 支持文件
- `references/tdd-checklist.md` — TDD 验证清单
- `references/debugging-flowchart.md` — 调试决策树