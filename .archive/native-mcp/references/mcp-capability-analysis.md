# MCP Capability Analysis Template

Before installing a new MCP server, systematically compare its tools against Hermes native capabilities to avoid redundancy and identify the real incremental value.

## Analysis Framework

Build a comparison table:

| Capability | Hermes Native | New MCP Server | Delta Value |
|---|---|---|---|
| (feature 1) | (how Hermes does it) | (how MCP does it) | 🔥/✅/❌ |
| (feature 2) | ... | ... | ... |

Use these signals:
- 🔥 = significant upgrade over Hermes native
- ✅ = parity or minor improvement
- ❌ = no Hermes equivalent (new capability)
- 🟢 = zero-config/low-friction advantage

## Decision Heuristics

**Install if** any of:
- At least one 🔥 capability
- At least one ❌ (brand new) capability that solves a recurring task
- Zero-config (no API key management) for a capability you'd use

**Skip if** all are ✅ parity — Hermes native tools are sufficient and don't burn external quota.

**Note on overlap**: New MCP tools should complement, not replace. Keep Hermes native tools enabled — they're the cost-free baseline; MCP tools are the premium upgrade path.

## Firecrawl Example (2026-06)

| Capability | Hermes Native | Firecrawl MCP | Delta |
|---|---|---|---|
| Web search | `web_search` → snippets | `search` → full page content | 🔥 |
| Single page | `web_extract` → markdown | `scrape` → markdown + structured | ✅ |
| Site crawl | ❌ none | `crawl` → multi-page recursive | ❌ new |
| Structured extraction | ❌ none | `extract` → JSON Schema driven | ❌ new |
| Web interaction | `browser_*` (heavy CDP) | Light API-level interact | complementary |
| Zero config | needs API keys | no key, 1000/mo free | 🟢 |

**Verdict**: Install. Three real gap-fills (search with content, crawl, structured extract). No conflict with existing tools.
