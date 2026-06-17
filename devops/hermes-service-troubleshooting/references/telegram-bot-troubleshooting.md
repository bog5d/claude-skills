# Telegram Bot 连接排查记录

## 案例：holo-local profile 不响应

### 现象
Telegram bot 发送消息后无响应，gateway 日志无连接记录。

### 排查路径

#### 1. 检查 gateway 进程
```bash
pgrep -a "hermes.*holo"
```
无进程 → 启动失败

#### 2. 检查日志
```bash
tail ~/.hermes/profiles/holo-local/logs/gateway.log
```
发现：启动后立即退出

#### 3. 检查 config.yaml 语法
```bash
grep -n 'enabled' ~/.hermes/profiles/holo-local/config.yaml
```
发现问题：`api_server.enabled: false` 缩进错误，导致 YAML 解析失败

#### 4. 检查端口冲突
```bash
lsof -i :8642
```
发现：端口 8642 已被 default gateway 占用

#### 5. 检查 Telegram 授权
```bash
grep TELEGRAM_ALLOWED_USERS ~/.hermes/profiles/holo-local/.env
```
发现问题：配置的是 PID（501），不是 Telegram User ID（8447296166）

### 修复步骤

```bash
# 1. 修正 config.yaml YAML 缩进
# 确保 api_server.enabled: false 正确嵌套在 platforms.api_server 下

# 2. 禁用 api_server（避免端口冲突）
# 在 config.yaml 中设置 api_server.enabled: false

# 3. 更新允许的用户 ID
sed -i '' 's/TELEGRAM_ALLOWED_USERS=.*/TELEGRAM_ALLOWED_USERS=8447296166/' \
  ~/.hermes/profiles/holo-local/.env

# 4. 重启 gateway
launchctl kickstart -k gui/501/ai.hermes.gateway-holo-local

# 5. 验证
tail ~/.hermes/profiles/holo-local/logs/gateway.log | grep "Telegram"
```

### 验证成功标志
- 日志中出现 `Connected via polling`
- Telegram bot 发送消息后能收到回复

### 测试消息
```bash
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=8447296166&text=🟢 Holo-3.1 本地模型已上线"
```
