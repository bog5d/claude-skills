from PIL import Image, ImageDraw, ImageFont
import os, sys

"""
WordPress cover image generator.
Creates 1200x630 JPEG covers with three-line titles and a brand bar.
Usage: python3 cover-image-generator.py
Adjust the `titles` dict and `colors` list for your articles.
"""

titles = {
    "post_id": ("主标题", "副标题行二", "副标题行三"),
    # Add more entries as needed
}

colors = ["#1a1a2e", "#16213e", "#0f3460", "#533483", "#e94560", "#2d6a4f"]

os.makedirs("/tmp/wp-covers", exist_ok=True)

for i, (pid, (line1, line2, line3)) in enumerate(titles.items()):
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), colors[i % len(colors)])
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 48)
        font_sub = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
        font_brand = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 28)
    except:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_brand = font_title

    y = 180
    for line, font, color in [
        (line1, font_title, "#ffffff"),
        (line2, font_sub, "#e0e0e0"),
        (line3, font_sub, "#a0a0a0"),
    ]:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) // 2, y), line, fill=color, font=font)
        y += 70

    # Brand bar at bottom
    draw.rectangle([0, h - 50, w, h], fill="#e94560")
    draw.text((30, h - 42), "hellobog.com", fill="#ffffff", font=font_brand)

    path = f"/tmp/wp-covers/{pid}.jpg"
    img.save(path, "JPEG", quality=85)
    print(f"  {pid}.jpg  {line1}")

print(f"\nGenerated {len(titles)} covers in /tmp/wp-covers/")
