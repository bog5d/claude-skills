---
name: telegram-file-delivery
description: Send files via Telegram. MEDIA directive limitations and curl fallback for generic document types like HTML, PDF, ZIP, CSV, JSON, YAML, MD
---

# Telegram File Delivery Workflow

## 问题背景

Hermes Agent Telegram 集成支持 `MEDIA:<path>` 发送文件。MEDIA 正则已覆盖常见文档格式（详见下方），但文件投递还受**路径白名单**（`HERMES_MEDIA_ALLOW_DIRS`）和 **MIME 映射**（`SUPPORTED_DOCUMENT_TYPES`）两重过滤。详见 `media-file-delivery` 技能。

## MEDIA 正则支持的全部扩展名

- 图片: png, jpg, jpeg, gif, webp
- 视频: mp4, mov, avi, mkv, webm, 3gp
- 音频: ogg, opus, mp3, wav, m4a, flac
- **文档**: pdf, doc, docx, xls, xlsx, ppt, pptx, txt, csv, md, epub, zip, rar, 7z, apk, ipa

文档类型走 `sendDocument` API（非 `sendPhoto`/`sendVideo`），功能正常。

**实际投递失败根因通常不是正则，而是：**
1. 路径不在 `HERMES_MEDIA_ALLOW_DIRS` 白名单 → 加载 `media-file-delivery` 技能
2. 旧 Office 格式（.xls/.doc/.ppt）缺少 MIME 映射 → 加载 `media-file-delivery` 技能，详见其 `references/legacy-office-mime-bug.md`

## 方案 A: MEDIA 指令（优先使用）

```
MEDIA:/tmp/file.xls
MEDIA:~/hermes/cache/documents/report.pdf
```

前提：路径在白名单中（`/tmp` 或 `~/.hermes/cache/*`）。

## 方案 B: curl Telegram Bot API

**提取 token（注意 strip 空格）：**
```bash
TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d ' ')
```

**三个常用端点：**
```bash
# PPTX/PDF/文档 → sendDocument
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendDocument" \
  -F chat_id=<CHAT_ID> \
  -F document=@<FILE_PATH> \
  -F caption="文件描述"

# MP3 音频 → sendAudio（可加 title）
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendAudio" \
  -F chat_id=<CHAT_ID> \
  -F audio=@<FILE_PATH> \
  -F title="标题"

# MP4 视频 → sendVideo（可加 supports_streaming）
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendVideo" \
  -F chat_id=<CHAT_ID> \
  -F video=@<FILE_PATH> \
  -F supports_streaming=true

# 验证返回值
... | python3 -c "import sys,json; r=json.load(sys.stdin); print('✅' if r.get('ok') else f'❌ {r}')"
```

**Telegram Bot 文件大小限制：50MB。** 超限用 ffmpeg 压缩视频：
```bash
ffmpeg -i input.mp4 -vcodec libx264 -crf 28 -preset fast -acodec aac -b:a 64k output.mp4 -y
```

## 方案 C: 修复正则

修改 `gateway/platforms/base.py` 的 `extract_media()` 中 `media_pattern` 的正则扩展名列表，重启网关。

## 接收文件（用户发送附件给 Hermes）

Hermes Gateway 自动处理 Telegram 文档接收流程：

```
用户发文件 → Gateway webhook 收到 message.document
→ 调用 getFile API 下载 → 解密（如有密码）
→ 落盘到 ~/.hermes/cache/documents/
→ 绝对路径注入到当前会话上下文
```

**路径格式**：`/Users/mac/.hermes/cache/documents/doc_<hash>_<原始文件名>`

### ⚠️ 文件落盘延迟（Race Condition）

Telegram 文件上传可能慢于消息文本投递。用户按发送键后，文本消息秒到，但大文件可能还在上传中。

**症状**：你收到用户指令要求处理一个文件，但上下文中没有文件路径。调用 `search_files` / `find` 搜索宿主机也找不到。

**正确做法**：
1. **不要**触发全局文件搜索——文件还没落地，搜不到
2. 告知用户"文件尚未落盘，请稍等"或等待几秒后重试
3. 如果用户重新发送，新消息会携带已下载的文件路径

**用户侧最佳实践**：发文件后等待 2-3 秒再发送处理指令，确保文件已完全上传。

### 加密文件

如果文件有密码保护（如 `.xls` 密码 18），xlrd 会报 `XLRDError: Workbook is encrypted`。系统可能在 `/tmp/decrypted_orders.xls` 等处留有解密副本——先检查是否有已解密版本。

### 123 网盘备份链路

当 Telegram 文件传输不稳定时，用户可能通过 123 网盘分享链接作为备份。加载 `123pan-download` 技能处理。

---

## 验证

- [ ] 文件路径存在
- [ ] MEDIA 指令的扩展名在白名单中
- [ ] curl fallback 的 token 和 chat_id 正确
- [ ] 接收文件时，确认上下文中有 `/Users/mac/.hermes/cache/documents/doc_*` 路径后再处理
