# Hermes Agent Robustness & Health Check Methodology

Systematic proactive audit for Hermes production setups. Run this before/after major config changes, after OS updates, or periodically (monthly).

## 1. Process & Launchd Audit

```bash
# All Hermes-related launchd services
launchctl list | grep -i hermes

# Check KeepAlive + RunAtLoad status
for label in ai.hermes.gateway ai.hermes.gateway-her-m2 ai.hermes.gateway-english-tutor; do
    launchctl print gui/501/$label 2>/dev/null | grep -E "PID|KeepAlive|RunAtLoad|last exit"
done

# Plist file contents (verify KeepAlive = true, not SuccessfulExit=false)
cat /Users/$USER/Library/LaunchAgents/ai.hermes.gateway.plist | grep -A3 KeepAlive

# Check for zombie/residual processes
ps aux | grep -i hermes | grep -v grep | grep '?? S' | grep -i 'bash\|sh'
```

**Brittle KeepAlive pattern**: `<dict><key>SuccessfulExit</key><false/></dict>` — only restarts on crash (exit≠0). For bulletproof recovery, use `<true/>` — restarts on any exit (including launchctl stop). Note: with `<true/>`, stopping a gateway requires `launchctl unload` not `launchctl stop`.

## 2. Process Memory & Health

```bash
# RSS per process
ps aux | grep -i hermes | grep -v grep | awk '{printf "%s RSS=%.1fMB\n", $11, $6/1024}'

# Total memory
ps aux | grep -i hermes | grep -v grep | awk '{sum+=$6} END {printf "Total RSS: %.1fMB\n", sum/1024}'

# Uptime
ps -eo pid,etime,command | grep -i hermes | grep -v grep
```

Gateways should each stabilize around 60-120MB RSS. API gateway ~6MB. If any process exceeds 200MB, investigate memory leak.

## 3. Network Connectivity

```bash
# Listening ports
lsof -i -P | grep LISTEN | grep -i hermes

# Telegram connectivity test (ping the bot API)
curl -s -o /dev/null -w "%{http_code}" "https://api.telegram.org/bot$(cat ~/.hermes/credentials 2>/dev/null || echo test)/getMe"

# DNS resolution
dig +short api.telegram.org

# Network interface status
ifconfig en0 | grep "status"
```

**Known issue**: If network drops >60-120 seconds, Telegram long-poll connection may die. Gateway process typically stays alive but bot is unreachable. Restore by: `launchctl unload` → `launchctl load` the gateway plist. Consider adding a heartbeat watchdog that curls /getMe every 60s and restarts gateway on 3 consecutive failures.

## 4. Disk & Logs

```bash
# Disk usage
df -h /

# Log sizes by profile
du -sh ~/.hermes/logs/
du -sh ~/.hermes/profiles/*/logs/ 2>/dev/null

# Largest log files
du -sh ~/.hermes/logs/*.log | sort -rh | head -5

# Check log rotation
ls ~/.hermes/logs/*.log.* 2>/dev/null  # Hermes built-in: .1, .2, .3 rotation

# Hermes config.yaml log settings
cat ~/.hermes/config.yaml 2>/dev/null | grep -A5 -i log
```

**Warning**: Without explicit log rotation config, gateway/error logs grow unbounded. Hermes has built-in agent.log rotation (.1/.2/.3), but gateway logs don't auto-rotate. Set `max_bytes` and `backup_count` in config.yaml for log rotation.

## 5. Cron Job Integrity

```bash
# List all scheduled jobs
hermes cron list

# Check persistence file
cat ~/.hermes/cron/jobs.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"jobs\"])} jobs')"

# Verify cron ticker is running
ps aux | grep cron-ticker | grep -v grep

# Check last job runs
ls -lt ~/.hermes/cron/output/ | head -5
```

**Persistence**: Cron jobs live in `~/.hermes/cron/jobs.json` (JSON file, not SQLite). Atomic writes with tempfile + fsync + `atomic_replace`. Survives gateway restart. But if `~/.hermes/` is lost, cron config is gone.

## 6. Secrets & Credentials

```bash
# Check credential files exist
ls -la ~/.hermes/*cred* 2>/dev/null
ls -la ~/.hermes/api_key.txt 2>/dev/null

# .env files
find ~/.hermes -name ".env" -not -path "*/.git/*" 2>/dev/null

# No plaintext secrets in config
grep -n "api_key\|password\|token" ~/.hermes/config.yaml 2>/dev/null | grep -v "^#" | head -5
```

**Gateway credential protection**: Hermes locks credential files at runtime — any external write (patch/sed/Python) gets rolled back. To update API keys: stop gateway → edit file → restart gateway.

## 7. Backup Status

```bash
# TimeMachine
tmutil status 2>/dev/null

# Local snapshots
tmutil listlocalsnapshots / 2>/dev/null | head -3

# Manual backups
find ~/.hermes -name "*.bak" -o -name "*.backup" 2>/dev/null
```

**Critical unbacked data**: `~/.hermes/*/state.db` (session history, up to 400MB), `~/.hermes/cron/jobs.json` (task definitions), credential files. Skills + memory pushed to GitHub (claude-skills, wangbo-brain) are already backed up.

## 8. Hermes Version & Dependencies

```bash
# Version
hermes --version

# Check commits behind
cd ~/.hermes/hermes-agent && git fetch && git rev-list --count HEAD..origin/master

# Python venv health
~/.hermes/hermes-agent/venv/bin/python3 --version
```

## 9. System Updates

```bash
# Available updates
softwareupdate --list 2>/dev/null

# macOS version
sw_vers
```

## Recovery Checklist (Post-Outage)

1. `launchctl list | grep hermes` — are all 3+ gateways registered?
2. `launchctl print gui/501/ai.hermes.gateway-her-m2 | grep PID` — reincarnated?
3. `hermes cron list` — cron jobs loaded from jobs.json?
4. `curl -s "https://api.telegram.org/bot$(TOKEN)/getMe"` — bot responsive?
5. `hero` log check — `tail -100 ~/.hermes/logs/gateway.log` — any startup errors?
6. After all green — `hermes cron run <job_id>` to re-trigger critical tasks
