---
name: pdf-unlock
description: 一键解除PDF密码保护。接收PDF文件+密码，输出无密码版本。一步到位，不废话。
version: 1.0.0
author: Hermes Agent
platforms: [macos, linux]
metadata:
  hermes:
    tags: [PDF, unlock, decrypt, password, pymupdf]
---

# PDF Unlock

## 什么时候用

用户发了一个加密的PDF或XLSX文件，给了密码，让你去掉密码。

## 支持格式

| 格式 | 工具 | 代码 |
|------|------|------|
| PDF | pymupdf | `doc.authenticate(pwd)` → `doc.save(out)` |
| XLSX | msoffcrypto | `OfficeFile(f).load_key(password=pwd)` → `decrypt(buf)` |

## XLSX 解密命令

```bash
cd /Users/mac/.hermes/hermes-agent && source venv/bin/activate && python3 << 'PYEOF'
import io, msoffcrypto
path = '<输入路径>'
decrypted = io.BytesIO()
with open(path, 'rb') as f:
    office_file = msoffcrypto.OfficeFile(f)
    office_file.load_key(password='<密码>')
    office_file.decrypt(decrypted)
out = '/Users/mac/.hermes/cache/documents/<文件名>_已解密.xlsx'
with open(out, 'wb') as f:
    f.write(decrypted.getvalue())
print('OK')
PYEOF
```

## 铁律：一步到位，别废话

收到PDF路径+密码 → 解密 → 发回去。中间不要问任何问题，不要解释过程。

## 命令

```bash
# 解密
cd /Users/mac/.hermes/hermes-agent && source venv/bin/activate && python3 << 'PYEOF'
import pymupdf
doc = pymupdf.open("<输入路径>")
result = doc.authenticate("<密码>")
if result == 0:
    print("密码错误")
    doc.close()
    exit(1)
doc.save("<输出路径>")  # 不要加任何 encryption 参数，pymupdf 新版本不再接受字符串
doc.close()
print("OK")
PYEOF
```

## 输出路径

输出到: `/Users/mac/.hermes/cache/documents/<原文件名>_已解密.pdf`

## 发送

解密后立即用 Telegram 发送：

```bash
TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d ' ')
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendDocument" \
  -F chat_id=8447296166 \
  -F document=@<输出路径> \
  -F caption="📄 <文件名>（已去密码）"
```

## 验证

```bash
cd /Users/mac/.hermes/hermes-agent && source venv/bin/activate && python3 -c "
import pymupdf
doc = pymupdf.open('<输出路径>')
print(f'页数: {doc.page_count}, 加密: {doc.is_encrypted}')
doc.close()
"
```

## Pitfalls

1. **密码可能不对** — `doc.authenticate(password)` 返回 `0`（失败），告诉用户"密码不正确"，不要猜
2. **`TypeError` on `save()`** — pymupdf 新版本 `save()` 的 `encryption` 参数只接受 int（如 `pymupdf.PDF_ENCRYPT_NONE`），不接受字符串 `"store"`。直接用 `doc.save(output_path)` 不加任何 encryption 参数即可去掉密码
3. **只解密不改动内容** — 用 `save(output)` 保留原内容，只是去掉加密
4. **不要问"要我做什么"** — 收到密码就直接解，解完直接发
