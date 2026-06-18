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
# 用 seed 参数保证每次同一位置得到同一张图
SEED_MAP = {
    "chapter1": "rural-night-1",
    "chapter2": "village-school-2",
    "chapter3": "watermelon-road-3",
    "chapter4": "friendship-night-4",
    "ending": "lantern-window-5",
}

# 配图描述文案
CAPTION_MAP = {
    "chapter1": "院坝里的夏夜",
    "chapter2": "刘小兵家的灶台",
    "chapter3": "路旁的碎西瓜",
    "chapter4": "夜路上的告别",
    "ending": "那盏灯",
}


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
        caption = CAPTION_MAP.get(key, key)
        return f'{url}" alt="{caption}"'
    
    html_content = re.sub(
        r'__PLACEHOLDER_IMAGE_(\w+)__',
        replacer,
        html_content
    )
    
    # 替换 caption 文案
    for key, caption in CAPTION_MAP.items():
        html_content = html_content.replace(
            f'配图 · {key}',
            caption
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
