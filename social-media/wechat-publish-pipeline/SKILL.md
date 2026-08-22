---
name: wechat-publish-pipeline
description: Use when 公众号发布流水线出错或需预检。记录脚本实测行为、已修复 Bug 与坑位。
category: social-media
---

# 微信公众号发布流水线（实测运维版）

**为什么存在**：bundled 的 `wechat-publish-direct` / `wechat-content-pipeline` 是技能文档，不是代码事实。2026-08-22 实测发现其声称的「HTML 直通模式」**从未实现**（#10 bug 修复只写了文档没写代码），导致 HTML 输入被当 Markdown 全量转义成乱码。本技能记录脚本的真实行为与已落地的修复。

## 真实管线

```
波总成品稿 → /tmp/article_raw.md
  → quality_layout.py --theme chinese --images /tmp/article_images.json → HTML（class 体系：.wechat-article/.wechat-section/.wechat-paragraph/.wechat-image-block）
  → regex 清除【配图建议】指令标记
  → image_replace.py → picsum 占位图替换
  → publish_article.py（HTML 直通模式）→ 微信 CDN 图 + 封面 → draft/add
```

脚本位置（bundled skill 的 references/ 目录）：
- `~/.hermes/skills/social-media/wechat-publish-direct/scripts/publish_article.py`
- `~/.hermes/skills/social-media/wechat-publish-direct/references/quality_layout.py`
- `~/.hermes/skills/social-media/wechat-publish-direct/references/image_replace.py`

## 已修复 Bug（2026-08-22 全部落地并验证）

| Bug | 症状 | 修复 |
|-----|------|------|
| #1 直通模式从未实现 | HTML 输入被 `markdown_to_wechat_html()` 全量 `html_lib.escape` → 草稿显示 `&lt;p class=...` 乱码 | publish_article.py 新增 `is_html_document()`（`<!DOCTYPE`/`<html` 开头）+ `extract_body()` + STEP 0 直通分支 |
| #2 两套 HTML 方言不兼容 | quality_layout 输出 class 体系，`parse_article_html` 只认 DeepSeek inline-style（`<div style="font-family:`、`<p style="font-size:18px;color:#888`）→ raise "Could not find article container div" | container 与 chapter 正则同时兼容 class 与 inline style |
| #3 `---` 分隔线渲染成文字段落 | 草稿正文出现 `---` 文本行 | quality_layout.py 的 parse_markdown 加 `^-{3,}$` → `{"type":"hr"}`，render 为 `<hr class="wechat-hr">` |

**直通模式真实语义**（2026-08-22 实现版）：
1. 检测输入以 `<!DOCTYPE` 或 `<html` 开头 → 提取 `<body>` 内容
2. **剥离输入中所有 `<img>` 与 `.wechat-image-block` 配图块**（picsum 占位 + caption 一并移除）——正文配图由 `--body-seeds` 在解析后的新位置重新生成
3. `sanitize_html()` 清洗 U+FFFC/U+FFFD/零宽字符
4. 跳过 Markdown 渲染 → 上传封面（`material/add_material`）+ 正文图（`media/uploadimg`）→ draft/add

实现细节见 `references/passthrough-impl-2026-08-22.md`。

## 预检清单（每次发布前）

```bash
# 1. Clash 规则（⚠️ 可能整条消失——Clash Verge 更新会覆盖生成的 yaml）
grep 'api.weixin.qq.com' ~/Library/Application\ Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml
# 0 匹配 与 DIRECT 同样视为失败 → 备份 → 补规则（插在 GEOIP,CN,DIRECT 之前）→ reload：
curl -s -X PUT --unix-socket /tmp/verge/verge-mihomo.sock \
  http://localhost/configs?force=true -H "Content-Type: application/json" -d '{"path": ""}'
# 验证规则生效：
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/rules | grep weixin

# 2. 凭证（her-m2 profile）
grep -E 'WECHAT_SECRET|DEEPSEEK_API_KEY' /Users/mac/.hermes/profiles/her-m2/.env | grep -v '^\*\*\*'

# 3. 微信 API 连通性（必须走代理，出口 IP 要在白名单）
https_proxy=http://127.0.0.1:7897 curl -s --connect-timeout 8 \
  "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=<APPID>&secret=<SECRET>" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'access_token' in d else d)"

# 4. 干跑验证（不触发微信）
cd ~/.hermes/skills/social-media/wechat-publish-direct/scripts
python3 publish_article.py --article /tmp/article_styled.html --cover-seed <s> \
  --body-seeds <s1,s2,...> --author "中本笨-BG" --title "..." --digest "..." \
  --dry-run --output /tmp/final.html
```

## Pitfalls

1. **【配图建议】标记残留**：quality_layout.py 不识别「【配图建议：xxx】」，当普通段落渲染。排版后必须 regex 清除：
   ```python
   re.sub(r'<p>【配图建议：.*?</p>', '', html, flags=re.S)
   re.sub(r'【配图建议：.*?】', '', html, flags=re.S)
   ```
2. **标题 55 字节 / 摘要 115 字节**（UTF-8 字节数，非字符数）。中文 1 字 = 3 字节。
3. **图片数量**：直通模式图片全部由 `--body-seeds` 决定（每 seed 一张 + 封面 1 张）。quality_layout 的 `get_image_slots` 上限 5 张（min(5, 字数//500)），JSON 里多余章节关键词不会全部用上——正常。
4. **输入必须是完整 HTML 文档**（`<!DOCTYPE`/`<html` 开头）才触发直通；裸 HTML 片段会被当 Markdown 转义成乱码。
5. **最终产物检查**：发布前 grep 确认 0 个 `picsum`、0 个 `&lt;`、0 个 `__PLACEHOLDER`、0 个「配图建议」。
6. **curl 必须显式走代理**：`https_proxy=http://127.0.0.1:7897`，直连 IP 不在白名单 → 40164。

## 验证状态（2026-08-22 干跑实测）

- 5 张图（封面+4正文）✅
- 0 picsum 残留 / 0 转义乱码 / 0 占位符 / 0 配图建议残留 ✅
- 9 章节 h2 识别、9 分隔线 hr ✅
- 内容完整性抽查（关键句全部命中）✅
