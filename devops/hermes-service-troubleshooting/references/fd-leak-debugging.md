# FD 泄漏侦查手册

## 快速诊断

```bash
# 1. 总 fd 数（接近 256 是危险信号，即使系统 ulimit 已拉高）
lsof -p <PID> 2>/dev/null | wc -l

# 2. 按类型/目标统计 — 找到泄露大户
lsof -p <PID> 2>/dev/null | awk '{print $5,$NF}' | sort | uniq -c | sort -rn | head -20

# 3. 找 CLOSED socket — httpx 连接池泄露
lsof -p <PID> 2>/dev/null | grep CLOSED
# 典型输出：localhost:52577->localhost:7897 (CLOSED)
# localhost:7897 = Clash 代理端口，每次代理抖动就多一个

# 4. 找残留 PIPE — subprocess 未清理
lsof -p <PID> 2>/dev/null | grep PIPE | grep -v 'fd.*[12][^0-9]'
# 排除 stdin(fd 1)/stdout(fd 2)，其余均为泄露
```

## 已知泄露源

| 泄露源 | 文件 | 泄露类型 | 触发条件 |
|--------|------|----------|----------|
| httpx 连接池（general request） | `gateway/platforms/telegram.py` | CLOSED socket | Clash 代理抖动 → Telegram 重连 |
| httpx 连接池（polling request） | `gateway/platforms/telegram.py` | CLOSED socket | Clash 代理抖动 → getUpdates 重连 |
| subprocess PIPE（中断路径） | `tools/environments/base.py` | PIPE fd | 终端命令被用户中断 |
| subprocess PIPE（超时路径） | `tools/environments/base.py` | PIPE fd | 终端命令超时被 kill |
| subprocess PIPE（KeyboardInterrupt） | `tools/environments/base.py` | PIPE fd | Gateway SIGTERM 时 mid-command |

## 代码修复（commit `ac74fe1ce`）

### Fix 1: telegram.py — 排空全部 httpx 池
```
原: _drain_polling_connections() 只排空 _request[0] (getUpdates)
改: 遍历 _request 全部索引，general pool 加 0.3s 延迟防止打断飞行请求
```

### Fix 2: base.py — 全 exit path 关 PIPE
```
原: 只在正常完成路径 (line 747) 关 proc.stdout
改: interrupt + timeout + KeyboardInterrupt 三个路径各加 try/except close
```
