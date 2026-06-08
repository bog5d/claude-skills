#!/usr/bin/env python3
"""Real-ESRGAN 4x super resolution — MPS GPU + tile mode, macOS optimized.

Usage:
    python3 realesrgan_4x.py                    # process default photos
    python3 realesrgan_4x.py /path/to/img1.jpg /path/to/img2.png  # custom inputs

Output: <stem>_4x.png in same directory as input (lossless PNG).
Delivery: convert to JPEG quality=92 for Telegram (~3MB vs 25MB PNG).
"""
import os, sys, time
import cv2
import requests
from pathlib import Path
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

MODEL_DIR = os.path.expanduser("~/.hermes/models/realesrgan/")
MODEL_PATH = os.path.join(MODEL_DIR, "RealESRGAN_x4plus.pth")
MODEL_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"

os.makedirs(MODEL_DIR, exist_ok=True)

# --- Model download ---
if not os.path.exists(MODEL_PATH):
    print(f"📦 Downloading model ({MODEL_URL})...", flush=True)
    r = requests.get(MODEL_URL, stream=True, timeout=120)
    r.raise_for_status()
    with open(MODEL_PATH, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"   ✅ Saved ({os.path.getsize(MODEL_PATH)/1024/1024:.0f} MB)", flush=True)

# --- Device detection ---
try:
    import torch
    if torch.backends.mps.is_available():
        device = 'mps'
    elif torch.cuda.is_available():
        device = 'cuda'
    else:
        device = 'cpu'
except Exception:
    device = 'cpu'
print(f"🚀 Device: {device}")

# --- Model setup ---
model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
upsampler = RealESRGANer(
    scale=4,
    model_path=MODEL_PATH,
    model=model,
    tile=200,        # tile size for MPS memory
    tile_pad=10,
    pre_pad=0,
    half=False,      # fp32 quality
    device=device,
)

# --- Input paths ---
if len(sys.argv) > 1:
    photos = sys.argv[1:]
else:
    INPUT_DIR = os.path.expanduser("~/.hermes/cache/documents/")
    photos = [
        os.path.join(INPUT_DIR, "photo1_enhanced.jpg"),
        os.path.join(INPUT_DIR, "photo2_enhanced.jpg"),
    ]

# --- Process ---
for img_path in photos:
    if not os.path.exists(img_path):
        print(f"⚠️  Skipping (not found): {img_path}")
        continue

    stem = Path(img_path).stem
    out_dir = os.path.dirname(img_path)
    output_path = os.path.join(out_dir, f"{stem}_4x.png")

    print(f"🖼️  {Path(img_path).name}", flush=True)
    t0 = time.time()

    img = cv2.imread(img_path, cv2.IMREAD_COLOR)
    if img is None:
        print(f"   ❌ Cannot read image", flush=True)
        continue

    h, w = img.shape[:2]
    print(f"   Input: {w}×{h}", flush=True)

    try:
        output, _ = upsampler.enhance(img, outscale=4)
        cv2.imwrite(output_path, output)
        oh, ow = output.shape[:2]
        size_kb = os.path.getsize(output_path) / 1024
        elapsed = time.time() - t0
        print(f"   Output: {ow}×{oh} ({size_kb:.0f} KB) — {elapsed:.0f}s ✅", flush=True)
    except Exception as e:
        print(f"   ❌ Error: {e}", flush=True)
        # Fallback to CPU
        print(f"   Retrying with CPU...", flush=True)
        upsampler.device = torch.device('cpu')
        upsampler.model.to(upsampler.device)
        output, _ = upsampler.enhance(img, outscale=4)
        cv2.imwrite(output_path, output)
        oh, ow = output.shape[:2]
        size_kb = os.path.getsize(output_path) / 1024
        elapsed = time.time() - t0
        print(f"   Output: {ow}×{oh} ({size_kb:.0f} KB) — {elapsed:.0f}s ✅ (CPU)", flush=True)

print("🎉 All done!")
