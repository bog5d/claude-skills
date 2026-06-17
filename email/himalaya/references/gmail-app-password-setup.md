# Gmail App Password + Himalaya 配置指南

## 为什么不用 OAuth2

- Himalaya Homebrew 版不支持 `oauth2` + `keyring` feature
- QQ邮箱不支持标准 OAuth2 IMAP
- Google App Password 是 Google 官方支持的替代方案

## 操作流程

### 第 1 步：开启两步验证

Google Account → 安全性 → 两步验证（如未开启）

### 第 2 步：创建 App Password

1. 打开 https://myaccount.google.com/apppasswords
2. 登录 `wangbo8805@gmail.com`
3. 选 **App 密码** → 设备选"其他" → 输入 "Himalaya"
4. 创建 → 得到 16 位密码（如 `abcd efgh ijkl mnop`）

### 第 3 步：存 Keychain

```bash
security add-generic-password \
  -s "himalaya-gmail-app-password" \
  -a "wangbo8805@gmail.com" \
  -w "<16位密码>"
```

### 第 4 步：写 config.toml

```bash
mkdir -p ~/.config/himalaya
cat > ~/.config/himalaya/config.toml <<'EOF'
[accounts.gmail]
email = "wangbo8805@gmail.com"
default = true

folder.aliases.inbox = "INBOX"
folder.aliases.sent = "[Gmail]/Sent Mail"
folder.aliases.drafts = "[Gmail]/Drafts"
folder.aliases.trash = "[Gmail]/Trash"

backend.type = "imap"
backend.host = "imap.gmail.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "wangbo8805@gmail.com"
backend.auth.type = "password"
backend.auth.cmd = "security find-generic-password -w -s himalaya-gmail-app-password -a wangbo8805@gmail.com"

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.gmail.com"
message.send.backend.port = 465
message.send.backend.encryption.type = "tls"
message.send.backend.login = "wangbo8805@gmail.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "security find-generic-password -w -s himalaya-gmail-app-password -a wangbo8805@gmail.com"
EOF
chmod 600 ~/.config/himalaya/config.toml
```

### 第 5 步：验证

```bash
himalaya account doctor gmail
himalaya envelope list --page-size 5
```

## 常见问题

### 路径不对

Himalaya 可能在 `~/Library/Application Support/himalaya/config.toml` 查找配置。如果 `~/.config/himalaya/` 不行，检查：
```bash
himalaya --debug envelope list 2>&1 | grep config
```

### Homebrew 版 vs 原版

Homebrew 版 Himalaya 功能受限。如果 App Password 方案也不行，考虑从源码编译带 `oauth2` + `keyring` feature 的版本，或用 `gcloud auth application-default login`（需 `gcloud` CLI 安装）。

### App Password 失效

- 两步验证重新设置后会失效
- Google 检测到异常活动会强制刷新
- 失效后重新创建即可
