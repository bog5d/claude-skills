---
name: editable-pptx-delivery
description: 交付真正可编辑的 .pptx，禁止整页贴图/图片化。适用投资人路演、正式外发等必须逐元素可改的场景，含结构自检门禁。
---

# Editable PPTX Delivery（可编辑 PPTX 交付纪律）

## 触发场景
- 波总要一份「拿出去看」的 .pptx，且后续会反复修改、逐页验收
- 投资人路演 BP、正式外发材料
- 从已有 PPTX / PDF / 素材库「填充图文」的任务（不是从零生成）

## 铁律（波总多次强调，最高优先级）

1. **禁止整页贴图** — 绝对不允许「把页面渲染成 2880×1620 大图 → 整张铺到幻灯片」。
   这会把「可编辑 PPT」偷换成「图片画册」。投资人类场景会直接拆包看 `shape_type`，
   一旦发现某页是整页图片、0 文本框，判定「可编辑能力 0 分」。
2. **验收优先级（定死，不可协商）**：`可编辑性 > 内容逻辑 > 图片真实性 > 视觉完成度`。
   先证明「复杂图文页能可编辑地做出来」，再追求漂亮。
3. **标题/正文 = 真文本框；产品图 = 独立图片对象（PICTURE shape）**。每个元素可单独选中、移动、修改。
4. **素材宁缺毋假** — 缺的图用占位框标注「待补」，绝不从整页截图里裁图冒充独立素材。

## 核心方法

### 已有 PPTX：python-pptx 直接改（保留 95%+ 原有元素）
```python
from pptx import Presentation
prs = Presentation('src.pptx')
slide = prs.slides[i]              # 0-indexed
# 删除整页贴图 / 清空某页
for shape in list(slide.shapes):
    sp = shape._element
    sp.getparent().remove(sp)
# 加真文本框（可编辑文字）
tb = slide.shapes.add_textbox(...)
# 加独立图片对象
slide.shapes.add_picture('img.png', left, top, width=..., height=...)
prs.save('out.pptx')
```

### 从零生成：SVG → DrawingML（走 bundled `ppt-master` skill 的正路）
文字=真文本框，图片=真 PICTURE 对象，逐元素可编辑。本 skill 不重复其管线，只补充纪律层。

### 中文/东亚字体设置（必须，否则 PowerPoint 渲染 fallback）
python-pptx 设置中文字体必须同时写 `a:ea` 元素：
```python
from pptx.oxml.ns import qn
rPr = run._r.get_or_add_rPr()
ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
ea.set('typeface', '微软雅黑')
```

## 交付前必跑：结构自检门禁

任何 .pptx 交付前，跑 `scripts/pptx_structure_check.py <file.pptx>`：
- 逐页统计：真文本框数 / 图片对象数 / Shape 数 / 是否全页图 / 最大图片尺寸
- 检测到「整页图 + 该页无文本框」→ FAIL，拒绝交付
- 退出码 0=通过 / 1=存在整页贴图页

交付物四件套（波总要求）：
1. 修改后 .pptx
2. 渲染 PNG 预览
3. 结构自检结果（文本框数 / 图片数 / Shape数 / 全页图 / 最大图尺寸）
4. 每张图的素材来源清单

## 素材定位技巧

### 视觉模型失效时，用 PDF 文本块坐标定位真实图
辅助视觉 key 失效、无法「看」图时，靠坐标交叉对齐确认图内容（不靠整页渲染裁图）：
```python
import fitz
doc = fitz.open('src.pdf')
page = doc[N]                      # 0-indexed
for b in page.get_text('blocks'):  # 文本块坐标 (x0,y0,x1,y1,txt)
    ...
for img in page.get_images(full=True):
    xref = img[0]
    rects = page.get_image_rects(xref)   # 图片 bbox
    info = doc.extract_image(xref)       # 按 xref 提取独立原图
    # info['ext'] 决定真实后缀（可能是 jpeg，非文件名后缀）
```
把「图 bbox」和「文字标签 bbox」上下对齐 → 确定哪张图对应哪个产品 → `extract_image(xref)` 提独立素材。

## 踩坑
- PDF 提取的图后缀由 `extract_image` 的 `ext` 字段决定（常见 `.jpeg`），别硬按 `.png` 存
- cairosvg 单独渲染某页 SVG 可能断图链（assets 引用断裂）→ 预览 PNG 异常小时，
  以 PPTX 内真实嵌入为准，别误判「图没进去」
- 动手前先确认素材是「纯单一主题版」还是「跨场景版」。若某场景素材在别的包（如 Codex 云端）本地没有，就占位标注，不硬造

## 与 bundled skill 的关系
- `ppt-master`（bundled，不可写）承载 SVG→DrawingML 生成管线细节
- 本 skill 承载「交付纪律 + 自检门禁 + 素材定位」，是波总侧的执行约束层
