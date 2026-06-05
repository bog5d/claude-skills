# pub2gg 全链路验证记录 — 2026-06-05

## 端到端实测结果

```
你的文章 ──→ 中继 47.85.62.133:8787
                  │
        ┌─────────┼─────────┐
        ▼                   ▼
   /publish            /push_telegram
   DeepSeek排版        MarkdownV2推送
   + Unsplash配图       → @AgentToWest
   + 公众号草稿
```

## 实测日志

```
[pub] 2026-06-05T08:34:49.637Z 收到文章 91 字
[pub] DeepSeek 排版完成: AI Agent的下一个十年
[wechat] 发现 2 个图片占位符，开始上传...
[wechat] 图片已注入: robot hand typing on laptop keyboard → mmbiz.qpic.cn...
[wechat] 图片已注入: AI agent interface with task list → mmbiz.qpic.cn...
[pub] 草稿已创建 media_id: bQqYgPWs61_ROOqZBKIhz6WdY0rdg...
[tg] 2026-06-05T08:36:06.813Z 推送TG: AI Agent的下一个十年
[tg] 推送成功 msg_id: 8
```

## 基础设施状态

| 组件 | 详情 |
|------|------|
| 中继服务器 | 47.85.62.133, Alibaba Cloud Linux |
| PM2 进程 | wx-publisher, PID 1788339, 端口 8787 |
| FRP 服务端 | frps :7000, token: f48653aaa631f8ce4814c3fb07a39955 |
| FRP 客户端 | macOS frpc, PID 1695 |
| 公众号 AppID | wx37940d296d26c91c |
| TG Bot | 8609798183 → @AgentToWest |
| Bear Token | d1f551894905ad52b2a1885216ff31ad11b07c146708d664 |
| DeepSeek Key | sk-*** (redacted, 在服务器 .env 中) |

## 已知 Bug

1. **MarkdownV2 `.` 未转义**: `escapeMd()` 缺少 `.` 和 `!` → TG 推送失败 "Can't parse entities: Character '.' is reserved"
   - 临时规避：标题/excerpt 避免英文句点和感叹号
   - 根治：修复 server.js escapeMd() 添加 `.` 和 `!` 到转义集

2. **Token Shell Redact**: macOS 端 curl 时 BEARER_TOKEN 被 redact → 401
   - 规避：SSH 到服务器 + source .env + curl localhost
