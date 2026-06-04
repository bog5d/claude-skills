---
name: wechat-publisher-relay
description: 阿里云中继服务器（47.85.62.133）管理 — SSH 登录、wx-publisher 服务运维、API 端点、代码修改与部署。当用户提到"阿里云服务器""中继""47.85""wx-publisher""push_telegram"或需要操作该服务器时使用。
category: devops
---

# 阿里云微信发布中继服务器

## 服务器信息

| 项 | 值 |
|---|-----|
| IP | 47.85.62.133 |
| 主机名 | iZ0xico4s35nx01ecj3anmZ |
| 云厂商 | 阿里云轻量应用服务器 |
| OS | Linux (Alibaba Cloud Linux / CentOS) |
| SSH | 密钥认证（`~/.ssh/id_ed25519_alicloud`），密码登录已关闭。VNC 应急用 root 密码。 |
| Node.js | ESM 模块，通过 PM2 管理 |

## 服务概览

```
/root/wx-publisher/
├── server.js       ← 主服务（Node.js http 模块，ESM import）
├── deepseek.js     ← DeepSeek AI 排版（formatArticle）
├── wechat.js       ← 微信公众号草稿创建（createDraft）
├── .env            ← BEARER_TOKEN + WECHAT_APP_ID/SECRET + DEEPSEEK_API_KEY
├── package.json
├── node_modules/
└── cover.jpg       ← 公众号封面图
```

进程管理：**PM2**，进程名 `wx-publisher`，端口 **8787**。

## SSH 登录

```bash
ssh -i ~/.ssh/id_ed25519_alicloud -o StrictHostKeyChecking=no root@47.85.62.133
```

⚠️ Hermes 运行在 macOS 上，无法使用 `read_file` 等本地工具读取远程文件。所有远程操作必须通过 `terminal` 执行 SSH 命令。

### 常用 SSH 操作模式

```bash
# 读远程文件
ssh -i ~/.ssh/id_ed25519_alicloud root@47.85.62.133 'cat /root/wx-publisher/server.js'

# 上传本地文件
scp -i ~/.ssh/id_ed25519_alicloud /local/file.js root@47.85.62.133:/root/wx-publisher/

# 执行远程命令
ssh -i ~/.ssh/id_ed25519_alicloud root@47.85.62.133 'pm2 restart all && sleep 1 && curl -s localhost:8787/health'
```

## VNC 救援操作

当 SSH 不可用时，需引导波总通过阿里云控制台 VNC 登录。

### ⚠️ VNC 交互铁律

波总在 VNC 端是手动逐条输入，**严禁给出多行组合命令**。每条命令必须：

- 单个代码块，带 `copy code` 按钮
- 一次只给一条命令
- 上一条确认执行后再给下一条
- 说明简洁，不解释原理

```bash
# ✅ 正确：单条逐个给
su -
# （等用户确认切到 root 后，再给下一条）
```

```bash
# ✅ 正确：继续给下一条
iptables -F INPUT
```

```bash
# ❌ 错误：多行组合，用户会粘贴出错
su -
iptables -F INPUT
iptables -P INPUT ACCEPT
```

### VNC 登录后标准恢复流程

先确认当前用户（`whoami`），如果不是 root 则逐条引导切换：

```bash
su -
```
（密码会提示输入，输入后回车，密码不显示字符）

切到 root 后，常见恢复操作：

```bash
iptables -F INPUT
```

```bash
iptables -P INPUT ACCEPT
```

```bash
nft flush ruleset
```

```bash
systemctl restart sshd
```

## API 端点

所有端点基础 URL：`http://47.85.62.133:8787`

| 方法 | 路径 | 认证 | 功能 |
|------|------|------|------|
| GET | `/health` | 无 | 健康检查 → `ok` |
| POST | `/publish` | Bearer TOKEN | 接收原始文本 → DeepSeek排版 → 创建公众号草稿 |
| POST | `/push_telegram` | Bearer TOKEN | 接收 JSON → MarkdownV2格式 → 推送到 @AgentToWest |
| 其他 | 任意 | — | 返回 `{"error":"not found"}` |

认证 Token 存储在 `.env` 的 `BEARER_TOKEN` 字段中。

### `/push_telegram` 详情

```json
// 请求
{
  "title": "文章标题",
  "excerpt": "摘要（前200字会被使用）",
  "wp_link": "http://hellobog.com/xxx",
  "wx_url": "微信原文链接（可选）",
  "mp_name": "公众号名称（默认：中本笨-BG）"
}

// 成功响应
{"ok": true, "message_id": 2}

// 认证头
Authorization: Bearer d1f551894905ad52b2a1885216ff31ad11b07c146708d664
```

Telegram Bot Token 和频道写在代码中：
- Bot: `8609798183:AAGcIIm_cSnLQRFtlYCaH9A5gaE6P86scGA`
- 频道: `@AgentToWest`

## 新增端点流程

当需要在 server.js 中新增路由时：

1. **本地写好完整文件**（用 `write_file`）
2. **SCP 上传**到服务器
3. **PM2 重启**并验证

```bash
# 1. 本地写文件（用 write_file 工具）
# 2. 上传
scp -i ~/.ssh/id_ed25519_alicloud /tmp/server.js root@47.85.62.133:/root/wx-publisher/
# 3. 重启 + 验证
ssh -i ~/.ssh/id_ed25519_alicloud root@47.85.62.133 'pm2 restart all && sleep 1 && curl -s localhost:8787/health'
```

### 代码注意事项

- 使用 `import` / `export`（ESM 模块），不是 `require()`
- MarkdownV2 模式需要转义特殊字符：`` _ * [ ] ( ) ~ ` > # + - = | { } . ! ``
- Telegram API 调用使用 Node.js 内置 `https` 模块（无需额外依赖）
- `.env` 文件包含敏感凭证，输出时会自动 redact

## PM2 常用命令

```bash
pm2 restart all          # 重启所有进程（修改代码后）
pm2 logs wx-publisher    # 查看日志
pm2 status               # 查看状态
pm2 stop all             # 停止
pm2 delete all           # 删除（需重新 start）
```

## 基础设施全景

> 📄 完整 server.js 代码模板见 `templates/server.js` — 可直接作为新增端点的基础代码。

该服务器是波总"Agentic-Capital-Workflow"全链路中的关键节点：

```
文章内容 → GitHub (bog5d/Agentic-Capital-Workflow)
              ↓ 发布
         WordPress (hellobog.com, 腾讯云 111.229.29.110)
              ↓ API 调用
    ┌─────────┼─────────┐
    ↓                   ↓
/publish              /push_telegram
(DeepSeek排版        (MarkdownV2推送
 → 公众号草稿)         → @AgentToWest)
```

关联服务器和服务：
- 腾讯云 111.229.29.110 — WordPress + 宝塔面板
- n8n — Docker 自动化平台（端口 5678）
- FRP 隧道 — 47.85.62.133:7000（⚠️ frps 是手动启动进程，非 systemd 服务，重启方式见下方）

## 故障排查

| 现象 | 可能原因 | 检查方法 |
|------|---------|---------|
| `/health` 不通 | PM2 挂了或端口被占 | `ssh root@47.85.62.133 'pm2 status'` |
| `/publish` 401 | BEARER_TOKEN 不匹配 | 检查 `.env` 和请求 Header |
| `/push_telegram` Markdown 解析错误 | 未转义特殊字符 | 使用 `escapeMd()` 函数（已在 server.js 中） |
| TG 消息发不出去 | Bot token 或频道错误 | 检查代码中硬编码的 TG_BOT_TOKEN 和 TG_CHANNEL |
| PM2 不识别 | PM2 未安装或 dump 丢失 | `pm2 list`，必要时 `pm2 start server.js --name wx-publisher` |
| frps 挂了 | 非 systemd 服务，进程被杀后需手动重启 | `ps aux \| grep frps`，若不存在则 `cd /root/frp_*/ && nohup ./frps -c ./frps.toml > /dev/null 2>&1 &` |
| frps token 泄露 | 需更新 token 并重启 | `sed -i "s/auth.token = .*/auth.token = '<NEW>'/" frps.toml && kill $(pgrep frps) && sleep 1 && nohup ./frps -c ./frps.toml > /dev/null 2>&1 &` |

## 🛡️ 安全加固

### 已知攻击面（当前状态：脆弱）

| 风险点 | 现状 | 风险等级 |
|--------|------|----------|
| SSH 密码登录 | `PermitRootLogin yes` + `PasswordAuthentication yes` | 🔴 致命 |
| Root 密码强度 | 弱密码，可能已泄露 | 🔴 致命 |
| FRP Token | `Cangjie2026` 明文，7000端口公网暴露 | 🔴 高 |
| 公网端口 | 22, 7000, 6000 全开 | 🟡 中 |
| 暴力破解 | 持续遭受多IP扫描 | 🔴 高 |

### ⛔ 致命陷阱：阿里云 Instance Connect 后门

**阿里云 ECS 默认启用了 `ecs_config_instance_connect`**，这是一个动态 SSH 密钥注入机制：

```bash
# sshd_config 中的默认配置（打开后门）
AuthorizedKeysCommand /usr/bin/ecs_config_instance_connect --uid %U
AuthorizedKeysCommandUser nobody
```

这意味着：**任何能访问阿里云控制台（或 Instance Connect API）的人，可以随时注入临时公钥登录 root**，完全绕过 `authorized_keys` 和 `PasswordAuthentication no`。

攻击者正是利用这个机制，在密码被改、密钥被换后仍然反复登录。日志显示：
```
Accepted publickey for root from 89.208.247.51: ED25519 SHA256:5NSEd7h6KU...
```
即使 authorized_keys 只有我们的公钥，攻击者仍能通过 Instance Connect 动态注入自己的密钥。

**加固时第一步必须禁用它**（在其他步骤之前）：

```bash
# 先禁掉 Instance Connect（否则后续所有加固都是徒劳）
ssh root@47.85.62.133 \
  "sed -i 's/^AuthorizedKeysCommand /#AuthorizedKeysCommand /' /etc/ssh/sshd_config && \
   sed -i 's/^AuthorizedKeysCommandUser /#AuthorizedKeysCommandUser /' /etc/ssh/sshd_config && \
   systemctl restart sshd"
```

### 加固清单（优先从高到低，严格按顺序）

```bash
# ⚠️ 关键顺序：先断后门再加固，否则攻击者始终在线

# 0. 先检查攻击者是否在线
ssh root@47.85.62.133 'ss -tnp | grep ESTAB | grep -v "127.0.0.1\|::1\|100.100"'
# 如果看到陌生 IP — 执行下面的封锁流程

# 1. 立刻禁用 Instance Connect 后门（最关键一步）
ssh root@47.85.62.133 \
  "sed -i 's/^AuthorizedKeysCommand /#AuthorizedKeysCommand /' /etc/ssh/sshd_config && \
   sed -i 's/^AuthorizedKeysCommandUser /#AuthorizedKeysCommandUser /' /etc/ssh/sshd_config && \
   systemctl restart sshd"

# 2. 上传 SSH 公钥（先在本地生成 ed25519 密钥对）
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_alicloud -N "" -C "hermes@alicloud"
sshpass -p '<current-pass>' ssh root@47.85.62.133 \
  "mkdir -p ~/.ssh && echo '<PUBKEY>' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# 3. 改 root 密码
sshpass -p '<current-pass>' ssh root@47.85.62.133 "echo 'root:<NEW_PASS>' | chpasswd"

# 4. 关闭 SSH 密码登录 + 禁止 root 密码登录
ssh -i ~/.ssh/id_ed25519_alicloud root@47.85.62.133 \
  "sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && \
   sed -i 's/^PermitRootLogin yes/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config && \
   systemctl reload sshd"

# 5. 更新 FRP token — NOTE: frps 不是 systemd 服务，需手动重启
ssh root@47.85.62.133 \
  "cd /root/frp_*/ && \
   sed -i \"s/auth.token = .*/auth.token = '$(openssl rand -hex 16)'/\" frps.toml && \
   kill \$(pgrep frps) && sleep 1 && \
   nohup ./frps -c ./frps.toml > /dev/null 2>&1 &"

# 6. 防火墙（⚠️ 见下方 iptables 陷阱，优先用 firewall-cmd）
ssh root@47.85.62.133 \
  "firewall-cmd --permanent --remove-service=ssh && \
   firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=YOUR_IP/32 port port=22 protocol=tcp accept' && \
   firewall-cmd --reload"
```

### ⛔ 致命陷阱：iptables 锁死服务器

**严禁在 SSH 会话中同时做 iptables DROP + sshd restart！** 这会导致服务器完全失联：

```bash
# ❌ 致命 — 这样做会把自己锁在外面：
iptables -I INPUT -s 89.208.247.51 -j DROP
systemctl restart sshd
# → 连接断开，此后所有 IP 的 SSH/HTTP/FRP 全部超时，只能 VNC 救援

# ✅ 正确方式（二选一）：
# 方案A: 用 firewall-cmd（更安全，重启后持久化）
firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=89.208.247.51/32 drop'
firewall-cmd --reload

# 方案B: 必须用 iptables 时，用 -A（追加）不用 -I（插入），只重启 reload 不 restart
iptables -A INPUT -s 89.208.247.51 -j DROP  # -A 追加到底部，不影响已有规则
iptables-save > /etc/sysconfig/iptables
systemctl reload sshd  # reload 不断已有连接，restart 会断！
```

**如果已经锁死**：只能通过阿里云控制台 → VNC 连接 → 执行恢复命令：

```bash
# 先用 nftables（Alibaba Cloud Linux 默认防火墙后端）
nft flush ruleset
```

```bash
# 再清 iptables 遗留
iptables -F INPUT
```

```bash
iptables -P INPUT ACCEPT
```

```bash
systemctl restart sshd
```

### ⛔ 自身 IP 陷阱

**排查可疑连接时，先确认当前客户端的公网 IP，避免自己封自己：**

```bash
# 在自己机器上查当前公网 IP
curl -s ifconfig.me
```

**注意：** 47.85.62.133 所在网络出口可能与你的本地 IP 相同（FRP/VPN 等导致）。曾发生将 `89.208.247.51` 判定为攻击者，反复封禁导致 SSH 自锁的教训——实际上那是波总 macOS 的公网出口 IP。

**判定攻击者 IP 的正确方法：**
- 断开自己的所有 SSH 会话，等待 10 秒
- 再查 `ss -tnp | grep ESTAB` — 此时看到的陌生 IP 才是真正攻击者
- 对比 `curl ifconfig.me` 的输出来排除自己

### 应急响应速查

当收到阿里云安全告警时，按以下顺序排查：

```bash
# Phase 1: 进程侦察
ps aux --sort=-%cpu | head -20          # 高CPU进程
ss -tlnp                                # 监听端口
ss -tnp | grep ESTAB                    # 活跃连接（找攻击者IP）
last -n 10                              # 近期登录
lastb | head -10                        # 失败登录（暴力破解痕迹）

# Phase 2: 定时任务
crontab -l                              # root crontab
ls -la /etc/cron.d/                     # 系统 cron
find /etc/systemd -name "*.service" -mtime -30  # 近期新增服务

# Phase 3: 恶意文件定位
find /usr/local/bin -type f -mtime -30  # 近期新增二进制
find /tmp /var/tmp /dev/shm -type f     # 临时目录可疑文件
cat /proc/<PID>/cmdline | tr '\0' ' '   # 查进程完整命令
ls -la /proc/<PID>/cwd                  # 查进程工作目录

# Phase 4: 清除
kill -9 <PID>                           # 杀进程
systemctl stop <service> && systemctl disable <service>  # 停服务
rm -f <malicious-file>                  # 删文件
systemctl daemon-reload                 # 重载 systemd
```

### 常见恶意软件伪装模式（本服务器曾发现）

> 📄 具体 IOC 见 `references/malware-ioc-20260604.md`

- **systemd.service** — 伪装的挖矿守护（`Restart=always`），二进制在 `/usr/local/bin/systemd`
- **observed.service** — 伪装的"系统观测服务"，实际是竞品清理守护
- **free_proc.sh** — 杀 CPU >200% 的非 self 进程，防止其他挖矿竞争资源
- CPU 160%+ 进程名 `systemd` 连接 `xmr.kryptex.network:8029` → XMR 挖矿

### 常驻合法服务（勿杀）

| 服务 | PID 模式 | 用途 |
|------|----------|------|
| `moltbot-gateway` | `/opt/moltbot/dist/index.js` (admin 用户) | 波总 AI Gateway |
| `wx-publisher` | `node /root/wx-publisher/server.js` (PM2) | 微信发布中继 |
| `AliYunDun` | `/usr/local/aegis/` | 阿里云盾 |
| `frps` | `/root/frp_*/frps` | FRP 隧道服务 |
| `node` / `docker-proxy` | Docker 容器端口映射 | n8n 等容器 |
