---
name: photo-slideshow-mv
description: Build and render a Remotion-based photo slideshow MV from local JPG photos, with cross-fade transitions, Ken Burns zoom, and Web Audio API generated piano background music.
---

# Photo Slideshow MV with Remotion

Use when you need to create a video montage from a folder of photos, with transitions, Ken Burns effect, and programmatic background music.

## Triggers
- User wants to make an "MV" from photos
- Photo slideshow with music
- Batch photo-to-video conversion
- Remotion-based photo montage

## Prerequisites
- Node.js + npm installed
- Chrome/Chromium available (system Chrome or headless)
- Photos in a local directory (JPG/PNG)
- Working directory for the project

## Project Setup

```bash
# Create project
mkdir -p ~/aider_workspace/photo_mv/src
cd ~/aider_workspace/photo_mv

# Init npm
npm init -y

# Pin Remotion to 4.0.0 (latest times out in non-TTY)
npm install @remotion/cli@4.0.0 remotion@4.0.0 @remotion/renderer@4.0.0 react@18.3.1 react-dom@18.3.1
npm install --save-dev @types/react@^18.2.0 typescript@^5.0.0
```

## File Structure

```
photo_mv/
├── src/
│   ├── index.ts           # registerRoot(Root)
│   ├── Root.tsx           # <Composition> definition
│   └── PhotoMV.tsx        # Main slideshow component
├── remotion.config.ts     # Config with OverwriteOutput
├── tsconfig.json
└── package.json
```

### package.json scripts
```json
"scripts": {
  "render": "npx remotion render src/index.ts PhotoMV out.mp4 --codec h264"
}
```

## PhotoMV.tsx Key Architecture

### Photo List
Hardcode photo filenames sorted by timestamp. Photos are loaded via `file://` absolute paths:

```tsx
const PHOTO_FILES = [
  "IMG_20250706_160544.jpg",
  // ... sorted by YYYYMMDD_HHMMSS
];
const PHOTOS_DIR = "/absolute/path/to/photos/";
const PHOTO_URLS = PHOTO_FILES.map(f => `file://${PHOTOS_DIR}${f}`);
```

### Component
- `useCurrentFrame()` for frame counting
- Each photo gets `durationPerPhoto` frames (e.g., 75 frames @ 30fps = 2.5s)
- Cross-fade: 15-frame overlap between photos
- Ken Burns zoom: scale from 1.0 to 1.03-1.05 during each photo
- Background color: black

### Transitions Logic
```tsx
const transitionFrames = 15;
const frameInPhoto = frame - currentPhotoIndex * durationPerPhoto;

if (frameInPhoto < transitionFrames) {
  // Fading in — opacity 0→1, scale 1.08→1.0 (zoom out)
} else if (frameInPhoto >= durationPerPhoto - transitionFrames) {
  // Fading out — opacity 1→0, scale 1.0→1.05 (zoom in)
} else {
  // Steady — slow zoom 1.0→1.03
}
```

### Background Music — Web Audio Piano

Generate a simple piano chord progression using `AudioContext.createBuffer()`:

```tsx
function generateAudioBuffer(ctx: AudioContext, totalDuration: number): AudioBuffer {
  const sampleRate = ctx.sampleRate;
  const buffer = ctx.createBuffer(2, sampleRate * totalDuration, sampleRate);

  // C major progression: C, G, Am, F, C, G, C
  const chords = [
    [261.63, 329.63, 392.00], // C
    [392.00, 493.88, 587.33], // G
    [440.00, 523.25, 659.25], // Am
    [349.23, 440.00, 523.25], // F
    // repeat...
  ];

  for (let channel = 0; channel < 2; channel++) {
    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate;
      // Arpeggiated chord notes with ADSR envelope + reverb
      // Sum of sine waves: fundamental + 2nd/3rd/4th harmonics
    }
  }
  return buffer;
}
```

Play via `useEffect` on mount:
```tsx
useEffect(() => {
  const ctx = new AudioContext();
  const buffer = generateAudioBuffer(ctx, totalDuration);
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  source.connect(ctx.destination);
  source.start();
}, []);
```

## Rendering

```bash
cd ~/aider_workspace/photo_mv
npx remotion render src/index.ts PhotoMV out.mp4 --codec h264 --overwrite
```

For 44 photos × 75 frames @ 30fps = 3300 frames (~110s). Render time ~5-10 min depending on machine.

## Photo Sourcing from Cloud Drives

### 123云盘
The download protection makes it tricky. Use the browser's network interception:
1. Navigate to share link with password
2. Click "提取文件" then "浏览器下载"
3. Intercept XHR/fetch to `/b/api/v2/file/batch_download_share_info`
4. Response contains `dispatchList` (CDN prefix) + `downloadPath` (file path)
5. Concatenate prefix + path, use `curl -L -o file.zip "url"` to download
6. Unzip: `unzip file.zip -d target_dir/`

Note: 123云盘 wraps files in a zip container even if they show as a single file. The filename may be misleading (e.g., `.jpg` but actually a zip). Check with `file` command.

## Pitfalls
- **DO NOT** use `@latest` for npm install — 10min+ timeout. Pin to `@4.0.0`.
- **File paths**: Remotion webpack doesn't have Node `path` module. Hardcode absolute paths as strings.
- **Web Audio in Remotion**: AudioContext must be created in component mount (useEffect), not at module level. The browser's playback API works in headless Chrome.
- **Large output**: 110s @ 30fps = ~50-100MB. May exceed Telegram's 50MB limit for direct sending. Compress with `ffmpeg -i out.mp4 -crf 28 -b:v 1M compressed.mp4` if needed.
- Chrome detection: Use system Chrome (`--chrome-binary="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`) if puppeteer's headless shell is not found.
