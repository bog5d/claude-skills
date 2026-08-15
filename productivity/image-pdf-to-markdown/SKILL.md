---
name: image-pdf-to-markdown
description: 图片型/超长页 PDF 转结构化 Markdown 全链路（渲染→切片→OCR→拼装）。
category: productivity
trigger: user sends image-based PDF, PDF has no text layer, course slides PDF, ultra-tall PDF pages, scan-to-markdown, 整理为 md 喂给 AI 讨论
---

# 图片型/超长页 PDF → Markdown 全链路

## 触发条件

- PDF 无文字层（`get_text()` 返回空/只有标题）：课程课件、扫描件、公众号长图转 PDF、设计型文档
- 页面是**超长图**（课件一页 540×9156 这种，等于 7 屏滚动截图）
- 用户要求"整理成 md / 映射为 md / 喂给 AI 讨论"
- 典型场景：波总发来得到APP课程 PDF 包 → 逐讲转结构化 md（表格保留、要点提炼、洞察）

## 核心链路（五步）

```
get_text() 探测 → 渲染 PNG → 超长页切片 → OCR/视觉识别 → 拼装结构化 md
```

### 第 1 步：探测文字层（10 秒，决定后续路线）

```bash
python3 -c "
import fitz
doc = fitz.open('文件.pdf')
print('pages:', len(doc))
for i, page in enumerate(doc):
    print(f'--- PAGE {i+1} ---')
    print(page.get_text()[:1500])
"
```

- 文字层完整 → 直接 `get_text()` 用，跳过后续全部
- 空/只有标题 → 图片型，走第 2 步

### 第 2 步：渲染页面为 PNG（150 DPI 起步）

```bash
python3 -c "
import fitz
doc = fitz.open('文件.pdf')
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=150)   # 或 Matrix(3,3)
    pix.save(f'page{i+1}.png')
    print(f'page{i+1}: {pix.width}x{pix.height}')  # 检查高度！
"
```

**CMYK/GRAY 颜色空间报错时**：`pix = fitz.Pixmap(fitz.csRGB, pix)` 先转 RGB 再 save。

### 第 3 步：超长页切片（关键新坑 — 2026-08-15 实测）

课程课件 PDF 页面常是**超长图**（实测 540×9156）。vision_analyze 和 tesseract 都吃不下整页，必须切成 ~1500px 竖条：

```python
from PIL import Image
for pn in [1, 2]:
    img = Image.open(f'page{pn}.png')
    w, h = img.size
    n = (h + 1499) // 1500
    for i in range(n):
        top, bottom = i * 1500, min((i + 1) * 1500, h)
        img.crop((0, top, w, bottom)).save(f'page{pn}_seg{i + 1}.png')
    print(f'page{pn}: {n} segments')
```

规则：**任何高度 >2000px 的渲染页先切片再识别**，段高 1500px 是安全值（内容不截断、单段尺寸适中）。

**⚠️ Apple Vision（ocr_apple.swift）同样必须切片（2026-08-15 实测）**：对 ~18000px 超长图整图直跑 swift OCR 会**静默截断**——17879px 图只返回 6 行乱码，不报错。Vision 专用切片参数：段高 **2400px + 200px 重叠**（防切词断行），每段约 1.5s，中文识别质量明显优于 tesseract。重叠区去重：每段开头与上一段结尾做前缀/后缀精确匹配（k 从 6 递减取最长命中），命中则跳过。

**优先直接提取嵌入图（纠正旧坑）**：课件截图类 PDF 每页常是**整页截图嵌入**（实测原生 1080×~18000），此时 `get_images()` 直取 = **无损原生分辨率**，比 dpi=150 渲染（只有 540px 宽）更清晰，OCR 质量更高。判断方法：嵌入图宽 ≥1000 且占满页面即正文（跳过 303×44 之类小 logo/水印）；提取方式 `fitz.Pixmap(doc, xref)` → save。设计型/排版型 PDF 才需要走渲染。

现成脚本：`scripts/slice_tall_pages.py`（本技能目录内，可复用）：
```bash
python3 scripts/slice_tall_pages.py page1.png page2.png   # 自动切片 >2000px 的页
```
批量全链路（提取嵌入图→切片→Apple Vision OCR→去重→按页存 raw）：`scripts/batch_apple_vision_ocr.py`

### 第 4 步：识别（按优先级，从上到下）

1. **vision_analyze（千问 VL）** — 逐段调用，question 必须写"完整逐条抄录所有文字，不要遗漏，不要概括"
2. **Apple Vision OCR（swift 直跑）** — 千问挂了用它：
   ```bash
   swift ~/.hermes/scripts/ocr_apple.swift 图片.png   # 中文+英文，比 tesseract 准
   # 或 ocr_pro.swift（双引擎增强版）
   ```
   ⚠️ `ocr_apple.py`（Python 包装）依赖 pyobjc 的 Vision 模块，未装 pyobjc 时 `ModuleNotFoundError`——**直接跑 .swift，别跑 .py**
3. **tesseract 批量 OCR** — 中文语言包已装时（`tesseract --list-langs | grep chi_sim`）：
   ```bash
   for f in page1_seg*.png page2_seg*.png; do
     echo "===== $f ====="
     tesseract "$f" stdout -l chi_sim 2>/dev/null
   done > ocr_raw.txt
   ```
   **实测结论（2026-08-15）**：tesseract 对**渲染后的高清 PDF 页**（干净排版、无压缩噪声）中文识别可用，错字率可接受（如"人脉"→"人肝"、漏字），语义校正后能复原 90%+。它怕的是压缩噪声大的聊天截图，不是渲染页。OCR 完成后通读一遍按语义修正明显错字。

### 第 5 步：拼装结构化 md

输出规范（波总"整理成 md 喂给 AI"场景的标准结构）：

```markdown
# 标题（课程名/章节名）

> 来源：<文件名> ｜ 整理时间：YYYY-MM-DD ｜ 用途：<讨论输入>

## 一、核心内容（保留层级结构）

- 表格 → 完整保留为 md 表格（表头说明 + 数据行）
- 要点 → 分节 + 列表
- 关键概念/定义 → 加粗或引用块

## 速览洞察（可选）

- 提炼 3-5 条跨章节洞察（如"高影响力×低亲密值得经营"）

## 待确认/待讨论问题（可选）

- [ ] 1. ...

---
*来源注明 + OCR 校正说明*
```

## 文件接收注意（Telegram 场景）

- 用户说"压缩包已发送"但 cache 里没有 → **先 verify 再动手**：
  ```bash
  find ~/.hermes/cache ~/Downloads -type f \( -iname "*.zip" -o -iname "*.rar" -o -iname "*.7z" -o -iname "*.tar*" \) -mtime -1 2>/dev/null
  ls -lat ~/.hermes/cache/documents/ | head
  ```
- **Telegram Bot 50MB 硬限制**：>50MB 的压缩包会被拒收，永远到不了。提示波总拆包或逐个发 PDF
- 文件未到就先处理已到的（逐份转 md），别干等；每份完成即汇报进度

## 相关技能（重叠提示）

- `pdf-image-extraction`（user-owned）：同领域三步法（get_text → 渲染 → 千问 VL），但**缺少切片步骤和批量 OCR 降级**——本技能是其超长页/批量场景的完整版
- `ocr-screenshot-extraction`（user-owned）：单张截图 OCR 链路，含千问 VL 配置与 Firecrawl 降级
- 建议 `hermes curator adopt pdf-image-extraction` 后合并本技能精华

## 陷阱

1. **别用 get_images() 提取嵌入图**——设计型 PDF 的嵌入大图常是装饰背景，白费一轮。渲染页面才包含全部文字（**例外：课件整页截图类 PDF——嵌入图即正文且分辨率更高，应直取，见第 3 步**）
2. **vision_analyze 一次一图**——多段/多页逐段调用，别塞多张
3. **渲染图必须检查高度**——超长页不切片直接 OCR 会截断/超时
4. **OCR 结果二次核对数字**（时间/金额/电话），关键数据对照逻辑一致性
5. **tesseract 可用的前提是高清渲染页**——别拿它裸跑压缩截图
