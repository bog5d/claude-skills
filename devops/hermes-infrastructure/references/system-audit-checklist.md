# Hermes 全系统审计清单

一次性摸清所有 Gateway / 守护进程 / 资源 / 配置的标准化命令集。适合：
- 系统异常排查前快速摸底
- 定期健康巡检（cron job 模板）
- 新 session 开始时确认当前状态

## 1. Gateway 进程状态

```bash
ps aux | grep -i "[h]ermes.*gateway" | awk '{printf "PID %s RSS %dMB CMD: %s\n", $2, $6/1024, substr($0, index($0,$11))}'
```

关注：PID 存活、RSS（>500MB 告警）、CPU 占用。

## 2. launchd 注册状态

```bash
launchctl list | grep -i hermes
```

⚠️ **exit code 列是历史值**，不是当前状态。必须用 `kill -0 <PID>` 交叉验证。

## 3. 守护进程状态

```bash
for svc in com.hermes.defibrillator com.hermes.system-watchdog com.hermes.network-watchdog; do
  pid=$(launchctl list | grep "$svc" | awk '{print $1}')
  if [ -n "$pid" ] && [ "$pid" != "-" ]; then
    alive=$(kill -0 "$pid" 2>/dev/null && echo "ALIVE" || echo "DEAD")
    echo "  $svc: PID=$pid $alive"
  else
    echo "  $svc: NOT RUNNING"
  fi
done
```

## 4. 资源使用

```bash
# 内存
vm_stat | head -5
# 磁盘
df -h / | tail -1
# DNS（检查 198.18.x 污染）
scutil --dns | grep 'nameserver\[' | head -5
```

## 5. Gateway 日志异常（最近）

```bash
for dir in /Users/mac/.hermes/logs /Users/mac/.hermes/profiles/her-m2/logs /Users/mac/.hermes/profiles/english-tutor/logs; do
  echo "=== $dir ==="
  tail -5 "$dir/gateway.error.log" 2>/dev/null | grep -E "ERROR|WARNING" | tail -3
done
```

## 6. 配置一致性检查

```bash
# .env 文件 key 对比
for p in her-m2 default english-tutor; do
  path="/Users/mac/.hermes/profiles/$p/.env"
  if [ -f "$path" ]; then
    keys=$(grep -o '^[A-Z_]*=' "$path" 2>/dev/null | tr '\n' ' ')
    echo "  $p: $keys"
  else
    echo "  $p: 无 .env"
  fi
done

# Skills 数量对比
for d in /Users/mac/.hermes/profiles/her-m2/skills /Users/mac/.hermes/skills /Users/mac/.hermes/profiles/english-tutor/skills; do
  count=$(find "$d" -name "SKILL.md" 2>/dev/null | wc -l)
  echo "  ${d}: ${count} skills"
done
```

## 7. Cron 覆盖检查

```bash
cronjob list  # 通过 Hermes tool
```

关注：关键任务（健康报告、记忆仓同步、DNS 刷新）是否在两个 profile 上都有覆盖。

## 8. 跨验证：PID 是否存活

```bash
# launchctl list 的 PID 列可能过时，必须交叉验证
for pid in $(launchctl list | grep hermes | awk '{if($1!="-")print $1}'); do
  kill -0 $pid 2>/dev/null && echo "PID $pid ALIVE" || echo "PID $pid DEAD (launchd exit code 是历史值)"
done
```

## 典型异常信号

| 信号 | 含义 | 行动 |
|------|------|------|
| launchd exit code 75 | 上次 EX_TEMPFAIL（DNS/网络） | 检查 DNS，`kill -0 PID` 确认当前存活 |
| defibrillator 报 "离线冷却中" | defib 判断 gateway 死，但冷却期内不复活 | 手动 `launchctl kickstart -k` |
| Skills 数量不一致 | 同步失败或某个 profile 路径错误 | 手动 rsync |
| .env key 不一致 | 某个 profile 缺关键 credential | 追加缺失的 key |
| 198.18.x DNS | Clash fake-ip 污染 | 重启 Clash 或加 DIRECT 规则 |
