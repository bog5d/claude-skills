---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior. 4-phase root cause investigation — NO fixes without understanding the problem first.
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, writing-plans, subagent-driven-development]
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

### Phase 0: Source-of-Truth Verification (Critical)

**Before assessing status, verify against CODE — not memory.**

Memory (session_search, semantic_search, mem0) can be stale or incomplete. When the user asks about project completion status, feature existence, or what's been built:
1. **Check actual files on disk FIRST** — `search_files(target='files')` or `read_file`
2. **Check git log** — `git log --oneline --follow <file>` for creation dates
3. **Only then** consult memory as supplementary context

**Real failure mode:** Claimed W5/W6/executor were "not done" based on memory → user corrected → code audit proved all were completed. 3 incorrect assessments because memory was 2-4 weeks stale.

**Rule:** If user pushes back on a status claim ("I think this was already done"), immediately audit code files. Do not defend the memory-based claim.

### Phase 0b: Tool Semantics Check (Common Traps)

**Before diving into code, verify you're using the right tools for the job.**

**mem0_search is NOT web search**
- `mem0_search` searches persisted memory only — it cannot retrieve real-time data (weather, news, prices, etc.)
- Signal: results always start with "User ..." memory fragments, no URLs/timestamps/sources
- If you need live data: use `web_search` or `browser_navigate` directly — don't burn 3+ turns trying mem0_search variants

**execute_code's read_file may truncate large files**
- `read_file` inside `execute_code` has a ~50KB stdout limit
- For files >25KB (like the guizang-ppt-skill template at 30KB), content may be silently truncated
- If you need the full file for string manipulation: use `terminal` with Python's `open().read()` instead

**delegate_task results may not return if they exceed output limits**
- Subagents produce a final summary that enters your context
- If the subagent generates a huge amount of content, it may get cut off
- Solution: have the subagent write results to a file instead of returning them inline

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully

- Don't skip past errors or warnings
- They often contain the exact solution
- Read stack traces completely
- Note line numbers, file paths, error codes

**Action:** Use `read_file` on the relevant source files. Use `search_files` to find the error string in the codebase.

### 2. Reproduce Consistently

- Can you trigger it reliably?
- What are the exact steps?
- Does it happen every time?
- If not reproducible → gather more data, don't guess

### 2b. Check: Is the Failure in Test Code or Production Code?

**Before deep investigation, a quick triage:** rule out the possibility that the test itself has a bug (calling a non-existent function, importing a non-existent module, or referencing code that hasn't been merged yet).

**Action:** Search for the failing symbol in the codebase:

```python
search_files("missing_function_or_module_name", path="src/", file_glob="*.py", output_mode="files_only")
```

**Common patterns:**
1. **Forward-looking tests** — test references a function/module name that doesn't exist yet (planned but not merged). Action: skip the test or create the missing module.
2. **Typo'd function names** — a rename happened but tests weren't updated. Action: fix the test or the production code reference.
3. **Deleted/renamed symbols** — the production code was refactored but tests reference the old name. Action: update the test to use the new name/import path.

This triage takes <30 seconds and saves 5-15 minutes of deep-dive investigation on dead ends.

**Action:** Use the `terminal` tool to run the failing test or trigger the bug:

```bash
# Run specific failing test
pytest tests/test_module.py::test_name -v

# Run with verbose output
pytest tests/test_module.py -v --tb=long
```

### 3. Check Recent Changes

- What changed that could cause this?
- Git diff, recent commits
- New dependencies, config changes

**Critical: Check BOTH committed AND uncommitted changes.**

A common trap: a test failure might be caused by **uncommitted working-tree changes** (staged or unstaged), not by your own code. The failure looks like a regression in your code, but the root cause is a pre-existing change in the working tree.

**Action:**

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes (staged + unstaged)
git status --short
git diff

# Or more comprehensively: check if there are any modifications
# that might have introduced behavior changes
git stash list
git diff --stat

# Important: if the failure involves code paths that don't exist in HEAD,
# check whether a worktree-only change introduced the behavior
git stash && pytest failing_test -v  # run on HEAD
git stash pop  # restore worktree
```

**Three-way comparison technique for working-tree-induced failures:**

When a test fails and you didn't touch the area of code it tests:
1. `git stash` (save your changes)
2. Run the failing test on HEAD — if it passes, the working tree changes are the cause
3. `git stash pop` (restore your changes)
4. Now investigate what in the unstaged changes broke it — compare the test expectations against the current behavior

This is especially important when extending an active refactoring branch where prior uncommitted changes may have subtly changed behavior (e.g., introducing new compression thresholds, test expectations, or API signatures).

### 4. Gather Evidence in Multi-Component Systems

**WHEN system has multiple components (API → service → database, CI → build → deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation:**

For EACH component boundary:
- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks.
THEN analyze evidence to identify the failing component.
THEN investigate that specific component.

### 5. Trace Data Flow

**WHEN error is deep in the call stack:**

- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source
- Fix at the source, not at the symptom

**Action:** Use `search_files` to trace references:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### Special Scenario: Fixture Scope Mismatch After DB Isolation

**When you add a function-scope autouse fixture that monkeypatches shared state (DB paths, env vars, global config), tests using module/class-scope fixtures that pre-populate that same state will silently break.**

**Root cause chain:**
1. Module-scope fixture runs FIRST → calls `_connect()` → writes data to **real DB path** (monkeypatch hasn't run yet — it's function-scope)
2. Individual test function runs → autouse fixture monkeypatches `_db_path` → points to **temp directory**
3. Test calls `db_job_get()` → reads from temp DB → empty → returns `None`
4. All assertions downstream fail: `NoneType has no attribute 'get'`, 404 on API, "not found"

**Diagnosis indicators (all must be present):**
- Multiple test files suddenly fail, all with the same error pattern
- Errors are "data not found" type (NoneType, 404, KeyError), not assertion logic failures
- The failing tests use module/class-scope fixtures that call database functions directly
- Failure started after adding or modifying an autouse fixture that alters shared state

**Fix approach (prefer A over B):**

| Approach | Mechanism | Pro |
|----------|-----------|-----|
| **A — Marker opt-out** | `@pytest.mark.real_db` on test class → fixture checks `request.node.get_closest_marker("real_db")` | Test file self-declares; no central list to maintain |
| B — Module name list | Hardcoded `_SKIP_MODULES` tuple in conftest, check `request.node.path` | Quick to implement |

**Full marker implementation recipe (Approach A):**

*Step 1: Register marker* — in `pyproject.toml` under `[tool.pytest.ini_options]`:
```toml
markers = [
  "real_db: 测试使用 module/class 级 fixture 预写数据，跳过 autouse DB 隔离",
]
```

*Step 2: Autouse fixture checks marker* — in `conftest.py`:
```python
@pytest.fixture(autouse=True)
def _isolate_db_per_test(request, tmp_path, monkeypatch):
    if request.node.get_closest_marker("real_db"):
        return  # self-declared — test manages its own DB
    # ... normal isolation logic
```

*Step 3: Test files self-declare* — add after imports in each test file:
```python
pytestmark = [pytest.mark.real_db]
```

*Step 4: Safety net* — git pre-push hook runs all `@pytest.mark.real_db` tests to catch scope mismatches before they hit remote:
```bash
#!/usr/bin/env bash
# .git/hooks/pre-push
uv run --extra dev pytest \
    tests/test_wizard_pipeline_e2e.py \
    tests/test_pipeline_e2e.py \
    ...all @real_db files... \
    -q --tb=short
```

**When to use `@pytest.mark.real_db`:**
- Test file has module/class-scope fixture that calls `_connect()` / `db_job_create()` directly
- Test file has its own `isolated_db` fixture that monkeypatches `_db_path` (avoids double-patch race)
- Any test that pre-populates DB before individual test functions run

**Real case:** Adding `_isolate_db_per_test` (function-scope autouse) broke 46 tests across 4 files (wizard/pipeline/retry-eval/follow-ups) — all had module fixtures pre-writing DB. Same pattern recurs when another AI adds `test_wiki_display` — requires updating centralized skip list. Marker-based approach would have self-documented.

### Special Scenario: Working-Tree Test Failures

When working on a refactoring branch with **uncommitted changes**, a test failure might be caused by pre-existing worktree changes, not your code.

**Three-way comparison technique:**

```bash
git stash  # save your changes
python -m pytest <failed_test> -x -v  # run on HEAD only
git stash pop  # restore
```

| git stash result | meaning | action |
|---|---|---|
| Passes on HEAD | Your changes OR worktree changes caused failure | Investigate what in unstaged changes broke it |
| Fails on HEAD too | Pre-existing bug in the branch, not your fault | The tests were failing before you started |

**Working tree also may have introduced new behavior that changed test expectations**, even if you didn't touch that area. Example: a prior uncommitted change added `_get_compression_level` threshold check → tests that previously triggered compression now need explicit `last_prompt_tokens` > threshold.

The fix pattern for such pre-existing breaking changes:
1. Identify the specific behavior change in the worktree
2. Patch the **test** to match the new expected behavior (not the other way around if the behavioral change was intentional)
3. Or if the behavioral change was unintended, patch the production code

**Never spend >5 min debugging a test failure until you've verified whether it fails on HEAD.**

### Phase 1 Completion Checklist

- [ ] Error messages fully read and understood
- [ ] Issue reproduced consistently
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypothesis formed

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

---

## Phase 2: Pattern Analysis

**Find the pattern before fixing:**

### 1. Find Working Examples

- Locate similar working code in the same codebase
- What works that's similar to what's broken?

**Action:** Use `search_files` to find comparable patterns:

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

### 2. Compare Against References

- If implementing a pattern, read the reference implementation COMPLETELY
- Don't skim — read every line
- Understand the pattern fully before applying

### 3. Identify Differences

- What's different between working and broken?
- List every difference, however small
- Don't assume "that can't matter"

### 4. Understand Dependencies

- What other components does this need?
- What settings, config, environment?
- What assumptions does it make?

---

## Phase 3: Hypothesis and Testing

**Scientific method:**

### 1. Form a Single Hypothesis

- State clearly: "I think X is the root cause because Y"
- Write it down
- Be specific, not vague

### 2. Test Minimally

- Make the SMALLEST possible change to test the hypothesis
- One variable at a time
- Don't fix multiple things at once

### 3. Verify Before Continuing

- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis
- DON'T add more fixes on top

### 4. When You Don't Know

- Say "I don't understand X"
- Don't pretend to know
- Ask the user for help
- Research more

---

## Phase 4: Implementation

**Fix the root cause, not the symptom:**

### 1. Create Failing Test Case

- Simplest possible reproduction
- Automated test if possible
- MUST have before fixing
- Use the `test-driven-development` skill

### 2. Implement Single Fix

- Address the root cause identified
- ONE change at a time
- No "while I'm here" improvements
- No bundled refactoring

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

### 4. If Fix Doesn't Work — The Rule of Three

- **STOP.**
- Count: How many fixes have you tried?
- If < 3: Return to Phase 1, re-analyze with new information
- **If ≥ 3: STOP and question the architecture (step 5 below)**
- DON'T attempt Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture

**Pattern indicating an architectural problem:**
- Each fix reveals new shared state/coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor the architecture vs. continue fixing symptoms?

**Discuss with the user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (Phase 4 step 5).

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

### Investigation Tools

Use these Hermes tools during Phase 1:

- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run tests, check git history, reproduce bugs
- **`web_search`/`web_extract`** — Research error messages, library docs

### With delegate_task

For complex multi-component debugging, dispatch investigation subagents:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**
