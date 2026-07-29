---
name: proxy-connectivity-diagnostics
description: ChatGPT/OpenAI 403 through Clash proxy. WAF, nodes, rules.
tags: [clash, proxy, network, cloudflare, openai, chatgpt, diagnostics]
---

# Proxy Connectivity Diagnostics

Use when the user reports that international AI services (ChatGPT, OpenAI API, Claude, etc.) are unreachable or returning errors through their Clash proxy.

## Quick Triage (3 checks, 10 seconds)

```bash
# 1. Domestic connectivity
curl -s -o /dev/null -w "HTTP %{http_code} | Time: %{time_total}s\n" https://www.baidu.com --connect-timeout 5

# 2. International via proxy
curl -s -o /dev/null -w "HTTP %{http_code} | Time: %{time_total}s\n" -x http://127.0.0.1:7897 https://www.google.com --connect-timeout 5

# 3. Target service via proxy
curl -s -o /dev/null -w "HTTP %{http_code} | Time: %{time_total}s\n" -x http://127.0.0.1:7897 https://chatgpt.com --connect-timeout 5
```

## Cloudflare WAF Detection

When a service returns **HTTP 403** with these headers, it's a Cloudflare WAF block — NOT a network issue:

```
server: cloudflare
cf-mitigated: challenge
```

### What This Means
- **Browser can pass**: Cloudflare JS challenges run in browsers. The service likely works in Safari/Chrome.
- **curl/API blocked**: Programmatic access through a flagged proxy IP is always blocked.
- **Not fixable locally**: The proxy node's IP is on OpenAI's blocklist. Must switch nodes or update subscription.

## Clash API Diagnostics

Clash Verge exposes a Unix socket API (no auth required):

```bash
# Check API availability
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/version

# List all proxies and groups
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/proxies

# Check current rules
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/rules

# Switch GLOBAL proxy
curl -s -X PUT --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/proxies/GLOBAL \
  -H 'Content-Type: application/json' -d '{"name":"<node-name>"}'

# Restart Clash kernel
curl -s -X POST --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/restart
```

### Key Checks via API

**All proxy groups and their current selection:**
```python
import json, sys
data = json.load(sys.stdin)
for name, p in data['proxies'].items():
    if p['type'] in ('Selector', 'Fallback', 'URLTest', 'LoadBalance'):
        print(f"【{p['type']}】{name} → current: {p.get('now','')}")
        for proxy in p.get('all', []):
            pp = data['proxies'].get(proxy, {})
            if pp and pp['type'] not in ('Selector','Fallback','Direct','Reject','Pass','RejectDrop'):
                alive = pp.get('alive', False)
                print(f"  ├─ {proxy} alive={alive}")
```

**Active rules for AI services:**
```python
for r in data['rules']:
    if not r['extra'].get('disabled') and any(domain in r['payload'].lower() for domain in ['openai','chatgpt','claude','anthropic']):
        print(f"  {r['type']:15s} | {r['payload']:30s} → {r['proxy']}")
```

## Clash Verge Profile Management

Clash Verge stores profiles in:
```
~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/profiles.yaml
```

### Switching Profiles Programmatically
```bash
# 1. Edit profiles.yaml to change "current" UID
sed -i '' 's/current: <old-uid>/current: <new-uid>/' "~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/profiles.yaml"

# 2. Restart kernel
curl -s -X POST --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/restart

# 3. Wait 3s and verify
sleep 3 && curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/proxies
```

### Known Profile Locations
From profiles.yaml, find items with `type: local`. Each has:
- `uid`: The profile's unique ID
- `name`: Display name (e.g. "配置文件.yaml", "0712")
- `selected`: If present, shows previous GLOBAL node selection

### Pitfall: Same Subscription, Different Names
Multiple profiles may all point to the same subscription URL. Switching between them won't help if the backend nodes are identical. Always verify with `proxies` API after switching.

## Proxy Node Nuances

### Fallback Group Behavior
- Health check targets `https://cp.cloudflare.com/generate_204`
- A node that passes (alive=True) can still be blocked by OpenAI's stricter WAF
- 403 from OpenAI ≠ node is down. Fallback won't auto-switch for WAF blocks.

### Available Nodes Are Limited
If only 2-3 nodes exist and all are blocked, the subscription provider's IP pool is exhausted. Options:
1. **Update subscription** — provider may have refreshed IPs
2. **Use browser** — bypasses Cloudflare JS challenge
3. **Change subscription provider** — to one with residential IPs

### Runtime Node Switching
```bash
# Switch AI服务 group to specific node
curl -s -X PUT --unix-socket /tmp/verge/verge-mihomo.sock \
  http://localhost/proxies/AI服务 \
  -H 'Content-Type: application/json' \
  -d '{"name":"<node-name>"}'

# Switch per-request (via proxy header, limited support)
curl -x http://127.0.0.1:7897 --proxy-header "X-Clash-Proxy: <node-name>" https://...
```

## Browser Workaround for Cloudflare Challenges

Cloudflare JS challenges only run in browsers. If service is important and proxy can't be fixed:

```bash
# Open Safari to the target URL
open -a Safari
# Then use computer_use to type URL and interact
```

The browser solves the Cloudflare challenge automatically via JS execution. Once logged in, the session cookie persists.

## Data Collection Template

When diagnosing, collect in this order:
1. Proxy port status (default: 7897)
2. Domestic vs international baseline
3. Target service response codes + timing
4. Clash API: all proxies + current selections
5. Clash API: relevant rules
6. Clash profiles.yaml for available profiles
7. If applicable: attempt browser access

## Pitfalls

- **Don't assume node health from alive=True**: A node alive to Cloudflare health check can still be blocked by OpenAI
- **Don't confuse profile names with distinct subscriptions**: Multiple profiles may use the same subscription URL
- **Don't immediately blame the network**: 403 + `cf-mitigated: challenge` = proxy IP blocked, not network down
- **Don't use Cursor to fix proxy issues**: Cursor is a code editor, not a network tool. Proxy IP blocklists can't be fixed by code
- **Clash Verge external controller port 9097 may need auth**: Prefer the Unix socket at `/tmp/verge/verge-mihomo.sock` which requires no auth
- **Always verify after switching profiles**: `profiles.yaml` change needs a kernel restart to take effect
