---
name: cron-env-contextvars
description: Fix cron job environment variable pollution by migrating from os.environ to contextvars.ContextVar — prevents cross-task leakage and test contamination.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [cron, contextvars, env-pollution, threading, testing]
---

# Cron Env Contextvars Migration

## Problem

Cron jobs set temporary env vars (e.g. `CRON_MODE=1`, `HERMES_CRON_AUTO_DELIVER_PLATFORM=telegram`) with `os.environ.update()` but never clean them up. This causes:

1. **Cross-job pollution** — subsequent jobs inherit stale env from previous
2. **Thread safety issues** — `os.environ` is process-global, not thread-local
3. **Test contamination** — tests that mock env vars get cron-leaked values
4. **Zombie context** — values persist in memory after the cron job has finished

## Solution: contextvars.ContextVar

Create a `cron/session_context.py` module:

```python
import os
from contextvars import ContextVar
from typing import Optional

# Define context vars for cron session data
_cron_mode: ContextVar[bool] = ContextVar("_cron_mode", default=False)
_cron_platform: ContextVar[str] = ContextVar("_cron_platform", default="")
_cron_chat_id: ContextVar[str] = ContextVar("_cron_chat_id", default="")
_cron_thread_id: ContextVar[str] = ContextVar("_cron_thread_id", default="")

# Tokens for reset
_tokens: dict[str, object] = {}


def set_cron_vars(
    platform: str = "",
    chat_id: str = "",
    thread_id: str = "",
) -> None:
    """Set cron context variables and return a reset token."""
    _tokens["platform"] = _cron_platform.set(platform)
    _tokens["chat_id"] = _cron_chat_id.set(chat_id)
    _tokens["thread_id"] = _cron_thread_id.set(thread_id)


def reset_cron_vars() -> None:
    """Reset all cron context variables to defaults."""
    for name, token in _tokens.items():
        var = _get_var(name)
        if var:
            var.reset(token)
    _tokens.clear()


def get_cron_env(name: str, default: str = "") -> Optional[str]:
    """Read cron context variable with os.environ fallback.

    Reads contextvar first; if empty/unset, falls back to os.getenv.
    This ensures other sessions/tests can still read legacy env-set values.
    """
    name = name.upper()
    # Try contextvar first
    value = _get_contextvar_value(name)
    if value:
        return value
    # Fallback to os.environ
    return os.getenv(name, default) or default or None


def _get_var(name: str) -> Optional[ContextVar]:
    return {
        "platform": _cron_platform,
        "chat_id": _cron_chat_id,
        "thread_id": _cron_thread_id,
    }.get(name)


def _get_contextvar_value(name: str) -> Optional[str]:
    mapping = {
        "HERMES_CRON_AUTO_DELIVER_PLATFORM": _cron_platform,
        "HERMES_CRON_AUTO_DELIVER_CHAT_ID": _cron_chat_id,
        "HERMES_CRON_AUTO_DELIVER_THREAD_ID": _cron_thread_id,
    }
    var = mapping.get(name)
    if var:
        val = var.get()
        return val if val else None
    return None
```

## Integration in scheduler.py

In `cron/scheduler.py`, modify `run_job()`:

```python
def run_job(self, job_id: str, ...):
    from cron.session_context import set_cron_vars, reset_cron_vars

    # 1. Load .env FIRST (before _resolve_delivery_target)
    load_dotenv(self._hermes_home / ".env", override=True)

    # 2. Resolve delivery target
    delivery_target = self._resolve_delivery_target(job)

    # 3. Set context vars
    if delivery_target:
        set_cron_vars(
            platform=delivery_target.get("platform", ""),
            chat_id=str(delivery_target.get("chat_id", "")),
            thread_id=str(delivery_target.get("thread_id", "")) if delivery_target.get("thread_id") else "",
        )

    try:
        # ... existing job execution code ...
    finally:
        reset_cron_vars()
```

## CRITICAL: load_dotenv Order

**`_resolve_delivery_target()` MUST be called AFTER `load_dotenv()`.**

The function reads `TELEGRAM_HOME_CHANNEL` from env — if `load_dotenv` hasn't run yet, the channel ID will be empty string instead of the correct value.

```python
# WRONG — delivery target reads env before .env is loaded
delivery_target = self._resolve_delivery_target(job)
load_dotenv(self._hermes_home / ".env", override=True)

# RIGHT — always load .env first
load_dotenv(self._hermes_home / ".env", override=True)
delivery_target = self._resolve_delivery_target(job)
```

## Testing

```python
# Example test for contextvar isolation
def test_cron_contextvars_isolated(tmp_path, monkeypatch):
    from cron.session_context import set_cron_vars, get_cron_env, reset_cron_vars

    monkeypatch.delenv("HERMES_CRON_AUTO_DELIVER_PLATFORM", raising=False)

    # Set in context
    set_cron_vars(platform="telegram")
    assert get_cron_env("HERMES_CRON_AUTO_DELIVER_PLATFORM") == "telegram"

    # Reset — should be gone
    reset_cron_vars()
    assert get_cron_env("HERMES_CRON_AUTO_DELIVER_PLATFORM") is None
```

## Pitfalls

1. **FakeAgent tests still use `os.getenv()`** — cron contextvars don't pollute os.environ, so any test that reads cron env vars via os.getenv will not see the contextvar values. Fix: use `get_cron_env()` instead of `os.getenv()` in tests.

2. **Empty string vs None** — contextvar default is `""`. `get_cron_env()` returns `None` when unset (not `""`). If tests expect `None`, ensure the contextvar isn't storing an empty string.

3. **`atexit` handlers** — if cron runs with `atexit`, ensure `reset_cron_vars()` is called in the `finally` block, not after `atexit` has already started.
