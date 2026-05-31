# Gateway MEDIA Delivery — Source Code Analysis

## Validation chain

```
User response with MEDIA:/path/to/file
  → gateway/run.py: _deliver_media_from_response()
    → adapter.extract_media(response)
    → BasePlatformAdapter.filter_media_delivery_paths(media_files)
      → validate_media_delivery_path(path)
        → resolves path (strict=True, must exist)
        → checks against _media_delivery_allowed_roots()
```

## Safe roots (MEDIA_DELIVERY_SAFE_ROOTS)

Defined in `gateway/platforms/base.py:830`:

```python
MEDIA_DELIVERY_SAFE_ROOTS = (
    IMAGE_CACHE_DIR,       # get_hermes_dir("cache/images", "image_cache")
    AUDIO_CACHE_DIR,       # get_hermes_dir("cache/audio", "audio_cache")
    VIDEO_CACHE_DIR,       # get_hermes_dir("cache/videos", "video_cache")
    DOCUMENT_CACHE_DIR,    # get_hermes_dir("cache/documents", "document_cache")
    SCREENSHOT_CACHE_DIR,  # get_hermes_dir("cache/screenshots", "browser_screenshots")
    _HERMES_HOME / "image_cache",
    _HERMES_HOME / "audio_cache",
    _HERMES_HOME / "video_cache",
    _HERMES_HOME / "document_cache",
    _HERMES_HOME / "browser_screenshots",
)
```

## Why profile cache doesn't work

`get_hermes_dir()` resolves paths against the **gateway process's** `HERMES_HOME`. The gateway runs under the default profile (`/Users/mac/.hermes/`), not any named profile.

When a session runs under `english-tutor` profile:
- `~` in terminal commands → `/Users/mac/.hermes/profiles/english-tutor/home/`
- `~/.hermes/cache/` → profile cache (gateway doesn't see it)
- Gateway's safe roots → `/Users/mac/.hermes/cache/` (default profile)

**Result**: Files copied to `~/.hermes/cache/` from a named profile session end up in the profile cache, not the gateway's allowed roots. The MEDIA tag is silently dropped.

## Fix

Always use absolute paths to the default profile cache:

```bash
cp file /Users/mac/.hermes/cache/screenshots/safe.png  # ✅ works
cp file ~/.hermes/cache/screenshots/safe.png            # ❌ profile context, gateway can't see
```

## HERMES_MEDIA_ALLOW_DIRS

Environment variable checked by `_media_delivery_allowed_roots()`. Set in the default profile's `.env` to add extra allowed roots. Requires gateway restart.

## Discovery method (2026-05-30)

- Symptom: MEDIA tags and send_message with MEDIA paths returned success but user received nothing
- Diagnosis: Compared `~` expansion in profile context vs. gateway's safe roots
- Validation: Source code inspection of `validate_media_delivery_path()` and `_media_delivery_allowed_roots()`
- Resolution: Copy to `/Users/mac/.hermes/cache/` (absolute, default profile)
