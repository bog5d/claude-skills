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
| SSH | `root / Wb88517aliyundl-` |
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
sshpass -p 'Wb88517aliyundl-' ssh -o StrictHostKeyChecking=no root@47.85.62.133
```

⚠️ Hermes 运行在 macOS 上，无法使用 `read_file` 等本地工具读取远程文件。所有远程操作必须通过 `terminal` 执行 SSH 命令。

### 常用 SSH 操作模式

```bash
# 读远程文件
sshpass -p 'Wb88517aliyundl-' ssh root@47.85.62.133 'cat /root/wx-publisher/server.js'

# 上传本地文件
sshpass -p 'Wb88517aliyundl-' scp /local/file.js root@47.85.62.133:/root/wx-publisher/

# 执行远程命令
sshpass -p 'Wb88517aliyundl-' ssh root@47.85.62.133 'pm2 restart all && sleep 1 && curl -s localhost:8787/health'
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
sshpass -p 'Wb88517aliyundl-' scp /tmp/server.js root@47.85.62.133:/root/wx-publisher/server.js
# 3. 重启
sshpass -p 'Wb88517aliyundl-' ssh root@47.85.62.133 'pm2 restart all'
# 4. 验证
curl -s http://47.85.62.133:8787/health
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
- FRP 隧道 — 47.85.62.133:7000（token: Cangjie2026）

## 故障排查

| 现象 | 可能原因 | 检查方法 |
|------|---------|---------|
| `/health` 不通 | PM2 挂了或端口被占 | `ssh root@47.85.62.133 'pm2 status'` |
| `/publish` 401 | BEARER_TOKEN 不匹配 | 检查 `.env` 和请求 Header |
| `/push_telegram` Markdown 解析错误 | 未转义特殊字符 | 使用 `escapeMd()` 函数（已在 server.js 中） |
| TG 消息发不出去 | Bot token 或频道错误 | 检查代码中硬编码的 TG_BOT_TOKEN 和 TG_CHANNEL |
| PM2 不识别 | PM2 未安装或 dump 丢失 | `pm2 list`，必要时 `pm2 start server.js --name wx-publisher` |
