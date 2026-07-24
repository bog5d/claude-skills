# Clash Fake-IP DNS Interception — Detection & Workaround

## The Problem

Clash running on this Mac Mini operates in **fake-IP mode**. When any program resolves a domain via the system DNS (or via `dig`/`nslookup` pointed at a local DNS), Clash intercepts the response and returns an IP from the **198.18.0.0/15** range (reserved for benchmark testing, not routable). Clash then transparently proxies any traffic to these fake IPs — so TCP connectivity checks (`socket.create_connection`) will PASS to a fake IP, making the contamination invisible to naive health checks.

**Example**: `dig @114.114.114.114 +short api.telegram.org` returns `198.18.0.10` instead of a real Telegram IP.

## Detection

Check if an IP is in the Clash fake-IP range:

```python
def _is_fake_ip(ip: str) -> bool:
    """198.18.0.0/15 -> 198.18.0.0 to 198.19.255.255"""
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError:
        return False
    return a == 198 and b in (18, 19)
```

## Workaround: DNS-over-HTTPS (DoH)

DoH bypasses Clash DNS interception entirely because it uses HTTPS to domain endpoints, not raw DNS protocol. The HTTPS connection itself goes through Clash's proxy (if configured), but the DNS response comes from the real upstream.

### DoH Endpoints Used

| Provider | URL |
|----------|-----|
| Cloudflare | `https://cloudflare-dns.com/dns-query` |
| Google | `https://dns.google/resolve` |

### Python Implementation (stdlib only, no deps)

```python
import json
import urllib.request

def resolve_with_doh(host: str, doh_url: str) -> list[str]:
    url = f"{doh_url}?name={host}&type=A"
    req = urllib.request.Request(url, headers={"accept": "application/dns-json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    ips = []
    for ans in data.get("Answer", []):
        if ans["type"] == 1:  # A record
            ips.append(ans["data"])
    return ips
```

## Applied Fix

`~/.hermes/profiles/her-m2/bin/dns-redundancy.py` was updated 2026-05-31 to use DoH + fake-IP filtering instead of `dig`. The script now:

1. **Primary**: Resolve via Cloudflare + Google DoH
2. **Fallback**: System DNS (`socket.getaddrinfo`) with fake-IP filter
3. **Ultimate**: Hardcoded Telegram seed IPs (DC1 + DC2)
