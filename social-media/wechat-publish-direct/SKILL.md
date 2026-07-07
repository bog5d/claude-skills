---
name: wechat-publish-direct
description: 波总发文章 → Hermes全自动排版+配图+创建公众号草稿。走 Clash 系统代理（不走阿里云中继/SOCKS5）。
category: social-media
---

# 微信公众号直接发布

**架构**：Mac Mini → Clash Verge（节点选择） → 微信 API
- 不需要 SOCKS5 隧道
- 不需要阿里云中继
- 不需要 raw socket 绕过系统代理

## 凭证

凭证存于 `~/.hermes/profiles/her-m2/.env`：

```ini
WECHAT_APPID=wx37940d296d26c91c
WECHAT_SECRET=85c02f63a114b67277ab39eb13ae8d19
DEEPSEEK_API_KEY=sk-096aff30...
```

**写入方式**：用 `write_file` 直接写入（不要用 `skill_manage action=write_file`，有工具验证 bug）。

**验证**：运行 `python3 publish_article.py --help` 确认不报 **WECHAT_SECRET not available**。

## 🔧 预检清单（每次发布前执行）

### 1. Clash 规则是否生效

```bash
grep 'api.weixin.qq.com' ~/Library/Application\ Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml
```
应返回 `DOMAIN,api.weixin.qq.com,节点选择`（非 DIRECT）。

若为 DIRECT → 修改：
```bash
patch ~/Library/Application\ Support/.../clash-verge.yaml <<'EOF'
--- a/clash-verge.yaml
+++ b/clash-verge.yaml
@@ -1 +1 @@
-- DOMAIN,api.weixin.qq.com,DIRECT
+- DOMAIN,api.weixin.qq.com,节点选择
EOF
```
然后重启 Clash 核心：
```bash
curl -s -X PUT --unix-socket /tmp/verge/verge-mihomo.sock \
  http://localhost/configs?force=true \
  -H "Content-Type: application/json" \
  -d '{"path": ""}'
```

### 2. .env 凭证完整性

```bash
grep -E 'WECHAT_SECRET|DEEPSEEK_API_KEY' /Users/mac/.hermes/profiles/her-m2/.env | grep -v '^\*\*\*'
```
检查两项均有 20+ 字符的值（非 `***`）。

### 3. 微信 API 连通性

```bash
curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx37940d296d26c91c&secret=XXXXXXX" \
  --connect-timeout 5 | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'access_token' in d else d)"
```
应返回 `OK`。若返回 40164 IP 白名单错误 → 把 Clash 代理节点出口 IP（查 `curl -s https://api.ip.sb/ip`）加到微信后台 CDN → 基本配置 → IP 白名单。30-60 分钟后生效。

**铁律**：任一项失败 → 不要运行发布脚本，先修前置条件。

## 📋 三层管线概览

```
波总文章 → Hermes 意图/参数层（只提取 title/digest/seeds/author）
  → 确定性发布引擎（Markdown→HTML、解析结构、计算插入点）
  → 下载 picsum 图片 + media/uploadimg 上传 → 微信 CDN URL
  → 插入 <img src="微信CDN URL"> 到正文
  → 封面图双重上传（material/add_material → media_id + uploadimg → CDN URL）
  → 查重 → draft/add 或 draft/update
  → 返回草稿 media_id
```

## 📝 完整流程

### 1. 接收文章
波总发送 MD 或纯文字 → 保存到 `/tmp/article_raw.txt`。

### 2. 意图与参数
Hermes 只负责判断这是公众号发布请求，并填充结构化参数：
- `article`
- `title`
- `digest`
- `author`
- `cover_seed`
- `body_seeds`

默认不让 AI 生成最终 HTML。`publish_article.py` 会用确定性 Markdown 渲染器生成微信 HTML。

DeepSeek 仅保留为兼容模式：显式传 `--layout-provider deepseek` 时才使用。

### 3. 配图
- **频率**：每 400-600 字配 1 张图。4000 字 ≈ 6-8 张
- 封面图：1 张，描述整体氛围
- 正文配图：按 `[IMAGE:keywords]` 占位符或按 500 字间距插入
- 图片来源：picsum.photos（seed 机制确保可复现）
- **正文图片走 `media/uploadimg`**（不占用素材库 10 万限制，返回微信 CDN URL）
- **封面图走 `material/add_material`**（返回 media_id 给 thumb_media_id）

### 4. 创建草稿
POST `cgi-bin/draft/add` → 返回 media_id → 波总在后台确认群发。

**自动查重**：先调 `draft/batchget` 检查同名草稿，存在则更新（`draft/update`），避免重复。

## ⚠️ 关键限制

### 标题：64 字节硬限制
- **不是字符数，是 UTF-8 字节数！** `len(title.encode())` 才是真实长度
- 中文 1 字 = 3 字节，保守截断到 **55 字节**
- 书名号《》、引号""、破折号——都各占 3 字节
- 失败错误码 45003

### 摘要：120 字节硬限制
- 保守截断到 115 字节
- **必须提炼金句**，禁用第一句话凑数
- 失败错误码 45004

### 封面图（thumb_media_id）：必填
- 不传就报 40007
- 用 `material/add_material`（永久素材）上传获取 media_id
- jpg/png 格式，1MB 以下

### 正文图片：必须用 `media/uploadimg`
- ⚠️ **不能用 `data-uimg`** 属性——那是微信编辑器前端特性，对 API 创建的草稿无效
- 必须通过 `media/uploadimg` 上传，返回 `http://mmbiz.qpic.cn/xxxx` 格式的 URL
- 直接在 `<img src="微信CDN URL">` 中使用
- 仅支持 jpg/png，1MB 以下
- 错误码 40005（格式不对）、40009（太大）

## 🌐 网络架构说明

### 以前的问题
本机宽带是**动态 IP**（C-G NAT / ISP 轮换），微信 IP 白名单只能加单个 IP，几分钟一变跟不上。之前用 SSH SOCKS5 隧道 → 阿里云固定 IP 做出口。

### 现在的方案
Mac Mini 开着 **Clash Verge**（系统代理 `127.0.0.1:7897`）。关键改造：

1. **改 Clash 规则**：`api.weixin.qq.com` 从 DIRECT → **节点选择**（走代理节点）
2. **代理节点有固定 IP** → 加一次微信白名单永久有效
3. **删掉 raw socket 代码**：所有 HTTP 调用用 `urllib.request`（自动走系统代理）
4. **删掉 `--socks5` 参数**：不再需要

### Clash 规则位置
```yaml
# ~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml
rules:
  - DOMAIN,api.weixin.qq.com,节点选择
```

### 查代理节点出口 IP
```bash
export https_proxy=http://127.0.0.1:7897
curl -s https://api.ip.sb/ip
```
当前节点 **CDN-无敌复活节点** → `89.208.247.51`（已在微信白名单）。

## 🚀 执行

`publish_article.py` 支持两种输入模式，**自动检测切换**：

### 模式一：Markdown 输入（默认）

```bash
cd ~/.hermes/profiles/her-m2/skills/social-media/wechat-publish-direct/scripts

python3 publish_article.py \
  --article /tmp/article.md \
  --cover-seed lantern \
  --body-seeds road,night,watermelon \
  --author "中本笨-BG" \
  --title "文章标题" \
  --digest "摘要" \
  --output /tmp/final.html
```

走确定性 Markdown 渲染管线：`markdown_to_wechat_html()` → 解析结构 → 计算插入点 → 下载上传图片 → 创建草稿。

### 模式二：HTML 直通（自动检测）

当输入文件以 `<!DOCTYPE` 或 `<html` 开头时，**自动切换为直通模式**：
- 提取 `<body>` 内容
- `sanitize_html()` 清洗异常 Unicode
- **跳过 Markdown 渲染**（绕过 `render_inline_markdown` → `html_lib.escape` 陷阱）
- 上传封面图 → 剥离 picsum 外链图片 → 创建草稿

典型使用场景：先用 `quality_layout.py` 排版 → 再用 `image_replace.py` 替换占位图 → 最后 `publish_article.py` 发布。

**不传 `--socks5`**（已移除）。

### 本地干跑（不触发微信）

收到文章后，优先用干跑验证结构：

```bash
python3 publish_article.py \
  --article /tmp/article.md \
  --cover-seed lantern \
  --body-seeds road,night,watermelon \
  --dry-run \
  --output /tmp/final.html
```

干跑会执行：参数归一 → 确定性排版 → 插图点计算 → 图片标签插入 → CDN URL 替换校验。不会下载图片、上传微信、创建草稿。

## ❓ 常见错误码速查

| 错误码 | 含义 | 解决 |
|--------|------|------|
| 402 | DeepSeek API 余额不足 | 充值或换 provider |
| 401 | API key 无效/不完整 | 检查 key 是否被 redact |
| 45003 | 标题超过 64 字节 | 截断到 55 字节 |
| 45004 | 摘要超过 120 字节 | 截断到 115 字节 |
| 40164 | IP 不在白名单 | 检查 Clash 规则（是否 DIRECT）→ 确认代理节点 IP 已加白名单 |
| 41005 | media data missing | `download_image()` 返回空了 → 检查 picsum 是否通 |
| 40005 | media/uploadimg 无效格式 | 仅 jpg/png |
| 40009 | media/uploadimg 太大 | 1MB 以下 |
| 40007 | thumb_media_id 缺失 | 封面图上传失败 |

## 🔧 排障速查

### 草稿显示 HTML 源代码而非渲染

**症状**：公众号草稿箱显示 `&lt;div class="wechat-article"&gt;...` 而不是正常排版。

**根因**：输入被 `render_inline_markdown()` → `html_lib.escape()` 全量 HTML 转义。

**修复**：
1. 确认输入是 Markdown（`.md`）而非完整 HTML（`.html`）
2. 如果是已排版 HTML，走直通模式：`publish_article.py` 检测到 `<!DOCTYPE`/`<html` 开头自动切换
3. 直通模式提取 `<body>` 内容，跳过 `render_inline_markdown`

**验证**：检查日志 `[STEP 0] 检测到已排版 HTML → 直通模式` 是否出现。

### cross-profile 文件修改静默失败

**症状**：`patch` 工具对 `~/.hermes/profiles/her-m2/...` 路径返回 `success` 但文件未修改。

**根因**：her-m2 profile 的 soft guard 拦截了 `patch` 写入。

**修复**：合并到主 skills 目录或显式传 `cross_profile=True`。skill_manage 不受影响。

## 📁 参考资料

- `scripts/publish_article.py` — 固化程序
- `references/40007-debug.md` — 封面图缺失排查
- `references/40066-upload-debug.md` — 素材上传 40066 错误
- `references/publish-article-script.md` — 脚本用法文档
- `references/publish_flow.md` — 发布流程
- `references/bug-diagnosis-prd-2026-06-18.md` — Bug 诊断历史
- `references/media-uploadimg-fix-2026-06-26.md` — draft/add 正文图片架构修复记录

**已废弃（旧 SOCKS5 架构，保留仅供回溯）**：
- ~~references/socks5-tunnel-setup.md~~
- ~~references/macos-proxy-bypass.md~~

## ✅ 验证状态 (2026-07-07 实测更新)

| 组件 | 状态 | 备注 |
|------|------|------|
| DeepSeek 排版 | 🟢 正常 | MD→HTML，无图片 |
| 默认排版 | 🟢 正常 | 确定性 Markdown→HTML，不依赖 AI |
| HTML 直通模式 | 🟢 正常 | 输入已排版 HTML → 提取 body → 跳过 render_inline_markdown |
| 正文图片 | 🟢 正确 | `media/uploadimg` → 微信 CDN URL → `<img src>` |
| 封面图 | 🟢 正确 | `material/add_material` → `thumb_media_id` |
| 草稿查重 | 🟢 正常 | `draft/batchget` → update 或 add |
| `--output` 写盘 | 🟢 正常 | 返回完整 HTML |
| Clash 代理 | 🟢 配置完毕 | `api.weixin.qq.com → 节点选择` |
| 微信 API 连通性 | 🟢 通过 | 经 Clash 代理节点，access_token 拿到 |
| draft/update 降级 | 🟢 正常 | 47001 错误自动 fallback 创建新草稿 |
| 异常字符清洗 | 🟢 正常 | sanitize_html() strip U+FFFC/U+FFFD/零宽字符 |
| 离线干跑 | 🟢 通过 | `--dry-run --output /tmp/final.html` 可验证主链路，不触发微信 |

## 🚫 已知 Bug 历史（全部已修复）

| Bug | 根因 | 修复时间 |
|-----|------|----------|
| #1 图片不显示 | `data-uimg` 对 API 无效，应改用 `media/uploadimg` CDN URL | 2026-06-26 |
| #2 草稿重复提交 | 无查重逻辑 | 之前修复 |
| #3 HTML 不写盘 | `--output` 空实现 | 之前修复 |
| #4 DeepSeek JSON 崩溃 | raw socket 不支持 chunked encoding | 2026-06-26 |
| #5 图片 41005 | picsum 302 重定向没跟 | 2026-06-26 |
| #6 配图 caption 跑偏 | quality_layout.py 硬编码农村关键词；默认改为 tech 主题 + 支持 --images 外置 JSON | 2026-07-07 |
| #7 表格渲染失败 | 缺少 Markdown 表格解析 | 2026-07-07 |
| #8 draft/update 47001 | API 格式错误阻塞；更新失败自动 fallback 到创建新草稿 | 2026-07-07 |
| #9 异常 Unicode 漏入草稿 | 无清洗步骤；新增 sanitize_html() 在发微信前 strip U+FFFC/U+FFFD/零宽字符 | 2026-07-07 |
| #10 排版 HTML 被当 Markdown 渲染 | 输入 HTML 被 `markdown_to_wechat_html()` 当 MD 重渲染；新增直通模式：检测 `<!DOCTYPE`/`<html` → 提取 body → 跳过渲染直接创建草稿 | 2026-07-07 |

## 📌 文章来源处理

当文章不在本地文件系统时：

1. **不要浪费时间搜索**：`session_search` + `grep` + `find` 搜不到就是搜不到
2. **立即让用户粘贴**：直接要求把文章贴到聊天中
3. **保存到 `/tmp/article_raw.txt`**：收到后立即保存

**铁律**：超过 3 次搜索无果就放弃，直接问用户。
