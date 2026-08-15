#!/usr/bin/env python3
"""Slice ultra-tall rendered PDF pages into ~1500px vertical segments for OCR/vision.

Usage:
    python3 slice_tall_pages.py page1.png page2.png ...
    python3 slice_tall_pages.py --max-h 2000 --seg-h 1500 page*.png

Reads every image passed as argument, checks its height, and if taller than
--max-h, crops it into overlapping-free segments of --seg-h height, saving as
<name>_seg<N>.png in the same directory. Pages under the threshold are left
untouched (reported as-is).

Rationale (2026-08-15): course-slide PDFs render as ultra-tall pages (e.g.
540x9156). Both vision_analyze and tesseract choke on full-height images;
~1500px segments work reliably and keep content intact.
"""
import sys
from PIL import Image
from pathlib import Path

MAX_H = 2000
SEG_H = 1500


def slice_image(path: str, max_h: int = MAX_H, seg_h: int = SEG_H) -> list[Path]:
    p = Path(path)
    img = Image.open(p)
    w, h = img.size
    if h <= max_h:
        return [p]
    n = (h + seg_h - 1) // seg_h
    out = []
    for i in range(n):
        top = i * seg_h
        bottom = min((i + 1) * seg_h, h)
        crop = img.crop((0, top, w, bottom))
        seg_path = p.with_name(f"{p.stem}_seg{i + 1}{p.suffix}")
        crop.save(seg_path)
        out.append(seg_path)
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    paths = [a for a in args if not a.startswith("--")]
    if not paths:
        print("usage: slice_tall_pages.py [--max-h 2000] [--seg-h 1500] img1.png img2.png ...")
        sys.exit(1)
    max_h = MAX_H
    seg_h = SEG_H
    if "--max-h" in args:
        max_h = int(args[args.index("--max-h") + 1])
    if "--seg-h" in args:
        seg_h = int(args[args.index("--seg-h") + 1])
    for p in paths:
        segs = slice_image(p, max_h, seg_h)
        tag = f"-> {len(segs)} segments" if len(segs) > 1 else "(as-is)"
        print(f"{p}: {tag}")
