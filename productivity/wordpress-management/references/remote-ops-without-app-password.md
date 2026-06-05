# Remote WordPress Operations Without Application Password

Use this when the WP site doesn't have Application Passwords enabled, and you can't SSH/cPanel in to enable them. This covers the cookie + nonce approach.

## Cookie Login + Nonce Extraction

When Application Passwords aren't available, use cookie-based session auth:

### Step 1: Login and Get Session Cookie

```bash
COOKIE_JAR=$(mktemp)
LOGIN_RESP=$(curl -s -c "$COOKIE_JAR" -X POST "https://SITE.com/wp-login.php" \
  -d "log=ADMIN_USER&pwd=ADMIN_PASS&redirect_to=%2Fwp-admin%2F&testcookie=1")
```

### Step 2: Extract REST Nonce

```bash
NONCE=$(curl -s -b "$COOKIE_JAR" "https://SITE.com/wp-admin/admin-ajax.php?action=rest-nonce" | tr -d '\n')
```

### Step 3: Call REST API with Nonce

```bash
curl -s -X POST "https://SITE.com/wp-json/wp/v2/..." \
  -b "$COOKIE_JAR" \
  -H "X-WP-Nonce: $NONCE" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## Enabling Application Passwords via Plugin Upload (No SSH)

If a site doesn't have Application Passwords enabled and you can't SSH:

```bash
# Construct a mini plugin ZIP in memory
PLUGIN_ZIP="/tmp/enable_app_passwords.zip"
python3 -c "
import zipfile, io
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as z:
    z.writestr('enable-app-passwords/enable-app-passwords.php',
        '<?php\\n/* Plugin Name: Enable Application Passwords */\\nadd_filter(\\\"wp_is_application_passwords_available\\\", \\\"__return_true\\\");\\n')
with open('$PLUGIN_ZIP', 'wb') as f:
    f.write(buf.getvalue())
"

# Upload via WP Admin (needs cookie + admin nonce)
PLUGIN_NONCE=$(curl -s -b "$COOKIE_JAR" "https://SITE.com/wp-admin/plugin-install.php" | grep -oP '"_wpnonce"\s*value="[^"]*"' | head -1 | grep -oP 'value="\K[^"]*')

curl -s -b "$COOKIE_JAR" -X POST "https://SITE.com/wp-admin/update.php?action=upload-plugin" \
  -F "_wpnonce=$PLUGIN_NONCE" \
  -F "pluginzip=@$PLUGIN_ZIP" \
  -F "install-plugin-submit=Install+Now"
```

**Pitfall:** WordPress plugin upload `_wpnonce` differs from REST API's `X-WP-Nonce`. Must extract from `plugin-install.php` page separately.

## Generating Application Password (Once App Passwords Enabled)

```bash
APP_PASS=$(curl -s -X POST "https://SITE.com/wp-json/wp/v2/users/me/application-passwords" \
  -u "ADMIN_USER:ADMIN_PASS" \
  -H "Content-Type: application/json" \
  -d '{"name":"app-name","app_id":"00000000-0000-0000-0000-000000000000"}')
```

⚠️ Password shown only once in response.

## Common Pitfalls

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| App passwords not enabled | 404/disabled on generation endpoint | Install plugin or create mu-plugins file |
| Cookie expired | Nonce failure, 401 | Re-login |
| Wrong Host header | 404 | Use correct domain for the site |
| SSL cert issues | curl SSL error | Add `-k` temporarily (debug only) |
| Old Office format upload rejected | "Unsupported document type" | Check MIME whitelist |
