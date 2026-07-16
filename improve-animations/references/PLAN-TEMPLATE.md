# Animation Improvement Plan Template

For each finding, generate a plan using this template. One file per finding or group related low-severity findings.

```markdown
## Plan {N}: {Short Title}

**Severity:** {HIGH / MEDIUM / LOW}
**Priority Score:** {number}
**Files Affected:** {count}
**Estimated Effort:** {S / M / L / XL}

### Source

| File | Line(s) | Rule ID | Finding |
|------|---------|---------|---------|
| `path/to/file.css` | 42–48 | EASING-03 | Linear transition on `.nav-link` hover |

### Current State

```css
.nav-link {
  transition: opacity 200ms linear;
}
```

### Target State

```css
.nav-link {
  transition: opacity 150ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Rationale

{1–2 sentences explaining WHY this change improves quality}

### Risk

| Risk | Level |
|------|-------|
| Visual regression | LOW |
| Interaction breakage | NONE |
| Performance impact | NEUTRAL |

### Verification

- [ ] Animation plays at 60fps (Chrome DevTools Performance panel)
- [ ] No layout shift during animation
- [ ] `prefers-reduced-motion` respected
- [ ] Visual diff passes review

### Implementation Notes

{Any edge cases, gotchas, or dependencies on other fixes}
```

## Severity-to-Effort Mapping

| Severity | Typical Effort | Example |
|----------|---------------|---------|
| HIGH | M–L | Adding reduced-motion fallback to 15 keyframe animations |
| MEDIUM | S–M | Fixing easing on 5 component files |
| LOW | S | Duration tweak on single element |

## Plan Naming Convention

`plan-{NN}-{short-slug}.md`

Examples:
- `plan-01-reduced-motion-fallback.md`
- `plan-02-easing-consistency.md`
- `plan-03-touch-targets-navigation.md`
