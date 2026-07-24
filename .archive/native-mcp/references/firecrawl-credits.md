# Firecrawl Credits & Limits Reference

> Maintained after the 2026-06-28 Firecrawl keyless integration session.
> Source: firecrawl.dev dashboard + live testing.

## Billing Models

### Keyless (anonymous)
- URL: `https://mcp.firecrawl.dev/v2/mcp` (no headers)
- Quota: 1,000 credits/month (shared pool)
- **Hard daily cap: ~5-10 requests** — after hitting it, all calls fail with credential errors
- Concurrency: 1 request, heavily throttled
- Verdict: **Demo only. Do NOT use for any real workflow.**

### Registered (free account)
- URL: same, plus `headers: {Authorization: "Bearer fc-..."}`
- Quota: 1,000 credits/month
- Daily cap: **NONE** (full 1,000 credits available anytime)
- Concurrency: 2 parallel requests
- Registration: https://www.firecrawl.dev → Get started → free (no credit card)
- Verdict: **The real path. Same credits, no daily lock.**

### Paid plans
- Hobby: $19/mo → 3,000 credits
- Standard: $99/mo → 10,000 credits
- Growth: $499/mo → 50,000 credits

## Credits Per Operation

| Operation | Cost | Notes |
|---|---|---|
| Search (web) | 2 credits / 10 results | Each result includes full page content |
| Search (images/news) | Included in web search | No extra charge |
| Scrape (single page) | 1 credit / page | Markdown, HTML, or screenshot |
| Scrape (JSON extraction) | ~3 credits / page | Schema-defined structured data |
| Scrape (branding) | 1 credit / page | |
| Crawl | Variable | Per page scraped + discovery overhead |
| Map (URL discovery) | 1 credit | |
| Interact (browser agent) | 2 credits / minute | Click, fill forms, navigate |
| Extract (batch structured) | ~3 credits / URL | |
| Parse (local PDF/Office) | 1 credit / file | |
| Agent (async research) | Variable | Complex, multi-step research |

## Real-World Budget

With 1,000 credits/month and typical usage:
- ~100 single-page scrapes, OR
- ~50 searches + scrape few results, OR
- ~30 structured extractions, OR
- ~500 minutes of browser interaction (unlikely MCP path)

For Hermes Agent daily use, 1,000 credits is tight but functional — search + scrape a few pages per session is fine. Crawling large sites or mass-structured extraction needs a paid plan.

## Multi-Profile Setup

Firecrawl API key must be added to ALL active Hermes profiles:

```yaml
# ~/.hermes/profiles/<profile>/config.yaml
mcp_servers:
  firecrawl:
    url: "https://mcp.firecrawl.dev/v2/mcp"
    headers:
      Authorization: "Bearer fc-xxx...xxxx"
```

Profiles: `her-m2`, `default`, `english-tutor`

## Troubleshooting

### "429 Too Many Requests" / credential errors on keyless
Hit the daily keyless cap. Register a free account and add the API key via `headers`.

### "403 Forbidden" with API key
Key may be invalid or expired. Check dashboard at firecrawl.dev.

### MCP tools not appearing after config update
Must restart Hermes Gateway (`hermes gateway restart`) — no hot-reload for MCP servers.
