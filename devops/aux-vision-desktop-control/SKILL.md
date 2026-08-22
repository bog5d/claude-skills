---
name: aux-vision-desktop-control
description: 主模型无视觉、computer_use som 空时用。vision_analyze 标定坐标再点击。
trigger: 主模型看不到 computer_use 的 som 截图、som 返回空 elements、需要点网页/App 上的按钮但 coordinate 盲点失败
version: 1.0.0
---

## When to Use

- 主模型无原生视觉（DeepSeek 等），`computer_use` som 截图自己看不到、elements 为空。
- 需要点网页/App 上的按钮，但 coordinate 盲点失败、background 点击无反应。
- 需要给非视觉主模型一个「标定坐标 → 点击 → 验证」的确定性桌面驱动链路。

# 无视觉主模型驱动 macOS 桌面（auxiliary.vision 标定坐标）

当主模型是 DeepSeek 等**无原生视觉**的模型时，`computer_use` 的 som 截图自己根本看不到，
且 som capture 对 Electron/Chromium 应用常返回 0 个 elements（AX 树不暴露）→ 只能靠坐标点击。
本 skill 记录「用辅助视觉模型标定坐标 + 知道点哪些 App 有效」的确定性链路。

## 核心链路：screencapture → vision_analyze 标定 → 点击

别盲点坐标。先抓图，再用 Hermes 自带 `vision_analyze`（走 auxiliary.vision，如硅基流动千问）问坐标：

```bash
screencapture -x -l <window_id> /tmp/win.png
```

```
vision_analyze(image_url="/tmp/win.png", question="标出「浏览器下载」按钮的中心像素坐标(x,y)，只回答数字")
```

返回精确坐标后，用 `computer_use` `click coordinate=[x,y]` 或 CGEvent 点击。
window_id 从 `computer_use action=list_windows` 拿（每次应用重启后 window_id 会变，重新查）。

## background 点击落在哪类 App 有效（关键坑，2026-08-22 实测）

- ✅ **原生 / Electron 桌面 App**（如 123云盘桌面端）：`computer_use` background CGEvent 点得动。
- ❌ **Chrome / Chromium 网页内容**：同一 background 坐标点击**零反应**（页面纹丝不动，
  `effect: unverifiable`，连点两次都没触发任何事件）。

对 Chromium 网页的升级阶梯（依次尝试，别在同一 rung 上反复重试）：
1. `delivery_mode='foreground'` —— 前置窗口 + 真实鼠标事件（会短暂抢用户焦点，需单独授权）。
2. AppleScript `execute javascript` 精确点 DOM 元素（`tell application "Google Chrome" to execute active tab of front window javascript "..."`）。
3. `computer_use` 的 typed-browser 系列（`cua_browser_state`/`cua_browser_click`）拿 ref 点击。

## 坐标映射坑

`screencapture -l <WID>` 的图片尺寸 ≠ `computer_use` capture 的尺寸，也 ≠ AppleScript 窗口 bounds：
- screencapture 含窗口阴影（Mac Mini 实测约 34px，`img_w - window_w` 算）。
- `computer_use` capture 返回的是窗口内容区逻辑像素，与 screencapture 像素/含阴影图不是同一坐标系。
- 因此 vision_analyze 在 screencapture 图上给的坐标，不能直接喂给 computer_use click ——
  先用 foreground 试 vision 原始坐标，偏了再按阴影偏移校正，或直接转 AppleScript JS / typed-browser。
- 屏幕是否 Retina 用 `system_profiler SPDisplaysDataType | grep -i retina`；1080p 非 Retina 时
  逻辑=物理，坐标映射更简单。

## 坑：Chrome 的 AppleScript JS 权限

「允许 Apple 事件中的 JavaScript」**不能**用
`defaults write com.google.Chrome AllowJavaScriptAppleEvents -bool true` 开启——
新版 Chrome 必须菜单手动开（查看 > 开发者 > 允许 Apple 事件中的 JavaScript），且要重启 Chrome；
defaults 写后重启仍报错 `通过 AppleScript 执行 JavaScript 的功能已关闭`。
验证 Chrome 是否接受 Apple Events：`osascript -e 'tell application "Google Chrome" to get URL of active tab of front window'`。

## 验证闭环

- 先用 `ls -la` 确认目标产物落地（如下载目录新文件、`*.crdownload` 消失），别只看页面状态。
- 每次 `click` 后 `capture_after=true` 或重新 `list_windows`/`screencapture` 确认状态变化再下一步。

## 相关 skill

- `macos-gui-inspection`（bundled）：锁屏 / Swift Vision OCR / CGEvent 点击，坐标映射细节更全。
- `123pan-download`（bundled）：分享页「浏览器下载 无需登录」按钮路线、`.cn` vs `.com` 元数据 API 差异。
