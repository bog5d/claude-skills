---
name: html-to-video
description: Convert HTML slides/pages to MP4 video with TTS narration. Playwright screenshots, ffmpeg encoding, edge-tts voice. Jinja2 templates + config.json driven + renderer/encoder separation.
category: creative
---

# HTML to Video Pipeline

Convert structured HTML content (slides, articles, infographics) into narrated MP4 video. One-shot or batch production.

> **💡 推荐配合 `taste-anti-slop` 使用。** 先加载 taste-anti-slop 做设计判读+反模板过滤，再进入 html-to-video 管线。顺序：`taste-anti-slop` → `html-to-video`。

## Architecture (the "director's cut")

```
project/
├── config.json       # Scene data: text, colors, fonts, timing
├── slides/           # Jinja2 HTML templates (zero code mixed in)
│   └── slide.html    # Uses {{ var }} placeholders
├── build.py          # Orchestrator: read config, render, encode
├── renderer.py       # Jinja2 to HTML to Playwright screenshot
└── encoder.py        # ffmpeg: frames to MP4 + audio
```

**Why three layers:** CSS and Python `.format()` should never cohabit a single string. Jinja2 `{% raw %}` block naturally isolates CSS from template variables. Config-driven means changing a scene does not touch code.

## Pitfalls

### 1. Never use Python `.format()` with CSS
CSS uses `{ }` for rules. `.format()` interprets them as placeholders. Symptom: `KeyError: ' margin'`, `KeyError: '\n    width'`.

**Fix:** Use Jinja2 (`jinja2.Template`) instead of `.format()`. If you MUST use `.format()`, double every CSS brace: `{ margin: 0 }` becomes `{{ margin: 0 }}`. Check EVERY brace in the template -- `body { ... }` blocks spanning multiple lines are especially dangerous.

### 2. Never use `npx playwright screenshot` CLI
The CLI parser (`[RTK:PASSTHROUGH]`) is unreliable on macOS. Always use the Python API:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1080, "height": 1920})
    page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
    page.screenshot(path=str(output_path), full_page=False)
    browser.close()
```

Note: `Path.as_uri()` produces `file:///path/to/file.html` -- required for `page.goto()`.

### 3. Playwright needs separate browser install
`pip install playwright` installs the library but NOT the browser binary. Missing browser causes: `BrowserType.launch: Executable doesn't exist`.

Run once per environment: `playwright install chromium` (~170 MB download).

### 4. `.format()` does not support expressions
`{W-120}` in a `.format()` call raises `KeyError: 'W-120'`. Pre-compute in Python and pass as a named variable: `W120 = W - 120`, then use `{W120}`. Jinja2 handles `{{ W - 120 }}` fine.

### 5. STHeiti for Chinese fonts on macOS
`/System/Library/Fonts/STHeiti Medium.ttc` is the reliable Chinese font for PIL rendering on macOS. PingFang may exist but STHeiti is guaranteed.

## Pipeline Steps

1. **TTS**: `edge_tts.Communicate(text, "zh-CN-YunxiNeural")` -- male narrative voice
2. **HTML to Screenshot**: Playwright Python API (see pitfall 2)
3. **Frame generation**: PIL draw progress bar overlay per frame, save PNG sequence
4. **Encode**: ffmpeg `-framerate 30 -i f_%05d.png -i audio.mp3 -c:v libx264 -preset fast -crf 23`
5. **Concatenate**: ffmpeg concat demuxer for multi-segment videos

## TTS Voice Options

| Voice | Gender | Style |
|-------|--------|-------|
| `zh-CN-YunxiNeural` | Male | Narrative, calm |
| `zh-CN-YunjianNeural` | Male | News-style |
| `zh-CN-XiaoxiaoNeural` | Female | Warm |
| `zh-CN-XiaoyiNeural` | Female | Bright |
