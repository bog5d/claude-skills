# WordPress → 阿里云中继 → Telegram 推送集成

此文档描述文章发布后自动推送到 Telegram 频道的流程架构。

## 架构

```
WordPress (hellobog.com)
    │
    │ REST API (pub2gg 应用密码)
    ▼
pub2gg 脚本 (Termux / n8n)
    │
    │ POST /push_telegram
    │ Bearer: d1f551894905ad52b2a1885216ff31ad11b07c146708d664
    ▼
阿里云中继 (47.85.62.133:8787)
    │
    │ Telegram Bot API
    │ bot8609798183:AAGcIIm_cSnLQRFtlYCaH9A5gaE6P86scGA
    ▼
Telegram 频道 @AgentToWest
```

## 中继服务器

| 项目 | 详情 |
|------|------|
| IP | 47.85.62.133 |
| SSH | root / Wb88517aliyundl- |
| 服务 | PM2 `wx-publisher` |
| 目录 | /root/wx-publisher/ |
| 端口 | 8787 |

## API 端点

### POST /publish — 发布到微信公众号

```
POST http://47.85.62.133:8787/publish
Authorization: Bearer d1f551894905ad52b2a1885216ff31ad11b07c146708d664
Content-Type: text/plain

<文章正文>
```

返回：`{"ok": true, "title": "...", "media_id": "..."}`
内部流程：DeepSeek 排版 → 微信公众平台创建草稿

### POST /push_telegram — 推送到 Telegram

```
POST http://47.85.62.133:8787/push_telegram
Authorization: Bearer d1f551894905ad52b2a1885216ff31ad11b07c146708d664
Content-Type: application/json

{
  "title": "文章标题",
  "excerpt": "摘要（超过200字自动截断）",
  "wp_link": "http://hellobog.com/xxx",
  "wx_url": "微信原文链接（可选）",
  "mp_name": "中本笨-BG"
}
```

返回：`{"ok": true, "message_id": N}`

消息格式（HTML）：
```
<b>文章标题</b>

摘要内容...

阅读全文: http://hellobog.com/xxx
本文首发于微信公众号【中本笨-BG】
```

### GET /health — 健康检查

```
GET http://47.85.62.133:8787/health
```

返回：`ok`

## 服务重启

```bash
ssh root@47.85.62.133
pm2 restart all
# 或
cd /root/wx-publisher && node server.js
```

## 代码结构

```
/root/wx-publisher/
├── server.js       ← 主服务（http模块 ESM，含 /publish + /push_telegram + /health）
├── deepseek.js     ← DeepSeek AI 排版
├── wechat.js       ← 微信公众号草稿创建
├── .env            ← BEARER_TOKEN + WECHAT 凭证
├── package.json
└── node_modules/
```

## 全链路环境变量

```bash
export BOGS_PUB_TOKEN="d1f551894905ad52b2a1885216ff31ad11b07c146708d664"
export BOGS_GH_TOKEN="ghp_YOUR_TOKEN_HERE"
export BOGS_GH_REPO="bog5d/Agentic-Capital-Workflow"
export BOGS_WP_URL="http://hellobog.com"
export BOGS_WP_USER="admin"
export BOGS_WP_APPPASS="j3dw cNtR Cqpn Y50X 78sj 0mMb"
export BOGS_MP_NAME="中本笨-BG"
export BOGS_TG_TOKEN="8609798183:AAGcIIm_cSnLQRFtlYCaH9A5gaE6P86scGA"
export BOGS_TG_CHANNEL="@AgentToWest"
```

## 故障排查

### /push_telegram 返回 Markdown 解析错误

改用 HTML parse_mode（已修复）。MarkdownV2 要求严格转义所有特殊字符
（`_*[]()~>#+-=|{}.!`），而 HTML 模式只用 `<b>`/`<i>` 标签，URL 和中文内容无需转义。

### /publish 返回 401

检查 `.env` 中的 `BEARER_TOKEN` 是否与请求的 `Authorization: Bearer xxx` 一致。

### 服务进程挂了

```bash
ssh root@47.85.62.133
pm2 status          # 查看状态
pm2 logs wx-publisher --lines 20  # 查看日志
pm2 restart all     # 重启
```
