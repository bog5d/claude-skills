# Gmail → Alipay 账单摘取管线（2026-06-29 验证）

## 核心工具链

```python
# 1. 用 imaplib 连接
import imaplib
APP_PASSWORD = open(os.path.expanduser('~/.config/himalaya/gmail-app-password')).read().strip()
imap = imaplib.IMAP4_SSL('imap.gmail.com')
imap.login('wangbo8805@gmail.com', APP_PASSWORD)
imap.select('INBOX')

# 2. 搜索支付宝邮件（用 FROM，不要用中文 Subject）
status, msg_ids = imap.search(None, b'FROM "service@mail.alipay.com"')

# 3. 取最新一封
mid = msg_ids[0].split()[-1]  # 这是真实序列号
status, data = imap.fetch(mid, '(RFC822)')
msg = email.message_from_bytes(data[0][1])
```

## ⚠️ Himalaya ID ≠ imaplib 序列号

Himalaya 显示的 envelope ID（如 13038）是 Gmail UID，**不是** imaplib `fetch()` 用的序列号。  
直接用该 ID fetch 返回 `data[0]=None`。

**正确做法**：用 `imap.search(None, ...)` 返回的 ID，或扫最近 N 封找支付宝。

## ⚠️ 两类密码严格区分

| 密码 | 用途 | 格式 | 来源 |
|------|------|------|------|
| Gmail App Password | IMAP 登录 | 16位字母数字 | `/Users/mac/.config/himalaya/gmail-app-password` |
| ZIP 解压密码 | 解压附件 | 6位数字（每次随机） | 波总从支付宝 App 获取 |

## 解压管线

```python
import io, zipfile
zf = zipfile.ZipFile(io.BytesIO(zip_data))
zf.setpassword(b'873622')  # 随机密码，每次不同
csv_raw = zf.read(name)  # 绕开中文文件名编码问题
csv_text = csv_raw.decode('gbk', errors='replace')
```

一定要用 `zipfile.setpassword()` + Python 读取，不要用系统 `unzip`（中文文件名报 `Illegal byte sequence`）。

## CSV 结构

- 前 1-22 行：元数据（导出信息、统计摘要）
- 第 23 行：表头 `交易时间,交易分类,交易对方,...`
- 第 24 行起：数据
- 编码：GBK → 解码用 `gbk`
- 列：交易时间,交易分类,交易对方,对方账号,商品说明,收/支,金额,收/付款方式,交易状态,交易订单号,商家订单号,备注

## 过滤链

import_csv.py 现在用的是严格过滤链（2026-06-29 翻车后修复）：
1. 零金额 → skip
2. direction != "支出" → skip
3. 交易分类 = "投资理财" → skip（不管方向字段）
4. "退款" in 交易分类 → skip
5. 关键字含 余额宝/基金/小荷包/转账/缴税 → skip

## 翻车记录

- **2026-06-29**：余额宝每天¥500定时转入（30天=¥15,000），方向="支出"，217条全部混入消费数据。
  - 原因：`parse_alipay()` 只判 `direction != "支出"`，没判 `tx_category == "投资理财"`
  - 修复：新增 tx_category + 关键字双保险过滤
