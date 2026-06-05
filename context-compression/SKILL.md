---
name: context-compression
description: Extend and upgrade Hermes Agent's context compression system — StagedArchiver, knowledge fingerprinting, /uncompress command, look-ahead triggers, and schema migration patterns.
version: 1.0.0
author: Hermes Agent (curator consolidation)
metadata:
  hermes:
    tags: [compression, context-management, sqlite, archiving, slash-commands]
---

# Context Compression Development

Class-level umbrella for extending Hermes's context compression system — from adding SQLite archives and knowledge fingerprints to slash commands and look-ahead triggers.

## When to Load

- Adding archive storage for compressed messages
- Adding knowledge fingerprint extraction
- Adding slash commands that interact with compression state
- Upgrading the compression schema (SCHEMA_VERSION bumps)
- Implementing look-ahead/pre-emptive compression triggers

## Sub-Skill Map

| Workflow | Reference |
|----------|-----------|
| Extending compression (archives, fingerprints, commands) | `references/context-compression-extend.md` |
| Full upgrade workflow (StagedArchiver + schema migration) | `references/context-compression-layer-upgrade.md` |

## Architecture Overview

```
Agent Loop → should_compress() → _compress_context() → context_compressor.compress()
  ├── FastTrimmer (cheap tool result pruning)
  ├── _extract_knowledge_fingerprint() (knowledge preservation)
  ├── _generate_summary() (LLM summarization)
  └── save_compressed_archive() (SQLite persistence)
```

## Key Files

- `agent/context_compressor.py` — compression logic
- `hermes_state.py` — SQLite schema + SessionDB methods
- `run_agent/_agent_monolith.py` — agent loop integration
- `hermes_cli/commands.py` — slash command registration
- `gateway/run.py` — gateway handler routing

## Common Pitfalls

- `session_id` MUST be passed to `compress()` — otherwise archives have no session reference
- Archive BEFORE the LLM summary call, so `_previous_summary` can be saved as best-effort
- `SCHEMA_VERSION` bumps need migration blocks AND `prune_sessions` cascade cleanup
- Tests must set `last_prompt_tokens` high enough for compression to trigger
- Workspace compatibility: stash/restore to isolate uncommitted changes from test expectations
