---
name: mcp-zombie-cleanup
description: Fix MCP tool subprocess zombie cleanup — ensure child processes are terminated on shutdown with atexit registration and force-kill fallback.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mcp, subprocess, zombie, cleanup, atexit, shutdown]
---

# MCP Zombie Subprocess Cleanup

## Problem

MCP servers spawn child subprocesses (e.g., `npx`, `uvx`, Node.js) that persist after the parent Python process exits. These become **zombie processes** — accumulating in the process table and potentially consuming ports/resources indefinitely.

**Symptoms:**
- `ps aux | grep mcp` shows orphaned processes from sessions that ended hours ago
- Port conflicts when restarting: "Address already in use"
- System resources leaked over time

## Root Cause

`tools/mcp_tool.py` stores spawned processes in the `_processes` dict, but `_shutdown()` only called `process.wait()` without `process.terminate()`. If the process doesn't die naturally (e.g., Node.js server that waits for input), it becomes a zombie.

## Solution

### 1. Force Kill in `_shutdown()`

Update the MCP tool's `_shutdown()` function:

```python
def _shutdown():
    """Terminate all MCP subprocesses and close sessions."""
    if not _processes:
        return

    logger.info("[MCP Shutdown] Terminating %d MCP subprocesses...", len(_processes))
    
    for name, process_data in _processes.items():
        proc = process_data.get("process")
        if proc and proc.poll() is None:
            logger.info(f"[MCP Shutdown] Terminating {name} (PID {proc.pid})")
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                logger.warning(f"[MCP Shutdown] {name} didn't terminate gracefully, force killing...")
                proc.kill()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    logger.error(f"[MCP Shutdown] {name} (PID {proc.pid}) still alive after kill")
            except Exception as e:
                logger.error(f"[MCP Shutdown] Error terminating {name}: {e}")

    _processes.clear()
```

### 2. `atexit` Registration

```python
import atexit

def _shutdown_named(name: str):
    """Register shutdown with a label for logging."""
    def _cleanup():
        logger.info(f"[{name}] Running shutdown...")
        _shutdown()
        logger.info(f"[{name}] Shutdown complete.")
    return _cleanup

# Register at module load time
atexit.register(_shutdown_named("_cleanup_mcp"))
```

### 3. Logging Wrapper

Add an `_shutdown_named()` wrapper so atexit messages are descriptive:

```python
@staticmethod
def _shutdown_named(name: str):
    """Return a shutdown function with descriptive logging."""
    def _cleanup():
        logger.info(f"[{name}] Running shutdown...")
        _shutdown()
        logger.info(f"[{name}] Shutdown complete.")
    return _cleanup
```

## Complete Pattern

```python
_processes: dict = {}

def _shutdown():
    if not _processes:
        return
    logger.info("[MCP] Cleaning up %d MCP processes...", len(_processes))
    for name, pd in list(_processes.items()):
        proc = pd.get("process")
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
            except Exception:
                pass
    _processes.clear()

def _shutdown_named(name):
    def _cleanup():
        logger.info(f"[{name}] Starting MCP process cleanup...")
        _shutdown()
        logger.info(f"[{name}] MCP process cleanup complete.")
    return _cleanup

atexit.register(_shutdown_named("_cleanup_mcp"))
```

## Pitfalls

1. **Don't block main process exit** — use `wait(timeout=3)` to prevent atexit from hanging forever. If the process ignores SIGTERM, SIGKILL is the final fallback.

2. **Process may already be dead** — always check `proc.poll() is None` before trying to terminate. Calling terminate on a dead process raises an error.

3. **atexit runs in LIFO order** — if MCP sessions are closed before atexit, `_processes` may already be empty. That's fine — idempotency is built in (check `if not _processes: return`).

4. **Performance** — iterating `_processes.items()` while yielding can cause `RuntimeError: dictionary changed size during iteration`. Use `list(_processes.items())` to create a snapshot.

5. **contextvars interaction** — if `_shutdown()` is called during `reset_cron_vars()`, ensure the order of cleanup is correct: close MCP connections before resetting session state.
