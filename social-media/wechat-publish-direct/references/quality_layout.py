#!/usr/bin/env python3
"""
高质量排版引擎 — 中国风主题 + 智能配图

用法:
  python3 quality_layout.py <markdown_file> --theme chinese --output <html_file>

功能:
  1. 读取 Markdown 原文，分析字数分布
  2. 按中国风 CSS 模板渲染 HTML
  3. 每 500-800 字自动插入配图（根据段落语义提取配图关键词）
  4. 生成可直接粘贴到微信公众号的 HTML
"""

import sys
import os
import re
import argparse
import json
from pathlib import Path

# === 配置 ===
# 脚本所在目录的 references/themes/
SCRIPT_DIR = Path(__file__).parent
THEMES_DIR = SCRIPT_DIR / "themes"

THEME_CSS = {
    "chinese": "chinese.css",  # 中国风
    "minimal": "minimal.css",   # 极简风（预留）
    "magazine": "magazine.css", # 杂志风（预留）
}

# 配图关键词映射（默认值，可被 --image-keywords JSON 覆盖）
IMAGE_KEYWORDS = {
    "chapter1": ["technology abstract", "code screen", "digital network"],
    "chapter2": ["workflow diagram", "connected nodes", "pipeline automation"],
    "chapter3": ["progress checklist", "milestone markers", "step by step"],
    "chapter4": ["speed selection", "route options", "control panel"],
    "ending": ["open source community", "team collaboration", "sharing knowledge"],
}

# 配图 Caption 映射（章节 → 中文描述）
IMAGE_CAPTIONS = {
    "chapter1": "自动化工作流示意",
    "chapter2": "Skill 串联管线",
    "chapter3": "8 个阶段一览",
    "chapter4": "三种速度模式",
    "ending": "开源，拿走直接用",
}


def read_css(theme_name: str) -> str:
    """读取 CSS 模板"""
    css_file = THEMES_DIR / THEME_CSS.get(theme_name, "chinese.css")
    if not css_file.exists():
        return ""
    return css_file.read_text(encoding="utf-8")


def parse_markdown(md_text: str) -> list:
    """
    解析 Markdown 为结构化段落列表
    返回: [{'type': 'title'|'section'|'paragraph'|'quote'|'image_placeholder', ...}]
    """
    lines = md_text.split("\n")
    blocks = []
    current_para = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            if current_para:
                blocks.append({"type": "paragraph", "content": " ".join(current_para)})
                current_para = []
            i += 1
            continue
        
        # 标题 (# 标题)
        if line.startswith("# "):
            if current_para:
                blocks.append({"type": "paragraph", "content": " ".join(current_para)})
                current_para = []
            blocks.append({"type": "title", "content": line[2:].strip()})
            i += 1
            continue
        
        # 二级标题 (## 标题)
        if line.startswith("## "):
            if current_para:
                blocks.append({"type": "paragraph", "content": " ".join(current_para)})
                current_para = []
            blocks.append({"type": "section", "content": line[3:].strip()})
            i += 1
            continue
        
        # 引用 (> 文本)
        if line.startswith("> "):
            if current_para:
                blocks.append({"type": "paragraph", "content": " ".join(current_para)})
                current_para = []
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip()[2:])
                i += 1
            blocks.append({"type": "quote", "content": " ".join(quote_lines)})
            continue
        
        # 分隔线 (---)
        if re.match(r'^-{3,}$', line):
            if current_para:
                blocks.append({"type": "paragraph", "content": " ".join(current_para)})
                current_para = []
            blocks.append({"type": "hr"})
            i += 1
            continue

        # Markdown 表格 (| col | col |)
        if line.startswith("|") and line.endswith("|"):
            if current_para:
                blocks.append({"type": "paragraph", "content": " ".join(current_para)})
                current_para = []
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                row = lines[i].strip()
                # 跳过分隔行 (|---|---|)
                if not re.match(r'^\|[\s\-:|]+\|$', row):
                    cells = [c.strip() for c in row[1:-1].split("|")]
                    table_rows.append(cells)
                i += 1
            blocks.append({"type": "table", "rows": table_rows})
            continue
        
        # 普通段落
        if "**" in line:
            # 带粗体的段落，保留格式
            current_para.append(line)
        else:
            current_para.append(line)
        
        i += 1
    
    if current_para:
        blocks.append({"type": "paragraph", "content": " ".join(current_para)})
    
    return blocks


def count_chars(blocks: list) -> int:
    """统计总字数"""
    total = 0
    for b in blocks:
        if b["type"] == "paragraph":
            total += len(b["content"])
    return total


def get_image_slots(blocks: list, total_chars: int) -> list:
    """
    计算配图位置：每 500-800 字插入一张，尽量均匀分布到不同章节
    返回: [(block_index, chapter_key, keywords)]
    """
    # 先找出所有段落块及其累计字数
    para_blocks = [(i, b) for i, b in enumerate(blocks) if b["type"] == "paragraph"]
    
    # 确定章节边界
    section_boundaries = []
    for i, b in enumerate(blocks):
        if b["type"] == "section":
            section_boundaries.append((i, b["content"]))
    
    # 确定配图数量：每 500-800 字一张，最少 2 张，最多 5 张
    num_images = max(2, min(5, total_chars // 500))
    
    # 均匀分布配图位置
    slots = []
    if len(para_blocks) >= num_images:
        step = len(para_blocks) // num_images
        for j in range(num_images):
            para_idx = para_blocks[(j + 1) * step - 1][0] if j < num_images - 1 else para_blocks[-1][0]
            
            # 确定这个位置属于哪个章节
            chapter_key = f"chapter{j+1}" if j < 4 else "ending"
            keywords = IMAGE_KEYWORDS.get(chapter_key, ["countryside night"])
            slots.append((para_idx, chapter_key, keywords))
    
    return slots


def render_paragraph(content: str) -> str:
    """渲染单个段落，处理粗体等 Markdown"""
    # 粗体 **text** → <strong>text</strong>
    content = re.sub(r"\*\*(.+?)\*\*", r'<strong class="wechat-em">\1</strong>', content)
    # 斜体 *text*
    content = re.sub(r"\*(.+?)\*", r'<em>\1</em>', content)
    return content


def render_blocks(blocks: list, image_slots: list) -> str:
    """将结构化块渲染为 HTML"""
    slot_set = set(s[0] for s in image_slots)
    slot_map = {s[0]: s for s in image_slots}
    
    html_parts = []
    
    for idx, block in enumerate(blocks):
        btype = block["type"]
        
        # 检查是否需要在此处插入配图
        if idx in slot_set:
            _, chapter_key, keywords = slot_map[idx]
            caption = IMAGE_CAPTIONS.get(chapter_key, f"配图")
            html_parts.append(f'''
<div class="wechat-image-block">
  <img src="__PLACEHOLDER_IMAGE_{chapter_key}__" alt="{chapter_key} illustration">
  <div class="wechat-image-caption">{caption}</div>
</div>''')
        
        if btype == "title":
            html_parts.append(f'<h1 class="wechat-title">{block["content"]}</h1>')
        elif btype == "section":
            html_parts.append(f'<h2 class="wechat-section">{block["content"]}</h2>')
        elif btype == "paragraph":
            html_parts.append(f'<p class="wechat-paragraph">{render_paragraph(block["content"])}</p>')
        elif btype == "quote":
            html_parts.append(f'<blockquote class="wechat-quote">{render_paragraph(block["content"])}</blockquote>')
        elif btype == "table":
            rows_html = []
            for row in block["rows"]:
                cells = "".join(f"<td>{cell}</td>" for cell in row)
                rows_html.append(f"<tr>{cells}</tr>")
            html_parts.append(f'<table class="wechat-table">{"".join(rows_html)}</table>')
        elif btype == "hr":
            html_parts.append(
                '<hr class="wechat-hr" '
                'style="border:none;border-top:1px solid #e2ddd4;'
                'margin:28px auto;width:60%">'
            )
    
    return "\n".join(html_parts)


def build_html(title: str, css: str, body: str) -> str:
    """组装完整 HTML"""
    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
{css}
</style>
</head>
<body>
<div class="wechat-article">
{body}
</div>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="高质量微信排版引擎")
    parser.add_argument("input", help="Markdown 文件路径")
    parser.add_argument("--theme", default="chinese", choices=["chinese", "minimal", "magazine"],
                        help="排版主题")
    parser.add_argument("--output", "-o", help="输出 HTML 文件路径")
    parser.add_argument("--images", help="配图关键词 JSON 文件（可选，覆盖默认）")
    args = parser.parse_args()
    
    # 读取 Markdown
    with open(args.input, encoding="utf-8") as f:
        md_text = f.read()
    
    # 加载外置配图关键词 JSON（覆盖默认）
    if args.images:
        with open(args.images, encoding="utf-8") as f:
            custom_kw = json.load(f)
        IMAGE_KEYWORDS.update(custom_kw.get("keywords", {}))
        IMAGE_CAPTIONS.update(custom_kw.get("captions", {}))
        print(f"📋 加载自定义配图关键词: {args.images}")
    
    # 解析
    blocks = parse_markdown(md_text)
    total_chars = count_chars(blocks)
    print(f"📝 文章总字数: {total_chars}")
    
    # 计算配图位置
    image_slots = get_image_slots(blocks, total_chars)
    print(f"🖼️  配图位置: {len(image_slots)} 张")
    
    # 读取 CSS
    css = read_css(args.theme)
    if not css:
        print(f"⚠️  未找到 CSS 模板: {args.theme}")
        sys.exit(1)
    
    # 渲染
    body = render_blocks(blocks, image_slots)
    html = build_html(blocks[0]["content"] if blocks else "", css, body)
    
    # 输出
    output = args.output or args.input.replace(".md", ".html")
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ 排版完成: {output}")
    print(f"📊 配图占位符: {[f'__PLACEHOLDER_IMAGE_{slot[1]}__' for slot in image_slots]}")
    
    # 输出配图关键词供后续使用
    print(f"\n📋 配图关键词:")
    for idx, key, kw in image_slots:
        print(f"  位置 {idx}: {key} → {kw}")


if __name__ == "__main__":
    main()
