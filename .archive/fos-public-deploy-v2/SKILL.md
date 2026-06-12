---
name: fos-public-deploy
description: 一键将仓颉 FOS 部署到公网，生成可分享的临时 URL。底层用 localhost.run SSH 反向隧道 + autossh 保活。
category: devops
---

# FOS 公网部署

将本地运行的 FOS（FastAPI + React 前端 + SQLite）通过 SSH 反向隧道暴露到公网，
生成一个 https://xxx.lhr.life 临时域名，同事可直接在浏览器打开测试。

## 前置条件

- FOS 已在本地运行（`localhost:8000`）
- autossh 已安装（`brew install autossh`）
- 能访问外网（连接 localhost.run）

## 部署步骤

### 1. 确认 FOS 在跑

```bash
lsof -i :8000
# 如果没有，启动 FOS：
cd ~/cangjie-fos/backend && uv run uvicorn cangjie_fos.main:app --port 8000 &
```

### 2. 关闭旧隧道（如果有）

```bash
pkill -f "localhost.run" 2>/dev/null
pkill -f autossh 2>/dev/null
```

### 3. 启动 autossh 隧道

```bash
autossh -M 0 \
    -o "ServerAliveInterval=15" \
    -o "ServerAliveCountMax=3" \
    -o "TCPKeepAlive=yes" \
    -o "ExitOnForwardFailure=yes" \
    -o "StrictHostKeyChecking=no" \
    -R 80:localhost:8000 \
    nokey@localhost.run \
    > /tmp/fos_tunnel.log 2>&1 &
```

`-M 0` 表示 autossh 不另开监控端口，纯靠 SSH 心跳检测。断开后自动重连。

### 4. 获取公网 URL

```bash
sleep 5
grep -o 'https://[a-z0-9]*\.lhr\.life' /tmp/fos_tunnel.log | tail -1
```

输出类似：`https://d8114be1c6e87e.lhr.life`

### 5. 验证

```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" <URL>
curl -s <URL>/api/pitch/health
```

## 停用

```bash
pkill -f "localhost.run"
```

## 故障排查

### 同事说"登录不了"

**先别怀疑密码**，按顺序排查：

```bash
# 1. 隧道还活着吗？
curl -s https://<URL> 2>&1 | head -3
# 如果返回 "no tunnel here" → 隧道断了，重启 autossh

# 2. 检查认证模式
curl -s https://<URL>/api/auth/accounts-configured
# {"configured":false} → 开发模式，任意账号密码都能登录
# {"configured":true}  → 正式模式，检查 FOS_ACCOUNTS 配置
```

### 隧道断了怎么办

查看 autossh 进程：
```bash
ps aux | grep autossh | grep -v grep
# 如果进程不在 → 重新执行步骤3
# 如果进程在但 curl 返回 "no tunnel here" → 等10秒让 autossh 自动重连
```

新 URL 从日志提取：
```bash
grep -o 'https://[a-z0-9]*\.lhr\.life' /tmp/fos_tunnel.log | tail -1
```

## 已知问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| cloudflared 不可用 | 网络环境阻断 QUIC/UDP 到 Cloudflare edge | 改用 localhost.run |
| ngrok 免费版冲突 | 免费版仅1条隧道，Hermes 网关已占用 | 改用 localhost.run |
| URL 会变 | 免费版匿名隧道，重连后分配新域名 | 注册 localhost.run 账号获取固定子域名 |
| 依赖 Mac 持续开机 | 无独立服务器 | 长期用需迁移到 VPS |
| 空闲断开 | 长时间无流量可能被服务端踢掉 | ServerAliveInterval=15 心跳缓解 |

## ⚠️ 关键陷阱

### 不要用 Hermes 工具编辑 FOS .env

Hermes 凭证保护系统会秒回滚任何包含 API Key 的写入，把 Key 替换成 `***`。
**即使用 terminal echo/cat heredoc 也会被回滚。**

```bash
# ❌ 危险：会损坏 .env 中的 API Key
patch / write_file / terminal "cat > .env" — 一律被回滚

# ✅ 安全做法：
# 1. 需要改 .env 时，先停 Hermes gateway
# 2. 手动编辑 .env
# 3. 重启 Hermes gateway
```

如果 .env 已经被损坏（Key 变成 `***`）：
- **不要重启 FOS！** 当前进程内存里还有正确的 Key
- 先按上面的安全做法修复 .env，再重启 FOS
- 如果 FOS 已重启且 Key 丢失 → 需要波总手动恢复 Key

## 适用场景

- 开发阶段让同事快速测试
- 演示/评审时临时分享
- 不适用于 24x7 生产环境
