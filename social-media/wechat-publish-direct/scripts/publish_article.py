#!/usr/bin/env python3
"""
微信公众号文章发布固化程序
==========================

确定性流程，不依赖临时字符串匹配。
每步有明确输入/输出，可独立验证。

用法:
    python3 publish_article.py \
        --article /tmp/article_test.md \
        --cover-seed lantern \
        --body-seeds road,night,watermelon \
        --output /tmp/wechat_final.html

凭证从 ~/.hermes/profiles/her-m2/.env 读取:
    - DEEPSEEK_API_KEY
    - WECHAT_APPID
    - WECHAT_SECRET
"""

import argparse
import hashlib
import html as html_lib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Union


# =============================================================================
# 网络工具 — WeChat API 走 Clash 系统代理（已配置节点白名单）
# =============================================================================
# 现在 Clash 规则中 api.weixin.qq.com 已改为走「节点选择」，
# 代理节点固定 IP 在微信白名单中，所以直接走标准库 + 系统代理即可。
# DeepSeek/picsum 也用标准库（不走 SOCKS5）。

TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}


def with_retries(operation, *, attempts=3, base_delay=1.0):
    """Retry transient network/API failures without hiding final errors."""
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in TRANSIENT_HTTP_CODES or attempt == attempts:
                raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == attempts:
                raise
        time.sleep(base_delay * attempt)
    raise last_error


# 微信 API 走系统代理（urllib.request 自动使用 macOS 系统代理设置）
def _wechat_post(path: str, body: bytes, headers: dict, timeout: int = 15) -> bytes:
    import urllib.request as urlreq
    url = f"https://api.weixin.qq.com{path}"
    req = urlreq.Request(url, data=body, headers=headers)
    return with_retries(lambda: urlreq.urlopen(req, timeout=timeout).read())

def _wechat_get(path: str, timeout: int = 15) -> bytes:
    import urllib.request as urlreq
    url = f"https://api.weixin.qq.com{path}"
    return with_retries(lambda: urlreq.urlopen(url, timeout=timeout).read())


# =============================================================================
# 常量
# =============================================================================

SKILL_DIR = Path(__file__).parent.parent
ENV_PATH = Path(
    os.environ.get("HERMES_ENV_PATH", "/Users/mac/.hermes/profiles/her-m2/.env")
)

DEESEEK_URL = "https://api.deepseek.com/chat/completions"
WECHAT_BASE = "https://api.weixin.qq.com"

PICSUM_BASE = "https://picsum.photos/seed/{}"
PICSUM_SIZE = "600/400"  # 封面 600x400, 正文 640x427
DEFAULT_DIGEST = "那年我们刚认识，他请我吃了一碗面，从此成了最好的兄弟。"

STYLES = {
    "article": (
        'style="font-family:Georgia,宋体,serif;'
        'font-size:15px;line-height:1.8;color:#333;'
        'padding:10px;"'
    ),
    "chapter": (
        'style="font-size:18px;color:#888;'
        'border-top:1px solid #ddd;padding-top:16px;'
        'margin-bottom:6px;"'
    ),
    "dropcap": (
        'style="float:left;font-size:3em;line-height:1;'
        'padding-right:5px;"'
    ),
    "img": (
        'style="display:block;margin:20px auto;'
        'max-width:100%;border-radius:8px;'
        'box-shadow:0 2px 8px rgba(0,0,0,0.1)"'
    ),
}


# =============================================================================
# 工具函数
# =============================================================================

def log(step, msg, icon="✓"):
    print(f"[{step}] {msg}", file=sys.stderr)


def extract_title_from_md(md_text: str) -> str:
    """从 Markdown 中提取标题（第一个 # 开头的一行，去除 # 和首尾空格）"""
    for line in md_text.split("\n"):
        line = line.strip()
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip()
    return ""


def truncate_utf8_bytes(text: str, max_bytes: int) -> str:
    """Trim a string to a UTF-8 byte budget without splitting characters."""
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore").rstrip()


def normalize_article_meta(title: str, digest: str) -> tuple[str, str]:
    """Apply WeChat byte limits before draft/add or draft/update."""
    return truncate_utf8_bytes(title, 55), truncate_utf8_bytes(digest, 115)


def normalize_body_seeds(body_seeds: Union[list[str], str]) -> list[str]:
    """Intent/parameter layer: normalize user or Hermes seed input."""
    if isinstance(body_seeds, str):
        body_seeds = body_seeds.split(",")
    return [seed.strip() for seed in body_seeds if seed and seed.strip()]


def infer_digest_from_md(md_text: str) -> str:
    """Deterministic digest fallback from the first real paragraph."""
    for block in split_markdown_blocks(md_text):
        if block.startswith("#"):
            continue
        text = re.sub(r"[*_`>#-]", "", block).strip()
        if text:
            return truncate_utf8_bytes(text, 115)
    return DEFAULT_DIGEST


def parse_publish_params(
    article_md: str,
    cover_seed: str,
    body_seeds: Union[list[str], str],
    title: str = "",
    author: str = "王波",
    digest: str = "",
):
    """
    Layer 1: Hermes/CLI intent normalization.

    AI should stop here: decide this is a publish request and fill these fields.
    Everything after this function is deterministic program flow.
    """
    parsed_title = title or extract_title_from_md(article_md) or "未命名文章"
    parsed_digest = digest or infer_digest_from_md(article_md)
    parsed_title, parsed_digest = normalize_article_meta(parsed_title, parsed_digest)
    return {
        "article_md": article_md,
        "cover_seed": (cover_seed or "lantern").strip(),
        "body_seeds": normalize_body_seeds(body_seeds),
        "title": parsed_title,
        "author": author or "王波",
        "digest": parsed_digest,
    }


def split_markdown_blocks(md_text: str) -> list[str]:
    """Split Markdown into non-empty paragraph/heading blocks."""
    blocks = []
    current = []
    for line in md_text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        if stripped.startswith("#") and current:
            blocks.append("\n".join(current).strip())
            current = []
        current.append(stripped)
    if current:
        blocks.append("\n".join(current).strip())
    return blocks


def render_inline_markdown(text: str) -> str:
    """Small deterministic inline renderer for WeChat-safe paragraph text."""
    escaped = html_lib.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped.replace("\n", "<br>")


def is_chapter_heading(text: str) -> bool:
    plain = text.lstrip("#").strip()
    return bool(re.match(r"^[一二三四五六七八九十]+[、.．]\s*.+", plain))


def markdown_to_wechat_html(md_text: str) -> str:
    """
    Layer 2: deterministic Markdown -> WeChat HTML renderer.

    This intentionally handles a conservative Markdown subset so the publishing
    pipeline is stable. AI can suggest text/metadata, but not own the HTML shape.
    """
    parts = [f"<div {STYLES['article']}>"]
    first_paragraph = True

    for block in split_markdown_blocks(md_text):
        if block.startswith("# "):
            continue

        if block.startswith("## ") or is_chapter_heading(block):
            heading = block.lstrip("#").strip()
            parts.append(f"<p {STYLES['chapter']}>{html_lib.escape(heading)}</p>")
            continue

        rendered = render_inline_markdown(block)
        if first_paragraph and rendered:
            first_char = rendered[0]
            rendered = (
                f"<span {STYLES['dropcap']}>{first_char}</span>"
                f"{rendered[1:]}"
            )
            first_paragraph = False
        parts.append(f"<p>{rendered}</p>")

    parts.append("</div>")
    return "\n".join(parts)


def read_env():
    """从 .env 文件读取凭证"""
    if not ENV_PATH.exists():
        print(f"ERROR: {ENV_PATH} not found", file=sys.stderr)
        sys.exit(1)
    
    env = {}
    with open(ENV_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val.startswith("***") and len(val) > 5:
                    # Redacted value - try to reconstruct or use alternative
                    continue
                env[key] = val
    return env


def get_access_token(appid, secret):
    """获取微信 access_token"""
    path = (f"/cgi-bin/token?"
           f"grant_type=client_credential&appid={appid}&secret={secret}")
    raw = _wechat_get(path, timeout=10)
    data = json.loads(raw)
    if "access_token" not in data:
        raise ValueError(f"Failed to get token: {data}")
    return data["access_token"]


def download_image(seed):
    """从 picsum.photos 下载图片，返回 bytes"""
    url = PICSUM_BASE.format(seed) + "/" + PICSUM_SIZE
    # urllib 自动跟重定向（picsum 302 → fastly），picsum 不走 SOCKS5
    import urllib.request as urlreq
    return with_retries(lambda: urlreq.urlopen(url, timeout=10).read())


def upload_image_for_content(access_token, image_bytes):
    """
    通过 media/uploadimg 上传正文图片，返回微信 CDN URL。
    
    media/uploadimg 不占用素材库名额，返回的 URL 可直接用于 draft/add 正文中的 <img src>。
    """
    path = f"/cgi-bin/media/uploadimg?access_token={access_token}"
    
    boundary = hashlib.md5(str(time.time()).encode()).hexdigest()
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"media\"; "
        f"filename=\"img.jpg\"\r\n"
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()
    
    raw = _wechat_post(path, body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        timeout=15)
    data = json.loads(raw)
    if "url" not in data:
        raise ValueError(f"Upload content image failed: {data}")
    return data["url"]  # e.g. "http://mmbiz.qpic.cn/XXXXX"


def upload_to_wechat(access_token, image_bytes, img_type="image"):
    """上传图片到微信素材库，返回 media_id"""
    path = (f"/cgi-bin/material/add_material?"
           f"access_token={access_token}&type=image")
    
    boundary = hashlib.md5(str(time.time()).encode()).hexdigest()
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"media\"; "
        f"filename=\"img.jpg\"\r\n"
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()
    
    raw = _wechat_post(path, body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        timeout=15)
    data = json.loads(raw)
    if "media_id" not in data:
        raise ValueError(f"Upload failed: {data}")
    return data["media_id"]


def call_deepseek(article_text, appid, secret):
    """
    调用 DeepSeek 排版文章，返回纯文字 HTML（不含任何图片标签）
    
    关键：明确要求不要图片，只排版文字
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        env = read_env()
        api_key = env.get("DEEPSEEK_API_KEY", "")
    
    if not api_key or api_key.startswith("***"):
        log("ERROR", "DEEPSEEK_API_KEY not available (missing or redacted)", "✗")
        sys.exit(1)
    
    prompt = (
        "你是一个专业的微信公众号排版助手。"
        "请将以下 Markdown 文章排版为微信编辑器可用的 HTML。"
        "\n\n要求：\n"
        "1. 输出纯 HTML，不要 <!DOCTYPE>、<html>、<head>、<body> 标签，"
        "只要正文内容（<div>...</div> 内部）。\n"
        "2. 不要插入任何 <img> 标签！只排版文字。\n"
        "3. 不要使用 markdown 代码块包裹输出。\n"
        "4. 样式：\n"
        "   - 文章容器：<div style=\"font-family:Georgia,'宋体',serif;"
        "font-size:15px;line-height:1.8;color:#333;padding:10px;\">\n"
        "   - 章标题（一、二、三、四）：<p style=\"font-size:18px;"
        "color:#888;border-top:1px solid #ddd;padding-top:16px;"
        "margin-bottom:6px;\">章节号</p>\n"
        "   - 首段首字下沉：<span style=\"float:left;font-size:3em;"
        "line-height:1;padding-right:5px;\">首字</span>\n"
        "   - 段落间距：每个段落之间空一行\n"
        "5. 不要在正文中包含标题和作者，微信会自动显示标题。正文直接以首段开头。\n"
        "\n文章：\n"
        + article_text
    )
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # DeepSeek 不走 SOCKS5，用标准库（避免自制 HTTP 的 chunked encoding bug）
    import urllib.request as urlreq
    req = urlreq.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(payload).encode(),
        headers=headers,
    )
    raw = with_retries(lambda: urlreq.urlopen(req, timeout=60).read(), attempts=2)
    result = json.loads(raw.decode())
    
    html = result["choices"][0]["message"]["content"].strip()
    
    # Remove markdown code blocks if present
    if "```" in html:
        parts = html.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Even index is code block content
                html = part
                break
    
    return html.strip()


def is_html_document(text: str) -> bool:
    """判断输入是否为完整 HTML 文档（直通模式触发条件）。"""
    stripped = text.lstrip().lower()
    return stripped.startswith("<!doctype") or stripped.startswith("<html")


def extract_body(html: str) -> str:
    """提取 <body> 内容；无 body 标签则原样返回。"""
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.S)
    return m.group(1) if m else html


def sanitize_html(html: str) -> str:
    """清洗异常 Unicode：U+FFFC/U+FFFD/零宽字符。"""
    return re.sub(r"[\ufffc\ufffd\u200b-\u200f\ufeff]", "", html)


def strip_layout_image_blocks(html: str) -> str:
    """直通模式：剥离排版引擎已插入的图片块（picsum 占位图 + caption），
    由发布流程在解析后的新位置重新插入微信 CDN 图片。

    图片块结构（quality_layout 输出）:
        <div class="wechat-image-block">
          <img ...>
          <div class="wechat-image-caption">...</div>
        </div>
    注意：必须连带外层 </div> 一起删，非贪婪匹配会留下孤立 </div>
    （微信解析器遇孤立闭合标签会截断正文）。
    """
    block_pattern = re.compile(
        r'<div class="wechat-image-block">.*?</div>\s*</div>', re.S
    )
    prev = None
    while prev != html:
        prev = html
        html = block_pattern.sub("", html)
    html = re.sub(r"<img[^>]*>", "", html)
    # 清理剥离后残留的空段落（配图建议标记清理留下的空壳）
    html = re.sub(r'<p class="wechat-paragraph">\s*</p>', "", html)
    return html


def validate_html_structure(html: str) -> None:
    """发布前 HTML 结构自检：标签配对（重点防孤立闭合标签）。

    微信解析器遇无配对开标签的孤立 </div> 等闭合标签会直接丢弃
    其后全部正文（2026-08-22 #12 截断事故根因）。用标签栈检查
    成对标签是否闭合。img/br/hr 为空元素，p 允许不闭合，均不检查。
    """
    stack = []
    for m in re.finditer(
        r'<(/?)(div|blockquote|section|table|ul|ol|h1|h2|h3)\b[^>]*>', html
    ):
        closing, tag = m.group(1), m.group(2)
        if not closing:
            stack.append(tag)
        else:
            if not stack or stack[-1] != tag:
                raise ValueError(
                    f"HTML 结构异常: 多余的闭合 </{tag}> (位置 {m.start()})。"
                    f"正文会被微信截断，请检查排版输出")
            stack.pop()
    if stack:
        raise ValueError(f"HTML 结构异常: 未闭合标签 {stack}。请检查排版输出")


def verify_draft_integrity(access_token, media_id, sent_content, title):
    """发布后回读草稿，验证内容完整性（微信可能静默截断且 errcode=0）。

    返回 (ok: bool, reason: str)
    """
    raw = _wechat_post(
        f"/cgi-bin/draft/get?access_token={access_token}",
        json.dumps({"media_id": media_id}).encode(),
        {"Content-Type": "application/json"}, timeout=15)
    saved = json.loads(raw)["news_item"][0].get("content", "")

    # 1. 长度检查（微信规范化允许 ±10%）
    if len(saved) < len(sent_content) * 0.9:
        return False, f"内容截断: 回读 {len(saved)} < 发送 {len(sent_content)}"

    # 2. 开头/结尾标记检查（纯文本前 20 / 后 20 字）
    def visible_text(html):
        return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", html))

    sent_visible, saved_visible = visible_text(sent_content), visible_text(saved)
    head_mark, tail_mark = sent_visible[:20], sent_visible[-20:]
    if head_mark not in saved_visible:
        return False, f"开头标记缺失: {head_mark[:12]}..."
    if tail_mark not in saved_visible:
        return False, f"结尾标记缺失: ...{tail_mark[-12:]}"

    # 3. 图片数量检查（微信可能把 src 规范化为 data-src）
    sent_imgs = len(re.findall(r"<img", sent_content))
    saved_imgs = len(re.findall(r"<img[^>]*src=", saved))
    if saved_imgs < sent_imgs:
        return False, f"图片缺失: 回读 {saved_imgs} < 发送 {sent_imgs}"

    return True, f"{len(saved)} chars / {saved_imgs} imgs / 头尾标记在位"


def parse_article_html(html):
    """
    解析排版后的 HTML，找到：
    - 文章容器 div
    - 各章标题位置
    - 正文段落位置
    
    返回结构化数据，用于确定配图插入点。
    """
    # 找到文章容器（兼容 quality_layout 的 class 体系 与 DeepSeek 的 inline style 体系）
    container_match = re.search(
        r'<div(?:\s+class="wechat-article"|\s+style="font-family:[^"]*")[^>]*>', html
    )
    if not container_match:
        raise ValueError("Could not find article container div")
    
    container_start = container_match.start()
    
    # 找容器 div 的闭合标签位置（图片不能插到 </div> 外面）
    container_end_match = re.search(r'</div>\s*$', html)
    container_end = container_end_match.start() if container_end_match else len(html)
    
    # 找到所有章标题（兼容两种格式）：
    # quality_layout: <h2 class="wechat-section">一、标题</h2>
    # DeepSeek: <p style="font-size:18px;color:#888...">一、标题</p>
    chapter_pattern = (
        r'<h2 class="wechat-section">[^<]*</h2>'
        r'|<p style="font-size:18px;color:#888[^"]*">[一二三四五六七八九十]、?[^<]*</p>'
    )
    chapters = list(re.finditer(chapter_pattern, html))
    
    # 找到所有段落
    paragraph_pattern = r'<p[^>]*>.*?</p>'
    paragraphs = list(re.finditer(paragraph_pattern, html))
    
    return {
        "container_start": container_start,
        "container_end": container_end,
        "chapters": chapters,
        "paragraphs": paragraphs,
        "html_length": len(html),
    }


def find_insertion_points(parsed, body_image_count=0, seed_count=0):
    """
    根据解析结果，确定配图插入位置。
    
    插入策略：
    - 封面图：放在第一个章标题之前（或文章开头）
    - 正文配图：优先分配到每章之间
    - 如果正文图多于章间隙，多余的均匀分配到段落之间（不堆末尾）
    
    返回恰好 1 + body_image_count 个插入位置的 HTML 偏移量列表。
    """
    chapters = parsed["chapters"]
    paragraphs = parsed["paragraphs"]
    fallback_end = parsed["container_end"]
    total_body = body_image_count  # 正文图数量（不含封面）
    positions = []
    
    # 封面插入点
    if chapters:
        positions.append(chapters[0].start())
    else:
        positions.append(fallback_end)
    
    # 正文配图插入点
    body_positions = []
    
    if chapters:
        # 优先分配到每章之前（跳过第一章，留给封面了）
        chapter_slots = [ch.start() for ch in chapters[1:]]
        body_positions.extend(chapter_slots)
    
    # 如果正文图多于章间隙，分配到段落之间
    # 用 paragraphs 作为额外插槽（跳过首段前面的）
    extra_needed = total_body - len(body_positions)
    if extra_needed > 0 and len(paragraphs) > 2:
        # 取中间段落（跳过首尾），均匀取 extra_needed 个
        middle_paras = paragraphs[1:-1]
        step = max(1, len(middle_paras) // (extra_needed + 1))
        for i in range(extra_needed):
            idx = min((i + 1) * step, len(middle_paras) - 1)
            body_positions.append(middle_paras[idx].end())
    
    # 如果还不够，回退到容器末尾
    while len(body_positions) < total_body:
        body_positions.append(fallback_end)
    
    positions.extend(body_positions[:total_body])
    
    return positions


def insert_image_tags(html, positions, seeds, image_style):
    """
    在指定位置插入图片标签。
    
    关键：按从后往前的顺序插入，避免偏移量变化。
    """
    # 从后往前插入，保证位置不变
    img_tags = []
    for seed in seeds:
        img_tags.append(
            f'<img src="https://picsum.photos/seed/{seed}/{PICSUM_SIZE}" '
            f'{image_style}>'
        )
    
    # 配对：positions[0] = 封面, positions[1:] = 正文配图
    if len(img_tags) != len(positions):
        raise ValueError(
            f"Image count ({len(img_tags)}) != position count ({len(positions)})"
        )
    
    # 从后往前插入
    for pos, img_tag in sorted(zip(positions, img_tags), reverse=True):
        html = html[:pos] + "\n\n" + img_tag + "\n" + html[pos:]
    
    return html


def replace_picsum_with_wechat_urls(html, wechat_urls):
    """
    将 HTML 中 picsum 图片标签的 src 替换为微信 CDN URL。
    
    按图片插入顺序一一对应替换 src 属性值，不动标签结构。
    """
    # 匹配完整的 <img> 标签（包含 picsum src）
    picsum_img_pattern = (
        r'<img\s+[^>]*src="https://picsum\.photos/seed/[^"]*"[^>]*>'
    )
    picsum_tags = re.findall(picsum_img_pattern, html)
    
    if len(picsum_tags) != len(wechat_urls):
        raise ValueError(
            f"Picsum img tag count ({len(picsum_tags)}) "
            f"!= wechat_url count ({len(wechat_urls)})"
        )
    
    for old_tag, wx_url in zip(picsum_tags, wechat_urls):
        if not re.match(r'^https?://mmbiz\.qpic\.cn/', wx_url):
            raise ValueError(f"Invalid WeChat CDN URL: {wx_url}")
        # 只替换完整 src 属性值，不动标签其他部分。
        new_tag = re.sub(
            r'src="https://picsum\.photos/seed/[^"]*"',
            f'src="{wx_url}"',
            old_tag,
            count=1,
        )
        html = html.replace(old_tag, new_tag, 1)
    
    return html


def find_existing_draft(access_token, title):
    """查找同名草稿，返回 (exists: bool, draft_media_id: str|None)"""
    path = (f"/cgi-bin/draft/batchget?"
           f"access_token={access_token}")
    payload = {
        "offset": 0,
        "count": 20,
        "no_content": 1,  # 不返回正文内容，节省带宽
    }
    raw = _wechat_post(path, json.dumps(payload).encode(),
                       {"Content-Type": "application/json"}, timeout=15)
    result = json.loads(raw)
    
    if "item" in result:
        for item in result["item"]:
            draft_title = ""
            if "content" in item and "news_item" in item["content"]:
                news = item["content"]["news_item"]
                if news and isinstance(news, list):
                    draft_title = news[0].get("title", "")
            if draft_title == title:
                return True, item.get("media_id", "")
    
    return False, None


def create_draft(access_token, title, author, digest, content, 
                 thumb_media_id):
    """创建或更新微信草稿（自动查重，避免重复创建）"""
    title, digest = normalize_article_meta(title, digest)

    # 先查重
    exists, existing_mid = find_existing_draft(access_token, title)
    
    if exists and existing_mid:
        # 更新已有草稿
        log("DRAFT", f"Found existing draft: {existing_mid[:20]}..., updating")
        # 注意：draft/update 的 articles 是【对象】；draft/add 才是数组
        # （用数组会报 47001 data format error，或静默不更新 content）
        payload = {
            "media_id": existing_mid,
            "index": 0,
            "articles": {
                "title": title,
                "author": author,
                "digest": digest,
                "content": content,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 1,
                "only_fans_can_comment": 0,
            }
        }
        path = f"/cgi-bin/draft/update?access_token={access_token}"
        raw = _wechat_post(path,
                        json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                        {"Content-Type": "application/json"}, timeout=15)
        result = json.loads(raw)
        if result.get("errcode", 1) != 0:
            raise ValueError(f"Update draft failed: {result}")
        log("DRAFT", f"Draft updated: media_id={existing_mid[:20]}...")

        # 微信 draft/update 存在静默不更新 content 的坑（2026-08-22 实测：
        # update 返回 errcode=0 但正文仍是旧截断内容）。
        # 对策：update 后 GET 回读验证 content 长度，未生效则删旧重建。
        try:
            raw2 = _wechat_post(
                f"/cgi-bin/draft/get?access_token={access_token}",
                json.dumps({"media_id": existing_mid}).encode(),
                {"Content-Type": "application/json"}, timeout=15)
            saved = json.loads(raw2)["news_item"][0].get("content", "")
            if len(saved) >= len(content) * 0.9:
                log("DRAFT", f"Draft content verified: {len(saved)} chars ✓")
                return existing_mid
            log("DRAFT", f"update 未生效 (saved {len(saved)} vs sent {len(content)})"
                         f"，降级为删除重建", "⚠")
        except Exception as e:
            log("DRAFT", f"update 验证异常: {e}，降级为删除重建", "⚠")

        # 降级：删除旧草稿，走 add 路径
        del_path = f"/cgi-bin/draft/delete?access_token={access_token}"
        raw_del = _wechat_post(
            del_path, json.dumps({"media_id": existing_mid}).encode(),
            {"Content-Type": "application/json"}, timeout=15)
        log("DRAFT", f"旧草稿已删除: {json.loads(raw_del)}")
        # 继续走下方 add 分支
    
    # 不存在则新建
    path = f"/cgi-bin/draft/add?access_token={access_token}"
    
    payload = {
        "articles": [{
            "title": title,
            "author": author,
            "digest": digest,
            "content": content,
            "content_action": 0,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
        }]
    }
    
    raw = _wechat_post(path,
                    json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    {"Content-Type": "application/json"}, timeout=15)
    result = json.loads(raw)
    
    if "media_id" not in result:
        raise ValueError(f"Create draft failed: {result}")
    
    return result["media_id"]


# =============================================================================
# 主流程
# =============================================================================

def publish_workflow(
    article_md: str,
    cover_seed: str,
    body_seeds: list[str],
    appid: str,
    secret: str,
    title: str = "",
    author: str = "王波",
    digest: str = "",
    layout_provider: str = "deterministic",
    dry_run: bool = False,
) -> dict:
    """
    端到端发布流程，每步输出验证日志。
    
    返回:
        {
            "draft_media_id": "...",
            "html_length": int,
            "image_count": int,
            "verification_log": list[str],
        }
    """
    params = parse_publish_params(
        article_md=article_md,
        cover_seed=cover_seed,
        body_seeds=body_seeds,
        title=title,
        author=author,
        digest=digest,
    )
    article_md = params["article_md"]
    cover_seed = params["cover_seed"]
    body_seeds = params["body_seeds"]
    title = params["title"]
    author = params["author"]
    digest = params["digest"]

    log("INIT", f"Starting workflow: article={len(article_md)} chars, "
               f"seeds={cover_seed} + {body_seeds}, "
               f"layout={layout_provider}, dry_run={dry_run}")
    
    # ---- Step 0/1: 直通模式（输入已是完整 HTML）----
    if is_html_document(article_md):
        log("STEP 0", "检测到已排版 HTML → 直通模式")
        html = extract_body(article_md)
        html = strip_layout_image_blocks(html)
        html = sanitize_html(html).strip()
        log("STEP 1", f"直通模式: 提取 body {len(html)} chars, "
                     f"已有图片 {len(re.findall(r'<img', html))} 张 (全部重插)")
    elif layout_provider == "deterministic":
        log("STEP 1", "Rendering Markdown with deterministic layout engine...")
        html = markdown_to_wechat_html(article_md)
    elif layout_provider == "deepseek":
        log("STEP 1", "Calling DeepSeek for optional HTML layout...")
        html = call_deepseek(article_md, appid, secret)
    else:
        raise ValueError(f"Unknown layout provider: {layout_provider}")
    
    # 发布前结构自检（防孤立闭合标签导致微信截断）
    validate_html_structure(html)

    # 验证：不应该有图片
    img_count_step1 = len(re.findall(r'<img', html))
    log("STEP 1", f"排版完成: {len(html)} chars, "
               f"{img_count_step1} images (should be 0)")
    if img_count_step1 > 0:
        log("STEP 1", "WARNING: layout returned images, will strip them", "⚠")
        # Remove all img tags
        html = re.sub(r'<img[^>]*>', '', html)
    
    # ---- Step 2: 解析插入点 ----
    log("STEP 2", "Parsing HTML structure...")
    parsed = parse_article_html(html)
    chapters_count = len(parsed["chapters"])
    total_images = 1 + len(body_seeds)  # 封面 + 正文配图
    positions = find_insertion_points(parsed, body_image_count=len(body_seeds))
    
    log("STEP 2", f"章标题数: {chapters_count}, 插入点: {len(positions)} "
               f"(封面+{len(body_seeds)}正文)")
    
    # ---- Step 3: 下载并上传配图 ----
    all_seeds = [cover_seed] + body_seeds
    if dry_run:
        log("STEP 3", f"Dry run: using fake WeChat CDN URLs for {total_images} images...")
        cover_media_id = "dry_run_cover_media_id"
        all_wechat_urls = [
            f"http://mmbiz.qpic.cn/dry-run/{i + 1}-{seed}"
            for i, seed in enumerate(all_seeds)
        ]
        body_wechat_urls = all_wechat_urls[1:]
    else:
        token = get_access_token(appid, secret)
        log("STEP 3", f"Downloading and uploading {total_images} images...")
        img_bytes_list = []
        for seed in all_seeds:
            img_bytes = download_image(seed)
            img_bytes_list.append(img_bytes)
            log("STEP 3", f"  Downloaded {seed}: {len(img_bytes)} bytes")
        
        # 封面图：用 material/add_material 获取 media_id（用于 thumb_media_id）
        cover_media_id = upload_to_wechat(token, img_bytes_list[0], "image")
        log("STEP 3", f"  封面上传完成: media_id={cover_media_id[:20]}...")
        
        # 封面图也上传 media/uploadimg 获取微信 CDN URL（用于正文第一张图）
        cover_wechat_url = upload_image_for_content(token, img_bytes_list[0])
        log("STEP 3", f"  封面 URL: {cover_wechat_url[:40]}...")
        
        # 正文配图：用 media/uploadimg 获取微信 CDN URL（用于正文 <img src>）
        body_wechat_urls = []
        for i, img_bytes in enumerate(img_bytes_list[1:], 1):
            wx_url = upload_image_for_content(token, img_bytes)
            body_wechat_urls.append(wx_url)
            log("STEP 3", f"  [{i}] seed={all_seeds[i]}, wx_url={wx_url[:40]}...")
        
        all_wechat_urls = [cover_wechat_url] + body_wechat_urls
        log("STEP 3", f"All {total_images} images uploaded ✓")
    
    # ---- Step 4: 插入图片标签（先用 picsum URL 占位）----
    log("STEP 4", "Inserting image tags at determined positions...")
    # all_seeds = [cover_seed] + body_seeds → 正文图片用 body_wechat_urls 替换
    html = insert_image_tags(
        html, positions, all_seeds, STYLES["img"]
    )
    
    img_count_step4 = len(re.findall(r'<img', html))
    log("STEP 4", f"图片插入完成: {img_count_step4} images "
               f"(expected {total_images})")
    if img_count_step4 != total_images:
        raise ValueError(
            f"Image count mismatch: {img_count_step4} != {total_images}"
        )
    
    # ---- Step 5: 替换 picsum URL 为微信 CDN URL ----
    log("STEP 5", "Replacing picsum URLs with WeChat CDN URLs...")
    html = replace_picsum_with_wechat_urls(html, all_wechat_urls)
    
    # 正文中所有图片都已替换为微信 CDN URL
    picsum_remaining = len(re.findall(r'picsum\.photos', html))
    if picsum_remaining > 0:
        # 封面图在正文中的标签也需替换
        log("STEP 5", f"WARNING: {picsum_remaining} picsum URLs remain in cover!", "⚠")
    else:
        log("STEP 5", f"所有图片已替换为微信 CDN URL ✓")
    
    # ---- Step 6: 创建草稿 ----
    if dry_run:
        log("STEP 6", "Dry run: skipping WeChat draft creation.")
        draft_media_id = "dry_run_draft_media_id"
    else:
        log("STEP 6", "Creating WeChat draft...")
        draft_media_id = create_draft(
            token, title, author, digest, html, cover_media_id
        )
        log("STEP 6", f"草稿创建成功: media_id={draft_media_id[:20]}...")

        # ---- Step 7: 发布后完整性验证（防微信静默截断）----
        log("STEP 7", "Verifying draft integrity (回读验证)...")
        ok, reason = verify_draft_integrity(token, draft_media_id, html, title)
        if not ok:
            log("STEP 7", f"验证失败: {reason} → 删除重建重试", "⚠")
            _wechat_post(
                f"/cgi-bin/draft/delete?access_token={token}",
                json.dumps({"media_id": draft_media_id}).encode(),
                {"Content-Type": "application/json"}, timeout=15)
            draft_media_id = create_draft(
                token, title, author, digest, html, cover_media_id
            )
            ok, reason = verify_draft_integrity(token, draft_media_id, html, title)
            if not ok:
                raise ValueError(
                    f"草稿创建成功但内容不完整（重试后仍失败）: {reason}")
        log("STEP 7", f"完整性验证通过 ✓ ({reason})")
    
    return {
        "draft_media_id": draft_media_id,
        "html_length": len(html),
        "image_count": img_count_step4,
        "cover_media_id": cover_media_id,
        "body_wechat_urls": body_wechat_urls,
        "final_html": html,
        "title": title,
        "digest": digest,
        "layout_provider": layout_provider,
        "dry_run": dry_run,
        "integrity_verified": (not dry_run),
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="微信公众号文章发布固化程序"
    )
    parser.add_argument(
        "--article", required=True,
        help="Markdown 文章文件路径"
    )
    parser.add_argument(
        "--cover-seed", default="lantern",
        help="封面图 picsum seed (default: lantern)"
    )
    parser.add_argument(
        "--body-seeds", default="road,night,watermelon",
        help="正文配图 seed 列表，逗号分隔 (default: road,night,watermelon)"
    )
    parser.add_argument(
        "--author", default="王波",
        help="作者名"
    )
    parser.add_argument(
        "--title", default="",
        help="文章标题（留空则从 Markdown 第一个 # 标题提取）"
    )
    parser.add_argument(
        "--digest", default="",
        help="文章摘要（留空则使用默认）"
    )
    parser.add_argument(
        "--output", default=None,
        help="保存最终 HTML 的文件路径"
    )
    parser.add_argument(
        "--layout-provider", default="deterministic",
        choices=["deterministic", "deepseek"],
        help="排版来源：默认 deterministic；deepseek 仅作为兼容模式"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只生成最终 HTML，不下载图片、不上传微信、不创建草稿"
    )
    parser.add_argument(
        "--appid", default=None,
        help="微信 AppID（默认从 .env 读取）"
    )
    parser.add_argument(
        "--secret", default=None,
        help="微信 AppSecret（默认从 .env 读取）"
    )
    
    args = parser.parse_args()
    
    # 读取文章
    with open(args.article, "r", encoding="utf-8") as f:
        article_md = f.read()
    
    # 读取凭证
    env = {} if args.dry_run else read_env()
    appid = args.appid or env.get("WECHAT_APPID", "wx37940d296d26c91c")
    secret = args.secret or env.get("WECHAT_SECRET", "")
    
    if not args.dry_run and (not secret or secret.startswith("***")):
        log("ERROR", "WECHAT_SECRET not available in .env", "✗")
        sys.exit(1)
    
    body_seeds = normalize_body_seeds(args.body_seeds)
    
    # 执行
    try:
        result = publish_workflow(
            article_md=article_md,
            cover_seed=args.cover_seed,
            body_seeds=body_seeds,
            appid=appid,
            secret=secret,
            title=args.title,
            author=args.author,
            digest=args.digest,
            layout_provider=args.layout_provider,
            dry_run=args.dry_run,
        )
        
        print(f"\n{'='*50}")
        print("✓✓✓ 干跑完成!" if args.dry_run else "✓✓✓ 发布完成!")
        print(f"标题: {result['title']}")
        print(f"摘要: {result['digest']}")
        print(f"草稿 Media ID: {result['draft_media_id']}")
        print(f"HTML 大小: {result['html_length']} 字符")
        print(f"配图数量: {result['image_count']}")
        if result.get('integrity_verified'):
            print(f"完整性: 已回读验证 ✓")
        print(f"{'='*50}")
        
        # 保存最终 HTML
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result["final_html"], encoding="utf-8")
            log("OUTPUT", f"Final HTML saved to {args.output}", "✓")
        
        print(f"\n[验证日志]")
        print(f"  封面 media_id: {result['cover_media_id'][:40]}...")
        for i, url in enumerate(result["body_wechat_urls"]):
            print(f"  正文图[{i}]: {url[:50]}...")
        
    except Exception as e:
        log("ERROR", str(e), "✗")
        sys.exit(1)


if __name__ == "__main__":
    main()
