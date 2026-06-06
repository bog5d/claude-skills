# Pexels Image Sourcing for ai-qujing

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

### 1. User-Agent REQUIRED
**Without User-Agent header → HTTP 403 on both search and download.**

Search:
```python
req = Request(url, headers={
    "Authorization": api_key,
    "User-Agent": "ai-qujing/1.0"  # REQUIRED
})
```

Download (image CDN blocks requests without UA too):
```python
req_dl = Request(src, headers={"User-Agent": "ai-qujing/1.0"})
```

### 2. Chinese search returns 0 results
Pexels search only works with English keywords. The `_build_query()` method uses English defaults:
- `corporate_visual` → `"modern office abstract dark"`
- `ai_concept_art` → uses first 30 chars of narration + `" abstract technology"`

### 3. Rate limits
- 200 requests/hour
- 20,000 requests/month
- API key: stored in `~/.hermes/.env` as `PEXELS_API_KEY=...`
- Module: `~/.hermes/tools/ai-qujing/imagesourcer.py`

### 4. Cache strategy
Images cached to `~/.hermes/cache/pexels/<photo_id>.jpg`. Same photo ID = skip download. No cache expiration; Pexels images are permanent.

## Key env setup

```bash
echo 'PEXELS_API_KEY=<key>' >> ~/.hermes/.env
```

Note: Hermes `.env` is defense-in-depth protected — cannot be read via `read_file`, must use terminal to append.

## Performance Note

PIL frame-by-frame rendering with photo backgrounds is SLOW. Each frame:
1. Opens a 200-300KB JPEG
2. Resizes to fill 1080×1920
3. Applies RGBA overlay + alpha composite
4. Gaussian blur
5. Draws text card

~0.3s per frame × ~5000 frames = ~25 minutes for a typical 8-scene video.

**Mitigation**: set `FPS=15` in build.py for previews, use 30fps + background mode for production.

| File | Purpose |
|------|---------|
| `~/.hermes/tools/ai-qujing/imagesourcer.py` | ImageSourcer class + load_api_key() |
| `~/.hermes/tools/ai-qujing/visual/producer.py` | `_photo_background()` method |
| `~/.hermes/tools/ai-qujing/build.py` | Phase 3a integration |
