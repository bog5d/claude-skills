---
name: wechat-article-reading
description: 读取微信公众号文章全文（标题/作者/时间/正文），web_extract 不可用时的 curl 解析降级方案。
trigger: 用户发 mp.weixin.qq.com 链接要求读取/总结内容
---

# WeChat Article Reading (mp.weixin.qq.com)

读取微信公众号文章正文，从链接到可读文本。

## 首选：web_extract

```python
from hermes_tools import web_extract
web_extract(urls=["https://mp.weixin.qq.com/s/..."])
```

**本机已知限制（2026-08）**: 当前 web.extract_backend 是 DuckDuckGo (ddgs) search-only，
`web_extract` 对 URL 返回 `"DuckDuckGo (ddgs) is a search-only backend and cannot extract URL content"`。
此时走 curl 降级方案。

## 降级方案：curl + Python 正则解析（已验证可靠）

```bash
curl -sL --max-time 30 -A "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1" \
  "<URL>" -o /tmp/wechat_article.html
```

**必须用手机 UA**（iOS Safari），桌面 UA 可能拿不到完整正文。文章 HTML 约 3MB。

解析要点（Python 正则，正文在 `id="js_content"` div 内）：
- 标题: `<meta property="og:title" content="...">` 或 `var msg_title = "..."`（注意实际标题常包在 `<span class="js_title_inner">` 里）
- 作者/公众号: `<meta property="og:article:author" content="...">` 或 `var nickname = "..."`
- 发布时间: `var ct = "<unix_timestamp>"` → datetime.fromtimestamp
- 正文: `<div id="js_content" ...>(.*?)</div><script` 提取后，先剥 `<script>`/`<style>`，`<br>`/`</p>`/`</section>` 换行，再剥标签 + html.unescape
- 图片数: `re.findall(r'<img[^>]*data-src="(.*?)"', ...)`（微信图片是懒加载 data-src）

完整解析脚本示例见 `scripts/parse_wechat.py`。

## 输出约定
提取正文后直接给结构化摘要（标题/作者/时间/正文要点），不要贴原始 HTML。
