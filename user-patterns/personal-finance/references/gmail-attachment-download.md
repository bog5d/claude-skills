# Gmail 邮件附件下载 — Python IMAP 管线

## 为什么不用 Himalaya

Himalaya v1.2.0 没有 `save-attachment` 命令。`message save` 是存邮件到文件夹，`message export` 导出原始邮件到临时目录但不直接提取附件。

## 可靠路径：Python `imaplib` 直连

```python
import imaplib, email, os
from email.policy import default

imap = imaplib.IMAP4_SSL('imap.gmail.com', 993)
with open('/Users/mac/.config/himalaya/gmail-app-password', 'r') as f:
    password = f.read().strip()
imap.login('wangbo8805@gmail.com', password)
imap.select('INBOX')

# 搜索（ASCII-safe）
status, msg_ids = imap.search(None, 'FROM service@mail.alipay.com')
if msg_ids[0]:
    msg_id = msg_ids[0].split()[-1].decode()  # 最新一封
    
    # 下载完整邮件
    status, msg_data = imap.fetch(msg_id, '(RFC822)')
    raw = msg_data[0][1]
    
    # 解析 multipart 找附件
    msg = email.message_from_bytes(raw, policy=default)
    for part in msg.walk():
        cd = str(part.get('Content-Disposition', ''))
        if 'attachment' in cd:
            fn = part.get_filename()
            data = part.get_payload(decode=True)
            if fn and data:
                with open(f'./downloads/{fn}', 'wb') as f:
                    f.write(data)
                print(f'Downloaded: {fn} ({len(data)} bytes)')
    
    imap.logout()
```

## 注意事项

- **搜索条件必须 ASCII-safe**：用 `FROM service@mail.alipay.com`，不要传中文
- **解压密码**：支付宝账单 ZIP 解压密码每次随机，在支付宝 App 消息对话框显示，需要波总手动发给你
- **GBK 编码**：支付宝导出的 CSV 是 GBK 编码，用 `encoding='gbk'` 打开
- **ZIP 中文文件名**：Windows 创建的 ZIP 文件名可能是 GBK 编码，用 Python `zipfile` 的 `setpassword()` 方法绕开 `unzip` 的编码问题