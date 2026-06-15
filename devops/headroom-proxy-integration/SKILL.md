---
name: headroom-proxy-integration
version: 1.0.0
author: Hermes Agent (波总 session)
tags: [headroom, token-compression, proxy, optimization, mcp]
description: Deploy and integrate headroom proxy as a token optimization layer for Hermes gateway — reduces context token usage by 60-95% with reversible CCR compression.
---

# Headroom Proxy Integration

When 波总 wants to reduce token costs, optimize LLM context, or deploy a token compression layer for Hermes. Also covers integrating headroom as a gateway middleware.

## What is headroom?

[headroom](https://github.com/chopratejas/headroom) — compresses LLM context before it enters the model. 60-95% token reduction, zero accuracy loss (benchmarked on GSM8K ±0, TruthfulQA +0.030). Supports three modes: library, proxy, and MCP server.

## Step 1: Install headroom

```bash
# Install in Hermes venv (always use venv python, NOT system pip)
/Users/mac/.hermes/hermes-agent/venv/bin/python -m pip install -e /path/to/headroom
# Or from PyPI:
/Users/mac/.hermes/hermes-agent/venv/bin/python -m pip install headroom
```

**Verify version:**
```bash
/Users/mac/.hermes/hermes-agent/venv/bin/headroom --version
# Should show 0.26.0 or later
```

## Step 2: Start the proxy

```bash
/Users/mac/.hermes/hermes-agent/venv/bin/headroom proxy \
  --port 8787 \
  --stateless \
  --memory
```

**Backend selection:**
- Default: Anthropic backend (`--backend anthropic`)
- For OpenAI-compatible APIs (DashScope, Agnes AI, OpenRouter): use `--backend litellm-openai --openai-api-url <upstream>`
- For custom Anthropic URL: `--anthropic-api-url https://custom.anthropic.com`
- For custom OpenAI URL: `--openai-api-url https://custom.openai.com`

## Step 3: Register with launchd (persistent)

```bash
# Create plist
cat > ~/Library/LaunchAgents/com.hermes.headroom-proxy.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hermes.headroom-proxy</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/mac/.hermes/hermes-agent/venv/bin/headroom</string>
        <string>proxy</string>
        <string>--port</string>
        <string>8787</string>
        <string>--stateless</string>
        <string>--memory</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/mac/.hermes/logs/headroom-proxy.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/mac/.hermes/logs/headroom-proxy.error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>HOME</key>
        <string>/Users/mac</string>
    </dict>
</dict>
</plist>
PLIST
chmod 644 ~/Library/LaunchAgents/com.hermes.headroom-proxy.plist
```

**Bootstrap into launchd:**
```bash
# If bootstrap fails with IO error (known macOS issue after uninstall/reinstall):
launchctl bootout gui/$(id -u)/com.hermes.headroom-proxy 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hermes.headroom-proxy.plist
# Then kickstart to actually launch:
launchctl kickstart gui/$(id -u)/com.hermes.headroom-proxy
```

## Step 4: Verify health

```bash
curl -s http://localhost:8787/health | python3 -m json.tool
# Check: status "healthy", ready true, version correct
```

## Step 5: Route Hermes gateway through headroom

**For Anthropic API (Claude Code, etc.):**
```bash
export ANTHROPIC_BASE_URL=http://localhost:8787
```

**For OpenAI-compatible APIs (DashScope, Agnes AI):**
```bash
export OPENAI_BASE_URL=http://localhost:8787/v1
```

**Note:** Hermes gateway reads provider `base_url` from config.yaml, not environment variables. To make Hermes go through headroom, you need to either:
1. Set the provider's `base_url` to `http://localhost:8787` (headroom acts as transparent proxy)
2. Or configure headroom with `--openai-api-url` pointing to the real upstream

## Pitfalls

1. **launchd bootstrap IO error** — After uninstalling and reinstalling a launchd agent, `bootstrap` may fail with "Input/output error". Fix: try `bootout` first, then `bootstrap`. If that fails, manually start the process and let `kickstart` take over.

2. **plist file permissions** — If chmod is 600 (owner-only), launchd cannot read it. Set to 644.

3. **venv python is a symlink to homebrew Python** — The Hermes venv python is a hardlink to `/opt/homebrew/Cellar/python@3.11/...`. This is expected and correct; headroom's shebang points to venv python which resolves to the homebrew binary.

4. **headroom version mismatch** — The binary in venv may be newer than what the running process uses. Always restart the launchd service after updating headroom.

5. **Backend selection matters** — Default backend is `anthropic`. For DashScope/Agnes AI (OpenAI-compatible), you MUST use `--backend litellm-openai --openai-api-url <upstream>`. Otherwise headroom won't proxy correctly.

6. **--stateless vs --memory** — `--stateless` means no filesystem state (faster, less persistent). `--memory` enables in-memory context compression. Use both together for best token savings.

## Verification Checklist

- [ ] `headroom --version` shows expected version
- [ ] `curl localhost:8787/health` returns healthy
- [ ] Process running under correct venv python
- [ ] launchd shows `kickstart` success (positive PID in `launchctl list`)
- [ ] Gateway/API calls route through port 8787
- [ ] Token savings visible in API logs (compare before/after)

## Related Skills

- `token-cost-analysis` — Diagnose which providers/models are burning tokens
- `hermes-custom-provider` — Configure custom API providers (headroom can be one)
- `hermes-gateway-monitoring` — Monitor headroom proxy uptime alongside gateway