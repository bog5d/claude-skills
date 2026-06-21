# Gmail 拉取支付宝账单 — 2026-06-21 新增陷阱

## 新增陷阱（本次会话发现）

### 1. App Password ≠ 用户密码

**症状**：IMAP 登录报 `AUTHENTICATIONFAILED: Invalid credentials (Failure)`

**原因**：波总发的 `420869` 是支付宝账单的 ZIP 解压密码，**不是** Gmail 的登录密码。Gmail 必须用 App Password（16位字母数字组合）。

**解法**：从 Himalaya 配置读取：
```bash
cat /Users/mac/.config/himalaya/gmail-app-password
# → wndncsmsdpemsara
```

**铁律**：拉 Gmail 附件永远用 App Password，不用波总发的普通密码。

---

### 2. Python imaplib 搜索中文 Subject 崩溃

**症状**：`UnicodeEncodeError: 'ascii' codec can't encode characters`

**原因**：Python 3.9 的 imaplib 用 ASCII 编码搜索条件，中文字符无法编码。

**解法**：只用 ASCII-safe 搜索条件：
```python
# ✅ 可以
conn.search(None, 'FROM "service@mail.alipay.com"')
# ❌ 崩溃
conn.search(None, 'SUBJECT "账单"')
```

---

### 3. IMAP 全量搜索超时

**症状**：`timeout after 300s` 无响应

**原因**：`SINCE "21-May-2026"` 不加 FROM 限制会搜全 Inbox（数千封），IMAP 逐个 fetch 很慢。

**解法**：先缩小范围再搜索：
```python
# 第一步：只搜支付宝发件人
status, data = conn.search(None, 'FROM "service@mail.alipay.com"')
msg_ids = data[0].split() if data[0] else []
# 第二步：只处理最后50封
for msg_id in msg_ids[-50:]:
    ...
```

---

### 4. Himalaya envelope list 只返回最近 ~10 封

**症状**：`himalaya envelope list -a gmail` 只返回 10 条，无分页

**原因**：Himalaya v1.2.0 的 envelope list 硬编码返回最近10封，`--page-size` 参数不被识别。

**解法**：需要历史邮件必须用 Python imaplib 直连。

---

## 完整管线（整合版）

```python
import imaplib
import email
import email.header
import zipfile
import csv
import io
import json
import os

# 1. 连接（用 App Password，不是普通密码！）
conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)
conn.login("wangbo8805@gmail.com", "wndncsmsdpemsara")  # ← App Password
conn.select("INBOX")

# 2. 搜索支付宝邮件（ASCII-safe）
status, data = conn.search(None, 'FROM "service@mail.alipay.com"')
msg_ids = data[0].split() if data[0] else []

# 3. 处理最近50封
for msg_id in msg_ids[-50:]:
    status, msg_data = conn.fetch(msg_id, "(RFC822)")
    raw = msg_data[0][1]
    msg = email.message_from_bytes(raw)
    subject = decode_header(msg["Subject"])
    
    # 4. 找 ZIP 附件
    for part in msg.walk():
        cd = str(part.get("Content-Disposition", ""))
        if "attachment" in cd:
            fn = decode_header(part.get_filename())
            payload = part.get_payload(decode=True)
            if fn and fn.lower().endswith(".zip") and payload:
                # 5. 用密码解压（密码从波总获取）
                password = b"420869"  # ← 这是 ZIP 密码，不是 App Password
                with zipfile.ZipFile(io.BytesIO(payload)) as zf:
                    for zname in zf.namelist():
                        if zname.lower().endswith(".csv"):
                            csv_bytes = zf.read(zname, pwd=password)
                            text = csv_bytes.decode("gbk", errors="replace")
                            # 6. 解析 CSV → 入库
                            ...
```

## 关键区别速查

| 密码类型 | 用途 | 获取方式 | 示例 |
|---------|------|---------|------|
| Gmail App Password | IMAP 登录 Gmail | Google Account → App Passwords | `wndncsmsdpemsara` |
| 支付宝 ZIP 密码 | 解压账单 ZIP | 支付宝 App → 账单 → 申请记录 | `420869`（每次随机） |
