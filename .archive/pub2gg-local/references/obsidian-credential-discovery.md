# Obsidian Vault 凭证发现技巧

波总的 Obsidian vault (`/Users/mac/Cangjie_OBS_Notes/`) 是 WordPress / 宝塔 凭证的"冷存储"。

## 搜索WP凭证

```bash
# 搜索 base64 编码的 WP auth header（"admin:" 的 base64）
grep -r "YWRtaW46" /Users/mac/Cangjie_OBS_Notes/ --include="*.md" -l

# 搜索 WordPress 密码明文
grep -rE "wordpress.*password|WP.*PASS|wp_pass" /Users/mac/Cangjie_OBS_Notes/ --include="*.md" -i

# 搜索宝塔凭证
grep -rE "宝塔.*密码|bt.*password|username.*f4d3" /Users/mac/Cangjie_OBS_Notes/ --include="*.md"
```

## 已知凭证位置

| 文件 | 内容 |
|------|------|
| `2026-04-20_=================_配置区_=================.md` | WP_AUTH_HEADER base64, DeepSeek key, pub2gg script |
| `Memory_AI/Ingest/2026-03-10/2025年_20250908_20250908腾讯云WordPress账号密码.md` | admin/bqS2SBlY2AKG, MariaDB pwd, 宝塔 creds |
| `2025年/20250908_1114_会议准备与演讲稿.md` | 宝塔 default info (username/password) |

## 凭证状态

| 服务 | 凭证 | 状态 |
|------|------|------|
| WordPress admin | admin / bqS2SBlY2AKG | ❌ EXPIRED |
| WordPress app pass | boWm4uPKgEET | ❌ EXPIRED |
| MariaDB | 684d6613893882a2 | ⚠️ 无法连接 |
| 宝塔 | f4d3548b / a5caa1905a54 | ⚠️ 端口不通 |
| 腾讯云 Lighthouse | lhins-iortl354 (ap-shanghai) | 控制台可访问 |

## 凭证刷新 SOP

当 WordPress 密码过期时：

1. 腾讯云控制台 → Lighthouse → `lhins-iortl354` → 远程连接(VNC)
2. 登录后重置 admin 密码：
   ```bash
   cd /path/to/wordpress
   wp user update 1 --user_pass=NEW_PASSWORD
   ```
   或直接 SQL：
   ```sql
   USE wordpress;
   UPDATE wp_users SET user_pass=MD5('NEW_PASSWORD') WHERE ID=1;
   ```
3. 用新密码登录 hellobog.com/wp-admin
4. Users → Profile → Application Passwords → 创建 `pub2gg-local`
5. 将新密码更新到本 reference 文件
