# pub2gg Webhook Gap — 实施计划

## 问题

WordPress 发布文章后，不会自动调用中继服务器的 `/publish` 和 `/push_telegram`。
pub2gg 管道在 WordPress 与中继之间断开。

## 两个方案

### 方案A：WordPress Webhook 插件（需 WP admin 登录）

1. 装插件 "WP Webhooks" 或 "WP Webhook Automator"
2. 配 hook：`post_published` → POST 到 `http://47.85.62.133:8787/publish`
3. 把文章内容作为 raw body 发送 + Bearer auth header

阻塞：WP admin 密码已过期，无法登录装插件。

### 方案B：Mac Mini Cron 轮询（推荐，不碰 WP）

WordPress REST API **读文章不需要认证**。设置 cron job 每 N 分钟轮询新文章。

```
检测逻辑：
1. curl http://hellobog.com/wp-json/wp/v2/posts?per_page=3
2. 对比最新 post ID 与上次记录的 last_id
3. 如有新文章 → 调中继 /push_telegram → 存 GitHub
4. 更新 last_id
```

**Hermes cron 配置：**
```bash
cronjob action=create name='pub2gg-wp-poll' schedule='5m' \
  prompt='检测 hellobog.com 最新文章，如有新文推送到 TG + GitHub'
```

**实现脚本（`scripts/wp_poll.py`）：**

```python
import json, urllib.request, subprocess, os

LAST_ID_FILE = '/tmp/pub2gg_last_post_id'

# Fetch latest posts
resp = urllib.request.urlopen('http://hellobog.com/wp-json/wp/v2/posts?per_page=3')
posts = json.loads(resp.read())

if not posts:
    print("No posts found")
    exit(0)

latest_id = posts[0]['id']
last_known = 0
if os.path.exists(LAST_ID_FILE):
    with open(LAST_ID_FILE) as f:
        last_known = int(f.read().strip())

if latest_id <= last_known:
    print(f"No new posts (latest={latest_id}, last_known={last_known})")
    exit(0)

# New posts found
for post in posts:
    if post['id'] <= last_known:
        continue
    title = post['title']['rendered']
    excerpt = post['excerpt']['rendered']
    link = post['link']
    
    # Push to Telegram via relay (SSH + source .env)
    subprocess.run([
        'ssh', '-i', '/Users/mac/.ssh/id_ed25519_alicloud', 'root@47.85.62.133',
        f'source /root/wx-publisher/.env && curl -s -X POST http://localhost:8787/push_telegram '
        f'-H "Authorization: Bearer $BEARER_TOKEN" '
        f'-H "Content-Type: application/json" '
        f'-d \'{{"title":"{title}","excerpt":"{excerpt}","wp_link":"{link}","mp_name":"中本笨-BG"}}\''
    ])

# Update last known ID
with open(LAST_ID_FILE, 'w') as f:
    f.write(str(latest_id))
```

### 方案C：去中继化的本地轮询（完全不依赖阿里云）

如果要把 Telegram 推送也本地化（不用中继 `/push_telegram`）：

1. 用 hex 编码法存储 TG Bot token（见 `pub2gg-local` skill）
2. 直接调 Telegram Bot API：`https://api.telegram.org/bot{TOKEN}/sendMessage`
3. GitHub push 用 hex 编码 PAT

这样整个 pub2gg 检测+推送链路零外部依赖。
