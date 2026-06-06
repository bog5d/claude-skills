# FD Leak Debugging — lsof 侦查手册

## 快速侦查（一命令摸清泄露大户）

```bash
# 统计当前 gateway 的 fd 类型分布
lsof -p <PID> 2>/dev/null | awk '{print $5}' | sort | uniq -c | sort -rn
```

正常 gateway 的 fd 组成：~60 REG (库文件) + ~30 unix + ~10 IPv4 + ~5 PIPE。  
**异常信号**：IPv4 > 20、PIPE > 5、CLOSED socket 出现 → 泄露。

---

## 泄露源 #1: httpx CLOSED socket（连接池泄露）

### 症状识别

```bash
lsof -p <PID> 2>/dev/null | grep CLOSED
```

典型输出：
```
Python  1459  mac  21u  IPv4  ...  TCP localhost:52577->localhost:7897 (CLOSED)
Python  1459  mac  22u  IPv4  ...  TCP localhost:52668->localhost:7897 (CLOSED)
```

- 目标端口 7897 = Clash/sing-box 代理
- 每次代理抖动（网络切换、VPN 断开）时 Telegram API 的 httpx 连接池残留 CLOSED socket
- 每天可累积 2-4 个，2-3 天后接近 256 上限

### 根因

`telegram.py` 的 `_drain_polling_connections` 只排空 `_request[0]`（getUpdates 池），漏了 `_request[1]`（send_message 等 general request 池）。

### 修复（commit ac74fe1ce）

`_drain_polling_connections` 遍历全部两个 request pool：
- polling pool 先 drain
- general pool 等 0.3s（让飞行中的 send 完成）再 drain

---

## 泄露源 #2: subprocess PIPE（终端命令清理不足）

### 症状识别

```bash
# 排除 stdin(1)/stdout(2)，其余 PIPE 即为泄露
lsof -p <PID> 2>/dev/null | grep PIPE | grep -vE '^\S+\s+\S+\s+(1u|2u)'
```

典型输出：
```
Python  1459  mac  36u  PIPE  ...  ->0x48c5174a44f72a72
Python  1459  mac  37u  PIPE  ...  ->0xf13ef3d31b4c1e00
```

### 根因

`tools/environments/base.py` 的 `_wait_for_process` 只在正常完成路径关闭 `proc.stdout.close()`，未在以下路径关闭：
- 用户中断（`is_interrupted()`）
- 命令超时（`time.monotonic() > deadline`）
- 进程级信号（`KeyboardInterrupt`/`SystemExit`）

### 修复（commit ac74fe1ce）

三个异常退出路径各加 `try: proc.stdout.close() except: pass`

---

## 泄露源 #3: 僵尸 terminal session（pipe 未 reap）

### 验证

```bash
# 检查是否有 zombie 子进程
ps aux | grep defunct

# 检查 gateway 持有的子进程数
ps --ppid <GATEWAY_PID> | wc -l
```

如果子进程数持续增长 → subprocess spawn 后未 wait/reap。

---

## 验证修复效果

```bash
# 重启 gateway 后观察 fd 增长速率
for pid in $(ps aux | grep 'hermes.*gateway' | grep -v grep | awk '{print $2}'); do
  echo "PID $pid: $(lsof -p $pid 2>/dev/null | wc -l) fds"
done

# 观察 CLOSED socket 是否不再增长（原每几小时多一个）
watch -n 3600 "lsof -p <PID> 2>/dev/null | grep CLOSED | wc -l"
```
