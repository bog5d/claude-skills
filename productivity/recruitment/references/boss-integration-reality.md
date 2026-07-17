# BOSS直聘自动化：能做什么、不能做什么

## 已验证不可行的路径

| 路径 | 结果 | 原因 |
|------|------|------|
| Headless Chrome (Playwright) | 白屏/5KB空白图 | BOSS 反 headless 极强 |
| AppleScript `open location` | 开新标签丢登录态 | 每次 open location 创建新浏览上下文 |
| Chrome DevTools Protocol (CDP) | 调试端口打不开 | 需活跃桌面会话，无头环境无效 |
| Chrome Cookie DB 直接读 | 0 条 BOSS cookie | 数据库被锁或 cookie 未持久化 |
| `chrome-cli` | 未安装/不可用 | macOS 无内置 Chrome CLI |

## 可行路径

### 路径 A：手动下载 → 自动打分（推荐）
1. 用户在 BOSS 直聘 App/Web 下载简历 PDF
2. Telegram 发给 Hermes 或放入 `~/boss_resumes/`
3. Hermes 运行 `boss_resume_scorer.py` 打分排序

### 路径 B：有人在 Mac 前时
1. 用 `osascript -e 'open location'` 开 BOSS 登录页
2. 用户扫码登录
3. 但后续 `open location` 切换页面可能丢登录态
4. 需要 Playwright `connect_over_cdp` 但要先开调试端口
5. **只在 Mac 有活跃桌面 + Chrome 以 debug 模式启动时可用**

### 调试端口启动命令
```bash
# 完全杀 Chrome 后：
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 --no-first-run &
# 验证：curl http://localhost:9222/json/version
```

## 总结

不要在本没必要的事情上浪费时间。BOSS 直聘的反爬投入远超我们破解它的边际收益。路径 A 每次多花 5 分钟，但 100% 可靠。
