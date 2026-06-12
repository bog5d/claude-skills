---
name: wordpress-site-management
description: "WordPress站点管理 via REST API: 文章/页面/媒体/分类/标签/插件/设置。含内容清理、SEO优化、缓存配置、站点诊断。"
category: devops
---

# WordPress Site Management via REST API

## 何时使用
- 管理 hellobog.com 或其他 WP 站点的文章、页面、分类、标签
- 清理重复/测试文章
- 安装/管理插件
- SEO 优化（标签、分类、封面图）
- 站点健康诊断
- 内容批量操作

## 认证方式

使用 Application Password（Basic Auth），不依赖 cookie/session：

```bash
WP_USER="admin"
WP_APP_PASS="应用密码（空格保留原样）"
curl -u "$WP_USER:$WP_APP_PASS" "http://hellobog.com/wp-json/wp/v2/posts"
```

应用密码中的空格是密码的一部分，不要删除或转义。

## 常用 API 端点

### 文章 (Posts)

```bash
# 列出
GET /wp-json/wp/v2/posts?per_page=20&orderby=date&order=desc&_fields=id,title,date,status

# 获取单篇
GET /wp-json/wp/v2/posts/{id}

# 创建
POST /wp-json/wp/v2/posts -d '{"title":"标题","content":"HTML内容","status":"publish","categories":[1]}'

# 更新（分类/标签/特色图片）
POST /wp-json/wp/v2/posts/{id} -d '{"categories":[19],"tags":[26,27]}'

# 永久删除（跳过回收站）
DELETE /wp-json/wp/v2/posts/{id}?force=true
```

### 分类 (Categories)

```bash
POST /wp-json/wp/v2/categories -d '{"name":"分类名","slug":"slug"}'
DELETE /wp-json/wp/v2/categories/{id}?force=true
GET /wp-json/wp/v2/categories
```

### 标签 (Tags)

```bash
# 创建（逐一调用，不支持批量）
POST /wp-json/wp/v2/tags -d '{"name":"标签名","slug":"tag-slug"}'

# 分配到文章
POST /wp-json/wp/v2/posts/{id} -d '{"tags":[8,20,21]}'
```

### 媒体 (Media)

```bash
# 上传图片（multipart form）
POST /wp-json/wp/v2/media -F "file=@/path/to/image.jpg"

# 设为特色图片
POST /wp-json/wp/v2/posts/{id} -d '{"featured_media":{media_id}}'
```

### 插件 (Plugins)

```bash
# 从官方仓库安装并激活
POST /wp-json/wp/v2/plugins -d '{"slug":"wp-super-cache","status":"active"}'

# 列出/激活/停用
GET /wp-json/wp/v2/plugins
PUT /wp-json/wp/v2/plugins/{plugin_slug} -d '{"status":"active"}'
```

### 站点信息

```bash
GET /wp-json/  # 站点名、描述、时区、命名空间
GET /wp-json/wp/v2/users/me  # 当前用户
GET /wp-json/wp/v2/settings  # 站点设置
```

## 内容清理 SOP

站内有大量测试/重复文章时：

1. 列出全部文章 → 按标题分组 → 找出重复组
2. 对比重复文章的 content 长度 → 保留原始篇（slug 无 `-2` 后缀）
3. `DELETE /posts/{id}?force=true` 删除重复
4. 建新分类 → 移动文章归入正确分类 → 删空分类
5. 批量创建标签 → 按主题分配到文章

## SEO 优化清单

- 每篇文章有分类（不能留在「未分类」）
- 每篇文章有 2-3 个标签
- 每篇文章有特色图片（1200x630，含品牌栏）
- 有 SEO 插件（SureRank SEO）
- 有缓存插件（WP Super Cache），安装后需登录 wp-admin 手动启用
- 删空分类/标签
- HTTPS 可用（检查 Cloudflare SSL 设置）

## 封面图生成

用 Pillow 批量生成 1200x630 统一风格封面：
- 深色背景 + 白色标题（双行或三行）
- 底部红色横条标注域名
- 字体：`/System/Library/Fonts/PingFang.ttc`（macOS）
- 上传后通过 `featured_media` 字段关联文章

详见 `references/cover-image-generator.py`

## 站点诊断命令

```bash
# 首页性能和大小
curl -s -o /dev/null -w "HTTP %{http_code} | %{size_download}B | %{time_total}s" http://hellobog.com/

# HTTPS 状态
curl -sk -o /dev/null -w "%{http_code}" https://hellobog.com/

# API 认证测试
curl -s -u "admin:APP_PASS" http://hellobog.com/wp-json/wp/v2/users/me
```

常见问题速查：
- HTTPS 521 → Cloudflare SSL 设为 Flexible
- 首页 >2s → 缓存未启用，装 WP Super Cache
- API 403 → 应用密码过期或权限不足

## 陷阱

- hellobog.com 的 HTTPS 不可用（Cloudflare 521），API 调用用 `http://`
- 创建文章时 content 需要 HTML，不是 Markdown
- 分类/标签参数用数字 ID，不用名称字符串
- `force=true` 才永久删除，不加只进回收站
- 不要用 cookie/session 登录 wp-admin 做简单操作——REST API 更快更稳
