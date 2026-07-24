# FD 级联崩溃恢复配方

## 场景
三端 gateway 全死或半死，watchdog/defibrillator 全部挂掉。用户报告"副官死了，英语 tutor 也死了"。

## 实战记录（2026-06-06）

### 初始状态
```
her-m2:       PID 1459  ✅ (但老 ulimit 256)
english-tutor: PID 47258 ✅ (部分响应，fd 355)
default 副官:  死 ❌ (exit code 1, PID -)

defibrillator:     死 (exit -9, PID -)
network-watchdog:  死 (exit -9, PID -)
system-watchdog:   死 (exit -1, PID -)
```

### 恢复三步法

**Step 1: 一次性摸清全貌（不要逐个排查）**
```bash
# 进程状态（最可靠）
ps aux | grep -i hermes | grep -v grep

# launchd 状态（exit code 是历史的！）
launchctl list | grep -i hermes

# FD 数（关键指标）
for pid in $(ps aux | grep 'hermes.*gateway' | grep -v grep | awk '{print $2}'); do
  echo "PID $pid: $(lsof -p $pid 2>/dev/null | wc -l) fds"
done

# 错误日志尾
tail -10 <profile>/logs/gateway.error.log
```

**Step 2: 复活顺序 — gateway 优先于 watchdog**
```bash
# 先复活死掉的 gateway
launchctl kickstart -k gui/501/ai.hermes.gateway          # default 副官
sleep 8 && kill -0 $(获取新PID)

# 再复活防线
launchctl kickstart -k gui/501/com.hermes.defibrillator
launchctl kickstart -k gui/501/com.hermes.network-watchdog
launchctl kickstart -k gui/501/com.hermes.system-watchdog
```

**Step 3: 验证 + 治本**
```bash
# 确认三端全活
for name in her-m2 default english-tutor; do
  pid=$(cat /Users/mac/.hermes/profiles/$name/gateway.pid 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['pid'])" 2>/dev/null)
  kill -0 $pid 2>/dev/null && echo "$name ✅ PID $pid" || echo "$name ❌"
done

# 确认防线全活
launchctl list | grep -E 'defib|watchdog'

# 确认 ulimit（系统级）
ulimit -n  # 应 >= 4096
```

### 根因
- **直接原因**：gateway 跑 2-3 天，fd 缓慢泄漏至 256+，触发 `[Errno 24] Too many open files`
- **级联原因**：gateway 自杀时资源争抢，macOS SIGKILL 轻量 watchdog 进程
- **launchd 没救**：watchdog 被 kill 后 launchd 崩溃节流，不再重启

### 治本措施
1. `sudo launchctl limit maxfiles 4096 8192`（已完成）
2. 每次修改 ulimit 后 **必须重启所有 gateway**（旧进程不继承新限制）
3. system-watchdog 加 FD 监控（任一 gateway fd > 2000 → 告警 + 自动 kickstart）