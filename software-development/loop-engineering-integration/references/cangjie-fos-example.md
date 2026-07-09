# 仓颉 FOS — Loop Engineering 注入记录

会话日期: 2026-07-09
项目: /Users/mac/cangjie-fos (v1.9.6, master)

## 注入前状态

- loop-audit 得分: **29/100 (L0)**
- 项目已有 AGENTS.md (305行, v1.9.6), .cursor/rules/, .codex/ 目录
- 测试基线: 803 passed (backend tests, excluding test_doctor_script.py)
- 启动: `cd backend && uv run uvicorn cangjie_fos.main:app --reload --port 8000`
- 测试: `cd backend && uv run --extra dev pytest tests/ --ignore=tests/test_doctor_script.py -q`
- AGENTS.md 已有 push hook 和 commit 规则

## 注入参数

```bash
node /tmp/loop-engineering/tools/loop-init/dist/cli.js \
  --pattern daily-triage \
  --tool codex
```

选择 `--tool codex` 的依据: 项目已有 `.codex/` 目录 + CODEX_TASKS.md，AGENTS.md 提到 Codex 自动测试收件箱。

## 注入的文件 (9个)

| 文件 | 定制程度 | 关键定制内容 |
|------|---------|-------------|
| STATE.md | 重度 | 项目名→仓颉 FOS, v1.9.6, 803 passed, 启动/测试命令, HP/Watch/Noise/TechDebt 区域 |
| LOOP.md | 重度 | 工具链表(Hermes M2/Cursor/Codex), L1 report-only, Human Gates 对齐 AGENTS.md |
| loop-budget.md | 重度 | 项目名→仓颉 FOS, 100k tokens/天, 1次/天, kill switch 指令 |
| loop-constraints.md | 重度 | 6类约束全部填入具体规则(never-commit-all, no-light-skip, always-full-test...) |
| loop-run-log.md | 轻度 | 模板JSON数组, 示例条目含timestamp/loop/level/tool/budget/summary/issues |
| .codex/skills/loop-triage/SKILL.md | 未修改 | 原样保留 |
| .codex/skills/loop-budget/SKILL.md | 未修改 | 原样保留 |
| .codex/skills/loop-constraints/SKILL.md | 未修改 | 原样保留 |
| .codex/agents/verifier.toml | 未修改 | maker/checker 分离, 默认 REJECT |

## loop-cost 结果

单次 full triage: ~50k tokens
每日预算: 100k tokens
每日运行: 1次

结论: 预算充足（50k << 100k），无 overrun 风险。

## 定制化要点

### STATE.md 关键字段
- 项目名称从 "My Project" → "仓颉 FOS (Cangjie FOS)"
- 版本从 "1.0.0" → "v1.9.6"
- 填入测试基线 803 passed
- 启动命令和测试命令直接可用
- High Priority 区留空待填充
- Watch List 区留空待填充
- Noise 区留空待填充
- Tech Debt 区留空待填充

### LOOP.md 关键配置
- Toolchain 表: Hermes M2(调度) / Cursor(IDE) / Codex CLI(执行) / Claude Code(备用)
- Active Loops: Daily Triage L1 report-only
- Human Gates:
  - 禁止 `git add -A`（AGENTS.md § Anti-Patterns）
  - 禁止把 skip 当垃圾桶
  - pre-push 全量 pytest 必须绿
  - 禁止 force push 到 shared branches
  - 任何 agent 代码修改必须先过测试
  - Check lint 跑 ruff
- Worktrees: 用于 L2+ 隔离修复
- Connectors: GitHub Issues / PRs, 本地 git log

### loop-constraints.md 六类规则
1. Push Rules: never-commit-all, no-light-skip, always-full-test
2. Merge Rules: human-merge-only, draft-pr-first
3. Path Rules: backend-code-only, no-generating-config-mix
4. Token Budget: 100k/日, 超限通知 Hermes, kill switch
5. Agent Delegation: no-chains, verifier-must-check
6. Environment Rules: python-venv, node-not-required

## 注入后状态

- loop-audit 不再重新运行（模板齐全理论 100/100，但定制化后才算真实启用）
- 文件全部为 untracked (git status 未提交)
- 原始项目已有修改未提交: roadshow.py, test_roadshow_api.py, PitchUploadWizard.tsx, RoadshowWizard.tsx

## 下一步 (供后续会话参考)

1. `git add` loop 文件并 commit
2. 配置 Hermes cron job 实际触发 Daily Triage
3. 试运行 L1 2周，只报告不改代码
4. 观察报告准确率后再决定是否升级到 L2
