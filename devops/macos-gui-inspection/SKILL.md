---
name: macos-gui-inspection
description: 锁屏/cua-driver 失效时读 macOS GUI 窗口内容（Vision OCR）。
trigger: computer_use capture 返回空、屏幕锁定、需要读应用窗口内容或模拟点击
---

# macOS GUI Inspection (Locked Screen / cua-driver 失效)

当 `computer_use` 抓不到画面（典型根因：**macOS 屏幕被锁**）或模型无 vision 时，
用 Quartz + Swift Vision OCR + CGEvent 读窗口内容、模拟点击。屏幕锁着也能读内容。

## 0. 先诊断：屏幕是否被锁（避免在锁屏上白点半天）

```bash
python3 -c "import Quartz; d = Quartz.CGSessionCopyCurrentDictionary(); print('locked:', d.get('CGSSessionScreenIsLocked'), '| since:', d.get('CGSSessionScreenLockedTime'))"
```

`locked: True` 时：
- computer_use capture 静默返回 0x0 空画面（无报错）、list_apps/windows 为空
- CGEvent 点击/键盘全部落在锁屏层，应用收不到
- osascript/System Events 超时（-1712 / -609）
- **但窗口仍在渲染**：CGWindowList 可见、screencapture -l 可抓 → OCR 可读

行动：汇报「屏幕锁了（since <日期>）」请用户解锁；锁屏期间只做读取，不做点击。

## 1. 按窗口抓图

```bash
WID=$(python3 -c "
import Quartz
wins = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
for w in wins:
    if w.get('kCGWindowOwnerName')=='Electron':   # 按 app 所有者名匹配
        print(w['kCGWindowNumber']); break
")
screencapture -x -l "$WID" /tmp/win.png
```

注意：owner 名不一定是应用名（如 Skill Recorder 的 owner 是 "Electron"）。

## 2. Swift Vision OCR（macOS 原生，中文+英文，无需安装）

```swift
// /tmp/ocr.swift — usage: swift /tmp/ocr.swift /tmp/win.png
import Vision; import AppKit; import Foundation
let path = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "/tmp/win.png"
guard let img = NSImage(contentsOfFile: path),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { exit(1) }
let req = VNRecognizeTextRequest(); req.recognitionLevel = .accurate
req.recognitionLanguages = ["zh-Hans", "en-US"]
try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
for obs in req.results ?? [] { if let t = obs.topCandidates(1).first { print(t.string) } }
```

带坐标版：boundingBox 是归一化、左下原点 → 左上原点：
`x = b.origin.x*W`，`y = (1 - b.origin.y - b.size.height)*H`。

## 3. CGEvent 模拟点击（仅解锁后有效）

```swift
// /tmp/click.swift — usage: swift /tmp/click.swift X Y
import CoreGraphics; import Foundation
let pt = CGPoint(x: Double(CommandLine.arguments[1])!, y: Double(CommandLine.arguments[2])!)
CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: pt, mouseButton: .left)?.post(tap: .cghidEventTap)
usleep(80000)
CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: pt, mouseButton: .left)?.post(tap: .cghidEventTap)
```

## 坐标映射

`screencapture -l` 带窗口阴影（Mac Mini 实测约 34px，验证：`img_w - window_w`）。
图片坐标 → 屏幕坐标：`screen = window_origin + (img_xy - shadow)`。
窗口 origin/size 从 `CGWindowListCopyWindowInfo` 的 `kCGWindowBounds` 取。

## 验证闭环（2026-08-08 Skill Recorder 自测实录）

- Electron 窗口在锁屏下 CGWindowList 可见、screencapture -l 可抓、Vision OCR 读到完整 UI 文案（"Ready to capture / 00:00"）
- 同一窗口 CGEvent 点击无效（落在锁屏）→ 先查锁屏再动手
- 此链路 5 条命令全走 /tmp，无持久依赖
