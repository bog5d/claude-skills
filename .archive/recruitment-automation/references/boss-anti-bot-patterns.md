# BOSS 直聘反爬机制与已验证方案

## 已验证不可行

| 尝试 | 命令/方式 | 失败表现 | 根本原因 |
|------|----------|---------|---------|
| Playwright headless | `p.chromium.launch(headless=True)` | 页面白屏，截图 5.2KB 纯白 | BOSS 检测 `navigator.webdriver` + 无头特征 |
| Playwright 非 headless 无桌面 | `headless=False` 从终端启动 | EPIPE 崩溃 / tcsetattr 错误 | Mac 无活跃桌面会话时无法创建 GUI 窗口 |
| AppleScript `open location` | 用 `open location` 切 URL | ✅ 页面加载，❌ 但登录态丢失 | 开新标签页而非复用已有标签 |
| Chrome CDP 远程调试 | `--remote-debugging-port=9222` | 端口从未打开 | 需要 Mac 桌面有人登录 |
| curl 直接抓取 | `curl zhipin.com` | 返回混淆 HTML | JS 渲染 + 动态 cookie |
| Chrome cookie 数据库读取 | `sqlite3 ~/Library/.../Cookies` | 0 条 BOSS cookies | HttpOnly + 加密存储 |

## 已验证可行

### 方案：AppleScript 开 Chrome + 真实窗口

```bash
osascript -e 'tell application "Google Chrome"
    activate
    open location "https://www.zhipin.com/web/user/?ka=header-login"
end tell'
```

- ✅ Chrome 正常打开，页面渲染完整
- ✅ 截图 57KB（非白屏，0% 白色像素）
- ❌ 限制：无法程序化控制后续操作

### 方案：boss-zhipin-automation + SSH 隧道

GitHub: `wensia/boss-zhipin-automation`

- ✅ FastAPI + React Web UI，手机浏览器可访问
- ✅ 二维码扫码登录，状态持久化
- ✅ Playwright 非 headless 控制
- ✅ SSH 隧道（localhost.run）暴露到公网
- ⚠️ 需 Mac 不锁屏

### TypeScript 编译修复

安装时遇到的 TypeScript 错误：
```
Property 'needs_verification' does not exist on type
```

修复：在 `frontend/src/hooks/useAutomation.ts` 第 335 行添加：
```typescript
needs_verification?: boolean;
```

## 商用替代方案

| 工具 | 类型 | BOSS 适配 |
|------|------|:--:|
| 影刀 RPA | 桌面 RPA | ✅ 有专用模块 |
| 八爪鱼 RPA | 桌面 RPA | ✅ 有专用模块 |
| 智聘 AI | 云端 SaaS | ⚠️ 需验证 |
| Moka | 企业 SaaS | ❌ 非 BOSS 专用 |
