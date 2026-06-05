# ai-qujing-v3 Build Script Reference

This is the working build script from the AI 取经记 02 production session.
It uses Playwright Python API + PIL + ffmpeg + edge-tts.

## Key decisions made in this script:

1. **HTML template uses `{{ }}` escaping for `.format()`** — not Jinja2 (quick fix, not ideal)
2. **Playwright Python API** — not the broken CLI
3. **PIL overlay for progress bar** — drawn per-frame in Python, not CSS animated
4. **Concatenation with two-pass fallback** — first tries `-c copy` (fast), then re-encodes

## Environment dependencies:
- `pip install playwright edge-tts pillow`
- `playwright install chromium`
- `brew install ffmpeg` (system package)

## Script location (reference):
`/tmp/ai-qujing-v3/build.py`

## Scene config format:
```python
SCENES = [
    {
        "id": "01",
        "text": "TTS narration text here...",
        "bg": "linear-gradient(135deg, #1a0a2e 0%, #16213e 50%, #0f3460 100%)",
        "big": "Main Title\nLine 2",
        "sub": "Subtitle text",
        "big_color": "#ffd700",
        "big_size": 64,
        "sub_size": 36,
        "sub_color": "#ccc",
        "big_top": 500,
        "sub_margin": 80,
        "extra_css": "",
    },
    ...
]
```

## Output:
- 1080x1920 (vertical, 9:16) at 30 FPS
- 6 scenes with edge-tts male narration
- 2.4 MB final MP4

## Debug timeline (this session):
1. `KeyError: ' margin'` → CSS single braces in `.format()` template
2. `KeyError: '\n    width'` → `body { ... }` block not escaped
3. `KeyError: 'W-120'` → expression in `.format()` template
4. `[RTK:PASSTHROUGH]` → npx playwright CLI broken, switched to Python API
5. `Executable doesn't exist` → `playwright install chromium` needed
