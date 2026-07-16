# Animation Quality Audit Rule Catalog

The audit engine checks these rules against a project's animation inventory.

## Rule Categories

### 1. Easing Consistency (MOTION_INTENSITY-aware)

| Rule ID | Check | Severity |
|---------|-------|----------|
| EASING-01 | Mixed cubic-bezier values within same component type | MEDIUM |
| EASING-02 | `ease` / `ease-in-out` as default (use penner equivalents instead) | LOW |
| EASING-03 | Linear transitions for UI elements (should use subtle ease) | HIGH |
| EASING-04 | Easing curve does not match apple-design spring spec when spring is intended | MEDIUM |

### 2. Duration Hierarchy

| Rule ID | Check | Severity |
|---------|-------|----------|
| DUR-01 | Micro-interaction duration > 200ms | MEDIUM |
| DUR-02 | Page transition duration < 300ms | LOW |
| DUR-03 | No duration variation — all animations exactly same length | HIGH |
| DUR-04 | Duration exceeds 800ms for any non-hero animation | HIGH |

**Reference scale:**
- Micro (hover/active feedback): 100–200ms
- Standard (layout shifts, reveals): 250–400ms
- Page (route changes, sheet entry): 400–600ms
- Hero (splash, dramatic reveals): 600–1000ms

### 3. Reduced Motion

| Rule ID | Check | Severity |
|---------|-------|----------|
| REDMO-01 | No `prefers-reduced-motion` media query anywhere | HIGH |
| REDMO-02 | Reduced-motion override uses `display: none` instead of cross-fade | MEDIUM |
| REDMO-03 | Orphaned keyframe animation without reduced-motion pair | MEDIUM |
| REDMO-04 | Scroll-driven animation not disabled in reduced-motion mode | HIGH |

### 4. Gesture Connectivity (apple-design §7–8)

| Rule ID | Check | Severity |
|---------|-------|----------|
| GEST-01 | Swipe/drag gesture release without velocity transfer to animation | HIGH |
| GEST-02 | Animation runs to completion without interruption support | HIGH |
| GEST-03 | No rubber-band effect at scroll/pan boundaries | MEDIUM |
| GEST-04 | Touch target < 44×44px for gesture-driven elements | HIGH |

### 5. Performance (Composite-Only)

| Rule ID | Check | Severity |
|---------|-------|----------|
| PERF-01 | Animating `width`/`height` instead of `transform: scale()` | HIGH |
| PERF-02 | Animating `top`/`left`/`margin` instead of `transform: translate()` | HIGH |
| PERF-03 | Animating `box-shadow` on large elements (> 50×50px) | MEDIUM |
| PERF-04 | No `will-change` on frequently animated elements | LOW |
| PERF-05 | `will-change` left on after animation ends (memory leak) | MEDIUM |

### 6. Stagger & Orchestration

| Rule ID | Check | Severity |
|---------|-------|----------|
| STAG-01 | List items or cards animate in simultaneously (no stagger) | MEDIUM |
| STAG-02 | Stagger delay > 80ms per item | LOW |
| STAG-03 | Exit animations happen before enter animations finish (overlap) | MEDIUM |

### 7. Material & Depth (apple-design §13–15)

| Rule ID | Check | Severity |
|---------|-------|----------|
| MAT-01 | Uses `opacity` instead of `backdrop-filter: blur()` for translucent surfaces | LOW |
| MAT-02 | Content scrolls over fixed chrome instead of under it | MEDIUM |
| MAT-03 | More than 3 visible depth planes without clear z-index hierarchy | LOW |

## Severity Scoring

| Severity | Base | User-impact multiplier |
|----------|------|----------------------|
| HIGH | 10 | × (1 + frequency/10) |
| MEDIUM | 5 | × (1 + frequency/10) |
| LOW | 2 | × (1 + frequency/10) |

Priority score = severity_base × user_impact_multiplier. Findings with zero user-visible impact are filtered out.

## Style-Aware Exceptions

Do NOT flag as violations:
- Linear transitions in brutalist/industrial designs (part of the aesthetic)
- Oversized touch targets when the UI is pointer-only (desktop web app)
- Missing reduced-motion on purely decorative canvas/webgl animations
- `ease` on `< 100ms` micro-interactions (imperceptible difference)
