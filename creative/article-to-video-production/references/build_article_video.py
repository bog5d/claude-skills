#!/usr/bin/env python3
"""
Agent Memory 文章→视频 完整脚本
PIL 逐帧渲染 + Edge TTS 旁白 + ffmpeg 合成

用法：python3 build.py
依赖：pip install edge-tts pillow
"""

import os, subprocess, asyncio, math
from pathlib import Path
import edge_tts
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path("/tmp/article-video")
OUT_DIR.mkdir(parents=True, exist_ok=True)
W, H = 1080, 1920
FPS = 30

FONT_BIG = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 52)
FONT_MID = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
FONT_SUB = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 28)
FONT_NUM = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 22)

def draw_centered(draw, text, y, font, color="white", shadow=True):
    lines = text.split("\n")
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0,0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        ly = y + i * (font.size + 15)
        if shadow:
            draw.text((x+2, ly+2), line, font=font, fill=(0,0,0,100))
        draw.text((x, ly), line, font=font, fill=color)

# SCENES: [{id, text(旁白), bg(颜色), big(大标题), sub(副标题)}]
SCENES = [
    {"id":"01","text":"你的旁白文字...","bg":"#0f0c29","big":"大标题","sub":"副标题"},
    # ... add more scenes
]

TTS_VOICE = "zh-CN-XiaoxiaoNeural"

FRAMES_DIR = OUT_DIR / "frames"
FRAMES_DIR.mkdir(exist_ok=True)

for s in SCENES:
    mp3 = OUT_DIR / f"scene_{s['id']}.mp3"

    # TTS
    if not mp3.exists():
        comm = edge_tts.Communicate(s["text"], TTS_VOICE)
        asyncio.run(comm.save(str(mp3)))
    r = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration",
        "-of","csv=p=0",str(mp3)],capture_output=True,text=True)
    dur = float(r.stdout.strip() or 3) + 2.0  # +2s padding
    total_frames = int(dur * FPS)

    # Render frames
    for fn in range(total_frames):
        t = fn / max(total_frames - 1, 1)
        pulse = 1.0 + 0.05 * math.sin(t * math.pi * 2)
        rgb = tuple(min(255, int(c * pulse)) for c in (int(s['bg'][1:3],16),int(s['bg'][3:5],16),int(s['bg'][5:7],16)))
        img = Image.new("RGB", (W,H), rgb)
        d = ImageDraw.Draw(img)
        d.rectangle([(0,0), (int(W*t), 4)], fill=(100,200,255))
        d.text((50,70), f"{s['id']}/{len(SCENES):02d}", font=FONT_NUM, fill=(100,100,100))
        draw_centered(d, s["big"], int(H*0.28), FONT_BIG, "white")
        draw_centered(d, s["sub"], int(H*0.82), FONT_SUB, (150,150,150), False)
        img.save(FRAMES_DIR / f"f_{s['id']}_{fn:05d}.png")

    # Encode
    seg = OUT_DIR / f"segment_{s['id']}.mp4"
    subprocess.run(["ffmpeg","-y","-framerate",str(FPS),
        "-i",str(FRAMES_DIR/f"f_{s['id']}_%05d.png"),"-i",str(mp3),
        "-c:v","libx264","-preset","fast","-crf","23","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k","-shortest",str(seg)],capture_output=True)

    # Cleanup frames
    for pf in FRAMES_DIR.glob(f"f_{s['id']}_*.png"):
        pf.unlink()
    print(f"✅ {s['id']}")

# Concat
concat = OUT_DIR / "concat.txt"
with open(concat, "w") as f:
    for seg in sorted(OUT_DIR.glob("segment_*.mp4")):
        f.write(f"file '{seg}'\n")

final = OUT_DIR / "final.mp4"
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0",
    "-i",str(concat),"-c","copy",str(final)],capture_output=True)
print(f"✅ {final}")
