---
name: pinme-deployment
description: Deploy static sites and full-stack apps to PinMe (IPFS-based hosting). One-command upload of HTML/directories, or full-stack project creation with frontend+backend+database. Authentication required — no anonymous upload path exists.
category: devops
---

# PinMe Deployment Pipeline

## Overview

PinMe is a zero-config deployment platform: static files go to IPFS, full-stack apps get frontend (SPA) + backend (Edge Runtime) + database (Serverless SQL) in one command. It also offers a Skill for AI agents (Claude Code, etc.) to auto-deploy.

## Prerequisites

```bash
npm install -g pinme
```

Installed at: `/opt/homebrew/lib/node_modules/pinme/` (macOS ARM) or `/usr/local/lib/node_modules/pinme/` (Intel).

## Authentication (REQUIRED)

**There is NO anonymous upload path.** All uploads require auth. Two options:

### Option A: Browser OAuth
```bash
pinme login
```
- Opens browser, starts local callback server on port 34567
- Requires phone number + SMS verification code
- Saves auth to `~/.pinme/auth.json` with `{address, token}`

### Option B: AppKey (no browser needed)
```bash
pinme set-appkey
```
- Get AppKey from https://pinme.dev → 应用控制台 → API Keys
- Paste when prompted
- This is the preferred method for headless/CI environments

Verify auth: `pinme show-appkey` or `pinme wallet`

## Static File Deployment

```bash
# Upload a single file
pinme upload index.html

# Upload a directory
pinme upload dist/

# Upload with custom domain binding
pinme upload dist/ --domain my-site
```

Returns: IPFS CID + public URL (e.g., `https://<cid>.pinme.dev/`)

File limits: 500 MB per file, 500 MB per directory.

## Full-Stack Project Deployment

```bash
# Create from template
pinme create my-app
cd my-app

# Edit code...

# Deploy (frontend + backend + database)
pinme save
```

Architecture: Frontend → IPFS, Backend → Edge Runtime, Database → Serverless SQL.

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `https://pinme.dev/api/v3` | IPFS upload API (chunk/init, chunk/upload) |
| `https://pinme.dev/api/v4` | Platform API |

Auth headers: `token-address` + `authentication-tokens`.

## Integration with Hermes

**Status: ✅ Pipeline verified (2026-05-22)**

Auth obtained from Mac Mini (`~/.pinme/auth.json`), synced to Hermes. Upload tested with `/tmp/pinme-test/index.html` → public URL confirmed working (HTTP 200).

Ideal flow:
```
Generate HTML (PPT skill, dashboard skill) → pinme upload <file_or_dir>/ → return public URL
```

The URL format is `https://<cid>.pinme.dev/` — stable and permanent (IPFS-based).

For the PinMe Skill (AI agent auto-deploy):
```bash
npx skills add glitternetwork/pinme
```

## Pitfalls

1. **No anonymous upload**: Every upload path (CLI, API, web drag-drop) requires auth. Plan for account setup first.
2. **Browser OAuth is fragile in headless environments**: The `pinme login` flow requires a browser with a local callback server on port 34567. Use `pinme set-appkey` instead for CI/headless.
3. **Port 34567 conflict**: If a previous login attempt left a zombie process, `pinme login` will fail with EADDRINUSE. Kill with `lsof -ti:34567 | xargs kill -9`.
4. **Auth file location**: `~/.pinme/auth.json` — not profile-aware. If using multiple Hermes profiles, each needs its own auth.
5. **Website login requires Chinese phone number**: The pinme.dev login dialog only shows phone + MetaMask options.
