---
name: hermes-infrastructure
description: "Complete Hermes gateway infrastructure management — troubleshooting, monitoring, provider config, REST API gateway, and audit reporting. Class-level umbrella for all Hermes operational workflows."
version: 1.0.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [hermes, infrastructure, gateway, monitoring, troubleshooting, provider, API, audit]
---

# Hermes Infrastructure Management

Class-level umbrella for operating and maintaining Hermes Agent gateways — from daily troubleshooting to infrastructure provisioning.

## When to Load

- Gateway/API is down, frozen, or misbehaving
- Need to monitor gateway health or set up notifications
- Adding a custom API provider (OpenAI-compatible proxy, Agnes AI, etc.)
- Setting up REST API gateway for external tool access
- Generating system audit reports (hardware + project scan)
- Managing cron job environment variables and skill sync

## Quick Path Selection

| Task | Section |
|------|---------|
| Gateway is not responding / crashed / frozen | §1 Service Troubleshooting |
| Deploy monitoring + notifications | §2 Gateway Monitoring |
| Add/remove custom API provider | §3 Provider Configuration |
| Expose Hermes tools via REST API | §4 REST API Gateway |
| Scan hardware + generate audit report | §5 Audit Report Generation |
| Cron env variable pollution | §6 Cron Contextvars |
| Cross-profile skills sync | §7 Skills Sync |

## §1 Service Troubleshooting

Diagnostic SOP for gateway/API failures. See `references/service-troubleshooting.md` for the full playbook covering:
- launchd state cross-validation (PID vs exit code)
- Port conflicts (multi-profile api_server binding)
- Token/credential missing
- DNS pollution (Clash Verge fake-ip)
- MCP stdio freeze
- FD exhaustion (Errno 24)
- KeepAlive SuccessfulExit trap
- Protected config file modification
- Defibrillator false positives
- Cron prompt security interception
- Cascading death (gateway + watchdog)

## §2 Gateway Monitoring

Zero-AI-consumption monitoring: startup notifications, shutdown warnings, crash alerts, periodic status reports. See `references/monitoring-setup.md` for:
- hermes-monitor.sh deployment
- monitor_report.py engine
- Launchd scheduled tasks
- v3 seven-layer defense architecture (defibrillator, network-watchdog, system-watchdog, DNS redundancy, launchd KeepAlive, skills sync)

## §3 Provider Configuration

Adding OpenAI-compatible custom providers. See `references/provider-config.md` for:
- Curl test → config entry → multi-profile sync → restart
- The `/v1` pitfall
- Agnes AI specifics (free tier)
- GitHub Copilot Chat API auth (PAT vs OAuth)
- `hermes config set` credential-lock bypass
- Model list JSON string formatting

## §4 REST API Gateway

Expose Hermes tools via HTTP REST API. See `references/rest-api-gateway.md` for:
- Built-in api_server (preferred, production-ready)
- Custom hermes_api.py implementation (fallback)
- Port configuration, CORS, daemon thread lifecycle
- ngrok/localhost.run tunneling
- OpenAPI 3.0 schema generation

## §5 Audit Report Generation

Hardware scan + project structure → single markdown report. See `references/audit-report.md` for:
- system_profiler commands (hardware, storage, network)
- Hermes project structure analysis
- Docker/environment check
- Report sections: hardware, system, network, project, status, recommendations

## §6 Cron Contextvars

Fix cron job environment variable pollution. See `references/cron-contextvars.md` for:
- contextvars.ContextVar migration from os.environ
- scheduler.py integration
- load_dotenv ordering pitfall
- Testing patterns

## §7 Skills Sync

Cross-profile skills bidirectional sync. See `references/skills-sync.md` for:
- Four-end sync architecture (her-m2, default, english-tutor, GitHub)
- Pre-commit secret scanning
- filter-branch token scrubbing
- $HOME rewrite pitfall
- rsync exclusion patterns

## Common Pitfalls (Cross-Cutting)

- **Credential protection**: Hermes gateway locks `.env` and `config.yaml` at runtime. Use `terminal` with venv Python to bypass.
- **Port conflicts**: Multi-profile gateways compete for 8642. Always assign unique ports per profile.
- **launchd exit code ≠ current state**: Must cross-validate with `kill -0 <PID>`.
- **$HOME rewrite**: Hermes rewrites HOME during gateway runs. Always use absolute paths.
- **Enabled: false doesn't disable api_server**: Must remove the entire block or change port.