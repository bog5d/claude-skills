# Gmail 拉取支付宝账单附件管线

## 背景
支付宝每月导出账单时会发邮件到指定邮箱（`service@mail.alipay.com`），附件为 ZIP（密码随机）。Himalaya v1.2.0 没有 `save-attachment` 命令，需要用 Python IMAP 直连下载。

## 完整流程

### Step 1: 搜索邮件
```bash
# 用 ASCII-safe 条件搜索
himalaya envelope list -a gmail --page-size 200 | grep -i "alipay\|支付宝\|交易流水"
```
⚠️ 搜索条件不能用中文（parse error），用 ASCII 条件：`FROM service@mail.alipay.com`

### Step 2: 确认附件
```bash
himalaya message read <envelope_id>
```
输出中包含 `<#part type=application/octet-stream filename="...">` 说明有附件

### Step 3: 用 Python IMAP 下载附件
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
    msg_id = msg_ids[0].split()[-1].decode()
    status, msg_data = imap.fetch(msg_id, '(RFC822)')
    raw = msg_data[0][1]
    msg = email.message_from_bytes(raw, policy=default)
    
    for part in msg.walk():
        cd = str(part.get('Content-Disposition', ''))
        if 'attachment' in cd:
            fn = part.get_filename()
            data = part.get_payload(decode=True)
            if fn and data:
                out_path = f'/path/to/downloads/{fn}'
                with open(out_path, 'wb') as f:
                    f.write(data)
```

### Step 4: 解压 ZIP
```python
import zipfile
zip_path = '/path/to/支付宝交易明细.zip'
extract_dir = '/path/to/extracted'
os.makedirs(extract_dir, exist_ok=True)
with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall(extract_dir, pwd=b'<密码>')
```

### Step 5: 导入
```bash
python3 /Users/mac/.hermes/adjutant/finance/scripts/import_csv.py <csv_path>
# 或用专用 GBK 解析器（import_csv.py 不支持 GBK 编码）
```

### Step 6: 同步 + git push
```bash
cp ~/.hermes/adjutant/finance/expenses.json ~/.hermes/adjutant/repo/hermes-adjutant/finance/expenses.json
cd ~/.hermes/adjutant/repo/hermes-adjutant && git add -A && git commit -m "..." && git push
```

## 注意事项
- App Password 文件位置：`/Users/mac/.config/himalaya/gmail-app-password`
- Profile sandbox 中 `~` 被改写，auth.cmd 必须用绝对路径
- 支付宝账单 ZIP 文件名含中文，Python `zipfile` 模块比 `unzip` CLI 更可靠
- 解压密码每次随机，在支付宝消息对话框中显示