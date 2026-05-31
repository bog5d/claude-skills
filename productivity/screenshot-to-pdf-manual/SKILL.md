---
name: screenshot-to-pdf-manual
description: 为软件系统生成带截图的 PDF 操作手册。适用于软著申请、用户手册、产品文档等场景。自动化全流程：启动系统 → 浏览器截图 → 生成 PDF。
category: productivity
trigger: 用户要求生成操作手册、软件截图做成PDF、软著材料准备
---

# Screenshot → PDF 操作手册生成工作流

## 背景

软著申请等场景需要提交详细的操作手册，含：登录界面、主界面、各功能模块的截图+文字描述。手动操作耗时巨大，此工作流全自动化。

## 工作流

### Step 1: 启动目标系统

确认系统可访问（本地/远程），记录访问地址。

```bash
# 例如 FastAPI 项目
cd ~/project/backend && uv run uvicorn main:app --port 8000 &
```

### Step 2: 收集截图 — 登录页

如果登录页无法通过清除 session 访问（SPA 的 localStorage 在 browser tool 中跨域受限），**从源码分析登录页结构，生成独立 HTML 文件渲染**：

```python
# 读 LoginPage.tsx → 提取表单结构 → 生成 HTML → 浏览器打开截图
html = '''<!DOCTYPE html>...<form>...</form>...'''
write_file("/tmp/login_page.html", html)
browser_navigate("file:///tmp/login_page.html")
browser_vision(question="x")  # DeepSeek不支持vision但截图会保存
```

### Step 3: 收集截图 — 主界面各区域（长页面 SPA）

对于单页应用（SPA），使用 scroll + screenshot 分段截取：

```
browser_navigate("http://localhost:8000")
browser_vision(question="x")  # 截顶部

browser_console(expression="window.scrollTo(0, 700)")
browser_vision(question="x")  # 截中段

browser_console(expression="window.scrollTo(0, 1400)")
browser_vision(question="x")  # 截底部
```

**关键发现**：
- `browser_vision` 使用 DeepSeek 模型时 vision 分析会报错（不支持 image_url），但**截图文件会正常保存**到 `~/.hermes/cache/screenshots/`
- 截图路径在 error 响应的 `screenshot_path` 字段中
- 只保留 >10KB 的截图（<10KB 是空白/无内容截屏）

### Step 4: 收集截图 — 弹窗/交互界面

点击按钮 → 截图 → 记录：

```
browser_click(ref="e10")   # 展开面板
browser_vision(question="x")
```

### Step 5: 生成 PDF

使用 fpdf2 + macOS 中文字体：

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_font("CJK", "", "/System/Library/Fonts/STHeiti Medium.ttc", uni=True)
pdf.add_font("CJK", "B", "/System/Library/Fonts/STHeiti Medium.ttc", uni=True)

# 封面
pdf.add_page()
pdf.set_font("CJK", "B", 22)
pdf.cell(0, 20, "软件名称", align="C")

# 目录
pdf.add_page()
pdf.set_font("CJK", "B", 18)
pdf.cell(0, 15, "目 录")

# 截图页（每章一页：标题 + 截图 + 文字描述）
for title, desc_lines, shot_path in chapters:
    pdf.add_page()
    pdf.set_font("CJK", "B", 16)
    pdf.cell(0, 12, title)
    pdf.image(shot_path, x=10, w=190)
    for line in desc_lines:
        pdf.set_font("CJK", "", 11)
        pdf.cell(0, 7, "  " + line)

pdf.output("/tmp/manual.pdf")
```

其他可选字体：
- PingFang: `/System/Library/Fonts/PingFang.ttc`
- Arial Unicode: `/Library/Fonts/Arial Unicode.ttf`

### Step 6: 发送给用户

```
MEDIA:/tmp/manual.pdf
```

## 软著操作手册格式要求

根据实际退稿反馈，需满足：
1. **封面**：软件全名 + 版本号 + 开发单位 + 日期
2. **目录**：章节结构清晰
3. **登录界面**：需有截图，含账号密码输入框、登录按钮
4. **各功能模块**：每模块独立章节，截全页面，配文字描述操作步骤
5. **截图要清楚、要截全**：整页截取，不要局部
6. **名称规范**：软件名称以"软件/系统/平台"结尾

## 注意事项

- browser_vision 在 DeepSeek 下分析必失败，只取截图文件
- 过滤 <10KB 的截图（空白页）
- fpdf2 默认不支持中文，必须 add_font 注册 CJK 字体
- 长页面 SPA 用 window.scrollTo 分段截（不要用 browser_scroll — 截到的是 viewport 顶部）
- 登录页截不到时用 HTML 渲染方案，不要死磕 session 清除
- 截图文件名在 error 响应的 `screenshot_path` 字段
