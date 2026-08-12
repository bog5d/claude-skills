---
name: pdf-image-extraction
description: 提取图片型/设计型 PDF（会议议程、邀请函、扫描件）的完整文本。
category: productivity
trigger: user sends PDF that needs text extraction, PDF has few text lines (design/scanned), agenda/invitation/poster PDF, pdf text not inlined
---

# PDF 图片型/设计型文本提取

## 触发条件

- 用户发来 PDF（会议议程/邀请函/海报/宣传单/扫描件），系统提示"text is not inlined (binary format)"
- 目标：拿到**完整**文本（议程逐条、名单逐条），不是部分摘要

## 核心判断：PDF 是"文字型"还是"图片/设计型"？

设计型 PDF（会议议程、邀请函、周年活动物料）的典型特征：
- 文字被**转曲**（转成轮廓）或放在图片层 → `get_text()` 只返回标题/头尾，正文缺失
- 内嵌大图（XObject Im*），常见 CMYK 颜色空间
- 文字有渐变/透明效果（Shading/ExtGState）

**判断方法**：`page.get_text()` 后看内容完整性——正文（议程表、名单）缺失 = 设计型，走三步法。

## 三步法（2026-08-12 实战验证）

### 第 1 步：尝试文字层提取（先试，成本最低）

```bash
python3 -c "
import fitz
doc = fitz.open('文件.pdf')
print(f'页数: {len(doc)}')
for i, page in enumerate(doc):
    print(f'===== 第{i+1}页 =====')
    print(page.get_text())
"
```

若正文完整 → 直接使用，结束。若正文缺失/只有头部 → 进入第 2 步。

### 第 2 步：渲染页面为高分辨率 PNG

```bash
python3 -c "
import fitz
doc = fitz.open('文件.pdf')
import os
os.makedirs('pdf_pages', exist_ok=True)
for pno in range(len(doc)):
    pix = doc[pno].get_pixmap(matrix=fitz.Matrix(3, 3))  # 3x 缩放，1786x2526
    pix.save(f'pdf_pages/page{pno+1}_render.png')
    print(f'page{pno+1}: {pix.width}x{pix.height}')
"
```

### 第 3 步：vision_analyze 逐页识别（走千问 VL Max）

```python
# 对每一页渲染图调用 vision_analyze，question 必须要求"逐条抄录、不遗漏、不概括"
vision_analyze(image_url='/abs/path/pdf_pages/page1_render.png',
               question='这是XX文档第N页。请完整逐条读出页面上所有文字：…。务必逐行抄录，不要遗漏，不要概括。')
```

**question 设计铁律**：明确列出要读的字段（如"时间段、环节名称、内容、发言人"）+ 强调"逐行抄录/不要遗漏/不要概括"——千问 VL 默认会概括，必须强制全文抄录。

### 降级链路（千问 VL 不可用时）

1. **Firecrawl parse**（云端 OCR，中文精度高）— 见 ocr-screenshot-extraction 技能
2. **Apple Vision OCR**：`swift ~/.hermes/scripts/ocr_pro.swift page.png`
3. 告知用户千问/Firecrawl 均不可用，本地 OCR 精度有限

## 陷阱与坑（全部踩过）

1. **嵌入图 ≠ 页面内容**：设计型 PDF 的内嵌大图常常是**纯装饰背景**（红色渐变/日出/帆船），没有文字。`get_images()` 提取的 Im13 可能是背景图。**优先渲染页面**（get_pixmap），渲染图才包含全部文字层。
   - 如果先提取嵌入图 → 千问 VL 会诚实回答"图中没有文字，是纯视觉设计图"→ 白费一轮。**直接渲染页面，别提取嵌入图。**
2. **CMYK/GRAY 颜色空间不能直接存 PNG**：`pix.save()` 报 `unsupported colorspace for 'png'` 时，先转 RGB：
   ```python
   pix = fitz.Pixmap(fitz.csRGB, pix)
   ```
3. **PDF 内年份可能是模板错误**：2026-08-12 收到的议程 PDF 印"2025年8月13日"，但徽标"2006-2026"（20周年）确认实际是 2026。**用徽标/上下文交叉验证年份，别盲信 PDF 正文**，并在入库时标注。
4. **vision_analyze 一次只处理一页**：多页文档逐页调用，别一次性塞多张图。
5. **页面渲染用 Matrix(3,3)**：低于 2x 小字会糊；3x 约 1786x2526 正好。
6. **识别结果必须二次核对关键数字**（时间、金额、电话）：千问 VL 对竖排/艺术字可能误读，入库前核对逻辑一致性（如议程时间 9:00-9:05 连续递增）。

## 产出规范

识别出的内容（尤其会议议程/名单）**立即入库**，不只回复在聊天里：
- 日程类 → `日程管理/YYYY-MM-DD_<事件>.md`（议程表 + 嘉宾名单 + 副官观察），并更新 `日程管理/UPCOMING.md` 对应行
- 与仓库中既有"疑云/待确认"条目交叉核对（如"8/13 对接会与路演是否同一场"→ 议程 PDF 落定）

## 相关技能

- `ocr-screenshot-extraction`：截图/单张图片的 OCR 链路（千问 VL → Firecrawl → 本地），本技能是其 PDF 场景扩展
