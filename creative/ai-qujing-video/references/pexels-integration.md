# Pexels Image Sourcing for ai-qujing v3

## Architecture

```
build.py (Phase 3a)
  → ImageSourcer.source(scene)
    → Pexels API /v1/search?query=...&per_page=3&orientation=portrait
    → Download best match to ~/.hermes/cache/pexels/<photo_id>.jpg
    → Inject scene["sourced_image"] = str(path)
  → VisualProducer.produce() checks scene["sourced_image"]
    → If exists: _photo_background() — load photo, resize-crop, dark 60% overlay, blur 1.5px, text card
    → If None: fallback to original PIL renderer
```

## Which visual types use Pexels

| visual_type | Uses Pexels | Fallback |
|-------------|-------------|----------|
| ai_concept_art | ✅ | PIL dark texture + noise + glow |
| corporate_visual | ✅ | PIL dark blue + gold geometry |
| gradient_text | ❌ | PIL gradient bg |
| cinematic_text | ❌ | PIL cinematic dark + light effects |
| tech_abstract | ❌ | PIL particles/grid/data |
| motion_infographic | ❌ | PIL wireframes/charts |

## Pexels API Quirks

### 1. User-Agent REQUIRED (HTTP 403 without it)

Search and download BOTH need User-Agent:
```python
# Search
req = Request(url, headers={
    "Authorization": api_key,
    "User-Agent": "ai-qujing/1.0"  # REQUIRED
})

# Download (CDN also blocks without UA)
req_dl = Request(src, headers={"User-Agent": "ai-qujing/1.0"})
```

### 2. Chinese search → 0 results

Must use English keywords. Defaults in `imagesourcer.py` TYPE_KEYWORDS:
- `corporate_visual` → `"modern office abstract dark"`
- `ai_concept_art` → first 30 chars of narration + `" abstract technology"`

### 3. Rate limits: 200/hr, 20,000/mo

API key stored in `~/.hermes/.env` as `PEXELS_API_KEY`. Hermes `.env` is defense-in-depth protected.

### 4. Cache: `~/.hermes/cache/pexels/<photo_id>.jpg`

Same photo ID = skip download. No expiration needed.

### 5. Python 3.9 compat

`Path | None` → `Optional[Path]` from `typing`. Same for `str | None` → `Optional[str]`.

## Performance: Fast Mode (default)

PIL per-frame replaced with single keyframe + ffmpeg `-loop 1 -tune stillimage`.
8 scenes ~3 min (vs ~25 min per-frame). User explicitly chose this over slow mode.
