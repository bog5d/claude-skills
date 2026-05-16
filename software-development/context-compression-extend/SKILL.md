---
name: context-compression-extend
description: Pattern for extending Hermes Agent's context compression system with archive storage, knowledge fingerprinting, and slash commands. Covers the StagedArchiver integration pattern.
version: 1.0.0
metadata:
  hermes:
    tags: [compression, context-management, sqlite, archiving, slash-commands]
    related_skills: [systematic-debugging, test-driven-development]
---

# Context Compression Extension Pattern

## When to Use

When adding new functionality to Hermes's context compression system (`agent/context_compressor.py`, `hermes_state.py`), specifically:
- Archiving pre-compression messages for later recovery
- Adding knowledge fingerprint extraction from compressed messages
- Adding new slash commands that interact with compression state
- Adding look-ahead/pre-emptive compression triggers

## Architecture Overview

The compression system has 3 layers:

```
Agent Loop (run_agent/_agent_monolith.py)
  → should_compress()  — decides WHEN to compress
  → _compress_context() — orchestrates compression + session split
    → context_compressor.compress() — core compression logic
      → FastTrimmer (cheap tool result pruning)
      → _extract_knowledge_fingerprint() — knowledge preservation
      → _generate_summary() — LLM summarization
      → save_compressed_archive() — SQLite persistence
```

SQLite schema (`compressed_archives` table):
```
id, session_id, compression_round, archived_at,
summary_text, knowledge_fingerprint, n_messages,
n_tokens_saved, messages_json
```

## Key Points

### 1. SessionDB Integration
When passing `session_db` to ContextCompressor:
- Add `session_db: Any = None` parameter to `__init__`
- Store as `self.session_db`
- DEFAULT to None so existing consumers (tests, manual compression) don't break
- In `_agent_monolith.py`, pass `session_db=getattr(self, "_session_db", None)`

### 2. session_id MUST be passed to compress()
The call site in `_compress_context()` was:
```python
compressed = self.context_compressor.compress(messages, current_tokens=approx_tokens)
```
Fix: add `session_id=self.session_id or ""` — otherwise the archive has no session reference.

### 3. Archive Timing
Insert the archive step AFTER computing `turns_to_summarize` but BEFORE the LLM summary call. At this point we know exactly which messages will be lost, and the summary hasn't been generated yet so we can save `self._previous_summary` as a best-effort record.

### 4. Knowledge Fingerprint
Extract from messages being compressed:
```python
def _extract_knowledge_fingerprint(messages) -> dict:
    return {
        "file_paths": [...],    # file paths from tool calls/content
        "commands": [...],      # shell commands from terminal output
        "key_values": [...],    # config keys, API endpoints
        "tool_names": [...],    # tools that were used
    }
```
Use regex patterns: `_file_pattern`, `_cmd_pattern`, `_kv_pattern`

### 5. Slash Command Registration
- Add `CommandDef` in `hermes_cli/commands.py`
- Add route in `gateway/run.py` command dispatch + handler method
- Handler reads from `self._session_db.get_compressed_archives(session_id, limit=N)`

### 6. Look-Ahead Trigger
In `should_compress()`, maintain a `_token_history` list. If 3 consecutive rounds show >10% token growth, trigger fast_trim early. Reset `_lookahead_triggered` flag when threshold-based compression fires.

## Known Pitfalls

### Working Tree Compatibility
When working on a branch with uncommitted changes, `_get_compression_level()` may have been added by a prior unstaged edit. This causes tests to fail because test fixtures create compressors with small messages that don't trigger the level check. Fix: set `compressor.last_prompt_tokens = 90000` (above threshold) before calling `compress()` in tests.

### Three-way Test Debugging
1. `git stash` → run test on HEAD → if passing, the failure is from uncommitted changes
2. `git stash pop` → restore changes
3. Compare old path vs new path to identify the behavior change

### SCHEMA_VERSION Bump
When adding new tables to `hermes_state.py`:
1. Bump `SCHEMA_VERSION` (e.g., 6 → 7)
2. Add CREATE TABLE to `SCHEMA_SQL`
3. Add migration block for `current_version < N`
4. Update `test_schema_version` to assert new version
5. Update `test_migration_from_v2` to assert new version
6. Add `DELETE FROM new_table` to `prune_sessions` for cascade cleanup

### `replace_all` Gotcha
When using `patch` with `replace_all=True`, the search string must be unique enough to not match unintended lines, but broad enough to catch all instances. For test fixes with identical patterns, use `replace_all=True`.
