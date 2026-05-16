---
name: monolith-to-package-while-active
description: "拆分巨型单文件（如 cli.py 9,300 行或类似的活跃入口脚本）为包结构，同时保持整个系统在过渡期间可运行、可测试。涵盖 __init__.py 桥接、spec_from_file_location 加载原文件、测试 patch 兼容性、运行时符号注入等技巧。"
category: software-development
---

# Monolith → Package While Active

## When to Use

当需要拆分一个**正在被频繁导入和测试的巨型 Python 文件**（8000+ 行）时：
- 该文件是 CLI 入口、核心类、或其他被大量外部代码 `from x import Y` 引用的模块
- 不能停服：拆分期间所有测试必须通过，所有 `from cli import X` 必须继续工作
- 外部代码（测试、工具模块）使用 `patch("cli.X")` 或 `monkeypatch.setattr("cli.Y")` 模式

## The Strategy: __init__.py Bridge + spec_from_file_location

### Phase 1: Create Package Structure

```bash
mkdir cli/
```

### Phase 2: Extract Submodules

Move function groups into submodules. Each submodule is independent:

```python
# cli/config.py — config loading logic
# cli/display.py — ANSI, formatting, ChatConsole
# cli/callbacks.py — callback functions
# cli/streaming.py — streaming helpers
# cli/commands_handler.py — command dispatch
# cli/git_worktree.py — git worktree management
```

### Phase 3: Backward-Compatible __init__.py

The critical piece. The `cli/` directory now shadows `cli.py` as the package. Create `cli/__init__.py`:

```python
# 1. Re-export symbols from new submodules (forward-compat)
from cli.config import CLI_CONFIG, load_cli_config
from cli.display import _cprint, ChatConsole, ...

# 2. Load original cli.py as a separate module (backward-compat)
import importlib.util as _importlib_util
import pathlib as _pathlib
_cli_py_path = str(_pathlib.Path(__file__).resolve().parent.parent / "cli.py")
_spec = _importlib_util.spec_from_file_location("_cli_original", _cli_py_path)
_orig_cli = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_orig_cli)

# 3. Export classes/methods from original cli.py
HermesCLI = _orig_cli.HermesCLI
main = _orig_cli.main

# 4. Inject symbols into _orig_cli module for test patch compatibility
# Tests may do: patch("cli._cprint"), and HermesCLI methods reference
# names in _orig_cli's module scope, not __init__.py's scope.
for _sym in ("_cprint", "CLI_CONFIG", "save_config_value", ...):
    if hasattr(_orig_cli, _sym) and hasattr(sys.modules[__name__], _sym):
        setattr(_orig_cli, _sym, getattr(sys.modules[__name__], _sym))
```

### Phase 4: Runtime Lookup for Test Patchability

Import the problem: `patch("cli._cprint")` intercepts `cli/__init__.py`'s `_cprint`, but code that does `from cli.display import _cprint` has bound a reference at import time — patching the module namespace doesn't affect it.

**Fix**: Use runtime lookup via the cli module rather than compile-time import:

```python
# BAD — compile-time binding, patches don't intercept
from cli.display import _cprint

# GOOD — runtime lookup, patches DO intercept
import cli as _cli_mod
_cprint = lambda *a, **kw: _cli_mod._cprint(*a, **kw)
```

### Phase 5: Override Key Methods on Class

If you move `process_command()` logic to `cli/commands_handler.py`, override the method on the original class:

```python
from cli.commands_handler import process_command as _handler_pc
def _bridged_pc(self, command):
    return _handler_pc(self, command)
HermesCLI.process_command = _bridged_pc
```

Without this, `cli_obj.process_command("/quit")` still executes the original cli.py method with its old module-scope references.

## Common Pitfalls

### 1. `spec_from_file_location` causes double initialization
The original `cli.py` has module-level side effects (`.env loading`, `skin engine init`, `logging setup`). Loading it via `spec_from_file_location` executes all of these again. Move module-level side effects into the submodules so the original is "just definitions."

### 2. The `import cli as cli_mod` binding changes
After adding `cli/__init__.py`, `import cli as cli_mod` now gets the **package**, not the **file**. All attribute access on `cli_mod` must go through `__init__.py`'s exports. Test code that does `patch.object(cli_mod, "_skill_commands", ...)` will fail if `_skill_commands` isn't re-exported from `__init__.py`.

### 3. `monkeypatch.setattr("cli._hermes_home", ...)` fails silently
When tests monkeypatch attributes on the `cli` module, they're monkeypatching on `cli/__init__.py`'s namespace. If `_hermes_home` lives in `cli/config.py`, it must be re-exported: `from cli.config import _hermes_home as _hermes_home`.

### 4. Circular imports from nested submodules
If `cli/config.py` imports from `cli/display.py` and `cli/display.py` imports from `cli/config.py`, you get a cycle. Solution: The submodules should not import from each other at module level — use lazy imports inside functions.

## Pitfalls Specific to "Rename + Package" Split (No Bridge)

When the original file is **fully replaced** by a package directory (no `spec_from_file_location` bridge), additional pitfalls arise:

### 5. `from __future__ import annotations` must stay at line 1-2
When auto-injecting cross-module imports, it's easy to push `from __future__` down. Python requires it at the **very beginning** of the file (only docstring can precede it). Result: `SyntaxError: from __future__ imports must occur at the beginning of the file`.

### 6. Cross-module function references silently break
In a monolith, `_make_client()` just works because it's defined earlier in the same file. After splitting, `_roadshow.py` calls `_make_client()` but doesn't import it. The fix: each submodule must explicitly `from ._evaluation import _make_client` for any function defined in a sibling submodule.

### 7. Test mock patches must target the actual import location
Before split: `patch("pkg.module.func")` works because `func` is in `module.py`'s namespace.
After split: `func` is defined in `pkg.module._sub_a` and imported into `pkg.module._sub_b`. 
Patch must target `pkg.module._sub_a.func` (where it's defined), not `pkg.module._sub_b.func` (where it's imported as a reference).

### 8. Line-boundary off-by-one errors
When using Python list slicing `lines[start:end]` to extract sections:
- `lines` is 0-indexed: `lines[0]` = line 1 of the file
- Slice `end` is **exclusive**: `lines[394:739]` = lines 395–739 (1-indexed)
- To exclude a line, the end index must point to that line: `lines[start:target_line_index]` excludes `target_line`
- **Always verify boundaries by checking the first and last line of each extracted section** before writing files

### 9. Logger must be replicated per submodule
In the monolith, `logger = logging.getLogger(__name__)` is defined once. After splitting:
- Each submodule that calls `logger.info()` or `logger.warning()` MUST have its own `logger = logging.getLogger(__name__)`
- The `import logging` line from the common header provides the `logging` module, but not the `logger` instance
- Run the split tests — any `NameError: name 'logger' is not defined` means a submodule is missing it

### 10. Auto-generating imports from the original file is fragile
When scripting the split, a naive approach like "scan body for used names → add imports" creates mangled output:
- Schema imports get split across lines incorrectly
- `from __future__` gets pushed down past sibling imports
- Unused imports bloat every submodule

**Better approach**: Copy the ENTIRE original import block (lines 1 through the last import) into each submodule. Then manually add only the cross-submodule imports needed. This is slightly wasteful but eliminates import errors.

### 11. Test mock patch paths: target the definition module, not the import module
Before split: `patch("pkg.module.func")` works because `func` lives in `module.py`.
After split (rename+package): `func` is defined in `pkg.module._sub_a.py` and imported into `pkg.module._sub_b.py` via `from ._sub_a import func`.

When `_sub_b.py` calls `func()`, it looks up `func` in its own namespace (where it was imported). So:
- ✅ `patch("pkg.module._sub_b.func")` — intercepts the call in `_sub_b`'s namespace
- ❌ `patch("pkg.module._sub_a.func")` — doesn't intercept, because `_sub_b` already has its own reference

**The rule**: Find which submodule actually CALLS the function at runtime, and patch THAT submodule's attribute, not the defining submodule's. If multiple submodules import and call the function, patch each one separately.

## Verification Checklist

- [ ] `python -c "from cli import HermesCLI; print('OK')"` works
- [ ] `python -c "import cli as _cli_mod; print(hasattr(_cli_mod, 'CLI_CONFIG'))"` is True
- [ ] All `patch("cli.X")` patterns in tests still intercept calls
- [ ] All `monkeypatch.setattr("cli.Y", ...)` patterns in tests still work
- [ ] `pytest tests/cli/ -q` shows no regression vs. baseline (check git stash baseline)
- [ ] `cli.py` itself still runs as a standalone: `python cli.py --help`

## Performance Warning

`spec_from_file_location.exec_module()` loads the original `cli.py` **every time** the `cli` package is imported. With 9000+ lines this adds ~100-200ms to import time. This is acceptable during the transition. Once all symbols are migrated, remove the `spec_from_file_location` bridge entirely.

### Phase 6: Mixin Extraction for Giant Methods

Once the lightweight functions are migrated, the class itself may still hold monster methods (e.g., `run()` at 1466 lines, `chat()` at 432 lines). Moving the entire class would break every `from cli import HermesCLI` import. Instead, extract giant methods into a **mixin class**:

```python
# cli/run_loop.py
class RunLoopMixin:
    \"\"\"Extracted run() and chat() from HermesCLI.\"\"\"

    def run(self):
        # 1466 lines — references self.agent, self.console, self._init_agent(), etc.
        ...

    def chat(self, message, images=None):
        # 432 lines
        ...
```

Then in the original module:

```python
# cli.py
from cli.run_loop import RunLoopMixin

class HermesCLI(RunLoopMixin):  # ← mixin added
    # __init__ and all other methods stay here
    # run() and chat() removed — resolved via MRO from RunLoopMixin
```

**Why this works:**
- `self` references resolve naturally through Python MRO — `self._init_agent()` finds the method in `HermesCLI` as before
- All existing `from cli import HermesCLI` imports work unchanged
- `patch("cli.X")` patterns still work if the mixin uses runtime `import cli as _cli_mod` lookups
- Zero test changes needed if the mixin handles its own imports (lazy imports inside methods, runtime displays via `_cli_mod`)

**Mixin imports checklist:**
- Bare function calls from the original module scope must be re-imported: `set_secret_capture_callback`, `set_sudo_password_callback`, `set_approval_callback`, `_skill_commands`
- Display helpers should use runtime lookup via `_cli_mod`: `_cprint = lambda *a, **kw: _cli_mod._cprint(*a, **kw)`
- Functions already in `cli/` submodules import directly: `from cli.display import ChatConsole, _format_image_attachment_badges`
- Type annotations: ensure `from typing import Optional, Dict, List, Any` is present

**What NOT to put in the mixin:**
- `__init__` — stays in the original class
- Methods that modify class-level state at definition time
- Methods with decorators that depend on the original class's module scope

## Related Pattern: run_agent Package (Identical Technique)

The same bridge pattern was used for `run_agent/` (from `run_agent.py` 10,103-line monolith). This confirms the pattern is reusable:

1. `__init__.py` re-exports from both submodules and `_agent_monolith.py` (the original file)
2. Tests rely heavily on `patch("run_agent.X")` and `monkeypatch.setattr("run_agent.Y")` — patch targets must exist in `__init__.py`'s namespace
3. Key symbols that WILL be needed (based on test analysis of 478 failing tests):
   - `check_toolset_requirements` (from `model_tools`)
   - `_hermes_home` (from the monolith itself)
   - `_set_interrupt`, `build_nous_subscription_prompt` (from monolith)
   - `sys`, `time` (stdlib modules — tests monkeypatch them at the `run_agent` level)
4. Use `# noqa: F401` on bridge imports so linters don't complain about \"unused\" re-exports
