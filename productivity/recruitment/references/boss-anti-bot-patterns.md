# BOSS直聘反爬对抗实录

## 已验证不可行方案

| 方法 | 结果 | 根因 |
|------|:--:|------|
| Playwright headless | ❌ 白屏 | BOSS 检测 headless，返回空白页 |
| Playwright 非 headless + CDP 远程调试 | ❌ | `chrome --remote-debugging-port=9222` 需要 Mac 有活跃桌面会话 |
| AppleScript `open location` | ⚠️ 部分可用 | 每次开新标签/窗口会丢登录态 |
| curl/wget 直接抓 | ❌ | Cookie 加密 + 动态 token |

## 成功路径

### 1. boss-zhipin-automation（推荐）
开源项目 `wensia/boss-zhipin-automation` — FastAPI + React + Playwright Web UI
- 手机浏览器扫码登录，一次登录状态持久化
- REST API 可命令行操控

### 2. AppleScript 开系统 Chrome + 用户扫码
```bash
osascript -e 'tell application "Google Chrome"
    activate
    open location "https://www.zhipin.com/web/user/?ka=header-login"
end tell'
```

### 3. OCR 验证登录状态
```bash
screencapture -x /tmp/boss_screen.png
swift ~/.hermes/scripts/ocr_pro.swift /tmp/boss_screen.png
```
关键词判断："找工作"/"沟通" → 已登录；"扫码登录" → 未登录。

## REST API 操控
```bash
curl -X POST "http://localhost:27421/api/automation/init?headless=false&manual_mode=false"
sleep 8
screencapture -x /tmp/boss_page.png
swift ~/.hermes/scripts/ocr_pro.swift /tmp/boss_page.png | grep "扫码登录"
curl "http://localhost:27421/api/automation/check-ready-state"
```

## OCR 截图验证步骤
```bash
# 1. 截图
screencapture -x /tmp/page.png

# 2. 白屏检测
python3 -c "
from PIL import Image; import collections
im=Image.open('/tmp/page.png')
p=list(im.get_flattened_data())[:5000]
w=collections.Counter(p).get((255,255,255),0)
print(f'white={w}/5000 ({w*100//5000}%)')
"

# 3. OCR 内容抽取
swift ~/.hermes/scripts/ocr_pro.swift /tmp/page.png | grep -E "BOSS|直聘|扫码|登录"
```