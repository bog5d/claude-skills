#!/usr/bin/env python3
"""
Article → Short Video via HTML + Playwright Screenshots
Pipeline: HTML slides → Playwright screenshots → ffmpeg encode → concat

Key design decisions:
- HTML for CSS gradients, typography, shadows — way beyond PIL's capability
- Edge TTS for free, zero-config narration
- PIL only used for ~animated~ progress bar overlay, not for rendering text
- No forced images — if article images don't fit the scene, skip them

Dependencies: pip install edge-tts playwright pillow
Playwright browsers: python -m playwright install chromium
"""

import os, json, subprocess, asyncio, time
from pathlib import Path
import edge_tts
from playwright.sync_api import sync_playwright

OUT = Path("/tmp/ai-qujing-v3")
OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS = 1080, 1920, 30
VOICE = "zh-CN-YunxiNeural"
PADDING = 2.5  # breathing room after each segment

# ── HTML 幻灯片模板 ──
# CRITICAL: CSS braces must be doubled {{ }} for Python .format()
# Single { } are treated as format placeholders → KeyError
HTML_BASE = """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    width:{W}px; height:{H}px; overflow:hidden;
    background: {bg};
    font-family: "PingFang SC","STHeiti","Heiti SC",sans-serif;
    display:flex; flex-direction:column; align-items:center;
    color:white;
  }}
  .progress {{ position:absolute; top:0; left:0; height:4px; background:#ffa040; }}
  .num {{ position:absolute; top:60px; left:50px; font-size:22px; color:#888; }}
  .big {{ margin-top:{big_top}px; font-size:{big_size}px; font-weight:700;
          text-align:center; line-height:1.3; color:{big_color};
          text-shadow:0 2px 12px rgba(0,0,0,0.6);
          max-width:{W120}px; }}
  .sub {{ margin-top:{sub_margin}px; font-size:{sub_size}px; color:{sub_color};
          text-align:center; opacity:0.85; max-width:{W120}px; }}
  .watermark {{ position:absolute; bottom:60px; left:50px; font-size:22px; color:#555; }}
  .overlay {{ position:absolute; inset:0; background:rgba(0,0,0,0.25); z-index:-1; }}
  {extra_css}
</style></head>
<body>
  <div class="overlay"></div>
  <div class="progress" style="width:0%"></div>
  <div class="num">{num}/06</div>
  <div class="big">{big}</div>
  <div class="sub">{sub}</div>
  <div class="watermark">AI 取经记 02</div>
</body></html>"""

# ── 分镜定义（改这里！） ──
SCENES = [
    {
        "id": "01",
        "text": "花了大半年研究RWA，最后幻灭了。一级市场股权融资，需要的不是区块链，是一把铲除信息摩擦的铁锹。我决定重构自己——做AI驱动的资本架构师，把这个系统命名为仓颉FOS。",
        "bg": "linear-gradient(135deg, #1a0a2e 0%, #16213e 50%, #0f3460 100%)",
        "big": "RWA 幻灭\n仓颉 FOS 诞生",
        "sub": "AI 驱动的资本架构师",
        "big_color": "#ffd700",
        "big_size": 64,
        "sub_size": 36,
        "sub_color": "#ccc",
        "big_top": 500,
        "sub_margin": 80,
        "extra_css": "",
    },
    # ... copy and fill scenes 02-06 ...
]

# ============ TTS ============
print("🎙️ TTS...")
for s in SCENES:
    mp3 = OUT / f"s_{s['id']}.mp3"
    if mp3.exists():
        r = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",str(mp3)],capture_output=True,text=True)
        s["dur"] = float(r.stdout.strip() or 3)
        print(f"  skip {s['id']} ({s['dur']:.1f}s)")
        continue
    comm = edge_tts.Communicate(s["text"], VOICE)
    asyncio.run(comm.save(str(mp3)))
    r = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",str(mp3)],capture_output=True,text=True)
    s["dur"] = float(r.stdout.strip() or 3)
    print(f"  ✅ {s['id']} ({s['dur']:.1f}s)")

# ============ HTML → Screenshots ============
print("\n📸 HTML → Screenshots...")
for s in SCENES:
    dur = s["dur"] + PADDING
    total_f = int(dur * FPS)
    
    # Build HTML
    html = HTML_BASE.format(
        W=W, H=H, W120=W-120,
        bg=s["bg"],
        big_top=s["big_top"],
        big_size=s["big_size"],
        big_color=s["big_color"],
        sub_margin=s["sub_margin"],
        sub_size=s["sub_size"],
        sub_color=s["sub_color"],
        extra_css=s.get("extra_css", ""),
        num=s["id"],
        big=s["big"].replace("\n", "<br>"),
        sub=s["sub"],
    )
    html_path = OUT / f"slide_{s['id']}.html"
    html_path.write_text(html)
    
    # Screenshot with Playwright Python API
    ss = OUT / f"screenshot_{s['id']}.png"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": W, "height": H})
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            page.screenshot(path=str(ss), full_page=False)
            browser.close()
    except Exception as e:
        print(f"  ❌ {s['id']}: {e}")
        continue
    
    if not ss.exists():
        print(f"  ❌ {s['id']} screenshot failed")
        continue
    
    # Load screenshot, render animated progress bar as frames
    from PIL import Image, ImageDraw, ImageFont
    FONT_SM = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 24)
    
    base = Image.open(ss).convert("RGB")
    seg_mp4 = OUT / f"seg_{s['id']}.mp4"
    
    print(f"  {s['id']}: {total_f}f ({dur:.1f}s)...", end=" ", flush=True)
    
    for fn in range(total_f):
        t = fn / max(total_f - 1, 1)
        frame = base.copy()
        draw = ImageDraw.Draw(frame)
        
        # Animated progress bar (overwrite the 0% one from HTML)
        pw = int(W * t)
        draw.rectangle([(0, 0), (pw, 4)], fill=(255, 160, 64))
        
        frame.save(OUT / f"f_{s['id']}_{fn:05d}.png")
    
    # Encode
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", str(OUT / f"f_{s['id']}_%05d.png"),
        "-i", str(OUT / f"s_{s['id']}.mp3"),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", str(seg_mp4)
    ], capture_output=True)
    
    for pf in OUT.glob(f"f_{s['id']}_*.png"):
        pf.unlink()
    print("✅")

# ============ CONCAT ============
print("\n🔗 Concatenating...")
cl = OUT / "concat.txt"
segs = sorted(OUT.glob("seg_*.mp4"))
with open(cl, "w") as f:
    for s in segs:
        f.write(f"file '{s}'\n")

final = OUT / "output-final.mp4"
for cmd in [
    ["ffmpeg","-y","-f","concat","-safe","0","-i",str(cl),"-c","copy",str(final)],
    ["ffmpeg","-y","-f","concat","-safe","0","-i",str(cl),
     "-c:v","libx264","-preset","fast","-crf","23","-c:a","aac","-b:a","128k",str(final)],
]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        break

mb = final.stat().st_size/1024/1024 if final.exists() else 0
print(f"\n{'✅' if final.exists() else '❌'} {final} ({mb:.1f} MB)")
if final.exists():
    print(f"MEDIA:{final}")
