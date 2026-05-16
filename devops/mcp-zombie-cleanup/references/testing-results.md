# 2026-04-26 Testing Results

## Environment
- macOS, Python venv at hermes-agent/venv/
- Default model: deepseek-chat (DeepSeek provider)
- Tests run: `pytest tests/ -q --timeout=120 --deselect ...`

## Results
- **agent/ module only**: 1,043 passed, 2 skipped ✅
- **Full suite (with deselects)**: 3,242 passed ✅
- **Pre-existing known failures** (not from our changes):
  - `test_api_server_jobs.py::test_update_job_rejects_unknown_fields`
  - 2x cron tests with `FakeAgent` that still use `os.getenv` (need `get_cron_env()` migration)

## Skills Created This Session
1. `cron-env-contextvars` — fixing os.environ pollution with contextvars
2. `mcp-zombie-cleanup` — force-killing MCP subprocesses on shutdown
