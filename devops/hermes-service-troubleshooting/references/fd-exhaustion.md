# File Descriptor Exhaustion — Full Diagnostic & Fix

## One-liner check

```bash
# For a specific PID
echo "fd count: $(lsof -p <PID> 2>/dev/null | wc -l) / limit: $(ulimit -n)"
```

## Full system check

```bash
for pid in $(pgrep -f "hermes.*gateway"); do
    profile=$(ps -p $pid -o command= | grep -oP '(?<=--profile )\S+' || echo "default")
    fd_count=$(lsof -p $pid 2>/dev/null | wc -l)
    limit=$(ulimit -n)
    pct=$((fd_count * 100 / limit))
    printf "%-15s PID=%-6s fd=%4d/%d (%d%%)\n" "$profile" "$pid" "$fd_count" "$limit" "$pct"
done
```

## TWO KNOWN LEAK SOURCES (fixed 2026-06-06)

### Leak #1: httpx CLOSED sockets → Clash proxy (localhost:7897)

**Symptom:**
```bash
lsof -p <PID> 2>/dev/null | grep CLOSED
# Output example:
# Python 1459 mac 21u IPv4 ... TCP localhost:52668->localhost:7897 (CLOSED)
# Python 1459 mac 22u IPv4 ... TCP localhost:52577->localhost:7897 (CLOSED)
```

**Root cause:** Telegram platform's `_drain_polling_connections()` only drained `_request[0]` (getUpdates polling pool). The general-request pool (`_request[1]`, used for send_message/edit_message) accumulated CLOSED sockets across proxy reconnection cycles.

**Fix applied in** `gateway/platforms/telegram.py`:
- `_drain_polling_connections()` now iterates BOTH request pools
- 0.3s delay before draining general pool to protect in-flight sends
- See: https://github.com/NousResearch/hermes-agent (local commit ac74fe1ce)

### Leak #2: subprocess PIPE fds not closed on interrupt/timeout

**Symptom:**
```bash
lsof -p <PID> 2>/dev/null | grep PIPE
# Extra PIPEs (not fd 1,2 for stdin/stdout) indicate leaked subprocess pipes
```

**Root cause:** `tools/environments/base.py` `_wait_for_process()` only called `proc.stdout.close()` in the normal-completion path. Three other exit paths (interrupt, timeout, KeyboardInterrupt) left stdout pipe open.

**Fix applied in** `tools/environments/base.py`:
- Added `proc.stdout.close()` in interrupt path (line 667)
- Added `proc.stdout.close()` in timeout path (line 684)
- Added `proc.stdout.close()` in KeyboardInterrupt path (line 748)

## Fast fd composition audit

```bash
# See what's consuming fds
lsof -p <PID> 2>/dev/null | awk '{print $5,$NF}' | sort | uniq -c | sort -rn | head -15
```

## Cross-gateway restart (NEVER self-restart)

When a gateway needs restart (to load new code or clear leaked fds), **never have it restart itself.** Use another profile's gateway:

```
her-m2 restart → 副官 executes: launchctl kickstart -k gui/501/ai.hermes.gateway-her-m2
副官 restart   → her-m2 executes: launchctl kickstart -k gui/501/ai.hermes.gateway
eng-tutor      → either of above
```

After restart, verify:
```bash
sleep 10 && ps aux | grep <profile> | grep -v grep
lsof -p <NEW_PID> | wc -l  # should be < 150
```

## Thresholds

| fd usage % | action |
|---|---|
| <60% | OK |
| 60-90% | ⚠️ monitor — fd leak likely, prepare restart |
| >90% | 🔴 critical — restart imminent |
| >100% | 💀 zombie — process alive but every open() fails |

## Recovery command

```bash
kill -9 <PID> && \
bash -c 'ulimit -n 4096 && hermes --profile <name> gateway run --replace' &
```

## Root cause on macOS

`launchctl limit maxfiles` default:
- Soft: 256
- Hard: unlimited (but capped by kernel `kern.maxfilesperproc`)

Hermes gateways running 24/7 for 2-3 days naturally accumulate open file descriptors
from terminal sessions, sockets, plugins, cron jobs, and log files.

**Permanent fix:** `sudo launchctl limit maxfiles 4096 8192`

## ⚠️ Hazard: .env overwrite during recovery

When using `write_file` or other tools to modify `.env` during fd-exhaustion recovery,
the credential scanner may corrupt the file content (replacing token values with `***`),
resulting in a 1-line `.env` with all original credentials lost.

**Before any .env edit, copy a backup:**
```bash
cp <profile>/.env /tmp/.env.backup.$(date +%s)
```

If `.env` is already lost:
1. Copy global `.env` as fallback: `cp ~/.hermes/.env <profile>/.env`
2. Append profile-specific keys (GITHUB_TOKEN, SUDO_PASSWORD, etc.)
3. If TELEGRAM_BOT_TOKEN differs from global, replace using the credential-scanner-workaround technique
4. Verify: `hermes config show` should list model/provider correctly

See `references/credential-scanner-workaround.md` for safe token writing.
