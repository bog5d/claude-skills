---
name: fos-screenshot-capture
description: 为仓颉FOS系统截取操作手册所需界面截图的标准流程。处理登录页捕获、页面滚动截图、Browserbase上下文隔离等坑点。
category: user-patterns
trigger: 波总要求截FOS界面/写操作手册/软著截图
---

# FOS系统截图流程

## 背景

FOS是React SPA（localhost:8000），截图用于软著操作手册。关键坑点：Browserbase browser_console运行在about:blank上下文，无法操作页面localStorage。

## 前置条件

1. FOS项目位置：`~/cangjie-fos`
2. 启动命令：`cd ~/cangjie-fos/backend && uv run uvicorn cangjie_fos.main:app --host 0.0.0.0 --port 8000`
3. 前端构建：`cd ~/cangjie-fos/frontend && npm run build`
4. 登录凭证：账号 T001，密码 123456，指挥官姓名"波总"
5. 软件全称："其烁仓颉FOS融资作战操作系统"

## 截图流程

### Step 1: 构建并启动

```bash
lsof -ti:8000 | xargs kill -9 2>/dev/null
cd ~/cangjie-fos/frontend && npm run build
cd ~/cangjie-fos/backend && uv run uvicorn cangjie_fos.main:app --host 0.0.0.0 --port 8000 &
sleep 5 && curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
```

### Step 2: 清除登录session（关键！）

⚠️ **核心坑点**：`browser_console` 在 `about:blank` 上下文中执行，`localStorage.clear()` 无效！

**唯一有效方法**：在 `frontend/dist/index.html` 的 `<head>` 中，**React加载之前**注入清除脚本：

```html
<script>localStorage.clear();sessionStorage.clear();</script>
```

放在 `<script type="module" ... src="/assets/index-xxx.js">` **之前**。

### Step 3: 截登录页

```python
browser_navigate(url="http://localhost:8000")
# 确认 snapshot 显示登录表单（3个输入框+登录按钮）
browser_vision(question="x")  # 截图
```

### Step 4: 登录并截主界面

```python
browser_type(ref="姓名框", text="波总")
browser_type(ref="账号框", text="T001")
browser_type(ref="密码框", text="123456")
browser_click(ref="登录按钮")
# 等待登录完成
browser_vision(question="x")  # 截Dashboard顶部
```

### Step 5: 滚动截取各区域

```python
# Dashboard顶部（指挥台+Pipeline漏斗）— 已截
browser_scroll(direction="down")
browser_vision(question="x")  # 豆豆AI + 机构看板

browser_scroll(direction="down")  
browser_scroll(direction="down")
browser_vision(question="x")  # 资产台账

browser_scroll(direction="down")
browser_vision(question="x")  # 尽调响应台 + 机构档案
```

### Step 6: 截复盘页面

```python
browser_navigate(url="http://localhost:8000/review/test-job-1")
browser_vision(question="x")
```

### Step 7: 恢复index.html

截图完成后**必须移除注入的清除脚本**，恢复原文件。

## 截图收集与PDF生成

```python
from pathlib import Path
d = Path.home() / ".hermes" / "cache" / "screenshots"
shots = sorted(d.glob("browser_screenshot_*.png"), key=lambda x: x.stat().st_mtime, reverse=True)[:6]
# 用 fpdf2 + STHeiti 字体生成中文PDF
```

## 陷阱

- **DO NOT** 用 `browser_console` 清除 localStorage——它在 about:blank 上下文
- **DO NOT** 用模拟HTML代替真实FOS登录页——波总能认出来
- 截图大小判断：有效截图通常 400-500KB，<10KB 的是空白/纯色截图
- 登录页截图约30KB（暗色主题+简单表单）是正常的
- 每次截图后检查文件大小，丢弃太小(<50KB)的截图
- 中文字体用 `/System/Library/Fonts/STHeiti Medium.ttc`
