#!/usr/bin/env python3
"""
配图获取与替换 — 用 picsum.photos 生成占位图，也可配置为真实图片 URL

用法:
  python3 image_replace.py <input_html> --output <output_html> [--preview]
"""

import sys
import os
import json
import argparse
from pathlib import Path


# picsum.photos 随机图生成器
SEED_MAP = {
    "chapter1": "technology-abstract-1",
    "chapter2": "workflow-pipeline-2",
    "chapter3": "checklist-progress-3",
    "chapter4": "speed-control-4",
    "ending": "open-source-community-5",
}

# 配图描述（已废弃：caption 现在由 quality_layout 的 IMAGE_CAPTIONS 控制）
# 保留 SEED_MAP 仅用于 picsum 图片生成


def generate_picsum_url(seed: str, width: int = 800, height: int = 450) -> str:
    """生成 picsum.photos 占位图 URL"""
    return f"https://picsum.photos/seed/{seed}/{width}/{height}"


def replace_placeholders(html_content: str, theme: str = "chinese") -> str:
    """
    将 HTML 中的配图占位符替换为真实图片 URL
    """
    # 匹配 __PLACEHOLDER_IMAGE_xxx__ 格式
    import re
    
    def replacer(match):
        key = match.group(1)
        url = generate_picsum_url(SEED_MAP.get(key, key))
        return url  # 只返回 URL，不加 alt（caption 由 quality_layout 模板处理）
    
    html_content = re.sub(
        r'__PLACEHOLDER_IMAGE_(\w+)__',
        replacer,
        html_content
    )
    
    return html_content


def main():
    parser = argparse.ArgumentParser(description="配图替换工具")
    parser.add_argument("input", help="输入 HTML 文件")
    parser.add_argument("--output", "-o", help="输出 HTML 文件")
    parser.add_argument("--preview", action="store_true", help="预览替换结果")
    args = parser.parse_args()
    
    with open(args.input, encoding="utf-8") as f:
        html = f.read()
    
    replaced = replace_placeholders(html)
    
    output = args.output or args.input.replace(".html", "_final.html")
    with open(output, "w", encoding="utf-8") as f:
        f.write(replaced)
    
    print(f"✅ 配图替换完成: {output}")
    print(f"📊 共替换 {len(SEED_MAP)} 张配图")
    
    if args.preview:
        print("\n--- 预览 ---")
        print(replaced[:2000])


if __name__ == "__main__":
    main()
