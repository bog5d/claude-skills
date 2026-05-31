---
name: software-copyright-submission
description: 软件著作权申请材料生成完整工作流。含操作手册截图、设计说明书撰写、源代码整理（前1500+后1500行）、PDF生成与打包。当用户需要软著申请材料时使用。
category: devops
trigger: 软著、著作权、操作手册、设计说明书、源程序、版权申请
---

# 软件著作权申请材料生成工作流

## 背景

软著申请通常需要三份核心材料：
1. **操作手册** — 含登录界面、各功能模块详细截图+操作说明
2. **设计说明书** — 含引言、平台介绍、各模块界面设计+功能介绍+功能用例
3. **源程序** — 前1500行+后1500行，约3000行，各模块功能在说明书中体现

## 前置条件

- 软件系统可运行（需要截图界面）
- 源代码可访问
- 软著代理提供的模板格式要求
- **FOS 系统登录**：T001 / 123456 + 指挥官姓名（波总）
- **软著代理联系人**：北京聚源企服 王璋腾 15313516504
- **命名铁律**：必须用"其烁仓颉FOS融资作战操作系统"（"仓颉"已被注册商标）

## 工作流

### Step 1: 理解需求

从软著代理获取反馈，确认：
- 操作手册需要多详细（登录界面截图、操作步骤、各模块覆盖）
- 源代码行数要求（通常3000行左右，前1500+后1500）
- 软件名称要求（注意商标冲突）
- 目标格式（PDF/Word）

### Step 2: 启动系统并截图

```bash
# 启动目标系统
cd <project>/backend && uv run uvicorn main:app --port 8000 &
```

**截图关键陷阱：**
- `browser_console` 运行在 `about:blank` 上下文，不是页面上下文！
- 因此在 console 中的 `localStorage.clear()` 不影响实际页面
- 需要登录页时，注入 `<script>localStorage.clear();sessionStorage.clear();</script>` 到 `index.html` 的 `<head>` 中
- 截完后务必恢复 index.html

**截图方案：**
1. 用 `browser_vision(question="x")` 截图——DeepSeek 不支持 vision 分析，但截图文件正常保存
2. 验证截图质量：好的截图 400KB+，差的只有 4KB（暗色主题在 Telegram 显示为纯色）
3. 暗色主题 Web 应用在 Telegram 上可能显示异常——通过文件大小判断质量

**需要截的页面（按软著标准）：**
- 登录页面（含账号密码输入框）
- 主界面/Dashboard 全貌（可能需要分段截长页面）
- 每个功能模块的独立区域
- 弹窗/模态框/展开面板

**截长页面技巧：**
```python
# 用 browser_console 滚动到不同位置分别截
browser_console(expression="window.scrollTo(0, 700)")
browser_vision(question="x")  # 截图虽分析失败但文件正常
```

### Step 3: 恢复 index.html

```bash
# 去掉注入的清除脚本
patch index.html: 删除 <script>localStorage.clear();...</script>
```

### Step 4: 生成操作手册 PDF

使用 Python fpdf2：

```python
from fpdf import FPDF
# 必须使用中文字体
pdf.add_font("CJK", "", "/System/Library/Fonts/STHeiti Medium.ttc", uni=True)
```

**PDF 结构：**
- 封面（软件名称 + 操作手册 + 版本 + 公司 + 日期）
- 目录
- 第一章：系统登录（截图 + 操作步骤说明）
- 后续章节：各功能模块（截图 + 功能描述）
- 注意：字符串中避免中文双引号「""」，使用「」替代

**截图插入：**
```python
pdf.image(str(shot_path), x=10, w=190)  # 宽度190mm适配A4
```

### Step 5: 生成设计说明书 PDF

**PDF 结构：**
- 封面 + 目录
- 1. 引言（编写目的、预期读者、平台名称、参考资料）
- 2. 平台介绍（概述、功能模块总览、开发目标、运行环境）
- 3. 详细设计（每个模块：界面设计 + 功能介绍 + 功能用例）
  - 3.1 系统登录与用户认证
  - 3.2 融资作战指挥台
  - ...
- 4. 源代码（源程序量、编程语言、主要模块列表）

### Step 6: 整理源代码

**行数要求：** 通常 3000 行左右，取前 1500 行和后 1500 行

**无单文件达标时的拼接方案：**
```python
files = [
    ("engine/report_builder.py", "报告生成引擎"),
    ("services/pitch_job_db.py", "数据库持久化"),
    ("engine/transcriber.py", "语音转写引擎"),
    ("engine/memory_engine.py", "记忆引擎"),
]
# 每个文件加分隔注释头
# 拼接后切分：all_lines[:1500] + all_lines[-1500:]
```

### Step 7: 最终打包

统一改名格式：`序号_文件类型_软件名称V版本号.扩展名`

```
01_操作手册_其烁仓颉FOS融资作战操作系统V1.0.pdf
02_设计说明书_其烁仓颉FOS融资作战操作系统V1.0.pdf
03_源程序_前1500行.txt
04_源程序_后1500行.txt
05_源程序_完整版.txt
README.md（说明文件）
```

打包：`zipfile.ZIP_DEFLATED` 压缩为 zip。**注意**：波总不喜欢压缩包——优先直接发单个 MEDIA 文件，不用 zip。

## 常见陷阱

| 陷阱 | 原因 | 解决 |
|------|------|------|
| 登录页截不到 | browser_console 在 about:blank 上下文 | 注入 HTML 脚本清 localStorage |
| 截图全是纯白/纯黑 | 暗色主题 + Telegram 压缩 | 检查文件大小（400KB+ 正常） |
| fpdf2 报 UnicodeEncodeError | Helvetica 不支持中文 | 使用 STHeiti/PingFang 字体 |
| Python 字符串中文引号冲突 | `"` 和 Python 的 `"` 相同 | 使用 `「」` 替代中文双引号 |
| 源程序行数不够 | 单文件不足 3000 行 | 拼接多文件 + 模块分隔注释 |
| 文档残留模板提示语 | 尽调表/协议模板含「请填写」「示例」等 | 生成时直接替换为实际内容或「以协议约定为准」 |
| macOS OCR 有水印遮挡 | Vision 框架识别受水印干扰 | 关键字段可手动确认；正文被挡不纠结直接用标准模板 |

## 交付检查清单

- [ ] 操作手册含真实登录页截图
- [ ] 每个功能模块有截图 + 文字说明
- [ ] 设计说明书含界面设计 + 功能介绍 + 功能用例
- [ ] 源代码前 1500 行 + 后 1500 行
- [ ] 软件名称统一（注意商标冲突）
- [ ] 版本号一致
- [ ] 所有模板提示语已删除（交付文件必须干净，无「请填写」「示例」等提示字样）
- [ ] 优先发 MEDIA 单文件，不用 zip 压缩包
