---
name: mac-mini-environment
description: Mac Mini M4 production environment profile — hardware, system, Hermes project layout, robustness health check, and known constraints
---

# Mac Mini Environment Profile

## Hardware
- **Model**: Mac Mini M4 (2024), Apple M4 10-core (4P + 6E), 16GB LPDDR5X unified memory
- **Storage**: APPLE SSD AP0256Z, 245GB total (~80GB free as of Apr 2026)
- **GPU**: Apple M4 integrated (family8 GPU, no separate VRAM)
- **Cache**: L1 192KB/128KB (P-core I/D), L1 128KB/64KB (E-core I/D), L2 16MB shared, L2 4MB (E-core cluster), L3 16MB (GPU)

## System
- **OS**: macOS 26.3.1 (Sequoia), Darwin 26.3.0
- **Kernel**: xnu-12223.3.122.6~1
- **CPU Load**: Load average frequently exceeds 10 — this is a capacity bottleneck
- **Network**: en0 (Wi-Fi, MAC 78:4B:A5:9D:03:6F), en2 (Thunderbolt), en3 (Thunderbolt), en4 (Thunderbolt), lo0 (loopback), ane0, wlan0, ap1
- **Users**: `mac` (primary), `bit` (git user "aider")
- **Shell**: zsh 5.9 (mac), /bin/bash for cron jobs

## Docker Status
- Docker CLI v29.2.1 installed, Docker Desktop NOT running
- `docker ps` returns empty with client disconnected error
- Docker socket at /var/run/docker.sock unavailable
- **Implication**: Docker-based sandbox (code_execution, terminal sandbox) is inoperable until Desktop is started

## Hermes Agent Project
- **Path**: `/Users/mac/.hermes/hermes-agent`
- **Scale**: ~518 Python files, ~3,814 commits, 3000+ tests
- **Architecture**: Interface (CLI/Gateway/ACP) → Core (agent loop, prompt builder, tool discovery) → Tools (20+ toolsets)
- **Binary**: `hermes` available as CLI command (python -m based)
- **Messaging**: Supports Slack, Discord, Telegram, WhatsApp, Home Assistant, Signal, WeChat adapters
- **Cron system**: Scheduler runs from `/Users/mac/.hermes/hermes-agent/cron/`; outputs go to `~/.hermes/cron/output/`
- **Models**: deepseek-chat via DeepSeek provider (user is "波总", located in 海淀, Beijing)
- **ACP**: cursor agent ACP protocol available via `/opt/homebrew/bin/cursor agent --acp --stdio`
- **Cron status commands**: `hermes cron status`, `hermes cron log --tail`
- **Plan command**: `hermes` CLI has `/plan` command for architecture analysis before execution

## Known Constraints
1. 16GB RAM is tight for running Hermes + Docker + Cursor ACP in parallel — high load average
2. Docker sandbox unavailable unless Desktop is manually launched first
3. Memory saving across sessions is disabled in this environment
4. Multiple Thunderbolt interfaces (en2, en3, en4) but no external storage connected
5. **Clash fake-IP DNS interception**: Clash runs in fake-IP mode — DNS resolution via system resolver or `dig` returns `198.18.0.0/15` addresses instead of real IPs. TCP connectivity checks to fake IPs pass because Clash transparently proxies them, so contamination is invisible to naive health checks. **Workaround**: use DNS-over-HTTPS (Cloudflare/Google DoH) + fake-IP range filtering. See `references/clash-fake-ip-dns.md` for detection code and DoH implementation.

## Tailscale & Remote Connectivity

The Mac Mini is on the user's Tailscale network (tailnet). Use this to discover and connect:

```bash
tailscale status | grep macmini
```

**Known identifiers:**
- Tailscale hostname: `macmac-mini` (may resolve as `macmac-mini.tailnet-xxx.ts.net`)
- Tailscale IP: dynamically assigned (e.g. `100.93.154.87`), re-discover via `tailscale status`
- Local LAN IP: `192.168.31.63` (only reachable from same subnet)

**SSH access:**
```bash
ssh -o ConnectTimeout=5 mac@<tailscale-ip>
```

If SSH key auth fails ("Permission denied" or "Too many authentication failures"):
1. Generate a diagnostic key pair: `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "hermes-diagnostic"`
2. The user must run on the Mac Mini: `echo '<public key>' >> ~/.ssh/authorized_keys`
3. Then reconnect with: `ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 mac@<tailscale-ip>`

**SSH key inventory (local machine):** Check `~/.ssh/` before generating — existing keys may already be authorized on the Mac Mini. Try each: `id_ed25519_tailscale`, `hermes_tailscale_47`, `id_ed25519_termius`, `id_ed25519_alicloud`.

## Codex on Mac Mini — Troubleshooting Quick-Start

When the user reports Codex is "反复重新链接" (repeatedly reconnecting/crashing on the Mac Mini):

**Most likely root cause**: Bubblewrap sandbox failure in launchd context.
Codex uses bubblewrap for `workspace-write` sandboxing; when invoked from a
launchd service context (no full user session namespace), bubblewrap fails and
Codex crashes → launchd restarts it → repeat.

**Workaround** (see `codex` skill for details):
```bash
codex exec --sandbox danger-full-access "<task>"
```

**Diagnostic commands (run on Mac Mini):**
```bash
# Check Codex process status
ps aux | grep -i codex

# Check launchd for Codex service
launchctl list | grep -i codex

# Check Codex crash logs
ls -lt ~/Library/Logs/DiagnosticReports/ | grep -i codex | head -5

# Test bubblewrap availability
bwrap --version 2>&1

# Check if running in a proper user session context
launchctl managername
```

**Other suspects (if bubblewrap isn't the issue):**
- OAuth token expired: check `~/.codex/auth.json`
- OOM kill: check `log show --predicate 'eventMessage CONTAINS "codex"' --last 1h`
- FD exhaustion: `lsof -p $(pgrep codex) 2>/dev/null | wc -l`

## Health Check & Robustness Audit

For a comprehensive system health audit — checking launchd KeepAlive, log rotation, cron persistence, disk space, network watchdog, backup status, and recovery checklist — see:

📄 `references/robustness-health-check.md` (load with `skill_view("mac-mini-environment", "references/robustness-health-check.md")`)

Trigger these checks when: asking about "system health", "robustness", "停电恢复", "outage recovery", or before/after major OS updates.