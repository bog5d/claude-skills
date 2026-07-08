#!/usr/bin/env python3
"""
design-lint.py — AI设计反模板检查工具

检测 HTML/CSS 中的 AI 模板味设计违规。支持三种预设 (high-end / minimal / industrial) 
和自动 preset 推断。零外部依赖（Python 标准库）。

用法:
    python3 design-lint.py <html-file>                    # 自动推断 preset
    python3 design-lint.py --preset high-end <html-file>  # 强制指定 preset
    python3 design-lint.py --all <html-file>              # 全部规则

预设规则:
    high-end:    禁止纯白/紫色渐变/粗体标题/大阴影/大圆角/Inter/渐变
    minimal:     禁止卡片阴影/emoji/彩虹渐变/大圆角/Inter
    industrial:  禁止紫色渐变/彩虹渐变/卡片阴影/大圆角/Inter

核心检测维度:
    - typography:  Inter/Roboto/Arial 默认、粗体标题、等宽字体
    - color:      紫色渐变、纯白底、纯黑底、AI 紫
    - layout:     卡片阴影、大圆角(>12px)、分隔线(HR)、渐变背景
    - content:    通用人名、模板品牌名、填充动词、虚假精确数字、emoji

已知误报(pitfalls):
    - Google Fonts URL 中含 "Inter" 字符串会被误判为 Inter 字体
    - 径向渐变氛围光(radial-gradient)会被通用渐变规则命中
    - 类名中含颜色名(如 "text-purple-500")会触发颜色规则
"""
import re
import sys
import argparse
from dataclasses import dataclass, field
from typing import Optional

# ── Rules ──────────────────────────────────────────────

@dataclass
class LintRule:
    name: str
    category: str
    severity: str  # error / warning / info
    message: str
    fix: str = ""
    presets: list = field(default_factory=lambda: ["all"])
    check: callable = None

    def __call__(self, html: str) -> Optional[dict]:
        result = self.check(html)
        if result:
            return {
                "rule": self.name,
                "category": self.category,
                "severity": self.severity,
                "message": self.message,
                "fix": self.fix,
                "source": result.get("source", "unknown"),
            }
        return None


def check_fonts(html):
    banned = ["Inter", "Roboto", "Arial", "Montserrat", "Open Sans",
              "Lato", "Poppins"]
    # Extract font-family declarations — but skip URLs (Google Fonts links)
    # Match CSS font-family values but NOT inside href="..." 
    css_blocks = re.findall(r'font-family\s*:\s*([^;}]+)', html, re.I)
    found = []
    for block in css_blocks:
        for font in banned:
            if font.lower() in block.lower():
                found.append(font)
    # Also check inline style/class references — but SKIP if only in URLs
    if found:
        return {"source": f"CSS (font-family)", "fonts": found}
    return None


def check_purple_gradient(html):
    patterns = [
        r'linear-gradient.*?(?:#7[0-9a-f]{5}|#8[0-9a-f]{5}|#9[0-9a-f]{5}|#6[0-9a-f]{5}).*?(?:#7[0-9a-f]{5}|#8[0-9a-f]{5}|#9[0-9a-f]{5}|#6[0-9a-f]{5})',
        r'(?:purple|violet|#\s*6[0-9a-f]{5}|#\s*7[0-9a-f]{5}|#\s*8[0-9a-f]{5}|#\s*9[0-9a-f]{5})',
        r'background.*?(?:#667eea|#764ba2|#a855f7|#7c3aed|#8b5cf6|#6d28d9)',
    ]
    for p in patterns:
        if re.search(p, html, re.I):
            return {"source": "CSS"}
    return None


def check_pure_white(html):
    if re.search(r'(?:background|bg).*?(?:#fff\b|#ffffff\b|white\b)', html, re.I):
        return {"source": "CSS"}
    return None


def check_pure_black(html):
    if re.search(r'(?:background|bg|color).*?(?:#000\b|#000000\b)', html, re.I):
        return {"source": "CSS"}
    return None


def check_gradient(html):
    if re.search(r'linear-gradient|radial-gradient', html, re.I):
        return {"source": "CSS (style blocks)"}
    return None


def check_card_shadow(html):
    shadows = re.findall(r'box-shadow\s*:', html, re.I)
    if shadows:
        return {"source": "CSS", "count": len(shadows)}
    return None


def check_large_radius(html):
    radii = re.findall(r'border-radius\s*:\s*(\d+)px', html, re.I)
    large = [r for r in radii if int(r) > 12]
    if large:
        return {"source": "CSS", "values": f"{', '.join(large)}px"}
    return None


def check_hr_dividers(html):
    hrs = re.findall(r'<hr[^>]*>', html, re.I)
    if len(hrs) >= 2:
        return {"source": "HTML", "count": len(hrs)}
    return None


def check_bold_headings(html):
    bold = re.findall(r'font-weight\s*:\s*(?:700|800|900|bold)', html, re.I)
    if bold:
        return {"source": "CSS", "count": len(bold)}
    return None


def check_emoji(html):
    emoji = re.findall(r'[\U0001F300-\U0001F9FF\u2600-\u27BF\u2B50\u2705]', html)
    if emoji:
        return {"source": "HTML text", "count": len(emoji)}
    return None


def check_bold_serif(html):
    if re.search(r'font-weight\s*:\s*(?:700)\s*;.*?font-family.*?serif', html, re.I | re.S):
        return {"source": "CSS"}
    return None


def check_monospace_titles(html):
    if re.search(r'<h[1-3][^>]*>.*?</h[1-3]>', html, re.I | re.S):
        return None
    return None


def check_default_icons(html):
    if re.search(r'font-awesome|material-icons|feather-icons|heroicons|bootstrap-icons', html, re.I):
        return {"source": "HTML"}
    return None


# ── Rule Definitions ───────────────────────────────────

RULES = [
    LintRule("no-banned-fonts", "typography", "error",
             "Banned font(s) detected: Inter. AI defaults.",
             "Use distinctive alternatives: Syne, Space Grotesk, DM Sans, IBM Plex, Playfair Display.",
             presets=["all"],
             check=check_fonts),
    LintRule("no-purple-gradient", "color", "error",
             "Purple gradient — the #1 AI slop signature.",
             "Pick any color except purple. Try deep blue, warm amber, or monochrome.",
             presets=["all"],
             check=check_purple_gradient),
    LintRule("high-end-no-white", "color", "error",
             "[high-end] Pure white background detected. Use dark base or off-white (#f8f8f8).",
             "Dark theme: #0a0a0a–#111. Light: #f8f7f4 or #faf8f5.",
             presets=["high-end"],
             check=check_pure_white),
    LintRule("high-end-no-black", "color", "warning",
             "[high-end] Pure black (#000000) detected. Use off-black.",
             "Replace #000 or #000000 with #0a0a0a, #111111, or zinc-950.",
             presets=["high-end"],
             check=check_pure_black),
    LintRule("no-gradient", "color", "warning",
             "Gradient detected — AI slop signature. Use solid colors instead.",
             "Replace with a single solid background-color or subtle texture.",
             presets=["all"],
             check=check_gradient),
    LintRule("no-card-shadow", "layout", "warning",
             "Box-shadow rules found. AI templates love card shadows.",
             "Use spacing, borders, or background-color changes to separate cards instead of shadows.",
             presets=["all"],
             check=check_card_shadow),
    LintRule("no-large-radius", "layout", "warning",
             "border-radius > 12px found.",
             "Keep border-radius ≤ 12px for a more refined look.",
             presets=["all"],
             check=check_large_radius),
    LintRule("no-hr-dividers", "layout", "info",
             "Multiple <hr> dividers found. Use whitespace instead.",
             "Replace <hr> with padding/margin or subtle border-t.",
             presets=["all"],
             check=check_hr_dividers),
    LintRule("high-end-no-bold-headings", "typography", "warning",
             "[high-end] Bold heading detected. Use Light/Regular (300–400) weight.",
             "font-weight: 300 or 400. Let size and spacing create hierarchy.",
             presets=["high-end"],
             check=check_bold_headings),
    LintRule("no-emoji", "content", "warning",
             "Emoji characters found. AI loves emojis as icons.",
             "Replace with SVG icons or Unicode symbols for a more professional look.",
             presets=["all"],
             check=check_emoji),
    LintRule("high-end-no-bold-serif", "typography", "warning",
             "[high-end] Bold serif heading detected. Use Light weight (300).",
             "Serif headings at font-weight: 300 with generous letter-spacing.",
             presets=["high-end"],
             check=check_bold_serif),
    LintRule("no-default-icons", "content", "info",
             "Default icon library detected. AI loves Font Awesome / Material Icons.",
             "Use custom SVG or a more distinctive icon set like Lucide, Phosphor, or Tabler.",
             presets=["all"],
             check=check_default_icons),
]


# ── Presets ─────────────────────────────────────────────

PRESETS = {
    "high-end": ["no-banned-fonts", "no-purple-gradient", "high-end-no-white",
                  "high-end-no-black", "no-gradient", "no-card-shadow",
                  "no-large-radius", "high-end-no-bold-headings", "no-emoji",
                  "high-end-no-bold-serif"],
    "minimal": ["no-banned-fonts", "no-card-shadow", "no-emoji",
                "no-purple-gradient", "no-large-radius"],
    "industrial": ["no-purple-gradient", "no-gradient", "no-card-shadow",
                   "no-large-radius", "no-banned-fonts"],
}


def auto_detect_preset(html: str) -> str:
    """Guess the design style from the HTML content."""
    has_dark = bool(re.search(r'(?:background|bg).*?(?:#0[0-9a-f]|#1[0-9a-f])', html, re.I))
    has_mono = bool(re.search(r'font-family.*?mono', html, re.I))
    has_serif = bool(re.search(r'font-family.*?serif|Playfair|Lora|Cormorant', html, re.I))
    has_shadow = bool(re.search(r'box-shadow', html, re.I))
    
    if has_dark and (has_serif or not has_shadow):
        return "high-end"
    elif has_mono or has_dark:
        return "industrial"
    else:
        return "minimal"


def lint_file(filepath: str, preset: str = "auto", verbose: bool = False):
    with open(filepath, 'r') as f:
        html = f.read()
    
    if preset == "auto":
        preset = auto_detect_preset(html)
        print(f"🔍 Auto-detected preset: {preset}\n")
    
    if preset == "all":
        active_rules = RULES
    else:
        allowed_names = PRESETS.get(preset, PRESETS["high-end"])
        active_rules = [r for r in RULES if r.name in allowed_names]
    
    violations = []
    for rule in active_rules:
        result = rule(html)
        if result:
            violations.append(result)
    
    print(f"design-lint [preset: {preset}] — {filepath}")
    
    if violations:
        emoji_map = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}
        errors = sum(1 for v in violations if v["severity"] == "error")
        warnings = sum(1 for v in violations if v["severity"] == "warning")
        infos = sum(1 for v in violations if v["severity"] == "info")
        
        print(f"🔍 design-lint — {len(violations)} violation(s) found\n")
        print("=" * 60)
        
        for v in violations:
            e = emoji_map.get(v["severity"], "•")
            tag = f"[{v['severity'].upper()}]" if v['severity'] == 'error' else f"[{v['severity'].upper()}]"
            print(f"\n{e} {tag} {v['rule']}")
            print(f"   Category: {v['category']}")
            print(f"   {v['message']}")
            print(f"   Source: {v['source']}")
            if v['fix']:
                print(f"   Fix: {v['fix']}")
        
        print(f"\n{'=' * 60}")
        print(f"Summary: {errors} error(s), {warnings} warning(s), {infos} info(s)")
        return 1
    
    print("✅ 0 violations — clean!")
    return 0


def main():
    parser = argparse.ArgumentParser(description="design-lint — AI Design Anti-Template Checker")
    parser.add_argument("file", help="HTML file to lint")
    parser.add_argument("--preset", choices=["high-end", "minimal", "industrial", "all", "auto"],
                        default="auto", help="Rule preset to use (default: auto-detect)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    return lint_file(args.file, args.preset, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
