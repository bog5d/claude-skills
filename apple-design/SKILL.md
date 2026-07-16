---
name: apple-design
description: >
  Apple's approach to interface design and fluid, physical motion, translated for the web.
  Use when building or reviewing gesture-driven UI, spring animations, drag/swipe/sheet
  interactions, momentum and interruptible transitions, translucent materials and depth,
  typography (optical sizing, tracking, leading), reduced-motion, or the design foundations
  (feedback, spatial consistency, restraint) behind Apple-style interfaces. Also applies to
  any HTML-rendered output with interactive elements — investor decks, annual reports,
  product pages, slide presentations (Reveal.js, Guizang PPT), interactive documents, and
  landing pages that need premium feel beyond static aesthetics. Not for static Word/PDF
  generation (typography rules only).
---

# Apple Design — Fluid Interfaces for the Web

Translates Apple's approach to fluid, physical motion for the web, based on WWDC 2018
"Designing Fluid Interfaces" and Apple HIG. Use when building or reviewing gesture-driven
UI, spring animations, drag/swipe/sheet interactions, momentum physics, or translucent
materials.

## 17 Design Principles

### Feedback & Response
1. **Instant visual feedback** — `:active { transform: scale(0.98) }` on every press
2. **Haptics-approximating** — spring response 0.3–0.5s mimics physical feel
3. **Push, don't jump** — content transitions use push/cover semantic directions

### Physics
4. **Spring default: critical damping** — `damping: 1.0, response: 0.4` for standard moves
5. **Sheets and drawers** — lighter: `damping: 0.8, response: 0.3`
6. **Momentum projection** — `project(velocity, decay=0.998)` for gesture release
7. **Velocity transfer** — `relativeVelocity = gestureVelocity / (targetPosition − currentPosition)`

### Interruptibility
8. **All animations must be gesture-interruptible** — never `await animation.finished` alone
9. **Rubber-band at boundaries** — scroll/pan resistance at edges, not hard stops
10. **Cancel previous** — `animation.cancel()` before starting a new one on the same property

### Spatial Consistency
11. **Mirror-path transitions** — enter animation path = reverse of exit path
12. **Consistent source of motion** — elements appear from and return to their origin

### Materials & Depth
13. **Translucency over opacity** — `backdrop-filter: blur(24px) saturate(180%)` for nav bars
14. **Content scrolls under material** — not over it; use `position: sticky` on shell
15. **Three depth planes** — foreground (gestures), midground (content), background (chrome)

### Typography
16. **Optical sizing** — large display text tighter tracking (`-0.03em`), body near zero
17. **Dynamic type scale** — respect user's preferred content size where possible

## Spring Parameters Reference

| Component | Damping | Response | Mass |
|---|---|---|---|
| Standard move | 1.0 | 0.4 | 1.0 |
| Sheet / Drawer | 0.8 | 0.3 | 1.0 |
| Light bounce | 0.7 | 0.45 | 1.0 |
| Snappy | 1.0 | 0.2 | 1.0 |

Formula for spring-to-css: `stiffness = mass × (2π / response)²`, `dampingRatio = dampingCoefficient / (2 × √(mass × stiffness))`

## Material Specs

| Layer | Backdrop Blur | Saturation | Background |
|---|---|---|---|
| Toolbar / Nav | 24px | 180% | rgba(255,255,255,0.72) |
| Sheet / Card surface | 12px | 150% | rgba(255,255,255,0.60) |
| System chrome | 8px | 120% | rgba(0,0,0,0.08) |

Dark mode: swap white backgrounds for `rgba(28,28,30,0.82)` with same blur values.

## Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; }
}
```

Always provide a cross-fade alternative instead of slide/spring when motion is reduced.

## Interactive Gesture Targets

| Target size | Minimum | Recommended |
|---|---|---|
| Touch | 44×44px | 48×48px |
| Pointer | 24×24px | 32×32px |

## Compatibility

See `references/compatibility.md` for orthogonality with `taste-anti-slop`, `gsap-animation`,
and `improve-animations`. Load order: taste-anti-slop → apple-design → gsap-animation.

## Checklist

- [ ] `:active` scale feedback on all tappable elements
- [ ] Spring defaults documented (damping, response) for each animation
- [ ] Gesture velocity transferred to animation on release
- [ ] All animations cancellable (interruptible)
- [ ] `prefers-reduced-motion` handled with cross-fade fallback
- [ ] Materials use `backdrop-filter`, not opacity
- [ ] Navigation ≤ 80px height, single row
- [ ] Touch targets ≥ 44×44px
