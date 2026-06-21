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


# =============================================================================
# 网络工具 — 绕过 macOS CFNetwork 系统代理
# =============================================================================
# macOS 系统级代理（Clash/Surge/Shadowrocket 等）在端口 7897，
# 会让 urllib、http.client、requests 全部走代理，导致微信 API 拒绝（IP 不在白名单）。
# 必须用 raw socket + ssl 完全绕过系统代理。

import socket
import ssl
import struct
from urllib.parse import urlparse

# SOCKS5 代理配置 — 用于固定出口 IP（解决公众号 IP 白名单动态变化问题）
SOCKS5_PROXY = None  # (host, port) 或 None
SOCKS5_HOSTS = {"api.weixin.qq.com"}  # 仅这些域名走代理


def _socks5_connect(target_host: str, target_port: int, timeout: int = 15):
    """通过 SOCKS5 代理连接目标主机，本地解析 DNS"""
    proxy_host, proxy_port = SOCKS5_PROXY
    
    # 本地解析目标 IP
    target_ip = socket.gethostbyname(target_host)
    
    # 连接代理
    s = socket.create_connection((proxy_host, proxy_port), timeout=timeout)
    
    # SOCKS5 握手: 无认证
    s.send(b"\x05\x01\x00")
    resp = s.recv(2, socket.MSG_WAITALL)
    if resp != b"\x05\x00":
        raise OSError(f"SOCKS5 handshake failed: {resp.hex()}")
    
    # SOCKS5 CONNECT: IPv4
    req = b"\x05\x01\x00\x01" + socket.inet_aton(target_ip) + struct.pack("!H", target_port)
    s.send(req)
    resp = s.recv(10, socket.MSG_WAITALL)
    if resp[1] != 0x00:
        raise OSError(f"SOCKS5 connect failed: code={resp[1]}")
    
    return s


def _build_request(method: str, host: str, path: str, body: bytes = None,
                   headers: dict = None, timeout: int = 15) -> str:
    """用 raw socket + ssl 构建完整 HTTP 请求，绕过系统代理"""
    # 创建连接：微信 API 走 SOCKS5，其他直连
    if SOCKS5_PROXY and host in SOCKS5_HOSTS:
        sock = _socks5_connect(host, 443, timeout=timeout)
    else:
        sock = socket.create_connection((host, 443), timeout=timeout)
    
    try:
        # 创建 SSL 上下文（不使用系统代理）
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ssl_sock = ctx.wrap_socket(sock, server_hostname=host)
        
        # 构建 HTTP 请求行
        if method == "GET":
            req = f"{method} {path} HTTP/1.1\r\n"
        else:
            req = f"{method} {path} HTTP/1.1\r\n"
        
        req += f"Host: {host}\r\n"
        if body:
            req += f"Content-Length: {len(body)}\r\n"
        if headers:
            for k, v in headers.items():
                req += f"{k}: {v}\r\n"
        req += "Connection: close\r\n"
        req += "\r\n"
        
        ssl_sock.send(req.encode())
        if body:
            ssl_sock.send(body)
        
        # 读取响应
        chunks = []
        ssl_sock.settimeout(timeout)
        while True:
            try:
                chunk = ssl_sock.recv(8192)
                if not chunk:
                    break
                chunks.append(chunk)
            except socket.timeout:
                break
        
        return b"".join(chunks).decode("utf-8", errors="replace")
    
    finally:
        try:
            ssl_sock.close()
        except:
            sock.close()


def _extract_body(http_response: str) -> bytes:
    """从 HTTP 响应字符串中提取 body"""
    if "\r\n\r\n" in http_response:
        return http_response.split("\r\n\r\n", 1)[1].encode("utf-8")
    return b""


def _http_post(host: str, path: str, body: bytes, headers: dict, timeout: int = 15) -> bytes:
    """POST 请求，raw socket + ssl，不经过系统代理"""
    raw = _build_request("POST", host, path, body=body, headers=headers, timeout=timeout)
    return _extract_body(raw)


def _http_get(host: str, path: str, timeout: int = 15) -> bytes:
    """GET 请求，raw socket + ssl，不经过系统代理"""
    raw = _build_request("GET", host, path, timeout=timeout)
    return _extract_body(raw)


def _http_download(url: str, timeout: int = 10) -> bytes:
    """下载远程文件（图片），raw socket + ssl，不经过系统代理"""
    parsed = urlparse(url)
    host = parsed.hostname
    path = parsed.path + ("?" + parsed.query if parsed.query else "")
    raw = _build_request("GET", host, path, timeout=timeout)
    return _extract_body(raw)


# =============================================================================
# 常量
# =============================================================================

SKILL_DIR = Path(__file__).parent.parent
ENV_PATH = Path("/Users/mac/.hermes/profiles/her-m2/.env")

DEESEEK_URL = "https://api.deepseek.com/chat/completions"
WECHAT_BASE = "https://api.weixin.qq.com"

PICSUM_BASE = "https://picsum.photos/seed/{}"
PICSUM_SIZE = "600/400"  # 封面 600x400, 正文 640x427

STYLES = {
    "article": (
        'style="font-family:Georgia,\\"宋体\\",serif;'
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
    raw = _http_get("api.weixin.qq.com", path, timeout=10)
    data = json.loads(raw)
    if "access_token" not in data:
        raise ValueError(f"Failed to get token: {data}")
    return data["access_token"]


def download_image(seed):
    """从 picsum.photos 下载图片，返回 bytes"""
    url = PICSUM_BASE.format(seed) + "/" + PICSUM_SIZE
    return _http_download(url, timeout=10)


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
    
    raw = _http_post(
        "api.weixin.qq.com", path, body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        timeout=15
    )
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
        "5. 标题和作者单独一行，不加 <p> 标签。\n"
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
    
    req_body = json.dumps(payload).encode()
    headers_raw = "\r\n".join(f"{k}: {v}" for k, v in headers.items())
    raw_resp = _http_post("api.deepseek.com", "/chat/completions", req_body,
                          {k: v for k, v in headers.items()}, timeout=60)
    result = json.loads(raw_resp)
    
    html = result["choices"][0]["message"]["content"].strip()
    
    # Remove markdown code blocks if present
    if "```" in html:
        parts = html.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Even index is code block content
                html = part
                break
    
    return html.strip()


def parse_article_html(html):
    """
    解析排版后的 HTML，找到：
    - 文章容器 div
    - 各章标题位置
    - 正文段落位置
    
    返回结构化数据，用于确定配图插入点。
    """
    # 找到文章容器
    container_match = re.search(
        r'<div style="font-family:[^"]*">', html
    )
    if not container_match:
        raise ValueError("Could not find article container div")
    
    container_start = container_match.start()
    
    # 找到所有章标题
    chapter_pattern = r'<p style="font-size:18px;color:#888[^"]*">[一二三四五六七八九十]</p>'
    chapters = list(re.finditer(chapter_pattern, html))
    
    # 找到所有段落
    paragraph_pattern = r'<p[^>]*>.*?</p>'
    paragraphs = list(re.finditer(paragraph_pattern, html))
    
    return {
        "container_start": container_start,
        "chapters": chapters,
        "paragraphs": paragraphs,
        "html_length": len(html),
    }


def find_insertion_points(parsed, body_image_count=0):
    """
    根据解析结果，确定配图插入位置。
    
    插入策略：
    - 封面图：放在第一个章标题之前（或文章末尾）
    - 正文配图：每章之间插入一张，优先使用章标题位置
    - 如果章节不够，剩余图片放在文章末尾
    
    返回恰好 1 + body_image_count 个插入位置的 HTML 偏移量列表。
    """
    chapters = parsed["chapters"]
    html_end = parsed["html_length"]
    positions = []
    
    # 封面插入点
    if chapters:
        positions.append(chapters[0].start())
    else:
        positions.append(html_end)
    
    # 正文配图插入点：从第二章节开始
    for ch in chapters[1:]:
        if len(positions) < 1 + body_image_count:
            positions.append(ch.start())
    
    # 如果章节不够，剩余图片放在文章末尾
    while len(positions) < 1 + body_image_count:
        positions.append(html_end)
    
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


def replace_picsum_with_media(html, url_to_mid):
    """
    将 picsum 图片标签替换为带 data-uimg 的格式。
    
    关键修复: 匹配整个 <img> 标签而非 URL 片段，
    避免嵌套 img 标签（Bug #1 根因）。
    确定性映射：按图片插入顺序一一对应。
    """
    # 匹配完整的 <img> 标签（包含 picsum src）
    picsum_img_pattern = (
        r'<img\s+[^>]*src="https://picsum\.photos/seed/[^"]*"[^>]*>'
    )
    picsum_tags = re.findall(picsum_img_pattern, html)
    
    if len(picsum_tags) != len(url_to_mid):
        raise ValueError(
            f"Picsum img tag count ({len(picsum_tags)}) "
            f"!= media_id count ({len(url_to_mid)})"
        )
    
    img_style_val = STYLES["img"]
    for i, (old_tag, mid) in enumerate(zip(picsum_tags, url_to_mid)):
        # 从旧标签中提取 picsum URL 作为 src
        src_match = re.search(
            r'src="(https://picsum\.photos/seed/[^"]*)"', old_tag
        )
        picsum_url = src_match.group(1) if src_match else ""
        # 构造新标签（替换整个标签，不是只替换 URL 字符串）
        new_tag = (
            '<img src="' + picsum_url + '" '
            + img_style_val + ' '
            + 'data-uimg="' + mid + '">'
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
    raw = _http_post("api.weixin.qq.com", path,
                     json.dumps(payload).encode(),
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
    # 先查重
    exists, existing_mid = find_existing_draft(access_token, title)
    
    if exists and existing_mid:
        # 更新已有草稿
        log("DRAFT", f"Found existing draft: {existing_mid[:20]}..., updating")
        payload = {
            "media_id": existing_mid,
            "index": 0,
            "articles": [{
                "title": title,
                "author": author,
                "digest": digest,
                "content": content,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 1,
                "only_fans_can_comment": 0,
            }]
        }
        path = f"/cgi-bin/draft/update?access_token={access_token}"
        raw = _http_post("api.weixin.qq.com", path,
                        json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                        {"Content-Type": "application/json"}, timeout=15)
        result = json.loads(raw)
        if result.get("errcode", 1) != 0:
            raise ValueError(f"Update draft failed: {result}")
        log("DRAFT", f"Draft updated: media_id={existing_mid[:20]}...")
        return existing_mid
    
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
    
    raw = _http_post("api.weixin.qq.com", path,
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
    log("INIT", f"Starting workflow: article={len(article_md)} chars, "
               f"seeds={cover_seed} + {body_seeds}")
    
    # ---- Step 1: 排版 ----
    token = get_access_token(appid, secret)
    log("STEP 1", "Calling DeepSeek for HTML layout...")
    html = call_deepseek(article_md, appid, secret)
    
    # 验证：不应该有图片
    img_count_step1 = len(re.findall(r'<img', html))
    log("STEP 1", f"DeepSeek排版完成: {len(html)} chars, "
               f"{img_count_step1} images (should be 0)")
    if img_count_step1 > 0:
        log("STEP 1", "WARNING: DeepSeek returned images, will strip them", "⚠")
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
    log("STEP 3", f"Downloading and uploading {total_images} images...")
    all_seeds = [cover_seed] + body_seeds
    media_ids = []
    for i, seed in enumerate(all_seeds):
        img_type = "thumb" if i == 0 else "image"
        img_bytes = download_image(seed)
        mid = upload_to_wechat(token, img_bytes, img_type)
        media_ids.append(mid)
        log("STEP 3", f"  [{i}] seed={seed}, media_id={mid[:20]}...")
    
    log("STEP 3", f"All {len(media_ids)} images uploaded ✓")
    
    # ---- Step 4: 插入图片标签 ----
    log("STEP 4", "Inserting image tags at determined positions...")
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
    
    # ---- Step 5: 替换 picsum URL 为 data-uimg ----
    log("STEP 5", "Replacing picsum URLs with data-uimg...")
    html = replace_picsum_with_media(html, media_ids)
    
    # 验证：所有 picsum URL 应被替换
    picsum_remaining = len(re.findall(r'picsum\.photos', html))
    if picsum_remaining > 0:
        log("STEP 5", f"WARNING: {picsum_remaining} picsum URLs remain!", "⚠")
    else:
        log("STEP 5", f"4张图全部替换为 data-uimg ✓")
    
    # ---- Step 6: 创建草稿 ----
    log("STEP 6", "Creating WeChat draft...")
    
    if not digest:
        digest = "那年我们刚认识，他请我吃了一碗面，从此成了最好的兄弟。"
    
    if not title:
        title = extract_title_from_md(article_md)
    if not title:
        title = "未命名文章"
    
    draft_media_id = create_draft(
        token, title, author, digest, html, media_ids[0]
    )
    log("STEP 6", f"草稿创建成功: media_id={draft_media_id[:20]}...")
    
    return {
        "draft_media_id": draft_media_id,
        "html_length": len(html),
        "image_count": img_count_step4,
        "media_ids": media_ids,
        "final_html": html,
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
        "--appid", default=None,
        help="微信 AppID（默认从 .env 读取）"
    )
    parser.add_argument(
        "--secret", default=None,
        help="微信 AppSecret（默认从 .env 读取）"
    )
    parser.add_argument(
        "--socks5", default=None,
        metavar="HOST:PORT",
        help="SOCKS5 代理地址（如 127.0.0.1:1080），用于固定出口 IP"
    )
    
    args = parser.parse_args()
    
    # SOCKS5 代理
    if args.socks5:
        host, port = args.socks5.rsplit(":", 1)
        import __main__
        __main__.SOCKS5_PROXY = (host, int(port))
        log("PROXY", f"SOCKS5 {host}:{port}", "⚡")
    
    # 读取文章
    with open(args.article, "r", encoding="utf-8") as f:
        article_md = f.read()
    
    # 读取凭证
    env = read_env()
    appid = args.appid or env.get("WECHAT_APPID", "wx37940d296d26c91c")
    secret = args.secret or env.get("WECHAT_SECRET", "")
    
    if not secret or secret.startswith("***"):
        log("ERROR", "WECHAT_SECRET not available in .env", "✗")
        sys.exit(1)
    
    body_seeds = [s.strip() for s in args.body_seeds.split(",")]
    
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
        )
        
        print(f"\n{'='*50}")
        print(f"✓✓✓ 发布完成!")
        print(f"草稿 Media ID: {result['draft_media_id']}")
        print(f"HTML 大小: {result['html_length']} 字符")
        print(f"配图数量: {result['image_count']}")
        print(f"{'='*50}")
        
        # 保存最终 HTML
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result["final_html"], encoding="utf-8")
            log("OUTPUT", f"Final HTML saved to {args.output}", "✓")
        
        print(f"\n[验证日志]")
        for mid_idx, mid in enumerate(result["media_ids"]):
            print(f"  [{mid_idx}] media_id={mid[:40]}...")
        
    except Exception as e:
        log("ERROR", str(e), "✗")
        sys.exit(1)


if __name__ == "__main__":
    main()
