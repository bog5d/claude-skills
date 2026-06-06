# Cross-Gateway Restart Strategy

## Iron Rule

**A gateway must NEVER restart itself.** If it tries to `launchctl kickstart` its own service
or `kill -9` its own parent, the restart dies mid-operation and the session is lost.

## Correct Pattern

When a gateway needs restart (code update, fd cleanup, memory pressure), use
**another profile's gateway** to do it.

| Target | Executor | Command |
|--------|----------|---------|
| her-m2 | 副官 (default) | `launchctl kickstart -k gui/501/ai.hermes.gateway-her-m2` |
| 副官 (default) | her-m2 | `launchctl kickstart -k gui/501/ai.hermes.gateway` |
| english-tutor | her-m2 or 副官 | `launchctl kickstart -k gui/501/ai.hermes.gateway-english-tutor` |

## Implementation Flow (for her-m2 self-restart)

her-m2 cannot restart itself. It sends a message to the user:

```
发给 @cosy_udbe_bot：

重启 her-m2 gateway，让它加载新代码。

操作：
launchctl kickstart -k gui/501/ai.hermes.gateway-her-m2

等 10 秒验证：
sleep 10 && ps aux | grep -E 'her-m2|gateway.*her-m2' | grep -v grep

检查 fd 数：
PID=$(pgrep -f 'gateway.*her-m2' | head -1) && lsof -p $PID 2>/dev/null | wc -l
```

User forwards to 副官, 副官 executes, reports result.

## Why This Works

- `launchctl kickstart -k` forcefully stops old process + starts new one
- The restarting gateway doesn't know it's being restarted — no cleanup race
- The executor gateway remains alive throughout
- After restart, the new PID has fresh fd count (typically < 150)

## Verification After Restart

```bash
# 1. New process exists
ps aux | grep <profile_pattern> | grep -v grep

# 2. fd count healthy
lsof -p <NEW_PID> | wc -l  # should be < 200

# 3. No CLOSED sockets
lsof -p <NEW_PID> | grep CLOSED  # should be empty

# 4. Gateway log shows startup
tail -3 <profile>/logs/gateway.log
# Should show: "Gateway running with N platform(s)" + "Cron ticker started"
```
