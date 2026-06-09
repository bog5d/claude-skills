---
name: recruitment-automation
description: BOSS直聘招聘全流程自动化——从简历提取到AI打分排序。覆盖工具选型、反爬应对、web界面隧道暴露、简历打分引擎。
version: 1.0.0
trigger: "波总说'招聘''BOSS直聘''筛选简历''打分排序''下载简历''自动打招呼'时"
---

# Recruitment Automation — BOSS直聘招聘自动化

全流程：登录 → 简历提取 → AI打分排序 → 报告推送。目标是一次扫码后全自动，波总不碰电脑。

## ⚠️ 核心铁律

**BOSS直聘反爬是业内最狠的。以下方案已验证不可行：**

| 方案 | 结果 | 原因 |
|------|:--:|------|
| Playwright headless | ❌ | 白屏，BOSS 直接拦截 |
| AppleScript `open location` | ⚠️ | 开新标签页丢登录态 |
| Chrome CDP 远程调试 | ❌ | 需 Mac 活跃桌面会话 |
| curl/wget 直接抓 | ❌ | Cookie 加密 + 动态 token |

**已验证可行的路径：`boss-zhipin-automation` 开源工具（FastAPI + React + Playwright Web UI）**

## 工具栈

### 核心工具：boss-zhipin-automation

GitHub: `wensia/boss-zhipin-automation`

功能：
- Web UI（FastAPI + React），手机浏览器可访问
- 二维码扫码登录（一次登录，状态持久化）
- 多账号管理
- 候选人筛选
- 自动打招呼

安装（一次）：
```bash
cd ~/.hermes/tools/boss-automation
chmod +x install.sh start.sh stop.sh
./install.sh  # 首次安装，自动装 Python 依赖 + Chromium
```

启动：
```bash
./start.sh   # 后端启动在 localhost:27421
```

### 简历打分引擎：`boss_resume_scorer.py`

位置：`~/.hermes/scripts/boss_resume_scorer.py`（skill 内副本：`scripts/boss_resume_scorer.py`）

六维打分：学习力(25%) / 专业力(20%) / 商务力(20%) / 销售属性(15%) / 抗压(10%) / 开放心态(10%)

红线淘汰：社恐、接待耗能型、玻璃心、封闭心态

用法：
```bash
python3 boss_resume_scorer.py resumes.json  # JSON 数组批量
python3 boss_resume_scorer.py resume.txt    # 单份简历
```

### 公网暴露：SSH 隧道

参考 `quick-tunnel-deploy` skill：
```bash
nohup ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -o ExitOnForwardFailure=yes -R 80:localhost:27421 \
  nokey@localhost.run > /tmp/boss_tunnel_url.txt 2>&1 &
sleep 5
grep -o 'https://[a-z0-9]*\.lhr\.life' /tmp/boss_tunnel_url.txt | head -1
```

URL 格式：`https://<随机ID>.lhr.life`

## 完整工作流

```
1. 装工具 → ./install.sh
2. 启动 → ./start.sh
3. 开隧道 → SSH localhost.run
4. 发 URL 给波总 → 手机打开 Web UI
5. 波总扫码一次 → 登录态保存
6. 自动翻简历 → Playwright 操作
7. 提取文本 → 跑 boss_resume_scorer.py
8. 排名推送 → Telegram
```

## 已知限制

- **当前 boss-zhipin-automation 只做"自动打招呼"**，简历下载和打分需二次开发
- **Mac 必须不锁屏**运行——休眠则浏览器不可用
- **SSH 隧道 URL 每次重启会变**，非固定地址
- BOSS 直聘无公开招聘方 API，官方不提供简历数据接口

## 替代方案（商用）

| 工具 | 模式 | 说明 |
|------|------|------|
| 影刀 RPA | 桌面客户端 | BOSS 直聘采集 + DeepSeek AI 打分，案例成熟 |
| 八爪鱼 RPA | 桌面客户端 | 有 BOSS 直聘专用模块 |
| Moka | 企业 SaaS | 全流程 AI 招聘，1000份简历5分钟 |
| 用友大易 | 企业 SaaS | 2025年排名第一的 AI 招聘系统 |

## Pitfalls

- ❌ 不要尝试 headless 模式——BOSS 直接白屏
- ❌ 不要用 AppleScript `open location` 开新标签——登录态会丢
- ❌ 不要指望 BOSS 官方 API——他们不提供
- ❌ **Web UI 菜单名与 README 不一致**：README 说「自动化向导」，实际 UI 显示「快速启动」。给波总指路前必须 API/OCR/截图三重验证
- ❌ **ngrok 免费版有警告插页**："You are about to visit..." 首次访问需手动点 "Visit Site"。优先用 localhost.run SSH 隧道
- ✅ **优先用 REST API 而非 Web UI**：API 端点 `/api/automation/init`、`/login`、`/check-ready-state` 更可靠，不被 UI 翻译问题困扰
- ✅ 唯一稳定路径：非 headless Chrome + REST API + 一次扫码
- ✅ **OCRsight 验证模式**：用 Swift Apple Vision OCR + PIL 白屏检测双重确认页面内容，不靠猜测

## REST API 操控（推荐，替代 Web UI）

不用让波总在手机上点界面——从命令行全程操控：

```bash
# 初始化浏览器（非 headless）
curl -X POST "http://localhost:27421/api/automation/init?headless=false&manual_mode=false"

# 等 Chrome 导航到 BOSS 直聘
sleep 8

# 截图 + OCR 验证页面
screencapture -x /tmp/boss_page.png
swift ~/.hermes/scripts/ocr_pro.swift /tmp/boss_page.png | grep "扫码登录"

# 检查状态
curl "http://localhost:27421/api/automation/check-ready-state"
# → current_url 变成 web/chat/index 说明已登录
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
