# Copilot Chat API Auth Pitfalls (2026-06-14)

## Summary
Session confirmed that GitHub Copilot Chat API (`https://api.githubcopilot.com/chat/completions`) does NOT accept PATs (Personal Access Tokens). Only OAuth tokens from Copilot org/business accounts work.

## Auth Format Matrix

| Token Type | Prefix | Works for GitHub REST? | Works for Copilot Chat? |
|-----------|--------|----------------------|------------------------|
| PAT | `ghp_` | Yes (with Bearer) | No — always "badly formatted" |
| OAuth App | `gho_` | Yes | Yes (with Bearer) |
| Fine-grained | `github_pat_` | Yes | No |
| Install | `ghs_` | Yes | No |

## Error Messages and Causes

| Error | Cause |
|-------|-------|
| `bad request: Authorization header is badly formatted` | PAT sent to Copilot endpoint, OR Bearer token has trailing whitespace |
| `missing required Authorization header` | No Authorization header at all |
| `Unauthorized` | Invalid/expired token, or token not for this endpoint |

## Debugging Commands

```bash
# Identify token type
echo "$TOKEN" | head -c 8

# Check Copilot Chat API response
curl -s "https://api.githubcopilot.com/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model":"test","messages":[],"max_tokens":10}'

# Check headroom proxy health (if configured as fallback)
curl -s "http://127.0.0.1:8787/health" | python3 -m json.tool | grep backend

# Check what headroom backend is configured
curl -s "http://127.0.0.1:8787/v1/models"  # if headroom routes model names
```

## Hermes Integration Notes

- When `model.provider` is `custom:copilot` or similar, always verify token type first
- PATs will NEVER work — this is a GitHub API design decision, not a config error
- Headroom proxy can route through different backends (anthropic, openai, anthropic)
- The headroom proxy's `/health` endpoint shows which backend is active

## Related
- `hermes-custom-provider` SKILL.md — Pitfall section covers this
- Headroom proxy: port 8787, runs via launchd, manages auth backend rotation
