#!/usr/bin/env python3
"""批量 OCR 全链路：PDF 嵌入图直取 → 2400px 切片(200px 重叠) → Apple Vision OCR → 重叠去重 → 按页存 raw。

2026-08-15 实测：课件截图类 PDF 每页 = 一整张嵌入长图（原生 1080×~18000），
直取嵌入图 = 无损原生分辨率（优于 dpi=150 渲染的 540px 宽）。
Apple Vision 对 ~18000px 整图会静默截断，必须先切片。

依赖：hermes venv python（fitz/PIL）+ /Users/mac/.hermes/scripts/ocr_apple.swift
用法：python3 batch_apple_vision_ocr.py <PDF目录> [输出目录]
输出：<输出目录>/<slug>/page<N>.raw.txt  + manifest.json
"""
import fitz, os, glob, sys, json, subprocess
from PIL import Image

OCR_SCRIPT = "/Users/mac/.hermes/scripts/ocr_apple.swift"
CHUNK_H = 2400   # Vision 专用段高
OVERLAP = 200    # 防切词断行
MIN_IMG_W = 1000 # 过滤小 logo/水印（如 303×44）

def extract_main_images(pdf, slug, out):
    """每页主图（宽>=1000）直取为 PNG，返回 [(page_label, png_path)]"""
    doc = fitz.open(pdf)
    out_paths = []
    for pi, page in enumerate(doc):
        for img in page.get_images(full=True):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.width >= MIN_IMG_W:
                d = os.path.join(out, slug)
                os.makedirs(d, exist_ok=True)
                p = os.path.join(d, f"page{pi+1}.png")
                pix.save(p)
                out_paths.append((f"page{pi+1}", p))
    doc.close()
    return out_paths

def slice_image(src):
    img = Image.open(src)
    w, h = img.size
    outdir = src.replace(".png", "_chunks")
    os.makedirs(outdir, exist_ok=True)
    chunks, y, i = [], 0, 0
    while y < h:
        top = max(0, y - OVERLAP) if i > 0 else 0
        bottom = min(h, top + CHUNK_H)
        img.crop((0, top, w, bottom)).save(os.path.join(outdir, f"c{i:03d}.png"))
        chunks.append(os.path.join(outdir, f"c{i:03d}.png"))
        i += 1
        y = bottom
        if bottom >= h:
            break
    return chunks

def ocr_image(path):
    r = subprocess.run(["swift", OCR_SCRIPT, path], capture_output=True, text=True, timeout=120)
    return [l.strip() for l in r.stdout.splitlines() if l.strip()] if r.returncode == 0 else []

def ocr_with_dedup(chunks):
    """逐块 OCR，重叠区去重：段首与上段尾做后缀/前缀精确匹配（k 从 6 递减）。"""
    lines = []
    for ch in chunks:
        ls = ocr_image(ch)
        if lines and ls:
            for k in range(min(len(ls), len(lines), 6), 0, -1):
                if ls[:k] == lines[-k:]:
                    ls = ls[k:]
                    break
        lines.extend(ls)
    return lines

def main():
    src_dir, out = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "/tmp/renmai_ocr")
    os.makedirs(out, exist_ok=True)
    manifest = []
    for f in sorted(glob.glob(os.path.join(src_dir, "*.pdf"))):
        slug = f"p{len(manifest)+1:02d}_" + os.path.basename(f).replace(".pdf", "")
        pages = extract_main_images(f, slug, out)
        for label, png in pages:
            lines = ocr_with_dedup(slice_image(png))
            raw = os.path.join(out, slug, label + ".raw.txt")
            with open(raw, "w") as fh:
                fh.write("\n".join(lines))
            manifest.append({"slug": slug, "raw": raw, "n_lines": len(lines)})
            print(f"{slug} {label}: {len(lines)} lines", flush=True)
    with open(os.path.join(out, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print("DONE ->", os.path.join(out, "manifest.json"))

if __name__ == "__main__":
    main()
