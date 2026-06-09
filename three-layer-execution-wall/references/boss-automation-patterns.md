# BOSS直聘自动化关键发现

2026-06-09 会话经验总结。下次遇到 BOSS 直聘自动化任务时参考。

## 已验证有效路径

### 1. 登录：AppleScript + 非 headless Chrome

```bash
# 唯一可靠方式——非headless Chrome，绕不过反爬
osascript -e 'tell application "Google Chrome"
    activate
    open location "https://www.zhipin.com/web/user/?ka=header-login"
end tell'
```

→ 用户在 Mac 屏幕上看到二维码 → 手机 BOSS直聘 App 扫码 → 登录成功。

**Pitfall**: `open location` 会开新标签页。如果原标签页已登录，新标签的 `open location` 不会自动带上 session。

### 2. 页面探读：OCR 最可靠

```bash
screencapture -x /tmp/screen.png
swift ~/.hermes/scripts/ocr_pro.swift /tmp/screen.png
```

→ 从 OCR 输出提取页面名称、URL、候选人姓名、关键字段。

**为什么不用 Playwright headless**：BOSS 直聘反爬极强，headless Chromium 返回白屏（100% white pixels）。

### 3. boss-zhipin-automation 工具

- 位置：`~/.hermes/tools/boss-automation/`
- 端口：`localhost:27421`
- 启动：`cd ~/.hermes/tools/boss-automation && ./start.sh`
- 停止：`./stop.sh`
- API 初始化：`POST /api/automation/init?headless=false&manual_mode=false`
- 就绪检查：`GET /api/automation/check-ready-state`
- 推荐候选人：`GET /api/automation/recommend-candidates`

**已知问题**：DOM 解析器可能跟不上 BOSS 直聘页面更新，返回空列表或 "未找到选择器" 错误。降级方案：OCR 提取。

### 4. 公网隧道

- **localhost.run SSH 隧道**（推荐）：`ssh -R 80:localhost:27421 nokey@localhost.run`，无警告页
- **ngrok**（备选）：免费版有警告页（需用户手动点 "Visit Site"）

### 5. 简历打分引擎

- 脚本：`~/.hermes/scripts/boss_resume_scorer.py`
- 用法：`python3 boss_resume_scorer.py resume.txt` 或 `boss_resume_scorer.py resumes.json`
- 六维权重：学习力25% / 专业力20% / 商务力20% / 销售属性15% / 抗压10% / 开放心态10%
- 红线：社恐/接待耗能型/玻璃心 → 直接淘汰

## 已验证无效路径

| 尝试 | 失败原因 |
|------|---------|
| Playwright headless | BOSS 反爬 → 白屏 (5KB screenshot) |
| Playwright 非headless (远程) | Mac 无活跃桌面会话 |
| Chrome CDP --remote-debugging-port=9222 | `open -a --args` 对已安装的 Chrome 不生效 |
| `osascript execute javascript` | Chrome 默认禁用 AppleEvent JavaScript |

## 下次优化方向

1. 修 boss-zhipin-automation 的 DOM 选择器，适配当前 BOSS 页面
2. 找到在 Mac 上打开 Chrome CDP 端口的方法
3. 或者放弃 CDP，改用 OCR + screencapture 全链路自动化
