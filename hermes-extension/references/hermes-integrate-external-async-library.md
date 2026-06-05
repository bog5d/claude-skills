---
name: hermes-integrate-external-async-library
description: Standardized workflow for integrating an external async Python library as a set of Hermes Agent tools. Covers research → tool file → registration → async tests → auth gating.
trigger: When the user asks to integrate a third-party Python library as Hermes tools, or when wrapping an async API for agent use.
---

# Hermes — Integrate External Async Library as Tools

## Overview

When integrating an external async Python library (e.g., `notebooklm-py`, `openai`, `httpx`-based clients) as Hermes Agent tools, follow this workflow.

Hermes supports async tool handlers natively via `is_async=True` + the `_run_async()` bridge in `model_tools.py`. The bridge uses a persistent event loop per thread so cached async clients (httpx, etc.) don't get "Event loop is closed" errors on GC.

## Step 1: Research & Feasibility

Before writing code:
1. Find the library on GitHub/PyPI
2. Read the README and Python API docs
3. Verify: async API? cookie/auth persistence? rate limiting? error handling?
4. Check Hermes compatibility: `is_async=True` in registry, persistent loop bridge

## Step 2: Install & Auth

```bash
source venv/bin/activate
pip install <library>
# If it needs browser auth (like notebooklm-py):
notebooklm login
notebooklm auth check --test --json
```

## Step 3: Create `tools/<name>_tool.py`

Template:

```python
import asyncio, json, logging
from pathlib import Path
from tools.registry import registry

logger = logging.getLogger(__name__)

# --- Lazy client singleton ---
_client = None
_client_lock: asyncio.Lock | None = None

async def _get_client():
    global _client, _client_lock
    if _client_lock is None:
        _client_lock = asyncio.Lock()
    async with _client_lock:
        if _client is None:
            from external_lib import Client
            _client = Client(...)
            await _client.__aenter__()
            logger.info("Client initialized")
        return _client

# --- Requirement check (gates tool availability) ---
def check_requirements() -> bool:
    try:
        import external_lib
    except ImportError:
        return False
    # Check auth file / API key / etc.
    return Path.home() / ".config" / "auth.json").exists()

# --- JSON helpers ---
def _ok(**kw) -> str:
    return json.dumps({"success": True, **kw}, ensure_ascii=False)

def _err(msg: str) -> str:
    return json.dumps({"success": False, "error": msg}, ensure_ascii=False)

# --- Async handlers ---
async def my_tool(param: str, task_id: str = None) -> str:
    try:
        client = await _get_client()
        result = await client.do_something(param)
        return _ok(data=result)
    except Exception as e:
        logger.exception("my_tool failed")
        return _err(str(e))

# --- Registration ---
_COMMON = dict(toolset="my_toolset", check_fn=check_requirements, requires_env=[], is_async=True)

def _reg(name, schema, handler):
    registry.register(name=name, handler=handler, schema=schema, **_COMMON)

_reg("my_tool", {
    "name": "my_tool",
    "description": "Does something useful.",
    "parameters": {
        "type": "object",
        "properties": {"param": {"type": "string", "description": "..."}},
        "required": ["param"]
    }
}, lambda args, **kw: my_tool(param=args["param"], task_id=kw.get("task_id")))

logger.info("Tools registered: %d", ...)
```

Key patterns:
- **Lazy client singleton**: `_get_client()` with `asyncio.Lock` — creates once per event loop
- **check_requirements()**: Gates tool availability. Returns False → tool hidden from model
- **Lambda handlers**: `lambda args, **kw: handler_func(...)` — registry passes `task_id` via `**kw`
- **JSON responses**: Always `{"success": true/false, ...}` for consistent error handling

## Step 4: Register in Hermes

### `model_tools.py` — add to `_discover_tools()`:
```python
"tools.my_tool",  # Description
```

### `toolsets.py` — add to `_HERMES_CORE_TOOLS`:
```python
"my_tool_1", "my_tool_2",
```

### `toolsets.py` — add dedicated toolset (optional):
```python
"my_toolset": {
    "description": "...",
    "tools": ["my_tool_1", "my_tool_2"],
    "includes": []
},
```

## Step 5: Write pytest-asyncio tests

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture(autouse=True)
def _clean_client_cache():
    import tools.my_tool as mt
    mt._client = None
    mt._client_lock = None
    yield
    mt._client = None
    mt._client_lock = None

@pytest.fixture
def mock_client():
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    client.do_something = AsyncMock(return_value="result")
    return client

@pytest.fixture
def mock_lib(mock_client):
    with patch("external_lib.Client", return_value=mock_client):
        yield

class TestMyTool:
    pytestmark = pytest.mark.asyncio  # CRITICAL — without this, async tests fail

    async def test_success(self, mock_client, mock_lib):
        from tools.my_tool import my_tool
        result = json.loads(await my_tool(param="test"))
        assert result["success"] is True

    async def test_error(self, mock_client, mock_lib):
        mock_client.do_something.side_effect = RuntimeError("fail")
        from tools.my_tool import my_tool
        result = json.loads(await my_tool(param="test"))
        assert result["success"] is False
        assert "fail" in result["error"]
```

**CRITICAL**: All async test classes must have `pytestmark = pytest.mark.asyncio`. Without it, pytest-asyncio won't handle `async def test_*` functions and they'll fail with "async def functions are not natively supported."

## Step 6: Verify

```bash
source venv/bin/activate

# Verify module imports
python3 -c "from tools.my_tool import check_requirements; print(check_requirements())"

# Run new tests
python3 -m pytest tests/test_my_tool.py -v -o "addopts="

# Regression check
python3 -m pytest tests/test_model_tools.py tests/test_toolsets.py -q -o "addopts="
```

## Pitfalls

1. **`pytestmark = pytest.mark.asyncio`**: MUST be on every test class with async test methods. Hermes uses pytest-asyncio in STRICT mode — no auto-detection.
2. **`-o "addopts="`**: pyproject.toml has `addopts = "-n auto"` which conflicts with single-file test runs. Override it.
3. **Client lifecycle**: Use lazy singleton with `asyncio.Lock`, NOT `asyncio.run()` per call. The persistent loop keeps cached httpx clients alive.
4. **Auth gating**: `check_requirements()` should check BOTH library import AND auth file existence. Tool only appears when truly usable.
5. **Lambda in handler**: Registry dispatch passes `args` dict + `**kw` (which includes `task_id`). Lambda is the cleanest way to map.
6. **`ensure_ascii=False`**: Always use in `json.dumps()` for non-ASCII content from external APIs.
