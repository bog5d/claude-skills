# PPTX Bulk Modification by Manual

## When

User provides an existing PPTX and a modification manual (逐页修改指令), requiring mechanical execution of text replacements, slide deletions, slide insertions, and format tweaks.

## Core Approach

Use **python-pptx** directly. Do NOT use ZIP-level manipulation for slide add/delete — it corrupts `[Content_Types].xml` and creates orphaned slide files.

## Slide Deletion

Delete from HIGHEST index to lowest to avoid index shifting:

```python
for idx in [9, 8, 7]:  # delete from highest-first
    slide_id = prs.slides._sldIdLst[idx]
    prs.slides._sldIdLst.remove(slide_id)
```

⚠️ This leaves orphaned slide XML files in the ZIP. To fully clean, also rebuild the ZIP without unreferenced slides.

## Slide Insertion + Reordering

python-pptx always adds new slides to the END. After adding, reorder by moving `_sldIdLst` elements:

```python
new_sld = prs.slides.add_slide(layout)  # goes to end
# Move to position 7:
sld_id_lst = prs.slides._sldIdLst
el = sld_id_lst[-1]
sld_id_lst.remove(el)
sld_id_lst.insert(7, el)
```

## Text Replacement

For existing text, iterate runs in paragraphs:

```python
for shape in slide.shapes:
    if shape.has_text_frame:
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                if old_text in run.text:
                    run.text = run.text.replace(old_text, new_text)
```

For complete replacement:
```python
shape.text_frame.clear()
p = shape.text_frame.paragraphs[0]
p.text = 'New Title'
p.font.size = Pt(14)
p.font.bold = True
```

## Shape Removal

```python
sp_tree = slide.shapes._spTree
for shape in to_remove:
    sp_tree.remove(shape._element)
```

## Image Compression for Telegram

PPTX with many PNGs (>10MB each) needs aggressive compression before Telegram sends:

```python
import zipfile, io
from PIL import Image

MAX_SIZE = 900  # pixels
JPEG_QUALITY = 30  # aggressive

# Read PPTX as ZIP, compress images, update Content_Types + slide rels
```

Key: PNG→JPG conversion MUST update:
1. `[Content_Types].xml` — PartName references
2. `ppt/slides/_rels/slideN.xml.rels` — Target references
3. Content type from `image/png` to `image/jpeg`

Otherwise PPT won't open.

## Known Limitations

- **50MB Telegram limit** is a hard blocker for image-heavy PPTX. Expected compressed size: 77-85MB for 22-slide decks with 99 images.
- Splitting PPTX into parts via deep-copy of XML elements works but each part inherits all images
- python-pptx Slide object has no `remove()` method — must manipulate `_sldIdLst` directly
- Adding textboxes to existing slides is straightforward; repositioning existing images/shapes is fragile
