---
name: converge-bare-exceptions
description: Systematically replace bare `except Exception` with specific exception types across a Python codebase. Use during code quality sprints or when preparing a project for production hardening.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [exception-handling, code-quality, production-hardening, python]
    related_skills: [systematic-debugging, requesting-code-review, test-driven-development]
---

# Converge Bare Except Exception

## Overview

Bare `except Exception` catches everything — including `KeyboardInterrupt`, `SystemExit`, `MemoryError`, and other signals that should propagate. Replace with specific exception types that match the actual operations being caught.

**Core principle:** The except block should only catch exceptions the operation can actually raise. If you don't know what can be raised, read the docs for the function being called.

## When to Use

- User asks to "improve code quality" or "harden production code"
- Code review identifies bare `except Exception` as a concern
- Preparing a project for deployment where swallowed signals cause operational issues
- Any time you touch a file with bare exceptions (fix as you go)

## The Workflow

### Phase 1: Audit — Find All Occurrences

```bash
grep -rn "except Exception" src/ --include='*.py' \
  | grep -v "# noqa" \
  | cut -d: -f1 | sort | uniq -c | sort -rn
```

This gives you a frequency-ranked list. Start with the top 3-5 files.

### Phase 2: Contextualize — Read Surrounding Code

For each `except Exception` block, read 3-5 lines above to identify the operation being caught:

```bash
grep -n -B5 "except Exception" path/to/file.py
```

### Phase 3: Map — Operation → Exception Types

Use this lookup table to determine the correct replacement:

| Operation | Replacement | Rationale |
|-----------|-------------|-----------|
| `urllib.request.urlopen()` | `(urllib.error.URLError, OSError, ValueError)` | Network failures, DNS, bad URLs |
| `json.loads()` / `json.load()` | `json.JSONDecodeError` | Malformed JSON |
| `datetime.strptime()` | `(ValueError, TypeError)` | Bad format string, None input |
| `PyPDF2.PdfReader()` | `(ValueError, RuntimeError, OSError)` | Corrupt PDF, file IO |
| `Document(io.BytesIO(data))` | `(ValueError, RuntimeError, OSError)` | Corrupt DOCX, file IO |
| `pd.read_excel()` | `(ValueError, KeyError, OSError)` | Bad sheet, missing columns, file IO |
| `df.to_string()` | `(ValueError, RuntimeError)` | Rendering failures |
| SQLite `conn.execute()` | `sqlite3.Error` (not `Exception`) | DB corruption, constraint violations |
| `open()`, `Path.read_text()` | `(OSError, UnicodeDecodeError)` | File missing, permissions, encoding |
| `int()`, `float()` conversion | `(ValueError, TypeError)` | Bad input format |
| `subprocess.run()` | `(subprocess.SubprocessError, OSError)` | Process failures, missing binary |
| `requests.get()` / HTTP calls | `(requests.RequestException, OSError)` | Network, timeout, DNS |
| OpenAI/LangChain API calls | Keep broader or use `(RuntimeError, OSError, ValueError)` | SDKs raise diverse exception types |
| Generic file parsing | `(ValueError, RuntimeError, OSError)` | Safe catch-all for document processing |

**Key rule:** If the operation is IO-bound, include `OSError`. If it's parsing, include `ValueError`. If it's computation, include `RuntimeError`.

### Phase 4: Replace — Batch Apply

Use `execute_code` with `patch()` for batch replacements across a single file:

```python
from hermes_tools import patch

path = "/path/to/file.py"

# Replace each unique except block
patch(path,
    old_string="""    except Exception as e:
        logger.warning("network failed: %s", e)""",
    new_string="""    except (urllib.error.URLError, OSError, ValueError) as e:
        logger.warning("network failed: %s", e)"""
)
```

**Important:** Use enough surrounding context in `old_string` to ensure uniqueness. Include the logging/return statement.

### Phase 5: Verify — Run Tests

```bash
# Run the full test suite
pytest tests/ -q

# If the file has specific tests
pytest tests/test_<module>.py -v
```

All tests must still pass. If any fail:
1. Check if the exception type is too narrow — the operation may raise types you didn't account for
2. Read the failing test to understand what exception was actually raised
3. Broaden the exception tuple accordingly

## Common Pitfalls

### Don't remove the `as e` binding if used

```python
# WRONG — loses the exception variable
except (ValueError, OSError):
    logger.error("failed: %s", e)  # NameError!

# RIGHT
except (ValueError, OSError) as e:
    logger.error("failed: %s", e)
```

### Don't narrow too aggressively

```python
# WRONG — sqlite3 may raise OperationalError, IntegrityError, etc.
except sqlite3.OperationalError:
    ...

# RIGHT — catch the base sqlite3.Error
except sqlite3.Error:
    ...
```

### Don't forget to add imports

If replacing with `urllib.error.URLError`, add `import urllib.error` at the top of the file (if not already present).

### Leave `# noqa: BLE001` only where justified

If an `except Exception` is genuinely needed (e.g., catch-all in top-level error boundary, or when wrapping an SDK with unknown exception hierarchy), tag it `# noqa: BLE001` and add a comment explaining why.

## When NOT to Converge

- **Top-level error boundaries** in `main.py` or web framework handlers — these SHOULD catch broadly to prevent crashes
- **Third-party SDK wrappers** where the SDK's exception hierarchy is undocumented or unstable
- **`KeyboardInterrupt` handlers** — sometimes bare Exception is correct for cleanup code that must run on any exit
- **Already tagged `# noqa: BLE001`** — someone already decided this one is intentional

## Verification Checklist

- [ ] `grep -c "except Exception" file.py` shows reduced count
- [ ] Imports added for new exception types (`import urllib.error`, etc.)
- [ ] `as e` bindings preserved where used
- [ ] Full test suite passes with zero regressions
- [ ] Intentionally-kept bare exceptions tagged `# noqa: BLE001` with comment
