# Himalaya + Gmail 配置指南

## 问题背景

Himalaya CLI (`himalaya v1.2.0`) 是波总用来拉 Gmail 账单的邮件客户端。
但 Homebrew 版有几个硬伤：
- 不支持 `oauth2` + `keyring` feature → 无法用 OAuth2 连 Gmail
- 配置 schema 和官方 sample 不一致 → `imap.server` 平铺写法不被识别为 backend
- `account list` 永远显示 BACKENDS 列为空

## 方案选择

### 方案 1：App Password + IMAP（推荐，但需 TTY）
```bash
himalaya
```
跟着向导操作：选 gmail → 输邮箱 → 选 IMAP → 输入 App Password → 完成。

### 方案 2：Python 脚本直连 IMAP（无需配置）
```python
import imaplib
m = imaplib.IMAP4_SSL('imap.gmail.com')
m.login('wangbo8805@gmail.com', 'APP_PASSWORD')
m.select('INBOX')
```

### 方案 3：手动导出账单
波总直接从支付宝/微信导出 CSV/XLSX 发给我，我解析导入。

## 关键步骤

### 生成 Gmail App Password
1. 打开 https://myaccount.google.com/apppasswords
2. 登录 wangbo8805@gmail.com
3. 选"其他" → 输入 "Himalaya"
4. 得到 16 位密码

### 写入 Himalaya 配置
```bash
himalaya account configure gmail
# 然后按向导输入 App Password
```

## Pitfall: Homebrew 版配置陷阱

| 症状 | 原因 | 解法 |
|------|------|------|
| `account list` BACKENDS 为空 | `imap.server` 平铺写法不被解析为 backend | 用 `himalaya` wizard 交互式生成 |
| `missing field login` | 嵌套 `[accounts.X.backend]` 表缺少必填字段 | 不用嵌套表，用 wizard |
| `unknown variant raw` | v1.2.0 auth type 只接受 `password` 或 `oauth2` | 用 wizard 或 Python 直连 |
| `Cannot find configuration at ...` | Profile sandbox 改了 HOME 路径 | 配置写到 `$HOME/.config/himalaya/config.toml` |

## 替代方案：Python IMAP 直连

如果 Himalaya 始终配不通，用 Python 脚本拉邮件：

```python
import imaplib, email

def pull_emails(email_addr, app_password, num_recent=50):
    m = imaplib.IMAP4_SSL('imap.gmail.com')
    m.login(email_addr, app_password)
    m.select('INBOX')
    status, data = m.search(None, f'(UNSEEN)')
    msg_ids = data[0].split()[-num_recent:]
    results = []
    for mid in msg_ids:
        _, msg_data = m.fetch(mid, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        results.append({
            'from': msg['From'],
            'subject': msg['Subject'],
            'date': msg['Date'],
        })
    m.logout()
    return results
```
