# Gmail 拉取支付宝账单完整管线

## 触发条件

波总发来支付宝账单邮件通知（发件人 `service@mail.alipay.com`，主题含"交易流水"），或自动检测到新账单邮件。

## 完整流程

### Step 1: 搜索邮件

```bash
# 用Himalaya列出最近邮件（ASCII关键词，不要中文）
himalaya envelope list 2>&1 | head -30

# 或用Python IMAP搜索（避免中文编码问题）
python3 -c "
import imaplib
mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
mail.login('wangbo8805@gmail.com', '<app_password>')
mail.select('INBOX')
status, msgs = mail.search(None, '(FROM \"service@mail.alipay.com\")')
# status='OK' → msgs[0].split() 是邮件ID列表
# 取最新: msgs[0].split()[-1]
"
```

### Step 2: 确认邮件有附件

```bash
# Himalaya 读取邮件确认有附件
himalaya message read <envelope_id>

# 预期输出包含 attachment 标记和 .zip 文件名
```

### Step 3: 下载附件

⚠️ **Himalaya v1.2.0 没有 `save-attachment` 命令**，必须用 Python `imaplib` 直连：

```python
import imaplib
import email
from email import policy
from email.parser import BytesParser
import os

# 连接IMAP
mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
mail.login('wangbo8805@gmail.com', app_password)
mail.select('INBOX')

# 获取邮件完整内容
status, msg_data = mail.fetch(latest_id, '(RFC822)')
raw_email = msg_data[0][1]
msg = BytesParser(policy=policy.default).parsebytes(raw_email)

# 遍历 multipart 找附件
for part in msg.walk():
    content_disposition = str(part.get("Content-Disposition", ""))
    if "attachment" in content_disposition:
        filename = part.get_filename()  # 如: 支付宝交易明细(20260616-20260618).zip
        payload = part.get_payload(decode=True)
        
        # 保存到本地
        save_path = f'/Users/mac/.hermes/adjutant/finance/email_cache/{filename}'
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(payload)
        print(f"Saved: {save_path} ({len(payload)} bytes)")
```

### Step 4: 获取解压密码

密码**不在邮件里**，在支付宝App中：
- 路径：支付宝 → 我的 → 账单 → 右上角... → 开具交易流水证明 → 申请记录
- 或支付宝服务消息（推送消息）

### Step 5: 解压加密 ZIP

⚠️ **不要用系统 `unzip`**，中文文件名会报 `Illegal byte sequence`。用 Python `zipfile`：

```python
import zipfile

zip_path = '/Users/mac/.hermes/adjutant/finance/email_cache/支付宝交易明细(20260616-20260618).zip'

with zipfile.ZipFile(zip_path, 'r') as zf:
    for name in zf.namelist():
        data = zf.read(name, pwd=b'700894')  # 密码是 bytes
        text = data.decode('gbk', errors='replace')
        print(text)
```

### Step 6: 解析 CSV

```python
# CSV 结构（GBK编码）:
# 交易时间,交易分类,交易对方,对方账号,商品说明,收/支,金额,收/付款方式,交易状态,交易订单号,商家订单号,备注
# 前22行是元数据，从第24行header开始

lines = text.split('\n')
# 扫描找到包含'交易时间,交易分类'的行作为header
for i, line in enumerate(lines):
    if '交易时间,交易分类' in line:
        header_line = i
        break

# 从 header+1 开始解析数据行
for line in lines[header_line+1:]:
    parts = line.strip().rstrip(',').split(',')
    if len(parts) < 7:
        continue
    txn_time = parts[0].strip()
    category = parts[1].strip()
    counterparty = parts[2].strip()
    amount_str = parts[6].strip()
    direction = parts[5].strip()  # '支出'/'收入'/'不计收支'
    
    if direction == '支出':
        # 入库
        pass
    elif direction == '不计收支':
        # 跳过（余额宝转入、小荷包自动攒等）
        pass
```

### Step 7: 去重 + 入库

```bash
# 已有去重逻辑: 日期 + 金额(±2元) + 商户名相似度 > 0.5
# 支付宝小荷包跳过（内部转账）
# 新增后更新 meta.last_updated
# cp 到 repo → git commit + push
```

## 常见陷阱

1. **密码每次随机** — 不是身份证后6位，每次导出都生成随机密码
2. **ZIP 文件名中文** — Windows端创建导致编码问题，Python zipfile 可绕开
3. **CSV 是 GBK** — 不能用 `utf-8` 解码，会乱码
4. **前导元数据** — 前22行不是数据，含导出信息、统计摘要
5. **不计收支 ≠ 支出** — 余额宝转入、小荷包自动攒是"不计收支"，不计消费
6. **邮件附件可能为空/占位符** — 如果下载的文件很小（<5KB），可能是加密容器而非真实数据

## 参考代码

见 `personal-finance` 技能 pitfalls #43。
