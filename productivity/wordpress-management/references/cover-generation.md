# Cover Image Generation with Pillow

Generate 1200×630 featured images for WordPress posts programmatically.

## Standard template

```python
from PIL import Image, ImageDraw, ImageFont
import os

w, h = 1200, 630
img = Image.new("RGB", (w, h), "#1a1a2e")  # dark navy background
draw = ImageDraw.Draw(img)

# macOS Chinese font
font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 48)
font_sub = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 28)

# Three-line layout
lines = [
    ("AI 取经记 01", font_title, "#ffffff"),
    ("给唐僧配上孙悟空", font_sub, "#e0e0e0"),
    ("完成大模型的第一次 Tool Use 跃迁", font_small, "#a0a0a0"),
]

y = 180
for text, font, color in lines:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, y), text, fill=color, font=font)
    y += 70

# Bottom branding bar
draw.rectangle([0, h - 50, w, h], fill="#e94560")
draw.text((30, h - 42), "site.com · 博客名", fill="#ffffff", font=font_small)

img.save("/tmp/cover.jpg", "JPEG", quality=85)
```

## Color palette (one per post for variety)

```python
colors = ["#1a1a2e", "#16213e", "#0f3460", "#533483", "#e94560", "#2d6a4f"]
```

## Bulk generation pattern

```python
titles = {
    "POST_ID_1": ("Line 1", "Line 2", "Line 3"),
    "POST_ID_2": ("Line 1", "Line 2", "Line 3"),
    ...
}

for i, (pid, (l1, l2, l3)) in enumerate(titles.items()):
    # ... generate with colors[i % len(colors)]
    img.save(f"/tmp/wp-covers/{pid}.jpg", "JPEG", quality=85)
```

## Upload and set as featured

```bash
for pid in 2834 2700 2691; do
  MEDIA_ID=$(curl -s -X POST -u "user:pass" -F "file=@/tmp/wp-covers/$pid.jpg" \
    "http://site.com/wp-json/wp/v2/media" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
  curl -s -X POST -u "user:pass" -H "Content-Type: application/json" \
    -d "{\"featured_media\":$MEDIA_ID}" "http://site.com/wp-json/wp/v2/posts/$pid"
done
```

## Notes

- Pillow is available in Hermes venv: `/Users/mac/.hermes/hermes-agent/venv/bin/python3`
- macOS PingFang font handles Chinese well; Linux may need `Noto Sans CJK`
- File size ~40-80KB at quality=85 — fits WP media size limits
- Always use `/tmp/wp-covers/` as staging dir (clean up after upload)
