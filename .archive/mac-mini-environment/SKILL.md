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

## Health Check & Robustness Audit

For a comprehensive system health audit — checking launchd KeepAlive, log rotation, cron persistence, disk space, network watchdog, backup status, and recovery checklist — see:

📄 `references/robustness-health-check.md` (load with `skill_view("mac-mini-environment", "references/robustness-health-check.md")`)

Trigger these checks when: asking about "system health", "robustness", "停电恢复", "outage recovery", or before/after major OS updates.