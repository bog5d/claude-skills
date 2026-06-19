# Service Troubleshooting — Hermes Gateway Diagnostic SOP

## Trigger
- Gateway/API "not responding", "crashed", "frozen"
- `/health` endpoint or ngrok URL unresponsive

## Phase 1: Quick Diagnosis (30 seconds)

```bash
# 1. Check all Hermes processes
ps aux | grep -i hermes | grep -v grep

# 2. Check launchd state
launchctl list | grep -i hermes

# 3. Check ngrok (if public URL configured)
ps aux | grep ngrok | grep -v grep
curl -s --max-time 5 http://127.0.0.1:4040/api/tunnels
```

## Phase 2: launchd ↔ Process Cross-Validation

**CRITICAL: launchd exit code is LAST EXIT, not CURRENT state.**

```bash
for svc in ai.hermes.gateway ai.hermes.gateway-her-m2 ai.hermes.gateway-english-tutor com.hermes.defibrillator com.hermes.network-watchdog com.hermes.system-watchdog; do
    launchctl print gui/501/$svc
done
```

Look for:
- `state` — running vs spawn scheduled
- `last exit code` — 0=normal, 1=abnormal (but this is PAST)
- `runs` — high number = repeated crashes
- `pid` — cross-validate with `kill -0 <PID>`
- `stdout path` / `stderr path` — log locations

## Phase 3: Common Failure Modes

### Port Conflict (API 端口被占)
- Symptoms: exit code 1 + high runs count, log says "Port 8642 already in use"
- Fix: `lsof -i :8642` → kill old process → `launchctl kickstart -k`
- ⚠️ `enabled: false` does NOT prevent api_server initialization. Must change port.

### Token/Credential Missing
- Symptoms: gateway runs but platform (Telegram, etc.) doesn't respond
- Fix: Check profile `.env` for required tokens

### DNS Pollution (Clash Verge fake-ip)
- Symptoms: `telegram connect timed out`, `httpx.ConnectError`
- Root cause: Clash Verge `enhanced-mode: fake-ip` hijacks ALL DNS to 198.18.0.x
- Fix: Add `DOMAIN,api.telegram.org,DIRECT` rule to Clash config

### MCP stdio Freeze
- Symptoms: gateway alive (PID visible), 0% CPU, no log output
- Root cause: MCP server subprocess blocks stdin/stdout → asyncio event loop freezes
- Fix: Kill MCP subprocess + gateway, remove MCP config, restart

### FD Exhaustion (Errno 24)
- Symptoms: "Too many open files", gateway alive but unresponsive
- Root cause: macOS default 256 fd limit exceeded after 2-3 days
- Fix: `sudo launchctl limit maxfiles 4096 8192` + restart all gateways
- Leak sources: httpx connection pool (CLOSED sockets), subprocess PIPE (unclosed pipes)

### KeepAlive SuccessfulExit Trap
- Symptoms: SIGTERM → gateway doesn't restart despite KeepAlive
- Root cause: `SuccessfulExit: false` treats SIGTERM as "successful"
- Fix: Change to `KeepAlive => true` or add `Crashed => true`

### Protected Config Modification → Death Loop
- Symptoms: gateway crashes → agent tries to patch config → write denied → SIGTERM → restart → repeat
- Root cause: config.yaml is locked during gateway runtime
- Fix: Stop gateway from OUTSIDE (different profile or launchctl), edit via terminal, restart

### Cron Prompt Security Interception
- Symptoms: `cronjob(action='create')` returns "Blocked: prompt matches threat pattern 'exfil_curl_url'"
- Root cause: Security scanner detects curl + URL pattern in cron prompt
- Fix: Use skill references instead of embedding curl commands in prompt

### Default Profile PID Location
- her-m2/english-tutor PID: `~/.hermes/profiles/<name>/gateway.pid`
- **default PID: `~/.hermes/gateway.pid`** (root level, NOT in profiles/default/)

### Weixin Token Conflict
- Same Weixin token can only be used by ONE gateway process
- Only her-m2 should have WEIXIN_* env vars
- Other profiles must NOT have WEIXIN_* in their launchd plists

### Memory Char Limit Cascade
- Low `memory_char_limit` (e.g., 2200) → constant limit errors → repeated replace/compact attempts → token waste → memory pressure → SIGKILL
- Fix: Set `memory_char_limit: 5000`, `user_char_limit: 3000`

## Phase 4: Recovery

```bash
# Force restart (works even if launchd throttled)
launchctl kickstart -k gui/501/<service>

# If kickstart fails (service not loaded), bootstrap first
launchctl bootstrap gui/501 /Users/mac/Library/LaunchAgents/<service>.plist
launchctl kickstart gui/501/<service>

# Verify
sleep 3 && kill -0 <PID> && echo "alive" || echo "dead"
curl -s --max-time 5 http://localhost:<port>/health
```

## Phase 5: FD Leak Diagnostics

```bash
# Count total FDs
lsof -p <PID> | wc -l

# By type
lsof -p <PID> 2>/dev/null | awk '{print $5,$NF}' | sort | uniq -c | sort -rn | head -20

# CLOSED sockets (httpx connection pool leak)
lsof -p <PID> 2>/dev/null | grep CLOSED

# Orphaned PIPEs (subprocess not cleaned up)
lsof -p <PID> 2>/dev/null | grep PIPE | grep -v '    1\|    2'
```

Known leak sources:
1. httpx connection pool in `gateway/platforms/telegram.py` — `_drain_polling_connections()` only drains polling pool, not general pool
2. Subprocess PIPE in `tools/environments/base.py` — `_wait_for_process()` only closes stdout on normal completion, not on interrupt/timeout

## PIDs Are Not Enough — Verify with Logs

A PID can be alive but the gateway can be frozen. Always check:
```bash
tail -20 <profile>/logs/gateway.log  # Look for recent entries
tail -20 <profile>/logs/gateway.error.log  # Look for errors
```

If the last log entry is hours old but PID is alive → frozen, not running.