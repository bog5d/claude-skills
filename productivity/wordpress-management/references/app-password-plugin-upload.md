# 无 SSH 时通过插件上传启用应用密码

当无法 SSH 到服务器创建 `mu-plugins/enable-app-passwords.php` 时，可以
通过 WordPress 的插件上传接口安装一个迷你插件来实现同等效果。

## 适用场景

- 没有 SSH 凭证
- 宝塔面板不可访问
- 只能通过 HTTP 与 WordPress 交互

## 操作步骤

### 1. 创建迷你插件文件

```php
<?php
/**
 * Plugin Name: Enable Application Passwords
 * Description: Enable WordPress Application Passwords via must-use plugin alternative
 * Version: 1.0
 */
add_filter( 'wp_is_application_passwords_available', '__return_true' );
```

保存为 `enable-app-passwords.php`，打包为 `enable-app-passwords.zip`。

### 2. 登录获取 Cookie

```bash
curl -c /tmp/wp_cookies \
  -d "log=admin&pwd=YOUR_PASSWORD&wp-submit=Log+In&redirect_to=/wp-admin/&testcookie=1" \
  -L "http://hellobog.com/wp-login.php"
```

### 3. 上传插件（需要先提取 nonce）

```bash
# 获取 nonce
NONCE=$(curl -s -b /tmp/wp_cookies "http://hellobog.com/wp-admin/plugin-install.php?tab=upload" | \
  grep -oP '"_wpnonce":"[^"]+"' | head -1 | cut -d'"' -f4)

# 上传并安装
curl -b /tmp/wp_cookies \
  -F "pluginzip=@enable-app-passwords.zip" \
  -F "install-plugin-submit=Install+Now" \
  -F "_wpnonce=$NONCE" \
  -L "http://hellobog.com/wp-admin/update.php?action=upload-plugin"
```

### 4. 激活插件

```bash
# 方式 A：通过 REST API（WP 6.5+）
curl -u "admin:YOUR_APP_PASSWORD" \
  -X PUT "http://hellobog.com/wp-json/wp/v2/plugins/enable-app-passwords/enable-app-passwords" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'

# 方式 B：通过 admin-ajax（需要 cookie + nonce）
NONCE2=$(curl -s -b /tmp/wp_cookies "http://hellobog.com/wp-admin/plugins.php" | \
  grep -oP '"_wpnonce":"[^"]+"' | head -1 | cut -d'"' -f4)

curl -b /tmp/wp_cookies \
  -X POST "http://hellobog.com/wp-admin/plugins.php?action=activate&plugin=enable-app-passwords%2Fenable-app-passwords.php&_wpnonce=$NONCE2" \
  -L
```

## 替代方案：直接用 REST API 创建应用密码

如果 WordPress 5.6+，应用密码支持内置但可能被主题/插件禁用。
插件上传方案绕过了所有主题级别的 filter 禁用。

## 已知验证方法

```bash
# 验证应用密码是否生效
curl -u "admin:NEW_APP_PASSWORD" "http://hellobog.com/wp-json/wp/v2/users/me"
# 成功返回用户 JSON，失败返回 401
```
