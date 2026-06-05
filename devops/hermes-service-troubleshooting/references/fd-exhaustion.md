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
