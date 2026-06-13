# External Repo Evaluation Playbook

## When to use
A "review the repos from this list and tell me what's worth integrating" task. The user drops a batch of trending GitHub projects and wants actionable integration decisions, not summaries.

## Phase 1: Triage (parallel, 5 min)

1. **Filter against existing capabilities first.** Before cloning anything, scan names/descriptions against our skill library and deployed tooling. Flag duplicates and known overlaps immediately.

2. **Clone in parallel.** All repos that pass the filter get cloned simultaneously to /tmp. Don't wait for each to finish sequentially.

3. **For each repo, identify the minimal invocation:**
   - Is there a direct API call that works? Try `curl` first.
   - Is there a pip/npm package? Check `pip install` time vs complexity.
   - Does it wrap upstream tools (e.g., Agent-Reach → bili-cli)? Skip the wrapper, test the underlying tool directly.
   - The goal: prove it works with the least code possible.

## Phase 2: Deep read (3-5 min per candidate)

For high-value candidates, read in this order:
1. README.md / llms.txt — architecture overview, integration modes
2. Core entry point (e.g., `compress.py`, `cli.py`) — actual API signature
3. Platform-specific channels (e.g., `channels/bilibili.py`) — how it actually reaches the service
4. Test files — reveals edge cases and expected behavior

## Phase 3: Integration classification

For each candidate, classify into exactly one:

| Tier | Label | Action |
|------|-------|--------|
| P0 | Works now, zero setup | Implement immediately |
| P1 | Works with minor config | Document setup steps, then implement |
| P2 | Promising but needs infra | Star + watch, revisit later |
| — | Overlap with existing | Skip, note the overlap |
| — | Not our domain | Skip, no action |

## Phase 4: Hermes-specific integration paths

When evaluating a tool for Hermes integration, ask these three questions:

1. **Can it be a tool?** — `tools/search_bilibili.py` calling a single endpoint
2. **Can it be middleware?** — Hook into the tool output pipeline before context
3. **Can it be a provider/config?** — Swap out a backend (e.g., compression provider)

The simpler the integration, the less maintenance. Prefer direct API calls over wrapping complex CLI tools.

## Key pitfall: confusing "the wrapper" with "the tool"

Agent-Reach is an *installer/doctor* that delegates to upstream tools (bili-cli, OpenCLI, xiaohongshu-mcp). It doesn't do search itself. When evaluating such a project, find the actual tool that does the work and test *that* directly.

Example: Agent-Reach's B站 channel → actual work done by `curl api.bilibili.com` or `bili-cli`. Test the curl first.
