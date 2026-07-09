---
name: loop-engineering-integration
description: Inject the open-source loop-engineering pattern (https://github.com/cobusgreyling/loop-engineering) into any project — audit, init, customize, validate budget. For Cursor/Codex/Claude Code toolchains.
triggers:
  - 'loop engineering'
  - 'loop-init'
  - 'loop-audit'
  - 'inject loop'
  - 'add loop to project'
  - 'set up daily triage'
  - 'AI agent running loop'
  - 'Boris loop prompt AI'
---

# Loop Engineering Integration

Inject the [loop-engineering](https://github.com/cobusgreyling/loop-engineering) pattern into a project. Core idea: "You no longer prompt AI yourself — you write a loop and let the loop prompt AI."

## Prerequisites

- Node.js (the CLI tools are TypeScript/Node)
- Git (shallow clone the upstream repo)
- Target project must exist and have a git repo

## Step-by-Step Workflow

### 1. Clone upstream repo

```bash
git clone --depth 1 https://github.com/cobusgreyling/loop-engineering.git /tmp/loop-engineering
```

> **PITFALL:** The `@cobusgreyling/loop-engineering` npm package is NOT published. Do NOT try `npx` — use git clone + local build instead.

### 2. Build CLI tools (on-demand, not all at once)

```bash
# loop-audit: scores project on loop readiness (0-100, L0-L3)
cd /tmp/loop-engineering/tools/loop-audit && npm ci && npm run build

# loop-init: injects loop structure (STATE.md, LOOP.md, skills, agents)
cd /tmp/loop-engineering/tools/loop-init && npm ci && npm run build

# loop-cost: estimates daily token spend
cd /tmp/loop-engineering/tools/loop-cost && npm ci
# (loop-cost dist/ is pre-built; no npm run build needed)
```

> **PITFALL:** Even when `dist/` exists pre-built, `npm ci` is still required for runtime dependencies (yaml, etc.).

### 3. Run loop-audit for baseline

```bash
cd /path/to/target-project
node /tmp/loop-engineering/tools/loop-audit/dist/cli.js
```

Output: score (0-100) and level (L0-L3). L0 = nothing. L3 = full loop.

### 4. Dry-run loop-init first

```bash
node /tmp/loop-engineering/tools/loop-init/dist/cli.js \
  --pattern daily-triage \
  --tool codex \
  --dry-run
```

Pick `--tool` based on what the project already uses:
- `codex` — if `.codex/` directory exists or project uses Codex CLI
- `claude` — if project uses Claude Code
- `cursor` — if Cursor is the primary IDE (check what ACP transport is configured)

### 5. Run loop-init for real

```bash
node /tmp/loop-engineering/tools/loop-init/dist/cli.js \
  --pattern daily-triage \
  --tool codex
```

This injects ~9 files:
- `STATE.md` — cross-session memory (High Priority / Watch List / Noise)
- `LOOP.md` — loop configuration (cadence, toolchain, human gates)
- `loop-budget.md` — daily token budget and kill switch
- `loop-constraints.md` — push/merge/path/budget rules
- `loop-run-log.md` — JSON append-only run log
- `.codex/skills/loop-triage/SKILL.md` — triage skill
- `.codex/skills/loop-budget/SKILL.md` — budget check skill
- `.codex/skills/loop-constraints/SKILL.md` — constraints reading skill
- `.codex/agents/verifier.toml` — maker/checker sub-agent

> **PITFALL:** After injection, loop-audit will report 100/100 (L3). This is a FALSE score — it only means templates exist, not that they're customized. The real work starts now.

### 6. Customize the injected files

**Must customize:**
- `STATE.md`: Replace "My Project" with actual project name, fill Current Sprint (version, test baseline, start commands, test commands)
- `LOOP.md`: Fill toolchain table, update active loops, align human gates with AGENTS.md rules, set L1/L2/L3 level
- `loop-budget.md`: Replace "YOUR_PROJECT", set realistic daily cap based on loop-cost output, add kill switch instructions
- `loop-constraints.md`: Translate AGENTS.md rules into constraint format (push rules, merge rules, path rules, environment rules), add `l1-only` constraint to start
- `loop-run-log.md`: Replace project name in header, keep JSON array empty

**Optionally customize:**
- `.codex/skills/loop-triage/SKILL.md` — adjust input sources (CI, issues, commits)
- `.codex/agents/verifier.toml` — adjust check list

### 7. Validate with loop-cost

```bash
node /tmp/loop-engineering/tools/loop-cost/dist/cli.js
```

> **NOTE:** loop-cost uses its internal registry to estimate cadence. For "daily-triage" it defaults to 12 runs/day. If your actual LOOP.md says 1 run/day, mentally divide by 12. The per-run token estimate is still valid (~50k for full triage, ~5k for no-op).

### 8. Commit and decide on automation

Files are injected as untracked. Do NOT auto-commit — let the human review first.

For cron-based automation: create a Hermes cronjob that triggers the loop at the configured cadence. Start with L1 (report-only, no code changes).

## Level Progression

| Level | Mode | What it does |
|-------|------|-------------|
| L0 | Nothing | No loop structure at all |
| L1 | Report only | Reads STATE.md + git log → generates report → human decides |
| L2 | Attempt fix | L1 + if fix is small, attempt in isolated worktree → create draft PR |
| L3 | Full auto | L2 + auto-merge (NEVER enable without explicit human approval) |

**Rule:** Always start at L1. Run 2+ weeks. If reports are accurate (no false positives), ask for approval to upgrade.

## 三层与现有工具链的配合

- **Hermes** — 调度层：cron 定时触发，Telegram 推送报告
- **Cursor** — 人的主力 IDE，loop 不干扰
- **Codex / Claude Code** — 执行层：loop 的实际 runner
- **loop-engineering** — 品控层：标准化 loop 结构，跨项目可移植

## References

- [cangjie-fos-example.md](references/cangjie-fos-example.md) — 仓颉 FOS 的完整注入记录（会话复现）
- Upstream: https://github.com/cobusgreyling/loop-engineering
