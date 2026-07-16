---
name: improve-animations
description: >
  Read-only animation audit system — analyze a project's existing animations, identify
  quality gaps, and generate actionable improvement plans. Never modifies source code.
  Phases: Recon → Parallel Audit → Vetting → Implementation Plans. Pairs with
  apple-design for physics validation and gsap-animation for implementation.
---

# Improve Animations — Audit & Plan Generator

Read-only animation quality audit. Analyzes existing animations, finds gaps,
and produces ranked improvement plans without touching source code.

## Workflow

### Phase 1 — Recon
- Scan project for animation declarations (CSS transitions, CSS animations, JS libraries)
- Catalog: selectors, properties animated, durations, easing, trigger type
- Output: animation inventory markdown

### Phase 2 — Parallel Audit
Run against `references/AUDIT.md` rule set:
- Easing consistency (mixed cubic-bezier values)
- Duration hierarchy (micro 150ms, standard 300ms, page 500ms)
- Missing reduced-motion overrides
- Orphaned keyframes (no reduced-motion pair)
- Gesture connectivity (velocity not transferred)
- Performance (layout-triggering properties vs composite-only)

### Phase 3 — Vetting
- Score each finding: severity (high/med/low) × frequency × user-impact
- Filter: ignore findings with zero user-visible impact
- Rank: by priority score

### Phase 4 — Implementation Plans
- Generate per-finding plans using `references/PLAN-TEMPLATE.md`
- Each plan: what to change, before/after code, risk level, verification
- Output: ranked plan list with estimated effort

## Hard Rules

1. **Read-only** — audit and plan; never modify source code
2. **Cite sources** — every finding links to the exact file and line
3. **Before/After** — every plan shows both states
4. **Respect existing style** — don't suggest Apple-style for a brutalist site

## Compatibility

Compatible with `apple-design` (physics validation), `taste-anti-slop` (aesthetic rules),
`gsap-animation` (implementation patterns). See `apple-design/references/compatibility.md`.

## References

- `references/AUDIT.md` — rule catalog for animation quality checks
- `references/PLAN-TEMPLATE.md` — implementation plan template
