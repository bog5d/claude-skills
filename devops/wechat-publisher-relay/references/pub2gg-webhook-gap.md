# pub2gg Webhook Gap — 实施计划

## 问题

WordPress (hellobog.com, 111.229.29.110) 发布文章后不会自动调用中继服务器 (47.85.62.133:8787) 的 /publish 和 /push_telegram 端点。

## 推荐方案：Mac Mini Cron 轮询

不动 WordPress，在 Mac Mini 上加 cron job 每 5 分钟扫描 hellobog.com 最新文章。

### 伪代码逻辑

1. GET hellobog.com/wp-json/wp/v2/posts?per_page=5&orderby=date&order=desc
2. 与上次记录的 latest_post_id 比较
3. 新文章 -> 提取 title + content (strip HTML tags) + excerpt
4. POST /publish   -> content raw text -> 公众号草稿
5. POST /push_telegram -> {title, excerpt, wp_link} -> Telegram @AgentToWest
6. 更新 latest_post_id

### 关键参数

- WP API: hellobog.com/wp-json/wp/v2/posts (HTTP, 非 HTTPS)
- WP 认证: admin + Application Password
- Relay: 47.85.62.133:8787, Bearer Token
- Cron 间隔: 5 分钟
- 状态文件: /tmp/pub2gg_last_post_id

### 注意

- WP REST API 返回 content 是 HTML，需 strip tags 后传给 /publish
- /publish 需要 raw text，不是 HTML
- 首次运行（无状态文件）-> 只处理最新一篇，不回溯历史
