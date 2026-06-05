# File Descriptor Exhaustion — Quick Diagnostic

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

Hermes gateways running 24/7 for 2-3 days naturally accumulate 300+ open file descriptors
from terminal sessions, sockets, plugins, cron jobs, and log files. This exceeds 256 and
triggers cascading Errno 24 failures across all subsystems.

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
