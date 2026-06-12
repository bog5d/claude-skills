# OCR Scanned PDF → NotebookLM Source Workflow

When a PDF source is image-only (scanned document, no embedded text), extract and OCR it before uploading.

## Step 1: Check if PDF has text

```python
import fitz
doc = fitz.open('file.pdf')
for page in doc:
    text = page.get_text()
    if text.strip():
        print(f'Page has {len(text)} chars of text')
    else:
        print('Page is image-only — needs OCR')
```

## Step 2: Extract images

```python
import fitz
doc = fitz.open('file.pdf')
page = doc[0]  # first page
for i, img in enumerate(page.get_images()):
    xref = img[0]
    base = doc.extract_image(xref)
    with open(f'/tmp/page_{i}.{base["ext"]}', 'wb') as f:
        f.write(base['image'])
```

## Step 3: OCR with Tesseract (Chinese)

```bash
# Install: brew install tesseract tesseract-lang
# Chinese traineddata should show chi_sim
tesseract --list-langs | grep chi_sim

# OCR (--psm 6 = uniform block of text)
tesseract input.jpg output -l chi_sim --psm 6
cat output.txt
```

## Step 4: Build structured markdown

For business documents (licenses, contracts, reports), create a key-value markdown file rather than dumping raw OCR:

```python
lines = []
lines.append(f'# {document_title}')
lines.append('')
for field, value in extracted_fields:
    lines.append(f'**{field}**：{value}')
    lines.append('')

with open('structured.md', 'w') as f:
    f.write('\n'.join(lines))
```

## Step 5: Upload as text source

```bash
notebooklm use <notebook-id>
notebooklm source add ./structured.md --title "Document Name (OCR)"
```

## Pitfalls

1. **Tesseract Chinese accuracy varies**: Scanned business licenses with stamps, watermarks, or low resolution will produce garbled output. Flag uncertain fields explicitly (e.g. `※OCR模糊，需人工核对`).

2. **Image preprocessing helps**: Converting to grayscale + 2x resize can improve OCR:
   ```python
   from PIL import Image, ImageEnhance, ImageFilter
   img = img.convert('L')
   img = ImageEnhance.Contrast(img).enhance(2.0)
   img = img.filter(ImageFilter.SHARPEN)
   img = img.resize((w*2, h*2), Image.LANCZOS)
   ```

3. **JPEG artifacts from PDF extraction**: `fitz` extracts images in their original embedded format. If the PDF contains heavily compressed JPEGs, re-extracting as PNG may help.

4. **Multi-page documents**: Loop over all pages, OCR each, concatenate results in order.

5. **Alternative: vision_analyze**: If the active model supports vision, use `vision_analyze` to read the image directly. DeepSeek models do NOT support `image_url` — this will fail with `unknown variant image_url, expected text`.
