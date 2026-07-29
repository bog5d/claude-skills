---
name: cloud-browser-setup
description: "Set up Browserbase for Hermes. Chinese phone workaround."
version: 1.0.0
author: her-m2
---

# Cloud Browser Setup for Hermes

Set up cloud browser services (Browserbase) so Hermes can navigate, click, type, and persist login sessions on the web — fully automated.

## When to Use

- User wants Hermes to automate website logins / form filling / data extraction
- User asks "set up Browserbase" or "how do I give Hermes a browser"
- User needs multi-account browsing with persistent login state
- Registration is blocked (Chinese phone, reCAPTCHA) and needs a workaround

## Browserbase vs Local Alternatives

| | Browserbase (cloud) | Ego Lite (local, Citro Labs) |
|---|---|---|
| Where it runs | Browserbase servers | User's Mac (`~/Applications/ego lite.app`) |
| Who operates it | Hermes via API (fully automated) | User manually (desktop app) |
| Login persistence | Per `session_id`, cookies + localStorage saved in cloud | Per Chromium profile, local disk |
| Multi-account | Isolated sessions | Isolated profiles |
| Chinese phone signup | BLOCKED | Not applicable (desktop app) |

**Hermes integrates with Browserbase; Ego Lite is only useful for manual operations.**

## Registration Workaround (Browserbase Blocks Chinese Numbers)

Browserbase signup at https://www.browserbase.com/sign-up requires:
- Email
- **US phone number (+1)** — Chinese (+86) numbers are rejected
- Password
- **reCAPTCHA** — blocks fully automated signup

### Manual Registration Path (3 minutes, mobile)

1. Get a free US number from https://quackr.io/temporary-numbers/united-states (pick any active +1 number)
2. On **mobile browser**, open https://www.browserbase.com/sign-up
3. Fill: email, the quackr US number, password
4. Solve reCAPTCHA manually
5. Click Continue → verification code sent to the US number
6. Open the quackr number's page (e.g., `quackr.io/temporary-numbers/united-states/<number>`) to read the SMS code
7. Enter verification code → done

### Why Fully Automated Fails
- reCAPTCHA requires human interaction
- `computer_use` (cua-driver) may be unreliable or timeout on the Mac
- Firecrawl `interact` may fail to execute JS-heavy forms

## Hermes Configuration

Once the user has API Key + Project ID from Browserbase Dashboard:

```bash
# Write credentials to env (NOT config.yaml — secrets belong in .env)
hermes config set env.BROWSERBASE_API_KEY <api_key>
hermes config set env.BROWSERBASE_PROJECT_ID <project_id>

# Restart gateway to pick up new env vars
hermes gateway restart
```

Verify:
```bash
hermes status | grep -i browser
# Should show: Browserbase   ✓ (configured)
```

## Usage Example

After setup, in any Hermes session:

> "Log into WeChat Official Account backend at mp.weixin.qq.com"

Hermes will:
1. Launch cloud Chrome via Browserbase
2. Navigate to the URL
3. Fill credentials from memory
4. If QR code appears → screenshot sent to user's Telegram for scanning
5. Session persists — next time it's already logged in

## Pitfalls

- **Public free numbers expose codes**: quackr numbers are public — anyone can see received SMS. Acceptable for one-time signup, not for ongoing use.
- **reCAPTCHA kills automation**: always plan for manual reCAPTCHA step during signup.
- **cua-driver timeout**: `computer_use` may fail to connect (timeout 30s). Fall back to mobile manual registration rather than fighting it.
- **Credentials in .env, not config.yaml**: Browserbase keys are secrets. Use `hermes config set env.*` not raw YAML edits.
- **Browserbase free plan**: 1 browser hour/month, 15 min/session max, 1 active browser. Upgrade for production.
