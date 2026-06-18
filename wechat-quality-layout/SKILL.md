---
name: wechat-quality-layout
description: 微信公众号高质量排版引擎 — 中国风主题 CSS + 智能配图（每500-800字一张）+ picsum占位图。替代原有粗糙HTML生成。
---

# wechat-quality-layout — 高质量微信排版引擎

## 概述

为微信公众号文章提供**中国风主题排版 + 智能配图**的完整管线。替代原有粗糙的 HTML 生成方式。

## 核心组件

### 1. 排版引擎 (`references/quality_layout.py`)

```bash
python3 references/quality_layout.py <markdown_file> --theme chinese --output <html_file>
```

功能：
- 解析 Markdown → 结构化块列表（title/section/paragraph/quote）
- 按字数分布智能插入配图占位符（每 500-800 字一张，最少 2 张，最多 5 张）
- 输出带中国风 CSS 的 HTML

### 2. 配图替换 (`references/image_replace.py`)

```bash
python3 references/image_replace.py <input_html> --output <output_html>
```

功能：
- 将 `__PLACEHOLDER_IMAGE_xxx__` 占位符替换为 picsum.photos 真实图片 URL
- 自动替换 caption 文案（中文描述）

### 3. 中国风 CSS 模板 (`references/themes/chinese.css`)

设计理念：
- 宣纸底色 `#faf9f6`
- serif 字体族（PingFang SC + Noto Serif SC + SimSun）
- 1.9 倍行距，16px 正文
- 金色点缀 `#c4a882`
- 大标题居中 + 章节标题左侧金线

## 配图策略

- 封面图：文章标题上方（通过微信 API 的 thumb_media_id 传入）
- 正文配图：每 500-800 字一张，均匀分布到不同章节
- 配图关键词映射在 `quality_layout.py` 的 `IMAGE_KEYWORDS` 字典中定义
- 当前使用 picsum.photos 占位，可替换为 Unsplash/Pexels/Seedream 真实图片

## 使用流程

```bash
# 1. Markdown 排版
python3 references/quality_layout.py article.md --theme chinese --output article_layout.html

# 2. 配图替换
python3 references/image_replace.py article_layout.html --output article_final.html

# 3. 上传封面图到微信素材库（获取 thumb_media_id）
# 4. 上传正文配图到微信素材库
# 5. 创建草稿（draft/add API）
```

## 限制与注意事项

- picsum.photos 生成的图是随机风景照，不是 AI 生成的主题图
- 如需 AI 配图，可对接豆包 Seedream 或 DALL-E（需在 image_replace.py 中扩展）
- 微信 IP 白名单必须提前配置（222.247.153.167）
- access_token 有效期 2 小时，每次操作前需重新获取

## 支持文件

- `references/quality_layout.py` — Markdown → HTML 排版引擎（中国风 CSS + 智能配图占位）
- `references/image_replace.py` — 将占位符替换为 picsum.photos 真实图片 URL
- `references/themes/chinese.css` — 中国风 CSS 模板（宣纸底色、serif 字体、金色点缀）

## 跨技能提示

- `skill_manage(action='write_file')` 有工具验证 bug（file_path 参数被拒绝）。详见 `wechat-publish-direct` 技能中的凭证持久化章节。
- 如需写入支持文件，用 `write_file(path='/Users/mac/.hermes/profiles/her-m2/skills/wechat-quality-layout/references/xxx', content='...')` 直接写入。
