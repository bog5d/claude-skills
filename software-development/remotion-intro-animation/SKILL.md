---
name: remotion-intro-animation
description: Build and render a Remotion-based brand intro animation (10s, 1080p, H.264) from scratch, including SVG particle systems, neon glow text, flash transitions, and spring animations.
---

# Remotion 品牌开场动画制作

Use when you need to create a Remotion video project from scratch (scaffolding CLI fails) or generate a 10s cinematic brand intro.

## Triggers
- User asks for a "Remotion" intro/opening animation
- Need to render a programmatic video with particle effects, text animations, glows
- `create-video` CLI scaffolding fails (non-interactive mode)

## Prerequisites
- Node.js + npm installed
- Chrome/Chromium available (`/Applications/Google Chrome.app` or system Chrome)
- Working directory for the project (e.g., `~/aider_workspace/hermes-intro`)

## Project Setup Steps

```bash
# 1. Create project dir and init npm
mkdir -p ~/aider_workspace/hermes-intro/src
cd ~/aider_workspace/hermes-intro
npm init -y

# 2. Install Remotion — PIN the version (latest may timeout)
npm install @remotion/cli@4.0.0 remotion@4.0.0 @remotion/renderer@4.0.0 @remotion/bundler@4.0.0 react@18.3.1 react-dom@18.3.1

# 3. Create source files (see below)
```

## Source File Structure

```
hermes-intro/
├── src/
│   ├── index.ts          # registerRoot(Root)
│   ├── Root.tsx          # <Composition> definition
│   └── HermesIntro.tsx   # Main animation component
├── remotion.config.ts    # Config.setVideoImageFormat("png")
├── tsconfig.json
└── package.json
```

### package.json scripts
```json
"scripts": {
  "build": "npx remotion render src/index.ts HermesIntro out.mp4"
}
```

## Key Component Architecture

### HermesIntro.tsx
- `useCurrentFrame()` for frame counting; `time = frame / 30`
- `spring()` for title/subtitle bounce-in (damping: 8-10, stiffness: 100-120, mass: 0.5-0.6)
- `interpolate()` with `extrapolateRight: "clamp"` for blur fade, opacity, flash

### SVG Particle System
- Pre-generate 180 particles with random position, phase, speed, amplitude
- Pre-compute nearest-3 connections for each particle (Euclidean distance)
- Animate with sinusoidal functions: `sin(t * speed + phase)` for organic flow
- Draw lines between connected particles, opacity based on distance / 250px threshold
- Add flow field overlay: `sin(x*0.003 + y*0.002 + t*0.3)` etc.

### SVG Glow Filter
```tsx
<filter id="neonGlow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="blur1" />
  <feGaussianBlur in="SourceGraphic" stdDeviation="16" result="blur2" />
  <feGaussianBlur in="SourceGraphic" stdDeviation="30" result="blur3" />
  <feMerge>
    <feMergeNode in="blur3" />
    <feMergeNode in="blur2" />
    <feMergeNode in="blur1" />
    <feMergeNode in="SourceGraphic" />
  </feMerge>
</filter>
```

### Timing (10s @ 30fps = 300 frames)
| Scene | Frames | Duration |
|-------|--------|----------|
| Particles build up | 0-60 | 2s |
| Flash 1 | 118-128 | 0.33s |
| "HERMES.AI" title | 132-160+ | spring+ease |
| Flash 2 | 208-218 | 0.33s |
| "SUPERVISOR PROTOCOL" subtitle | 222-250+ | spring+ease |

### Flash Transition
```tsx
const flash = interpolate(frame, [118, 122, 128], [0, 1, 0], {
  extrapolateLeft: "clamp", extrapolateRight: "clamp",
});
// Render as white div with opacity * 0.85
```

## Rendering
```bash
cd ~/aider_workspace/hermes-intro
npx remotion render src/index.ts HermesIntro out.mp4 --codec h264 --crf 23 --overwrite
```

CRF 23 on 10s produces ~3MB which is well under 5MB target.

## Pitfalls
- **DO NOT** use `@latest` for npm install — 10min+ timeout. Pin to `@4.0.0`.
- Chrome must be locatable by Remotion; verify with `which google-chrome` or check `/Applications/`.
- `create-video` CLI has a template selector that hangs in non-TTY mode. Always scaffold manually.
- `remotion.config.ts` must call `Config.setOverwriteOutput(true)` or re-renders fail on existing out.mp4.
- Use `React.memo` on the particle canvas component to avoid re-render of all SVG nodes each frame.
- Particle connections pre-computation (nearest-neighbor) should happen once in `useMemo`, not per frame.
- The `GlowFilter` SVG component goes in a `<defs>` block with a `<svg width="0" height="0">` wrapper — don't render it visibly.
