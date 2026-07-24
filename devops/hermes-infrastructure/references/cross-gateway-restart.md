# 跨 Gateway 重启协调

## 核心原则

**永远不要让一个 gateway 重启自己。** 自杀式重启可能：
- 主进程在 kill 信号到达前崩溃
- launchd 的崩溃节流导致无法自动重启
- 正在进行的对话丢失

## 方法一：副官 Relay（推荐）

当 her-m2 需要重启时，通过 Telegram relay 让副官执行：

```
her-m2 → 发送 Telegram 消息给用户 → 用户转发给 @cosy_udbe_bot → 副官执行 kickstart
```

发给副官的标准指令模板：

```
重启 her-m2 gateway，让它加载新代码。

操作：
launchctl kickstart -k gui/501/ai.hermes.gateway-her-m2

等 10 秒验证：
sleep 10 && ps aux | grep 'her-m2' | grep -v grep && echo "✅ her-m2 复活"

检查 fd 数：
PID=$(pgrep -f 'her-m2' | head -1) && lsof -p $PID 2>/dev/null | wc -l
```

## 方法二：直接 kickstart（gateway 不在当前对话时）

```bash
launchctl kickstart -k gui/501/<service_name>
```

## 方法三：bootstrap + kickstart（服务未加载时）

```bash
launchctl bootstrap gui/501 /Users/mac/Library/LaunchAgents/<plist> && \
launchctl kickstart gui/501/<service>
```

## 服务名映射

| Gateway | launchd service | plist | 
|---------|----------------|-------|
| her-m2 | `ai.hermes.gateway-her-m2` | `ai.hermes.gateway-her-m2.plist` |
| 副官 default | `ai.hermes.gateway` | `ai.hermes.gateway.plist` |
| English tutor | `ai.hermes.gateway-english-tutor` | `ai.hermes.gateway-english-tutor.plist` |

## 重启后验证

```bash
# 1. 进程存活
kill -0 <PID> 2>&1 && echo "alive" || echo "dead"

# 2. fd 健康（< 200 正常，> 300 有问题）
lsof -p <PID> 2>/dev/null | wc -l

# 3. Telegram 连接正常
tail -3 <profile>/logs/gateway.log | grep "Gateway running"

# 4. 无 CLOSED socket 残留
lsof -p <PID> 2>/dev/null | grep CLOSED | wc -l  # 应为 0
```
