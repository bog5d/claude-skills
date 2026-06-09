---
name: boss-recruitment-automation
description: BOSS直聘招聘自动化全流程——Web UI手机扫码登录 → 简历提取 → AI打分排序。用户不碰电脑，手机扫码一次后全自动。
version: 2.0.0
triggers:
  - 用户说"BOSS直聘 自动化 下载简历 打分 排序 筛人 招聘"
  - 用户提到投融资助理岗位简历筛选
  - "不碰电脑 招聘"
---

# BOSS直聘招聘自动化

## 最高原则

**用户不碰电脑。** 要么手机浏览器访问 Web UI，要么完全自动化。Mac 需要开着不锁屏，但用户不需要坐在电脑前。

---

## 前置依赖

```bash
pip3 install playwright && python3 -m playwright install chromium
brew install ngrok          # 公网隧道
# localhost.run 无需安装（SSH 自带）
```

---

## 方案一：boss-zhipin-automation（推荐，Web UI）

开源项目 `wensia/boss-zhipin-automation` — FastAPI + React + Playwright，手机可访问的管理面板。

### 安装

```bash
git clone https://github.com/wensia/boss-zhipin-automation.git ~/.hermes/tools/boss-automation
cd ~/.hermes/tools/boss-automation
chmod +x install.sh start.sh stop.sh manage.sh
./install.sh
```

### 常见安装错误：TypeScript 编译失败

**症状**：`Property 'needs_verification' does not exist on type`

**修复**：在 `frontend/src/hooks/useAutomation.ts` 第 331-339 行的内联返回类型中添加 `needs_verification?: boolean;`（放在 `on_recommend_page` 和 `has_frame` 之间）。然后重新 `./install.sh`。

### 启动 & 暴露公网

```bash
cd ~/.hermes/tools/boss-automation
./start.sh  # localhost:27421
```

**公网隧道优先级**：

| 方案 | 命令 | 坑 |
|------|------|-----|
| **localhost.run SSH** ⭐ | `nohup ssh -R 80:localhost:27421 nokey@localhost.run > /tmp/boss_tunnel.txt 2>&1 &` | 断开后 URL 会变；需要 `sleep 8` 后从文件提取 URL |
| ngrok | `ngrok http 27421` | **免费版有警告页** "ngrok-skip-browser-warning"，用户需多点一次 "Visit Site"，体验差 |

localhost.run URL 提取：`grep -o 'https://[a-z0-9]*\.lhr\.life' /tmp/boss_tunnel.txt | head -1`

### 用户操作流程（手机端）

1. 手机浏览器打开公网 URL
2. 点「自动化向导」→ 勾选「显示浏览器窗口」→「开始初始化」
3. Mac 弹出 Chrome，显示 BOSS 直聘登录页
4. 用户用手机 BOSS 直聘 App 扫码
5. 登录成功后即可配置自动任务

**当前限制**：boss-zhipin-automation 原生只支持"自动打招呼"，简历下载/打分需二次开发。

---

## 方案二：自建 Playwright 脚本（更灵活但需开发）

### BOSS直聘反爬对抗实录

| 方法 | 结果 | 根因 |
|------|:--:|------|
| Playwright headless | ❌ 白屏 | BOSS 检测 headless，返回空白页 |
| Playwright 非 headless + CDP 远程调试 | ❌ | `chrome --remote-debugging-port=9222` 需要 Mac 有活跃桌面会话，远程终端启动时端口不开放 |
| AppleScript `open location` | ⚠️ 部分可用 | **每次开新标签/窗口会丢登录态**，页面对 `open location` 重定向到登录页 |
| AppleScript `tell Chrome to activate` + 手动扫码 | ✅ | 系统 Chrome 窗口 + 用户扫码，登录态稳定 |

### 成功路径：AppleScript 开系统 Chrome + 用户扫码

```bash
# 打开系统 Chrome 到 BOSS 直聘登录页
osascript -e 'tell application "Google Chrome"
    activate
    open location "https://www.zhipin.com/web/user/?ka=header-login"
end tell'

# 截图发用户确认
sleep 5
screencapture -x ~/.hermes/cache/documents/boss_qrcode.png
```

**注意**：`open location` 会开新标签页。如果用户之前已经在该窗口登录过，建议直接让用户手动在 Chrome 地址栏输入 BOSS 直聘网址，而不是用 `open location`。

### 登录后状态验证

Cookie 提取可能失败（Chrome 锁住数据库、httpOnly cookie 等），用 **OCR 读截图** 来确认页面状态：

```bash
swift ~/.hermes/scripts/ocr_pro.swift ~/.hermes/cache/documents/boss_screen.png
```

关键词判断：出现 "找工作" 或 "沟通" → 已登录；出现 "扫码登录" → 未登录。

---

## 打分引擎

脚本：`~/.hermes/scripts/boss_resume_scorer.py`

六维权重：
- 学习力 25% / 专业力 20% / 商务力 20% / 销售属性 15% / 抗压 10% / 开放心态 10%

红线自动淘汰：社恐、排斥社交、玻璃心等关键词命中。

用法：
```bash
python3 ~/.hermes/scripts/boss_resume_scorer.py resumes.json   # JSON 数组
python3 ~/.hermes/scripts/boss_resume_scorer.py resume.txt     # 单份文本
```

---

## 商业替代方案

如果自建维护太累：

| 工具 | 类型 | 说明 |
|------|------|------|
| 影刀 RPA | 桌面 RPA（付费） | BOSS 专用，采集 + DeepSeek AI 打分 |
| 八爪鱼 RPA | 桌面 RPA（付费） | BOSS 专用模块 |
| Moka | HR SaaS（按年） | 全流程 AI 招聘 |
| 智聘AI | 云端 SaaS | 声称可远程操作 BOSS |

注意：所有商业方案仍需电脑运行桌面端或浏览器。
