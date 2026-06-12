---
name: software-copyright-screenshot-workflow
description: 为软件著作权申请截取SPA系统界面并生成操作手册/设计说明书PDF的完整工作流。含Browserbase localStorage跨上下文问题解决方案、中文字体PDF生成、截图→PDF全自动化。
category: devops
trigger: 软著申请、操作手册截图、软件著作权材料生成
---

# 软件著作权截图与文档生成工作流

## 背景

软著申请需要：操作手册（含登录+各功能模块截图）、设计说明书（含界面设计+功能+用例）、源代码（前1500+后1500行）。

对于 SPA（单页应用），需要系统化截取登录页、主界面各区域、子页面，并生成含截图的 PDF。

## 关键坑点

### ⚠️ Browserbase 的 browser_console 不在页面上下文中！

`browser_console` 执行在 `about:blank`，不是页面 origin。因此：
- `localStorage.clear()` 在 browser_console 中无效（清除的是 about:blank 的 localStorage）
- 无法通过 browser_console 修改页面状态

**解决方案：修改 `dist/index.html`，在 React bundle 加载前注入清除脚本：**

```html
<script>localStorage.clear();sessionStorage.clear();</script>
<script type="module" crossorigin src="/assets/index-xxx.js"></script>
```

然后 `browser_navigate` 到页面，会先清空 session 再加载 React，从而显示登录页。

**截图完成后务必恢复 index.html。**

### ⚠️ Browser_vision 在 DeepSeek 上失败

DeepSeek 不支持 `image_url` 类型的消息。`browser_vision` 会报错但截图文件正常保存。**直接用截图文件路径发 MEDIA，不需要 vision 分析结果。**

### ⚠️ 中文字体 PDF

fpdf2 默认 Helvetica 不支持中文，需要用系统 CJK 字体：
```python
pdf.add_font("CJK", "", "/System/Library/Fonts/STHeiti Medium.ttc", uni=True)
```
macOS 上的可用字体：`STHeiti Medium.ttc`, `PingFang.ttc`, `Arial Unicode.ttf`

## 截图工作流

### Step 1: 启动系统
```bash
cd ~/project && uv run uvicorn app.main:app --port 8000 &
```

### Step 2: 截登录页
1. 修改 dist/index.html 注入 localStorage.clear()
2. `browser_navigate(url="http://localhost:8000")`
3. `browser_vision(question="x")` — 截图保存
4. 恢复 index.html

### Step 3: 登录并截主界面
1. 恢复 index.html 后 navigate
2. 用 `browser_type` 填写登录表单
3. `browser_click` 登录按钮
4. 截主界面顶部
5. `browser_scroll` + 截图中部
6. `browser_scroll` + 截图底部

### Step 4: 截子页面
1. `browser_navigate` 到子页面路由
2. `browser_vision` 截图

### Step 5: 生成 PDF
用 fpdf2 + CJK 字体生成操作手册和设计说明书。

## 截图命名与组织

截图按时间戳保存到 `~/.hermes/cache/screenshots/browser_screenshot_*.png`。按 `st_mtime` 排序取最新 N 张。

过滤规则：小于 10KB 的截图通常是空白页，丢弃。

## 源代码整理

软著要求约 3000 行源码（前 1500 + 后 1500 行）。如果单个文件不足：
1. 拼接核心模块文件
2. 加注释标注模块边界
3. 取前 1500 行和后 1500 行分别保存

## 模板参考

操作手册模板结构（参考"润宇智慧停车"范本）：
- 封面 + 目录
- 第一章：系统登录
- 第N章：每个功能模块配截图+操作步骤文字

设计说明书模板结构：
- 封面 + 目录
- 1 引言
- 2 平台介绍
- 3 详细设计（每个模块：界面设计+功能介绍+功能用例）
- 4 源代码说明
