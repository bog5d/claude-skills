# PyMuPDF + python-pptx 可用代码片段

本文件是 `pdf-to-pptx-image-transfer` 的执行参考，含本类任务验证过的代码。

## 1. 提取 PDF 嵌入图片（去重靠 xref + 尺寸命名）

```python
import fitz
doc = fitz.open('in.pdf')
for pno in range(len(doc)):
    page = doc[pno]
    imgs = page.get_images(full=True)
    for idx, img in enumerate(imgs):
        xref = img[0]
        pix = fitz.Pixmap(doc, xref)
        # CMYK / 带 alpha 的图要转 RGB，否则保存的 PNG 色彩异常
        if pix.n - pix.alpha > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        w, h = pix.width, pix.height
        pix.save(f'p{pno+1:02d}_i{idx:02d}_w{w}x{h}.png')
```

`get_images(full=True)` 返回同一 xref 可能在多页重复出现（同一 logo 每页都嵌）。
用 `page.get_image_rects(xref)` 拿到该图在本页的位置和占比，判断是整页背景还是局部内容图：

```python
for img in page.get_images(full=True):
    xref = img[0]
    for r in page.get_image_rects(xref):
        print(f'x={r.x0:.0f} y={r.y0:.0f} w={r.width:.0f} h={r.height:.0f} '
              f'占页宽{r.width/page.rect.width*100:.0f}%')
```

## 2. 整页高清渲染（供整页贴图）

```python
page = doc[pno]
pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0))  # 2880x1620 for 16:9
pix.save(f'hi_page{pno+1:02d}.png')
```

3x 得到 2880×1620（16:9 960×540pt 页面）。2x 只有 1920×1080，投屏/打印偏糊。

## 3. python-pptx 全出血贴图（删 shape 再铺满）

```python
from pptx import Presentation
from pptx.util import Emu

mapping = {1: 1, 2: 2, 3: 3, 4: None}  # PPT页(index 1-based) -> PDF页；None=保留原文字
prs = Presentation('in.pptx')
sw, sh = prs.slide_width, prs.slide_height

for idx, slide in enumerate(prs.slides, 1):
    pdf_page = mapping.get(idx)
    if pdf_page is None:
        print(f'第{idx}页: 保留原文字')
        continue
    # 关键：先删掉该页所有 shape，否则原文字会叠在新图上
    for shape in list(slide.shapes):
        shape._element.getparent().remove(shape._element)
    slide.shapes.add_picture(f'hi_page{pdf_page:02d}.png', 0, 0, width=sw, height=sh)

prs.save('out.pptx')
```

## 4. 验证贴图结果

```python
from pptx import Presentation
prs = Presentation('out.pptx')
for i, s in enumerate(prs.slides, 1):
    pics = sum(1 for sh in s.shapes if sh.shape_type == 13)
    txts = sum(1 for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip())
    print(f'第{i}页: 图片{pics}张, 文本框{txts}个')
# 预期：1:1贴图页 = 图片1/文本框0；保留页 = 图片0/文本框≥1
```

## 5. 页面比例核对

```bash
# PPT 尺寸（EMU -> inch）
python3 -c "from pptx import Presentation; from pptx.util import Emu; \
prs=Presentation('in.pptx'); print(Emu(prs.slide_width).inches, Emu(prs.slide_height).inches)"
# PDF 页尺寸
python3 -c "import fitz; d=fitz.open('in.pdf'); print(d[0].rect)"
```

16:9 的 PPT 是 13.33×7.5 inch；PDF 960×540pt 也是 16:9。比例一致才能全出血铺满，不一致会拉伸。

## 真实案例速记（2026-08 泽天智航 BP）

- PPT `zth_project.pptx`：14 页，0 图，纯文字+装饰形状（「图被剥离」的残缺版）。
- PDF `泽天智航圳港杯专项BP2026.08.20.pdf`：13 页，55 张嵌入图。
- **口径冲突**：PPT 说「30–40 亿 / 11 款批产」，PDF 说「17.1 亿 / 5 类海洋产品」——是两个用途不同的版本，非先后关系。
- 最终混合方案：12 页 1:1 整页贴图；PPT 独有的 P4「四项核心能力」、P7「ZenixOS 三层市场」保留原文字（PDF 无对应页，且唯一相近的订单页口径冲突）。
- 成品 16MB：`泽天智航圳港杯专项BP_图文版.pptx`。
