# Pexels Integration Notes

Duplicate of `article-to-video-production/references/pexels-integration.md`.  
See that reference for full Pexels quirks and setup.

Key facts:
- User-Agent REQUIRED for search + download
- Chinese search → 0 results, use English only
- Rate limits: 200/hr, 20,000/mo
- Cache: `~/.hermes/cache/pexels/<photo_id>.jpg`
- API key in `~/.hermes/.env` as `PEXELS_API_KEY`
