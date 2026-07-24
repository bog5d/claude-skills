# macOS Screenshot Fallback — Terminal-Based

When `computer_use(action="capture")` is unavailable (model doesn't support vision,
cua-driver broken, etc.), use terminal-based `screencapture` as a reliable fallback.
These work regardless of model capabilities — they produce real PNG files that can
be sent via MEDIA or curl.

## Tier 1: Full-Screen Capture (most reliable)

```bash
screencapture -x -t png /tmp/capture.png
```

- `-x`: no sound effect (silent)
- `-t png`: PNG format
- Full screen, all monitors captured
- Always works, no osascript needed, no window targeting needed

## Tier 2: App-Specific Attempt (may timeout)

```bash
# Get window ID of Chrome's frontmost window
WID=$(osascript -e 'tell application "System Events" to get id of window 1 of process "Google Chrome"' 2>/dev/null)

# If WID is non-empty, capture that window
if [ -n "$WID" ]; then
  screencapture -x -l"$WID" /tmp/capture.png
else
  # Fall back to full screen
  screencapture -x -t png /tmp/capture.png
fi
```

**Known issue**: `osascript` with "System Events" frequently times out on some macOS
configurations (security prompts, TCC permissions, etc.). When it fails, skip
straight to Tier 1 — don't retry osascript multiple times.

## Tier 3: Open App + Capture

When no browser window with the target page is available:

```bash
# Open the target file in Chrome
open -a "Google Chrome" /path/to/file.html

# Wait for render (2-3 seconds)
sleep 3

# Full-screen capture
screencapture -x -t png /tmp/capture.png
```

## Sending the Screenshot

Copy to a known-safe directory and send via MEDIA:

```bash
cp /tmp/capture.png ~/Downloads/capture.png
```

Then in reply: `MEDIA:/Users/mac/Downloads/capture.png`

If MEDIA delivery fails (httpx.ConnectError, etc.), try curl Telegram Bot API as
documented in `telegram-file-delivery` skill.

## When to use this vs computer_use

| Situation | Tool |
|---|---|
| Model supports vision + cua-driver healthy | `computer_use(action="capture")` |
| Model can't process images (DeepSeek) | Terminal `screencapture` fallback |
| Need to inspect a rendered HTML page visually | Terminal `screencapture` + send to user |
| cua-driver not installed or broken | Terminal `screencapture` fallback |
