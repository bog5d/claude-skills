# 直通模式真实实现（2026-08-22）

bundled `wechat-publish-direct` skill 声称的「HTML 直通模式」（bug #10，标记 2026-07-07 修复）**代码从未实现**——`publish_article.py` 里没有任何 `<!DOCTYPE`/`<html` 检测分支。HTML 输入直接进 `markdown_to_wechat_html()` 被 `html_lib.escape()` 全量转义，草稿显示 `&lt;p class="wechat-paragraph"&gt;...` 乱码。

## 三处修复

### 1. publish_article.py：直通模式分支（STEP 0）

`publish_workflow()` 排版段替换为：

```python
    # ---- Step 0/1: 直通模式（输入已是完整 HTML）----
    if is_html_document(article_md):
        log("STEP 0", "检测到已排版 HTML → 直通模式")
        html = extract_body(article_md)
        html = strip_layout_image_blocks(html)
        html = sanitize_html(html).strip()
        log("STEP 1", f"直通模式: 提取 body {len(html)} chars, "
                     f"已有图片 {len(re.findall(r'<img', html))} 张 (全部重插)")
    elif layout_provider == "deterministic":
        ...原逻辑
```

### 2. publish_article.py：四个辅助函数（放 parse_article_html 前）

```python
def is_html_document(text: str) -> bool:
    """判断输入是否为完整 HTML 文档（直通模式触发条件）。"""
    stripped = text.lstrip().lower()
    return stripped.startswith("<!doctype") or stripped.startswith("<html")

def extract_body(html: str) -> str:
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.S)
    return m.group(1) if m else html

def sanitize_html(html: str) -> str:
    return re.sub(r"[\ufffc\ufffd\u200b-\u200f\ufeff]", "", html)

def strip_layout_image_blocks(html: str) -> str:
    """剥离排版引擎已插入的图片块（picsum 占位 + caption），
    由发布流程在解析后的新位置重新插入微信 CDN 图片。"""
    html = re.sub(r'<div class="wechat-image-block">.*?</div>', "", html, flags=re.S)
    html = re.sub(r"<img[^>]*>", "", html)
    return html
```

### 3. publish_article.py：parse_article_html 兼容 class 体系

```python
    container_match = re.search(
        r'<div(?:\s+class="wechat-article"|\s+style="font-family:[^"]*")[^>]*>', html
    )
    ...
    chapter_pattern = (
        r'<h2 class="wechat-section">[^<]*</h2>'
        r'|<p style="font-size:18px;color:#888[^"]*">[一二三四五六七八九十]、?[^<]*</p>'
    )
```

### 4. quality_layout.py：`---` 分隔线支持

parse_markdown 循环内（表格判断前）：

```python
        # 分隔线 (---)
        if re.match(r'^-{3,}$', line):
            if current_para:
                blocks.append({"type": "paragraph", "content": " ".join(current_para)})
                current_para = []
            blocks.append({"type": "hr"})
            i += 1
            continue
```

render_blocks 内加：

```python
        elif btype == "hr":
            html_parts.append(
                '<hr class="wechat-hr" '
                'style="border:none;border-top:1px solid #e2ddd4;'
                'margin:28px auto;width:60%">'
            )
```

## 验证（dry-run 通过）

- `[STEP 5] 所有图片已替换为微信 CDN URL ✓`（修复前是 `WARNING: 5 picsum URLs remain in cover`）
- final.html：img 5 / picsum 0 / `&lt;` 0 / PLACEHOLDER 0 / 配图建议 0 / 段落 132 / hr 9
- 关键句抽查：30MB、agent-exchange、任务漂移、写在最后、痛并快乐、gh release download 全部命中

## 检查命令

```bash
# 发布前检查最终产物
python3 - <<'PYEOF'
import re
c = open('/tmp/final.html', encoding='utf-8').read()
print('img:', len(re.findall(r'<img', c)), '| picsum:', c.count('picsum'),
      '| 转义&lt;:', c.count('&lt;'), '| hr:', c.count('wechat-hr'))
PYEOF
```
