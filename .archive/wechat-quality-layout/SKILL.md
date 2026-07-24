---
name: wechat-quality-layout
description: 微信公众号高质量排版引擎 — 中国风主题 CSS + 智能配图（每500-800字一张）+ picsum占位图。替代原有粗糙HTML生成。
---

# wechat-quality-layout — 高质量微信排版引擎

## 概述

为微信公众号文章提供**中国风主题排版 + 智能配图**的完整管线。替代原有粗糙的 HTML 生成方式。

> ⚠️ **路径说明**：本 Skill 的排版脚本（`quality_layout.py`、`image_replace.py`、`themes/chinese.css`）实际存储在 **`~/.hermes/skills/social-media/wechat-publish-direct/references/`**。本 SKILL.md 中所有 `references/` 均指该目录。
> 本地 `references/` 目录不存在，不要在 `~/.hermes/skills/wechat-quality-layout/references/` 下找文件。

## 核心组件

### 1. 排版引擎

脚本实际路径：`~/.hermes/skills/social-media/wechat-publish-direct/references/quality_layout.py`

```bash
cd ~/.hermes/skills/social-media/wechat-publish-direct/references

python3 quality_layout.py <markdown_file> \
  --theme chinese \
  --images /tmp/article_images.json \
  --output <html_file>
```

功能：
- 解析 Markdown → 结构化块列表（title/section/paragraph/quote/table）
- 按字数分布智能插入配图占位符（每 500-800 字一张，最少 2 张，最多 5 张）
- 支持 `--images` JSON 传入自定义配图关键词和 caption
- Markdown 表格自动渲染为 HTML `<table>`
- 输出带中国风 CSS 的 HTML

### 2. 配图替换

脚本实际路径：`~/.hermes/skills/social-media/wechat-publish-direct/references/image_replace.py`

```bash
python3 image_replace.py <input_html> --output <output_html>
```

功能：
- 将 `__PLACEHOLDER_IMAGE_xxx__` 占位符替换为 picsum.photos 真实图片 URL
- 自动应用 caption 文案（从 `--images` JSON 的 `captions` 字段）

### 3. 中国风 CSS 模板

实际路径：`~/.hermes/skills/social-media/wechat-publish-direct/references/themes/chinese.css`

设计理念：
- 宣纸底色 `#faf9f6`
- serif 字体族 + 非衬线表格
- 1.9 倍行距，16px 正文
- 金色点缀 `#c4a882`
- 大标题居中 + 章节标题左侧金线
- 表格支持（`.wechat-table`）

## 配图策略

- 封面图：文章标题上方（通过微信 API 的 `thumb_media_id` 传入）
- 正文配图：每 500-800 字一张，均匀分布到不同章节
- **配图关键词必须外置 JSON**——默认 `IMAGE_KEYWORDS` 仅作 fallback，每次排版应传 `--images` 指定文章相关关键词
- 当前使用 picsum.photos 占位，可替换为 Unsplash/Pexels/Seedream 真实图片

### 配图关键词 JSON 格式

```json
{
  "keywords": {
    "chapter1": ["tech abstract", "code screen"],
    "chapter2": ["workflow diagram", "connected nodes"],
    "chapter3": ["progress checklist", "milestone markers"],
    "chapter4": ["speed selection", "route options"],
    "ending": ["open source community", "knowledge sharing"]
  },
  "captions": {
    "chapter1": "配图描述",
    "chapter2": "配图描述",
    "chapter3": "配图描述",
    "chapter4": "配图描述",
    "ending": "配图描述"
  }
}
```

## 使用流程

```bash
cd ~/.hermes/skills/social-media/wechat-publish-direct/references

# 1. Markdown 排版（带自定义关键词）
python3 quality_layout.py article.md \
  --theme chinese \
  --images article_images.json \
  --output article_layout.html

# 2. 配图替换
python3 image_replace.py article_layout.html --output article_final.html

# 3. 上传封面图到微信素材库（获取 thumb_media_id）
# 4. 上传正文配图到微信素材库
# 5. 创建草稿（draft/add API）
```

## 限制与注意事项

- picsum.photos 生成的图是随机风景照
- 配图关键词取英文种子词，caption 取中文描述
- 默认 IMAGE_KEYWORDS 是 tech 主题，不匹配时用 `--images` 覆盖
- 微信 API 必须走 Clash 代理（`https_proxy=http://127.0.0.1:7897`）

## 相关文件

所有脚本和主题在：`~/.hermes/skills/social-media/wechat-publish-direct/references/`
- `quality_layout.py` — Markdown → HTML 排版引擎
- `image_replace.py` — 占位符 → picsum 真实图片 URL
- `themes/chinese.css` — 中国风 CSS 模板
