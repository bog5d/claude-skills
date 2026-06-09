---
name: quick-tunnel-deploy
description: 快速把本地 Web 应用暴露到公网（测试用）。依次尝试 ngrok → localhost.run SSH → cloudflared，自动选可用的方案。
---

# 快速公网隧道部署

把本地正在运行的服务暴露给公网访问，适合给同事发链接测试、临时演示。

## 触发条件
- 用户说「部署」「发链接给同事测试」「开个公网地址」
- 本地服务已在某个端口运行

## 优先级链

### 1. ngrok（首选，已认证，URL 固定）

**⚠️ 免费版警告页坑**：ngrok 免费版会在用户首次访问时弹出 "ngrok-skip-browser-warning" 页面，用户需手动点击 "Visit Site"。这在手机端体验很差。

```bash
# 启动隧道
nohup ngrok http <本地端口> --log=stdout > /tmp/ngrok_url.log 2>&1 &

# 提取 URL
sleep 4 && cat /tmp/ngrok_url.log | grep -o 'https://[a-zA-Z0-9.-]*\.ngrok-free\.\w*' | head -1
```

### 2. localhost.run SSH 隧道（备选，无需安装）

```bash
# 关键：必须用 nohup + 后台，否则 SSH 会在非 TTY 环境下断开
nohup ssh -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ExitOnForwardFailure=yes \
    -R 80:localhost:<本地端口> \
    nokey@localhost.run \
    > /tmp/tunnel.log 2>&1 &

sleep 3
# 从日志提取 URL
grep -o 'https://[a-z0-9]*\.lhr\.life' /tmp/tunnel.log | tail -1
```

**坑：**
- ❌ 不用 `nohup` → 命令结束就断开
- ❌ 不加 `ServerAliveInterval` → 闲置几分钟就断
- ✅ URL 格式：`https://<随机ID>.lhr.life`
- ✅ 自带 HTTPS（Let's Encrypt）

**关闭：** `pkill -f "localhost.run"`

**⚠️ 坑：SSH 输出在 Hermes process log 中可能全空白。** `process(action='log')` 返回的 output 字段全是空行，无法提取 `.lhr.life` URL。**已验证的绕过方案**：重定向到文件 `ssh ... > /tmp/tunnel_url.txt 2>&1`，等待 5 秒后用 `cat /tmp/tunnel_url.txt` 提取 URL。原因：localhost.run 的欢迎 banner + URL 可能经 SSH 的 PTY 分配逻辑处理后不在 stdout/stderr 的缓冲区中正常显示。

### 3. cloudflared（备选，需提前认证）

```bash
# 首次使用需认证
cloudflared tunnel login

# 启动隧道
cloudflared tunnel --url http://localhost:<本地端口>
```

## 验证部署

```bash
# 测试前端
curl -s -o /dev/null -w "HTTP %{http_code}" <公网URL>

# 测试 API
curl -s <公网URL>/api/health
```

## 局限性

| 维度 | 说明 |
|------|------|
| URL 稳定性 | SSH 隧道断开后地址会变 |
| 持久化 | 依赖本地机器持续运行 |
| 性能 | 受限于家用网络上传带宽 |
| 适用场景 | 临时测试、演示、同事试用 |

## 永久部署用

- 云服务器 VPS + systemd 守护进程
- Docker + 容器平台
- 不适合 PinMe（只支持静态站点，动态后端不行）
