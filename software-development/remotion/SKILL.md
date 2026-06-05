---
name: remotion
description: Remotion-based video generation — brand intros, photo MVs, slideshows. Covers project scaffolding, rendering, and common pitfalls.
version: 1.0.0
author: Hermes Agent (curator consolidation)
metadata:
  hermes:
    tags: [remotion, video, react, animation, rendering]
---

# Remotion Video Generation

Class-level umbrella for building and rendering Remotion-based videos — from brand intros to photo slideshows to beat-synced music videos.

## When to Load

- Building any Remotion video project from scratch
- Rendering a video with Remotion CLI
- Debugging Remotion setup issues (npm timeouts, Chrome detection, scaffolding)

## Common Setup (All Remotion Projects)

```bash
mkdir -p ~/project-name/src
cd ~/project-name
npm init -y
# PIN to @4.0.0 — @latest times out in non-TTY
npm install @remotion/cli@4.0.0 remotion@4.0.0 @remotion/renderer@4.0.0 react@18.3.1 react-dom@18.3.1
npm install --save-dev @types/react@^18.2.0 typescript@^5.0.0
```

### Essential Config Files

**remotion.config.ts:**
```ts
import { Config } from "@remotion/cli/config";
Config.setVideoImageFormat("png");
Config.setOverwriteOutput(true);
```

**src/index.ts:**
```ts
import { registerRoot } from "remotion";
import { Root } from "./Root";
registerRoot(Root);
```

**src/Root.tsx:**
```tsx
import { Composition } from "remotion";
import { YourComponent } from "./YourComponent";

export const Root: React.FC = () => (
  <Composition
    id="YourComposition"
    component={YourComponent}
    durationInFrames={300}
    fps={30}
    width={1920}
    height={1080}
  />
);
```

### Rendering

```bash
cd ~/project-name
npx remotion render src/index.ts YourComposition out.mp4 --codec h264 --crf 23
```

## Sub-Skill Map

| Use Case | Reference |
|----------|-----------|
| Brand intro animation (particles, neon glow, flash) | `references/remotion-intro-animation.md` |
| Photo MV with beat sync + BPM analysis | `references/remotion-photo-mv-pro.md` |
| Simple photo slideshow (obsoleted by pro version) | `references/photo-slideshow-mv.md` |

## Common Pitfalls

- **DO NOT** use `@latest` for npm install — 10min+ timeout. Pin to `@4.0.0`.
- **Manual scaffolding only** — `create-video` CLI hangs in non-TTY mode.
- **Use `staticFile()` not `file://`** for images — `file://` renders black in headless Chrome.
- **Audio via `<Audio>` component** — Web Audio API not captured by renderer.
- **Chrome path** — if auto-detection fails: `--chrome-binary="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`.
- **OverwriteOutput** — set in config or pass `--overwrite` flag, or re-renders fail.
- **Large output** — compress for Telegram: `ffmpeg -i out.mp4 -crf 32 -vf "scale=854:480" -movflags +faststart out_small.mp4 -y`.
