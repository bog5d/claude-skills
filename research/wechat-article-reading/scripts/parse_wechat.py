#!/usr/bin/env python3
"""解析微信公众号文章 HTML 到结构化文本。

用法:
    python3 parse_wechat.py <wechat_article.html> [输出.md]

输出: 标题 / 作者 / 发布时间 / 图片数 / 正文文本（去 HTML 标签）。
验证于 2026-08-08（v0.4.2 文章抓取）。
"""
import re, html, sys, datetime

def parse_wechat_html(content: str) -> dict:
    out = {}

    # 标题
    m = re.search(r'<meta property="og:title" content="(.*?)"', content) \
        or re.search(r'var msg_title = [\'"](.*?)[\'"]', content) \
        or re.search(r'<h1[^>]*>(.*?)</h1>', content, re.S)
    if m:
        out['title'] = html.unescape(m.group(1)).strip()

    # 作者/公众号
    m = re.search(r'<meta property="og:article:author" content="(.*?)"', content) \
        or re.search(r'var nickname = [\'"](.*?)[\'"]', content)
    if m:
        out['author'] = m.group(1).strip()

    # 发布时间（unix ts）
    m = re.search(r'var ct = "(\d+)"', content)
    if m:
        out['time'] = datetime.datetime.fromtimestamp(int(m.group(1))).strftime('%Y-%m-%d %H:%M')

    # 图片（懒加载 data-src）
    out['images'] = len(re.findall(r'<img[^>]*data-src="(.*?)"', content))

    # 正文
    m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', content, re.S) \
        or re.search(r'id="js_content"[^>]*>(.*)', content, re.S)
    text = ''
    if m:
        raw = m.group(1)
        raw = re.sub(r'<script.*?</script>', '', raw, flags=re.S)
        raw = re.sub(r'<style.*?</style>', '', raw, flags=re.S)
        raw = re.sub(r'<br\s*/?>', '\n', raw)
        raw = re.sub(r'</p>', '\n', raw)
        raw = re.sub(r'</section>', '\n', raw)
        raw = re.sub(r'<[^>]+>', '', raw)
        text = html.unescape(raw)
        text = re.sub(r'\n\s*\n+', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text).strip()
    out['text'] = text
    return out

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1], encoding='utf-8', errors='ignore') as f:
        content = f.read()
    d = parse_wechat_html(content)
    parts = []
    for k in ('title', 'author', 'time'):
        if d.get(k):
            parts.append(f"{k.upper()}: {d[k]}")
    parts.append(f"IMAGES: {d['images']}")
    parts.append(f"LEN: {len(d.get('text',''))}")
    result = "\n".join(parts) + "\n=====CONTENT=====\n" + d.get('text', '')
    print(result)
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            f.write(result)

if __name__ == '__main__':
    main()
