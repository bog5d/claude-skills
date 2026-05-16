---
name: Hermes Integration Assessment
description: Deep-read Hermes source code to map component architecture and assess external project integration feasibility
trigger: When user wants to introduce a new open-source project into Hermes and needs to know if it's worth it and how to do it
tags: [architecture, integration, assessment, planning]
---

## Overview

Evaluate whether an external open-source project is worth integrating into Hermes Agent, and if so, how. Uses Cursor (ACP delegate) to deep-read Hermes's own source code, mapping each component's strengths and weaknesses, then cross-references against the external project's capabilities.

## When to Use

- User provides a list of trending open-source projects and asks "which should we integrate?"
- User suggests a specific project (e.g., "should we use n8n?")
- Need to decide between integration approaches: MCP bridge, direct integration, component replacement, or just borrow design ideas
- Before making architectural investments that could turn out to be wrong

## Steps

### 1. Gather the candidate list

Accept the user's list of projects. If none provided, ask.

### 2. Deep-read Hermes's own source code (via Cursor delegate)

This is the critical step. Do NOT guess what Hermes can/can't do based on memory alone. Have Cursor deep-read the actual code:

**Core files to inspect:**

| File | What it reveals |
|------|----------------|
| `tools/registry.py` | Tool registration architecture |
| `tools/mcp_tool.py` | MCP client depth (sampling, dynamic discovery, reconnection) |
| `tools/delegate_tool.py` | Subagent isolation, parallelism, depth limits |
| `tools/send_message_tool.py` | Cross-platform messaging |
| `agent/memory_manager.py` | Memory plugin system |
| `agent/prompt_builder.py` | System prompt assembly, skill injection |
| `agent/context_compressor.py` | Token compression strategy |
| `agent/auxiliary_client.py` | Provider routing (often messy, good to check line count) |
| `hermes_state.py` | Session DB (FTS5, WAL, concurrency) |
| `gateway/run.py` | Platform adapter architecture |
| `gateway/platforms/*.py` | Individual adapter complexity |
| `cron/scheduler.py` | Tick-based scheduling, file locks |
| `cron/jobs.py` | Job CRUD, `_recoverable_oneshot_run_at`, grace windows |
| `plugins/memory/` | Available memory providers (mem0, honcho, hindsight) |

**How to invoke:**
```python
from hermes_tools import delegate_task
# Pass the file list as context, ask Cursor to read each one and map the architecture
```

### 3. Map each component's maturity

Grade each Hermes component on:
- **Maturity**: (1-5 stars) based on error handling, edge case coverage, test coverage
- **Deficits**: What capabilities are missing (NOT what could be "better")
- **Pain points**: User-facing issues vs developer-facing maintenance burden

### 4. Cross-reference against each candidate project

For each external project, ask:
- Does it solve a **real deficit** (not a "nice to have")?
- What's the **integration cost**: lines of code changed, new dependencies, operational overhead?
- **Integration approach**:
  - *MCP bridge*: Hermes MCP client already supports tools, sampling, dynamic discovery. Just configure in config.yaml. Zero code change.
  - *Direct integration*: New tool file + registry registration + run_agent.py wiring. 1-2 files to create.
  - *Component replacement*: Replace existing module (e.g., cron → Temporal). High risk, needs thorough testing.
  - *Design reference only*: Don't integrate the code, just borrow the idea.

### 5. Generate the prioritization matrix

```
                    High impact
                        │
                   P0   │   P0
                        │
            Low risk ───┼─── High risk
                        │
                   P2   │   P1
                        │
                   Low impact
```

- **P0**: High impact, low risk → Do immediately (e.g., Mem0 via config)
- **P1**: High impact, high risk → Plan carefully (e.g., Temporal replacing cron)
- **P2**: Low impact, low risk → Nice to have, defer (e.g., LiteLLM)
- **Ignore**: Low impact, high risk → Don't

### 6. Produce a final deliverable

Write an MD report covering:
- Quick conclusion table (P0/P1/P2/Ignore)
- Hermes current capability map
- Per-project deep analysis with integration approach
- Action items with estimated effort
- Test plan: "how does the user tell the difference before vs after"

## Pitfalls to Avoid

1. **Don't assume the MCP bridge is the only way** — Hermes already has native memory providers (mem0 plugin). Check `plugins/memory/` before suggesting MCP bridge.
2. **Don't guess about Hermes's capabilities** — always delegate Cursor to read the actual code. The code is the source of truth, not your memory.
3. **Don't ignore the config** — Always check `~/.hermes/config.yaml` and `~/.hermes/.env`. Many features are already integrated but not activated (memory.provider='' means Mem0 is dormant).
4. **Don't recommend n8n for Agent use cases** — Hermes's MCP + delegate_task + cron can cover 90% of workflow scenarios. n8n is a low-code platform, too heavy for an Agent.
5. **Integration cost ≠ lines of code** — MCP bridge = 0 code change but adds a dependency process. Direct integration = 100-300 lines but no external dependency. Choose based on reliability needs, not LOC.

## Verification / Test Plan

After any integration, the user needs to feel the difference:

| Scenario | Before | After |
|----------|--------|-------|
| "Remember X" + ask "what was X?" days later | FTS5 keyword only | Semantic search finds it |
| "Fix this bug in file Y" | patch-based, error-prone | Aider handles file-aware edits |
| "Daily report at 9 AM" | single-machine, no retry | Distributed, retry on failure |

Each integration should have a 5-minute "wow" test the user can run.

## Related Skills

- `system-scanning-and-migration-analysis` — broader system-level scanning (processes, project inventory)
- `plan` — for the planning phase before execution
- `subagent-driven-development` — for executing the actual integration work
