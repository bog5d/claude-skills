---
name: image-super-resolution
description: "Upscale and restore images with Real-ESRGAN on macOS — 4x AI super resolution with MPS GPU acceleration. For old photos, blurry images, low-res enlargements."
category: creative
---

# Image Super Resolution (Real-ESRGAN)

Use Real-ESRGAN (Tencent ARC Lab) for AI-powered 4x image upscaling on macOS. Targets: old photo restoration, blurry image deblurring, low-res enlargement.

**Principle**: Real-ESRGAN only sharpens and upscales — it does NOT change faces, colors, or lighting. Safe for "don't change the original look" requirements.

## Triggers

- "修复老照片" / "restore old photos"
- "放大 / 超分 / upscale / 4x"
- "让照片更清晰但不要改变原貌"
- User sends blurry/low-res image and asks for enhancement

## Quick Start

```bash
# Install (in venv with PyTorch already)
pip install realesrgan gdown

# Patch basicsr import (REQUIRED — torchvision API changed)
PYTHON_SITE=$(python3 -c "import site; print(site.getsitepackages()[0])")
sed -i '' 's/from torchvision.transforms.functional_tensor import rgb_to_grayscale/from torchvision.transforms.functional import rgb_to_grayscale/' \
  "$PYTHON_SITE/basicsr/data/degradations.py"

# Download model (once)
mkdir -p ~/.hermes/models/realesrgan/
# Script handles auto-download, or manually:
curl -L -o ~/.hermes/models/realesrgan/RealESRGAN_x4plus.pth \
  "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"

# Run (use the script from scripts/)
python3 scripts/realesrgan_4x.py
```

## Workflow

### 1. Conservative pass first (PIL)
Before AI upscaling, do a conservative PIL enhancement (Lanczos 2x + unsharp mask + denoise). This is fast, lossless, and gives the user a baseline. Only then run Real-ESRGAN for the full 4x AI pass.

### 2. AI 4x upscaling
Use the reference script `scripts/realesrgan_4x.py`. Key parameters:

| Parameter | Value | Why |
|-----------|-------|-----|
| `device` | `'mps'` | Apple Silicon GPU — 10x faster than CPU |
| `tile` | `200` | Tile size — prevents MPS OOM on large images |
| `half` | `False` | fp32 for quality (fp16 degrades on MPS) |
| `scale` | `4` | 4x upscale factor |
| `model` | `RealESRGAN_x4plus` | General-purpose (not anime-specific) |

### 3. Output delivery
- Save as PNG first (lossless)
- Convert to JPEG quality=92 for Telegram delivery (PNG at 4x can be 25MB+)
- Use `MEDIA:` directive with files in `~/.hermes/cache/documents/` (whitelisted)

## Pitfalls

### ❌ ncnn-vulkan binary segfaults on ARM Mac
The precompiled `realesrgan-ncnn-vulkan` binary from GitHub releases is x86-only. On Apple Silicon it segfaults (exit code 139, SIGSEGV 11). Both `-g 0` (auto GPU) and `-g -1` (CPU) fail identically.
**Fix**: Use the Python package (`pip install realesrgan`) which uses PyTorch natively on ARM.

### ❌ basicsr import error with modern torchvision
`ModuleNotFoundError: No module named 'torchvision.transforms.functional_tensor'`
Newer torchvision (0.27+) removed `functional_tensor`. basicsr still imports from the old path.
**Fix**: Patch `basicsr/data/degradations.py` line 8:
```diff
-from torchvision.transforms.functional_tensor import rgb_to_grayscale
+from torchvision.transforms.functional import rgb_to_grayscale
```

### ❌ pip install timeout
The `realesrgan` package pulls PyTorch as a dependency (~2GB). Default 120s timeout may not be enough.
**Fix**: Run in background with 300s timeout, or pre-install PyTorch separately.

### ❌ Venv isolation
`pip3` and `python3` may resolve to different environments. Always use explicit venv path:
```bash
~/.hermes/hermes-agent/venv/bin/pip3 install realesrgan
~/.hermes/hermes-agent/venv/bin/python3 script.py
```

### ❌ CPU-only is DOG SLOW
Without MPS, 4x upscaling a 1152×1344 image takes 5+ minutes and may time out.
**Fix**: Always use `device='mps'` on Apple Silicon. Falls back to CPU gracefully if MPS unavailable.

### ❌ MPS OOM without tiling
MPS has limited unified memory. Full-image inference on 4x upscale can exhaust it.
**Fix**: Set `tile=200` in RealESRGANer — processes image in 200px tiles, 42-48 tiles per image at ~1150px input.

## Model Info

| Property | Value |
|----------|-------|
| Model | RealESRGAN_x4plus (RRDBNet) |
| Size | 63.9 MB (.pth) |
| Scale | 4x |
| Architecture | RRDBNet: 23 blocks, 64 features, 32 growth channels |
| Origin | https://github.com/xinntao/Real-ESRGAN |
| Local path | `~/.hermes/models/realesrgan/RealESRGAN_x4plus.pth` |

## Performance (M1/M2/M3 Mac)

| Input | Tiles | Time (MPS) | Output |
|-------|-------|-----------|--------|
| 1152×1344 | 42 | ~27s | 4608×5376 |
| 1120×1472 | 48 | ~28s | 4480×5888 |
| 576×672 | 12 | ~8s | 2304×2688 |

## Comparison: Approaches

| Approach | Speed | Quality | Changes original? | ARM Mac? |
|----------|-------|---------|:---:|:---:|
| PIL Lanczos + Unsharp | Instant | Moderate | ❌ No | ✅ |
| Real-ESRGAN Python (MPS) | ~30s/img | Excellent | ❌ No | ✅ |
| Real-ESRGAN ncnn binary | N/A | N/A | N/A | ❌ Segfault |
| GFPGAN (face enhance) | ~30s | Excellent | ⚠️ Alters faces | ✅ |

**Recommendation**: PIL conservative pass first → Real-ESRGAN 4x as the upgrade. Skip GFPGAN unless user explicitly wants face reconstruction.
