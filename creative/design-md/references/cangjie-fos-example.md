# 仓颉 FOS — DESIGN.md Worked Example

Real-world DESIGN.md created for Cangjie FOS (融资作战系统 / Fundraising
Operations System). 358 lines, 24 colors, 12 typography scales, 27 components.
Serves as a reference for complex dark-theme design systems.

## Design Language

**深海暗色 × 军工科技 × 中国水墨** (Deep-sea dark × Defense tech × Chinese
ink wash). The UI is a HUD-style command cockpit: dark void backgrounds,
plasma-purple primary actions, cyan secondary accents, ink-gold highlights,
and vermillion danger signals.

## Palette Architecture (24 colors)

```
void:       #070b14  ← deepest background (viewport)
voidCard:   #0d1326  ← card/surface
voidPanel:  #111b33  ← elevated panel
plasma:     #7b5cff  ← primary CTA / active (WCAG WARNING: 4.36:1 on white)
plasmaMuted:#5a3fd4  ← primary hover (WCAG PASS: 5.2:1 on white)
cyan:       #2ec4b6  ← secondary / success / links
cyanMuted:  #1a8a7d  ← secondary hover
ember:      #ff9f1c  ← warning / tertiary accent
emberMuted: #cc7a0f  ← warning hover
vermillion: #C41E3A  ← danger / delete
jade:       #2F9B6A  ← success alt
inkGold:    #C9A84C  ← premium / highlighted data
inkLight:   #e8e4dc  ← primary text on void (warm off-white)
inkMid:     #9ca3af  ← secondary text / labels
inkDark:    #1f2937  ← muted text on light backgrounds
stoneWarm:  #F7F5F2  ← light surface accent (rare: print/export)
success:    #2ec4b6  ← semantic alias
warning:    #ff9f1c  ← semantic alias
danger:     #C41E3A  ← semantic alias
```

## Typography Scale (12 levels)

Primary: `Inter` (system UI stack). Monospace: `JetBrains Mono` (data tables).
Chinese fallback: `PingFang SC, Noto Sans SC, Microsoft YaHei`.

| Token | Size | Weight | Use |
|-------|------|--------|-----|
| h1 | 2.5rem | 700 | Page title |
| h2 | 1.75rem | 600 | Section header |
| h3 | 1.25rem | 600 | Card header |
| display-xl | 3.5rem | 800 | Dashboard KPI |
| display-lg | 2.75rem | 700 | Hero metric |
| body-lg | 1.125rem | 400 | Body copy |
| body-md | 1rem | 400 | Default |
| body-sm | 0.875rem | 400 | Labels, meta |
| caption | 0.75rem | 400 | Timestamps |
| overline | 0.625rem | 600 | Section overline |
| mono-md | 0.875rem | 400 | Code / data |
| mono-sm | 0.75rem | 400 | Compact data |

## Component Inventory (27 components)

- **Buttons:** primary, primary-hover, secondary, secondary-hover, ghost, danger
- **Inputs:** text, text-focus, select, textarea, search
- **Data:** table-header, table-row, table-row-alt, table-cell
- **Navigation:** nav-item, nav-item-active, breadcrumb
- **Feedback:** badge-info, badge-warning, badge-success, badge-danger
- **Cards:** card, card-header, card-elevated
- **Misc:** tooltip, divider, skeleton-loader

## Delivered Files

| File | Lines | Purpose |
|------|-------|---------|
| `DESIGN.md` | 358 | Canonical spec (YAML front matter + Markdown rationale) |
| `tailwind.theme.json` | ~200 | Tailwind `extend.theme` for Tailwind-based projects |
| `cangjie-theme.css` | ~150 | Native CSS variables for non-Tailwind skills |
| `design-system-demo.html` | ~200 | Visual gallery rendering all 27 components |

## Lessons Learned

1. **24 colors is a lot** for a first DESIGN.md. Start with 6-8 and expand.
   The lint CLI doesn't validate semantic redundancy — we had `success: #2ec4b6`
   and `cyan: #2ec4b6` aliasing the same hex.

2. **Purple plasma #7b5cff failed WCAG AA on white (4.36:1).** Fixed by
   introducing `plasmaMuted: #5a3fd4` for text-on-light scenarios. This is a
   structural pattern: every accent color needs a `-Muted` variant for WCAG.

3. **CSS variables file must resolve ALL token references.** `{rounded.sm}` →
   `4px`, not `${rounded-sm}`. Self-contained CSS wins over DRY when
   distributing to skills that don't parse DESIGN.md.

4. **The demo page proved the palette works in practice.** Browser rendering
   catches issues that lint doesn't: glow effects on void backgrounds look
   great, but cyan-on-voidCard is barely readable at small sizes.
