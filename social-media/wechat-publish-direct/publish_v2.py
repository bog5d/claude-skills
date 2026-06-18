#!/usr/bin/env python3
"""
微信公众号发布 v2.0 — 完整流程
1. 获取 access_token
2. 上传封面图和章节配图
3. 创建草稿（含 HTML + 封面图）
"""
import urllib.request
import json
import os
import time

APPID = "wx37940d296d26c91c"
SECRET="85c02f63a114b67277ab39eb13ae8d19"

def get_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    if "errcode" in data:
        print(f"❌ Token 获取失败: {data}")
        return None
    print(f"✅ Token 获取成功")
    return data["access_token"]

def upload_image(token, filepath, img_type="cover"):
    """上传永久图片素材"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    
    boundary = "boundary" + str(time.time()).replace(".", "")
    body = []
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"{os.path.basename(filepath)}\"\r\nContent-Type: image/jpeg\r\n\r\n")
    
    with open(filepath, "rb") as f:
        img_data = f.read()
    
    body.append(img_data.decode("latin-1"))
    body.append(f"\r\n--{boundary}--\r\n")
    
    req = urllib.request.Request(url, data=("".join(body)).encode("latin-1"), 
                                  headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        if "media_id" in data:
            print(f"  ✅ {os.path.basename(filepath)} → media_id: {data['media_id'][:30]}...")
            return data["media_id"]
        else:
            print(f"  ❌ {os.path.basename(filepath)}: {data}")
            return None
    except Exception as e:
        print(f"  ❌ {os.path.basename(filepath)}: {e}")
        return None

def create_draft(token, title, digest, content, cover_media_id):
    """创建草稿"""
    url = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=" + token
    
    article = {
        "title": title,
        "author": "王波",
        "digest": digest,
        "content": content,
        "thumb_media_id": cover_media_id,
        "content_code": "NEWS_CARD_LINK",
    }
    
    req = urllib.request.Request(url, 
                                  data=json.dumps(article, ensure_ascii=False).encode("utf-8"),
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        if "media_id" in data:
            print(f"\n🎉 草稿创建成功!")
            print(f"   media_id: {data['media_id']}")
            return data["media_id"]
        else:
            print(f"\n❌ 草稿创建失败: {data}")
            return None
    except Exception as e:
        print(f"\n❌ 草稿创建失败: {e}")
        return None

if __name__ == "__main__":
    print("=" * 50)
    print("微信公众号发布 v2.0")
    print("=" * 50)
    
    # Step 1: Token
    print("\n[1/4] 获取 access_token...")
    token = get_token()
    if not token:
        exit(1)
    
    # Step 2: 上传图片
    print("\n[2/4] 上传图片到素材库...")
    
    # 封面图
    cover_path = "/tmp/cover_image.jpg"
    if not os.path.exists(cover_path):
        print(f"  ⚠️  封面图不存在: {cover_path}")
        cover_media_id = None
    else:
        cover_media_id = upload_image(token, cover_path)
    
    # Step 3: 读取 HTML
    print("\n[3/4] 读取排版 HTML...")
    with open("/tmp/wechat_article_v2.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Step 4: 创建草稿
    print("\n[4/4] 创建草稿...")
    digest = "十二岁那年，我一个人过。煤气灶、插卡游戏机、第一顿豆芽。可真正让我记住的，是刘小兵家那盏灯。"
    
    result = create_draft(token, "刘小兵家的夜路", digest, content, cover_media_id or "")
    
    if result:
        print("\n" + "=" * 50)
        print("✅ 发布完成！")
        print("去公众号后台 → 草稿箱 查看文章")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ 发布失败，请检查错误信息")
        print("=" * 50)
