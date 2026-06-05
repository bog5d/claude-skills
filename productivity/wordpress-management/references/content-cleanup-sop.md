# WordPress Content Cleanup SOP

When a site has accumulated test/duplicate articles, follow this procedure.

## Duplicate Article Cleanup

1. List all posts → group by title → identify duplicates
2. Compare `content` length in duplicate groups → keep the original (slug without `-2` suffix)
3. `DELETE /posts/{id}?force=true` for duplicates (skip trash)
4. Create new categories → move orphaned posts → delete empty categories
5. Batch create tags → assign by topic to each post

## SEO Optimization Checklist

- [ ] Every post has a category (not "Uncategorized")
- [ ] Every post has 2-3 tags
- [ ] Every post has a featured image (1200x630, with brand bar)
- [ ] SEO plugin active (e.g., SureRank SEO)
- [ ] Cache plugin active (e.g., WP Super Cache) — note: may need wp-admin to enable after install
- [ ] Empty categories/tags removed
- [ ] HTTPS functional (check Cloudflare SSL settings)

## Site Diagnostic Commands

```bash
# Homepage performance and size
curl -s -o /dev/null -w "HTTP %{http_code} | %{size_download}B | %{time_total}s" http://hellobog.com/

# HTTPS status
curl -sk -o /dev/null -w "%{http_code}" https://hellobog.com/

# API auth test
curl -s -u "admin:APP_PASS" http://hellobog.com/wp-json/wp/v2/users/me
```

Quick reference:
- HTTPS 521 → Cloudflare SSL set to Flexible
- Homepage >2s → cache not enabled, install WP Super Cache
- API 403 → app password expired or insufficient permissions

## Common Operations Reference

### Site Info
```bash
GET /wp-json/  # site name, description, timezone, namespaces
GET /wp-json/wp/v2/users/me  # current user
GET /wp-json/wp/v2/settings  # site settings
```

### Media Upload with Featured Image
```bash
# Upload image
POST /wp-json/wp/v2/media -F "file=@/path/to/image.jpg"

# Set as featured image
POST /wp-json/wp/v2/posts/{id} -d '{"featured_media":{media_id}}'
```

### Plugin Management
```bash
# Install from repo and activate
POST /wp-json/wp/v2/plugins -d '{"slug":"wp-super-cache","status":"active"}'

# List / activate / deactivate
GET /wp-json/wp/v2/plugins
PUT /wp-json/wp/v2/plugins/{plugin_slug} -d '{"status":"active"}'
```
