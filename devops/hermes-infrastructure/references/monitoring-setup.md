# Gateway Monitoring Setup

## Architecture

```
监控系统
├── hermes-monitor.sh      ← entry script (routing + notifications)
├── monitor_report.py      ← report engine (Python, YAML/JSON/ps/curl)
├── Launchd plist           ← scheduled status reports (default 4h)
└── CLI commands            ← startup / shutdown / crash / report / status / watch
```

## Core Principle
**Zero AI consumption, zero memory burden.** Bash scheduling + Python report generation + curl Telegram Bot API. Never goes through any LLM.

## Report Dimensions

| Dimension | Source | Description |
|-----------|--------|-------------|
| Model info | `config.yaml` | Primary model + provider + fallback |
| Sessions | `sessions/*.json` count | Storage per profile |
| Disk | `du -sh logs/ sessions/` | Separate stats |
| Errors | `gateway.error.log` (last 1h) | API/connection/tool/timeout/infra/other |
| Provider health | `curl <base_url>/models` | Real-time reachability |

## Deployment

### 1. Scripts
- Entry: `~/.hermes/profiles/<profile>/bin/hermes-monitor.sh`
- Engine: `~/.hermes/profiles/<profile>/bin/monitor_report.py`
- **All paths must be ABSOLUTE** (Hermes rewrites $HOME at runtime)

### 2. Launchd Scheduled Report
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.hermes.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/mac/.hermes/profiles/her-m2/bin/hermes-monitor.sh</string>
        <string>report</string>
    </array>
    <key>StartInterval</key><integer>14400</integer>
    <key>RunAtLoad</key><true/>
</dict>
</plist>
```

### 3. Gateway Startup Wrapper
```bash
MONITOR_SCRIPT="${HOME}/.hermes/profiles/her-m2/bin/hermes-monitor.sh"
"$MONITOR_SCRIPT" startup "$PROFILE_NAME" &
trap '"$MONITOR_SCRIPT" shutdown "$PROFILE_NAME" 30' EXIT
exec python3 -m hermes_cli.main --profile "$PROFILE_NAME" gateway run --replace
```

## Commands

| Command | Purpose | Telegram |
|---------|---------|----------|
| `status` | Console output | No |
| `report` | Full status report | Yes |
| `startup <profile> [pid]` | Startup notification | Yes |
| `shutdown <profile> [delay]` | Shutdown warning | Yes |
| `crash <profile>` | Crash alert | Yes |
| `watch` | Continuous monitoring | On change |

## Known Pitfalls

1. **Default profile PID file**: Located at `~/.hermes/gateway.pid`, NOT `~/.hermes/profiles/default/gateway.pid`
2. **launchd exit code ≠ current state**: Must cross-validate with `kill -0 <PID>`
3. **PID file is JSON**: Parse with Python
4. **Bash reports are buggy**: Use Python `monitor_report.py` for complex reports
5. **$HOME is rewritten**: Always use absolute paths
6. **Telegram Markdown special chars**: `_` and `*` need escaping
7. **NO HardResourceLimits → RSS**: macOS launchd doesn't support RSS key
8. **NO pkill for gateways**: her-m2 and default gateways don't have profile name in cmdline

## v3 Defense Architecture (Seven Layers)

| Layer | Component | Interval | Responsibility |
|-------|-----------|----------|----------------|
| 1 | defibrillator v2 | 10s | PID detection → single gateway revival |
| 2 | network-watchdog | 30s | Clash→DNS→TCP→HTTPS 4-level check |
| 3 | system-watchdog | 5min | Swap/Disk/Zombie/RSS threshold alerts |
| 4 | DNS redundancy | 2h | Multi-path DNS + Telegram seed IP cache |
| 5 | launchd KeepAlive | instant | 7 services, unconditional survival |
| 6 | skills sync | 30min | Three-end 192 skills sync + GitHub push |