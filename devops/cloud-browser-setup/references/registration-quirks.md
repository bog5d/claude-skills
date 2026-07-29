# Browserbase Registration — Live Reference

> Captured 2026-07-29. Quackr numbers rotate; re-check before use.

## Signup Page Structure

URL: https://www.browserbase.com/sign-up
Fields: Email, Phone (+1 prefixed), Password, reCAPTCHA

- No GitHub/Google OAuth on signup page
- Sign-in page (https://www.browserbase.com/sign-in) is email-only, no social login either

## Quackr Free US Numbers (as of 2026-07-29)

Active numbers found on https://quackr.io/temporary-numbers/united-states:
- +1 775 986 5200
- +1 701 997 6600
- +1 775 980 2006

SMS inbox URL pattern: `https://quackr.io/temporary-numbers/united-states/<10-digit-number>`

⚠️ These are PUBLIC — anyone viewing the page sees all received SMS. OK for one-time signup only.

## Attempted Automation & Failures

| Approach | Result |
|---|---|
| `web_extract` (DuckDuckGo backend) | Failed — DuckDuckGo is search-only |
| Firecrawl `scrape` | Worked — got page structure, confirmed reCAPTCHA |
| Firecrawl `interact` (prompt-based) | Failed — "Job not found" |
| `computer_use` (cua-driver) | Failed — timed out after 30s (cua-driver spawn issue) |
| Manual mobile registration | ✅ Recommended path |

## Hermes Browserbase Plugin

- Plugin: `plugins/browser/browserbase/` (installed, not configured)
- Config: `browser.engine: auto` — picks Browserbase when env vars are set
- Tools: `browser_navigate`, `browser_click`, `browser_type`, `browser_snapshot`, etc. (9 tools, enabled)
- Status before setup: `hermes status` shows `Browserbase ✗ (not set)`
- Env vars: `BROWSERBASE_API_KEY` + `BROWSERBASE_PROJECT_ID` in `~/.hermes/.env`

## User's Account

- Email for registration: `wangbo8805@gmail.com`
- Password template: `Bog8805Browserbase!`
