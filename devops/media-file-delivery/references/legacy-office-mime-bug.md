# Legacy Office MIME Bug — Full Reproduction & Fix

## Problem

Users uploading `.xls`, `.doc`, or `.ppt` files to Hermes via Telegram receive "Unsupported document type" and the file is silently rejected. The MEDIA regex pattern already matches these extensions (via `xlsx?`, `docx?`, `pptx?`), but after extraction the code checks `SUPPORTED_DOCUMENT_TYPES` which lacked the legacy binary format MIME types.

## Root Cause

`gateway/platforms/base.py` line 908–928 defines `SUPPORTED_DOCUMENT_TYPES` dict:

```python
SUPPORTED_DOCUMENT_TYPES = {
    ...
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    # MISSING: .doc, .xls, .ppt
    ...
}
```

This dict is checked at `telegram.py` line 5237:
```python
if ext not in SUPPORTED_DOCUMENT_TYPES:
    supported_list = ", ".join(sorted(SUPPORTED_DOCUMENT_TYPES.keys()))
    event.text = f"Unsupported document type '{ext or 'unknown'}'. Supported types: {supported_list}"
    ...
    return  # File rejected
```

## Fix

Added three entries after the Office OpenXML entries:

```python
".doc": "application/msword",
".xls": "application/vnd.ms-excel",
".ppt": "application/vnd.ms-powerpoint",
```

Applied via `patch` tool at `gateway/platforms/base.py:925`.

## Verification

```python
from gateway.platforms.base import SUPPORTED_DOCUMENT_TYPES

for ext in ['.xls', '.doc', '.ppt']:
    mime = SUPPORTED_DOCUMENT_TYPES.get(ext)
    assert mime is not None, f"{ext} still missing!"
    print(f"  {ext} → {mime}")
```

## Affected Platforms

This dict is imported and used by:
- `telegram.py` — line 5237 (user upload check)
- `slack.py` — line 2116, 2119, 2134 (file delivery)
- `feishu.py` — line 172, 3224, 3765 (file delivery + MIME resolution)
- `whatsapp.py` — line 1227 (MIME fallback)

All platforms that receive documents from users were potentially affected.
