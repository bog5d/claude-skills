---
name: wordpress-remote-ops
description: Remote WordPress administration via REST API — plugin install, app password generation, content publishing. Use when you need to manage a WordPress site without SSH, cPanel, or backend panel access.
---

# WordPress Remote Operations via REST API

## When to use

WordPress 管理任务，但无法 SSH 或登录宝塔面板时。场景包括：

- 开启应用密码（Application Passwords）
- 安装/激活插件
- 发布/编辑文章
- 调试 REST API 端点
- 在 n8n/Make.com 中编排 WP 操作

## Prerequisites

需要一组有效的 WordPress 管理员凭证（用户名 + 密码），以及站点的 `wp-admin` 和 `wp-json` 可访问。

## 核心技巧：curl 登录 + Nonce 获取

WordPress REST API 的写操作需要 `X-WP-Nonce`，但 Nonce 只有登录后才能获取。标准做法：

### Step 1: 登录获取 Cookie 和 Nonce

```bash
# 登录 → 获取 session cookie
COOKIE_JAR=$(mktemp)
LOGIN_RESP=$(curl -s -c "$COOKIE_JAR" -X POST "https://SITE.com/wp-login.php" \
  -d "log=ADMIN_USER&pwd=ADMIN_PASS&redirect_to=%2Fwp-admin%2F&testcookie=1")

# 用 cookie 访问后台 → 从页面提取 nonce
NONCE=$(curl -s -b "$COOKIE_JAR" "https://SITE.com/wp-admin/admin-ajax.php?action=rest-nonce" | tr -d '\n')
```

### Step 2: 使用 Nonce 调用 REST API

```bash
curl -s -X POST "https://SITE.com/wp-json/wp/v2/..." \
  -b "$COOKIE_JAR" \
  -H "X-WP-Nonce: $NONCE" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## 关键操作

### 1. 启用应用密码（Application Passwords）

如果 WP 站点未开启应用密码，需先启用（两种等效方式）：

**方式 A：通过插件上传（纯 API，无需文件系统访问）**

```bash
# 构造一个迷你插件 ZIP（纯内存，不落盘）
PLUGIN_ZIP="/tmp/enable_app_passwords.zip"
python3 -c "
import zipfile, io
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as z:
    z.writestr('enable-app-passwords/enable-app-passwords.php',
        '<?php\n/* Plugin Name: Enable Application Passwords */\nadd_filter(\"wp_is_application_passwords_available\", \"__return_true\");\n')
with open('$PLUGIN_ZIP', 'wb') as f:
    f.write(buf.getvalue())
"

# 通过 WP Admin 上传插件（需要 nonce + cookie）
PLUGIN_NONCE=$(curl -s -b "$COOKIE_JAR" "https://SITE.com/wp-admin/plugin-install.php" | grep -oP '"_wpnonce"\s*value="[^"]*"' | head -1 | grep -oP 'value="\K[^"]*')

curl -s -b "$COOKIE_JAR" -X POST "https://SITE.com/wp-admin/update.php?action=upload-plugin" \
  -F "_wpnonce=$PLUGIN_NONCE" \
  -F "pluginzip=@$PLUGIN_ZIP" \
  -F "install-plugin-submit=Install+Now"

# 激活插件
curl -s -b "$COOKIE_JAR" -X POST "https://SITE.com/wp-admin/plugins.php" \
  -d "action=activate&plugin=enable-app-passwords%2Fenable-app-passwords.php&_wpnonce=<activate_nonce>"
```

⚠️ **Pitfall**: WordPress 插件上传接口的 `_wpnonce` 与 REST API 的 `X-WP-Nonce` 不同，需要从 `plugin-install.php` 页面单独提取。

**方式 B：创建 mu-plugins 文件（需要文件系统访问）**

```bash
# 在 wp-content/mu-plugins/ 下创建
mkdir -p /www/wwwroot/SITE/wp-content/mu-plugins/
cat > /www/wwwroot/SITE/wp-content/mu-plugins/enable-app-passwords.php << 'PHP'
<?php
add_filter( 'wp_is_application_passwords_available', '__return_true' );
PHP
```

### 2. 生成应用密码

```bash
APP_PASS=$(curl -s -X POST "https://SITE.com/wp-json/wp/v2/users/me/application-passwords" \
  -u "ADMIN_USER:ADMIN_PASS" \
  -H "Content-Type: application/json" \
  -d '{"name":"app-name","app_id":"00000000-0000-0000-0000-000000000000"}')
```

⚠️ 生成前必须已启用应用密码功能（见上一步）。返回的密码**仅显示一次**。

### 3. 验证应用密码

```bash
curl -s -u "ADMIN_USER:APP_PASSWORD" "https://SITE.com/wp-json/wp/v2/users/me"
# 成功 → 返回 {"id":1,"name":"admin","roles":["administrator"],...}
```

### 4. 发布文章（JSON）

```bash
curl -s -X POST "https://SITE.com/wp-json/wp/v2/posts" \
  -u "ADMIN_USER:APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Post Title",
    "content": "<p>HTML content</p>",
    "status": "publish"
  }'
```

### 5. 发布文章（Markdown → HTML）

WordPress REST API 原生接受 HTML。如需发送 Markdown，需先转换：

```bash
pandoc input.md -f markdown -t html -o - | python3 -c "
import sys, json
content = sys.stdin.read()
payload = json.dumps({'title': 'Title', 'content': content, 'status': 'publish'})
print(payload)
" > /tmp/wp_post.json

curl -s -X POST "https://SITE.com/wp-json/wp/v2/posts" \
  -u "ADMIN_USER:APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d @/tmp/wp_post.json
```

## 常见坑

| 坑 | 现象 | 解法 |
|---|------|------|
| 未启用应用密码 | 生成接口 404/disabled | 先装插件或创建 mu-plugins 文件 |
| Cookie 过期 | Nonce 失效、401 | 重新登录获取新 cookie |
| 宝塔面板有域名绑定 | 返回 404 | 用正确的 Host header 访问 |
| SSL 证书问题 | curl 报 SSL 错误 | 加 `-k` 临时跳过（仅调试） |
| 旧 Office 格式上传被拒 | "Unsupported document type" | 加载 `media-file-delivery` 技能 |

## 相关技能

- `media-file-delivery` — Hermes 文件发送/接收的 MIME 和路径白名单修复
- `telegram-file-delivery` — Telegram Bot API curl fallback 方案
