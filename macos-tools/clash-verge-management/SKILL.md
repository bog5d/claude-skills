---
name: clash-verge-management
title: Clash Verge Profile & Node Management
description: "Proxy fails for AI? Diagnose, merge, restart core."
trigger: "User asks why a site (ChatGPT/OpenAI/Claude) won't load; general proxy troubleshooting; Clash profile switching"
---

# Clash Verge Profile & Node Management

Diagnose and fix proxy connectivity issues on macOS Clash Verge (mihomo kernel).

## Diagnostic Flow

### 1. Isolate the problem layer

```bash
# Test local network
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 https://www.baidu.com

# Test proxy (will go through Clash at mixed-port)
curl -s -o /dev/null -w "%{http_code} | %{time_total}s" -x http://127.0.0.1:7897 --connect-timeout 10 https://chatgpt.com

# Test direct (no proxy) to see if GFW blocks it
curl -s -o /dev/null -w "%{http_code} | %{time_total}s" --noproxy "*" --connect-timeout 10 https://chatgpt.com
```

### 2. Interpret HTTP codes

| Code | Meaning |
|------|---------|
| 200 | Site works |
| 000 / timeout | GFW block or DNS failure |
| 403 (cf-mitigated) | **Cloudflare WAF blocking proxy IP** — the root cause 90% of OpenAI/ChatGPT failures |
| 403 (other) | Site-specific block (login/auth) |

### 3. Check Cloudflare WAF

```bash
curl -sI -x http://127.0.0.1:7897 --connect-timeout 10 https://chatgpt.com | grep -i cf
```

Look for: `cf-mitigated: challenge` → IP-level block.

## Profile & Node Discovery

Master config: `~/Library/Application\ Support/io.github.clash-verge-rev.clash-verge-rev/profiles.yaml`

Profile files are in the `profiles/` subdirectory. L*.yaml files contain the full config. p-prefixed files contain proxy overrides.

**Key technique**: Same UUID + different server IP = same subscription, different egress. Scan all profiles for backup IPs.

## Creating & Importing a Merged Config

1. **Create profile file** → `profiles/<name>.yaml` with all nodes + url-test groups + AI rules
2. **Create companion files** (m_<uid>.yaml, s_<uid>.js, r_<uid>.yaml, p_<uid>.yaml, g_<uid>.yaml)
3. **Register in profiles.yaml** via Python yaml.safe_load/dump
4. **Apply to runtime**: `cp profiles/<new>.yaml clash-verge.yaml && cp profiles/<new>.yaml clash-verge-check.yaml`
5. **Restart kernel**: `curl -s -X POST --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/restart`
6. **Verify**: `curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/proxies`

## Pitfalls

- Same provider = same IP reputation. All IPs may be blocked together.
- `clash-verge.yaml` + `clash-verge-check.yaml` **both** need updating.
- No auto-detect on profiles.yaml change → must restart core.
- Use `url-test` (not `fallback`) for AI groups.
- Browser can pass Cloudflare JS challenges that curl can't.
