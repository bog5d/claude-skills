---
name: telegram-file-delivery
description: Send files via Telegram. MEDIA directive limitations and curl fallback for generic document types like HTML, PDF, ZIP, CSV, JSON, YAML, MD
---

# Telegram File Delivery Workflow

## 问题背景

Hermes Agent Telegram 集成支持 `MEDIA:<path>` 发送文件。但底层正则只匹配媒体后缀，通用文档被静默忽略。

## 自带支持的扩展名

- 图片: png, jpg, jpeg, gif, webp
- 视频: mp4, mov, avi, mkv, webm, 3gp
- 音频: ogg, opus, mp3, wav, m4a

**需要 fallback**: html, pdf, zip, tar.gz, tgz, csv, json, xml, yaml, md

## 方案 A: MEDIA 指令

```
MEDIA:~/Desktop/file.png
```

仅限自带支持的后缀。

## 方案 B: curl Telegram Bot API

```bash
TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.hermes/.env | cut -d= -f2)
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendDocument" \
  -F chat_id=<CHAT_ID> \
  -F document=@<FILE_PATH> \
  -F caption="文件描述"
```

## 方案 C: 修复正则

修改 `gateway/platforms/base.py` 的 `extract_media()` 中 `media_pattern` 的正则扩展名列表，重启网关。

## 验证

- [ ] 文件路径存在
- [ ] MEDIA 指令的扩展名在白名单中
- [ ] curl fallback 的 token 和 chat_id 正确
