---
name: pdf-to-pptx-image-transfer
description: Use when 用户发来缺图PPT+含图PDF要抽图填进PPT。
version: 1.0.0
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [pptx, pdf, pymupdf, fitz, python-pptx, image-extraction, slides, 填图, 配图]
    category: productivity
    related_skills: [powerpoint, pdf, pdf-image-extraction]
---

# PDF → PPT 图片填充

用户手头常有两份「同一份 BP / 报告」的不同载体：一份缺图的 PPTX（纯文字+装饰形状），
一份图文齐全的 PDF。任务是把 PDF 的视觉内容（产品图、架构图、证书、场景图）填进 PPT，
让 PPT 变成图文完整、可交付的成品。

## 触发条件

- 用户发来一个 .pptx 说「缺东西」「太干了」，同时（或随后）发来一个 .pdf 让你「抽图填满」。
- 需要把某个文档里的图片搬进另一份幻灯片，而不是从零画图。
- 「从 PDF 里抠图 / 提取对应图片 / 用图填满 PPT」这类措辞。

## 核心流程

### 1. 读透两份文档（先理解，再动手）

```bash
# PPT：逐页文字 + 图片数 + 占位符 + 页面尺寸
python3 -c "from pptx import Presentation; from pptx.util import Emu; \
prs=Presentation('in.pptx'); print('页数',len(prs.slides),'尺寸',Emu(prs.slide_width).inches,'x',Emu(prs.slide_height).inches)"
```

用 python-pptx 遍历 `slide.shapes`：`shape.has_text_frame` 取文字、
`shape.shape_type == 13` 记图片、`shape.is_placeholder` 记占位符、`shape.has_table` 取表格。
关键信号：**图片总数为 0** 而文字齐全 = 典型的「图被剥离」的残缺版。

PDF 用 PyMuPDF（`import fitz`）：
- `len(doc)` 页数、`page.get_text()` 文字、`page.get_images(full=True)` 嵌入图片清单、
  `page.get_image_rects(xref)` 每张图的位置与占比（判断是整页背景还是局部内容图）。

### 2. 版本/口径比对 —— 最容易踩的坑（必做）

两份「看起来是同一份 BP」的文档，很可能**不是同一版本的先后，而是两个用途/口径不同的版本**。
逐页比对标题和关键数字，把冲突先列给用户，**不要盲目合并**。

典型冲突（本类任务的真实案例）：
- 页数不同（14 vs 13），其中几页是甲方独有、几页是乙方独有。
- 关键财务数字不同：一份说「订单空间 30–40 亿 / 11 款批产」，另一份说「17.1 亿 / 5 类产品」。
  若把 17.1 亿口径的图整页贴进讲 30–40 亿的 PPT，会**静默改写财务数据**——必须显式提醒用户统一口径。

做法：先输出一个映射表（PPT 页 ↔ PDF 页 ↔ 是否口径冲突），让用户拍板策略。

### 3. 选填充策略（三种，各有取舍）

| 策略 | 做法 | 优点 | 缺点 |
|---|---|---|---|
| 整页贴图 | PDF 每页渲染高清 PNG，铺满 PPT 对应页 | 视觉 100% 还原、快、干净 | 文字变图片，不可编辑 |
| 抽图插入 | 只抠「完整图」（产品/场景/证书/封面）插进 PPT，保留文字 | 文字可编辑 | 架构图/财务图常被拆成几十个 2~170px 碎块，单独抽无意义；部分页仍偏空 |
| 混合（推荐默认） | 有 1:1 对应关系的页整页贴图；PDF 里没有的独有页保留原文字 | 成品最接近可用 | 需先想清独有页怎么处理 |

**整页贴图的判断要点**：只有存在清晰的 1:1 页面对应、且口径一致时才整页贴。
口径冲突页、PDF 缺失页 → 保留原文字或另想办法，绝不硬贴。

### 4. 执行

见 `references/pymupdf-pptx-snippets.md` 的可用代码：嵌入图提取、整页 3x 高清渲染、
python-pptx 全出血贴图（删掉该页所有 shape 再 `add_picture` 铺满）。

### 5. 验证

贴完重开文件统计每页 `图片N张 / 文本框M个`，确认：
- 1:1 页 = 1 图 0 文本（全出血贴图）；
- 保留页 = 0 图 原文本；
- 无「图片和文字叠在一起」的页（贴图前必须删干净该页 shape）。

## Pitfalls

- **口径/版本不一致是头号风险**：先比对再合并，冲突先抛给用户，别自以为「就是同一份」。
- **PDF 嵌入图分两种**：整块内容图（能干净抽）和配合矢量版式的碎片图（架构卡片、图表被拆成几十个小 PNG，单独抽出没有意义）。碎片图别硬抽，改用整页渲染。
- **CMYK 图片**：`fitz.Pixmap` 提取时若 `pix.n - pix.alpha > 3`，需转 `fitz.Pixmap(fitz.csRGB, pix)` 再 save，否则 PNG 色彩异常。
- **贴图前删 shape**：`for shape in list(slide.shapes): shape._element.getparent().remove(shape._element)`，否则原文字会叠在新图上。
- **页面比例**：确认 PDF 页宽高比与 PPT slide 一致（都是 16:9 才可全出血铺满；不一致会被拉伸）。
- **高清渲染**：整页贴图用 `fitz.Matrix(3.0, 3.0)`（2880×1620），2x 的 1920×1080 在投屏/打印时偏糊。

## 验证

1. 贴图后 `python-pptx` 重开统计每页图片数/文本框数，对照预期映射表。
2. 交付前明确告知用户哪些页保留文字、哪些页口径仍冲突，附上遗留待办。
3. 原文件保留不动，完全可逆；交付用新文件名（如 `<原名>_图文版.pptx`）。
