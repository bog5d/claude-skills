---
name: wordpress-management
description: Manage WordPress sites via REST API with application passwords — posts, pages, media, plugins, settings, site health. Covers auth setup, capability matrix, SSH vs API tradeoffs, and Cloudflare pitfalls.
category: productivity
---

# WordPress 管理（REST API + 应用密码）

用 WordPress REST API 管理博客站点。通过应用密码（Application Password）进行 Bearer Auth，无需浏览器或 SSH。

## 适用场景

- 发布/编辑/删除文章和页面
- 管理媒体库、分类、标签
- 查看/启停/安装插件
- 站点健康检查和设置修改
- n8n / Make.com / 自定义脚本对接

## 前置条件

### 1. 确保应用密码已启用

如果 WP 后台 > 用户 > 个人资料 > 没有「应用程序密码」区块，需要启用：

**方法 A（mu-plugins，推荐）**：在 `wp-content/mu-plugins/` 下创建 `enable-app-passwords.php`：
```php
<?php
add_filter( 'wp_is_application_passwords_available', '__return_true' );
```

**方法 B（插件上传，SSH 不可用时）**：通过 WP REST API 上传一个迷你插件。流程见 `references/app-password-plugin-upload.md`。

### 2. 生成应用密码

1. 访问 `wp-admin/profile.php`
2. 底部「应用程序密码」→ 输入名称 → 「添加新的应用程序密码」
3. 复制生成的密码（仅显示一次，格式：`Ab12 Cd34 Ef56 Gh78 Ij90 Kl12`）

## 认证方式

### 应用密码（推荐，用于 API）

```bash
curl -u "admin:j3dw cNtR Cqpn Y50X 78sj 0mMb" \
  "http://hellobog.com/wp-json/wp/v2/posts?per_page=5"
```

应用密码等价于登录密码，但可单独撤销。支持所有 REST API 端点。

### Cookie 认证（用于 wp-admin 操作）

```bash
# 获取登录 cookie
curl -c /tmp/wp_cookies -d "log=admin&pwd=xxx&wp-submit=Log+In" \
  "http://hellobog.com/wp-login.php"

# 带 cookie 访问后台
curl -b /tmp/wp_cookies "http://hellobog.com/wp-admin/edit.php"
```

## REST API 能力矩阵

### ✅ 可完全操作（应用密码即可）

| 端点 | 操作 | 示例 |
|------|------|------|
| `/wp/v2/posts` | CRUD | 发布文章、修改内容、删除 |
| `/wp/v2/pages` | CRUD | 页面管理 |
| `/wp/v2/media` | 上传/列表 | 图片、文件上传 |
| `/wp/v2/categories` | CRUD | 分类管理 |
| `/wp/v2/tags` | CRUD | 标签管理 |
| `/wp/v2/comments` | CRUD | 评论审核 |
| `/wp/v2/users` | 只读 | 用户列表 |
| `/wp/v2/settings` | 读写 | 站点标题、描述、时区等 |
| `/wp/v2/plugins` | 安装/启停 | 插件管理（WP 6.5+） |
| `/wp/v2/themes` | 只读 | 主题查看 |
| `/wp/v2/block-types` | 只读 | 块类型信息 |

### ⚠️ 受限（需要 SSH 或 wp-admin 页面）

| 操作 | 说明 |
|------|------|
| 主题文件直接编辑 | 需 SSH 或 wp-admin 主题编辑器 |
| Nginx/PHP/MySQL 配置 | 需 SSH |
| 数据库直接操作 | 需 SSH 或 phpMyAdmin |
| 文件系统级操作 | 需 SSH |
| 插件 .zip 上传（旧 WP） | WP 6.5 以下需 admin 页面 |

## 常见操作

### 发布文章

```bash
curl -u "admin:PASSWORD" \
  -X POST "http://SITE/wp-json/wp/v2/posts" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "文章标题",
    "content": "<!-- wp:paragraph --><p>正文</p><!-- /wp:paragraph -->",
    "status": "publish",
    "categories": [3],
    "tags": [5]
  }'
```

### 更新文章

```bash
curl -u "admin:PASSWORD" \
  -X POST "http://SITE/wp-json/wp/v2/posts/2852" \
  -H "Content-Type: application/json" \
  -d '{"title": "新标题", "status": "draft"}'
```

### 列出文章（含字段过滤）

```bash
curl -u "admin:PASSWORD" \
  "http://SITE/wp-json/wp/v2/posts?per_page=5&_fields=id,title,date,status,link"
```

### 站点健康检查

```bash
curl -u "admin:PASSWORD" \
  "http://SITE/wp-json/wp-site-health/v1/tests/background-updates"
```

### 安装插件

```bash
curl -u "admin:PASSWORD" \
  -X POST "http://SITE/wp-json/wp/v2/plugins" \
  -H "Content-Type: application/json" \
  -d '{"slug": "wp-super-cache", "status": "active"}'
```

## 站点优化清单

清理/优化 WordPress 时按此顺序：

1. **清理重复文章** — `GET /posts` → 按标题分组 → `DELETE` 重复项
2. **补全分类** — 为未分类文章创建匹配分类，清理空分类
3. **添加标签** — 每篇文章 2~3 个相关标签，利于 SEO
4. **安装缓存插件** — `POST /plugins {"slug":"wp-super-cache","status":"active"}`
5. **生成封面图** — 用 Pillow 批量生成 1200×630 特色图片 → 上传 → 设 featured_media
6. **检查 SSL** — 若 HTTPS 返回 521，去 Cloudflare SSL/TLS 设为 Flexible

## 封面图生成（Pillow）

见 `references/cover-generation.md`。核心流程：

1. Python Pillow 创建 1200×630 PNG
2. 深色背景 + 三行文字（标题 / 副标题 / 描述）
3. 底部红色条 + 域名水印
4. 上传到 WP Media → 获取 media_id → 设置 featured_media

```bash
# 上传封面并设为特色图片
MEDIA_ID=$(curl -s -X POST -u "user:pass" -F "file=@/tmp/cover.jpg" \
  "http://site.com/wp-json/wp/v2/media" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
curl -s -X POST -u "user:pass" -H "Content-Type: application/json" \
  -d "{\"featured_media\":$MEDIA_ID}" "http://site.com/wp-json/wp/v2/posts/POST_ID"
```

## 批量操作

```bash
# 通用模式：遍历文章 ID
for pid in ID1 ID2 ID3; do
  curl -s -X POST -u "user:pass" -H "Content-Type: application/json" \
    -d "{\"tags\":[TAG_IDS]}" "http://site.com/wp-json/wp/v2/posts/$pid" | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(f'#{d[\"id\"]} OK')"
done
```

## 常见问题

### Cloudflare 521 / HTTPS 不可用

若 HTTPS 返回 Cloudflare 521（源站不响应 443），用 HTTP：
```bash
curl ... "http://hellobog.com/wp-json/..."  # 注意 http://
```

### 应用密码提示 "未授权"

检查 `.htaccess` 或 Nginx 配置，确保 Authorization header 不被 strip：
```nginx
# Nginx 需添加
proxy_set_header Authorization $http_authorization;
```

### 文章内容格式

WP REST API 接受 HTML 或 Gutenberg block 格式。发布文章时 `content` 字段应包含 Gutenberg 块标记（`<!-- wp:paragraph -->` 等）或纯 HTML（WordPress 会自动转换）。

## 记忆调取

此用户的 WordPress 凭证已存储在 mem0 中。需要时调用 `mem0_search` 获取：
- WP 后台密码
- 应用密码（pub2gg）
- 服务器 IP

### Cloudflare HTTPS 521

修改 Cloudflare SSL/TLS 为 **Flexible** 模式（面板 → hellobog.com → SSL/TLS → 概述）。

### Shell 引号与中文

中文弯引号 `""` 在 shell 中会被解释为 ASCII 引号，导致语法错误。
在 curl `-d` 中传递中文时，用单引号包裹整个 JSON，内部中文不用弯引号。

## Absorbed Skills

| Former Skill | Now In |
|-------------|--------|
| wordpress-remote-ops | §远程操作（无 SSH） |
| wordpress-site-management | §站点管理与优化 |

---

## § 远程操作（无 SSH / 无应用密码）

当无法 SSH 且应用密码不可用时，通过 Cookie + Nonce 操作。

### 核心技巧：curl 登录 + Nonce

```bash
# 1. 登录获取 cookie
COOKIE_JAR=$(mktemp)
curl -s -c "$COOKIE_JAR" -X POST "https://SITE.com/wp-login.php" \
  -d "log=ADMIN_USER&pwd=ADMIN_PASS&redirect_to=%2Fwp-admin%2F&testcookie=1"

# 2. 获取 nonce
NONCE=$(curl -s -b "$COOKIE_JAR" "https://SITE.com/wp-admin/admin-ajax.php?action=rest-nonce")

# 3. 带 nonce 调用 API
curl -s -X POST "https://SITE.com/wp-json/wp/v2/posts" \
  -b "$COOKIE_JAR" -H "X-WP-Nonce: $NONCE" \
  -H "Content-Type: application/json" \
  -d '{"title":"Title","content":"<p>Content</p>","status":"publish"}'
```

### 启用应用密码（纯 API，无 SSH）

```bash
# 构造迷你插件 ZIP
PLUGIN_ZIP="/tmp/enable_app_passwords.zip"
python3 -c "
import zipfile, io
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as z:
    z.writestr('enable-app-passwords/enable-app-passwords.php',
        '<?php\n/* Plugin Name: Enable Application Passwords */\nadd_filter(\"wp_is_application_passwords_available\", \"__return_true\");\n')
with open('$PLUGIN_ZIP', 'wb') as f: f.write(buf.getvalue())
"
# Upload via WP Admin
curl -s -b "$COOKIE_JAR" -X POST "https://SITE.com/wp-admin/update.php?action=upload-plugin" \
  -F "_wpnonce=$NONCE" -F "pluginzip=@$PLUGIN_ZIP" -F "install-plugin-submit=Install+Now"
```

### 生成应用密码
```bash
curl -s -X POST "https://SITE.com/wp-json/wp/v2/users/me/application-passwords" \
  -u "ADMIN_USER:ADMIN_PASS" \
  -d '{"name":"app-name","app_id":"00000000-0000-0000-0000-000000000000"}'
```

---

## § 站点管理与优化（absorbed from wordpress-site-management）

### 内容清理 SOP
1. 列出全部文章 → 按标题分组 → 找出重复组
2. `DELETE /posts/{id}?force=true` 删除重复
3. 建新分类 → 移动文章 → 删空分类
4. 批量创建标签 → 按主题分配

### SEO 优化清单
- 每篇文章有分类（不能留在「未分类」）
- 每篇文章有 2-3 个标签
- 有特色图片（1200×630，含品牌栏）
- 有缓存插件（WP Super Cache）
- HTTPS 可用（检查 Cloudflare SSL 设置）

### 封面图生成（Pillow）
```bash
MEDIA_ID=$(curl -s -X POST -u "user:pass" -F "file=@/tmp/cover.jpg" \
  "http://site.com/wp-json/wp/v2/media" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
curl -s -X POST -u "user:pass" -H "Content-Type: application/json" \
  -d "{\"featured_media\":$MEDIA_ID}" "http://site.com/wp-json/wp/v2/posts/POST_ID"
```

### 站点诊断
```bash
curl -s -o /dev/null -w "HTTP %{http_code} | %{size_download}B | %{time_total}s" http://hellobog.com/
```
常见问题：HTTPS 521 → Cloudflare SSL 设为 Flexible；首页 >2s → 缓存未启用；API 403 → 应用密码过期。

---

- `references/app-password-plugin-upload.md` — 无 SSH 时通过插件上传启用应用密码
- `references/relay-telegram-integration.md` — WordPress → 阿里云中继 → Telegram 推送全链路架构
- `references/cover-generation.md` — Pillow 批量生成文章封面图（1200×630），含色彩方案和字体配置
- `references/remote-ops-without-app-password.md` — Cookie + Nonce 远程管理（无应用密码时）
- `references/content-cleanup-sop.md` — 内容清理 SOP + SEO 优化清单 + 站点诊断命令

## 相关技能

- `media-file-delivery` — Hermes 文件发送白名单机制
- 如需操作中继服务器（47.85.62.133），SSH 凭证和 PM2 管理方式见 `references/relay-telegram-integration.md`
