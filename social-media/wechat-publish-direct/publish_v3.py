#!/usr/bin/env python3
"""微信公众号发布 v3.0"""
import urllib.request
import json
import os
import time

APPID = "wx37940d296d26c91c"
SECRET=*** get_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    if "errcode" in data:
        print(f"ERR: {data}")
        return None
    print("OK token")
    return data["access_token"]

def upload_image(token, filepath):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    boundary = "BOUNDARY" + str(int(time.time()))
    with open(filepath, "rb") as f:
        img_data = f.read()
    body = f'--{boundary}\r\nContent-Disposition: form-data; name="media"; filename="{os.path.basename(filepath)}"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()
    body += img_data
    body += f'\r\n--{boundary}--\r\n'.encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    if "media_id" in data:
        print(f"  OK {os.path.basename(filepath)}")
        return data["media_id"]
    else:
        print(f"  FAIL {os.path.basename(filepath)}: {data}")
        return None

def create_draft(token, title, digest, content, cover_media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    article = {
        "news_item": [{
            "title": title,
            "author": "王波",
            "digest": digest,
            "content": content,
            "thumb_media_id": cover_media_id,
            "url": "",
        }]
    }
    req = urllib.request.Request(url,
        data=json.dumps(article, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    if "media_id" in data:
        print(f"\nDraft OK: {data['media_id']}")
        return data["media_id"]
    else:
        print(f"\nDraft FAIL: {data}")
        return None

if __name__ == "__main__":
    print("Starting v3.0...")
    token = get_token()
    if not token:
        exit(1)
    
    files = {
        "cover": "/tmp/cover_image.jpg",
        "img_a": "/tmp/img_a.jpg",
        "img_b": "/tmp/img_b.jpg",
        "img_c": "/tmp/img_c.jpg",
        "img_d": "/tmp/img_d.jpg",
    }
    
    media_ids = {}
    for name, path in files.items():
        if os.path.exists(path):
            media_ids[name] = upload_image(token, path)
        else:
            print(f"Missing: {path}")
            media_ids[name] = None
    
    with open("/tmp/wechat_article_v2.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    img_map = {
        "img_a.jpg": media_ids.get("img_a"),
        "img_b.jpg": media_ids.get("img_b"),
        "img_c.jpg": media_ids.get("img_c"),
        "img_d.jpg": media_ids.get("img_d"),
    }
    for fn, mid in img_map.items():
        if mid:
            html = html.replace(f'src="{fn}"', f'src="{mid}"')
    
    digest = "十二岁那年，我一个人过。煤气灶、插卡游戏机、第一顿豆芽。可真正让我记住的，是刘小兵家那盏灯。"
    create_draft(token, "刘小兵家的夜路", digest, html, media_ids.get("cover", ""))
