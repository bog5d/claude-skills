#!/usr/bin/env python3
"""Frame-level validation: extract key frames and verify differences"""
import json, subprocess, sys
from pathlib import Path

PROJECT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/Users/mac/aider_workspace/photo_mv_feifei")
VIDEO = PROJECT / "test_segment.mp4"
FRAMES_DIR = PROJECT / "test_frames"

def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)
def G(s): return f"\033[32m{s}\033[0m"

result = run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_type", "-of", "json", str(VIDEO)])
info = json.loads(result.stdout)
streams = {s["codec_type"] for s in info.get("streams", [])}
assert "video" in streams and "audio" in streams
print(G(f"Video: {float(info['format']['duration']):.1f}s OK"))

config = json.loads((PROJECT / "mv_config.json").read_text())
merged = config["merged_switch_frames"]
FRAMES_DIR.mkdir(exist_ok=True)
test_frames = [f for f in merged if f <= 1800]
sample = test_frames[::10]
if test_frames[-1] not in sample: sample.append(test_frames[-1])

ok = sum(1 for i, sf in enumerate(sample) if (
    run(["ffmpeg", "-y", "-v", "error", "-i", str(VIDEO), "-vf", f"select=eq(n\\,{sf})", "-vframes", "1", str(FRAMES_DIR / f"sw_{i:03d}_f{sf}.png")]),
    (FRAMES_DIR / f"sw_{i:03d}_f{sf}.png").stat().st_size > 500)[1])
print(G(f"Frames: {ok}/{len(sample)} OK"))

gaps = [(test_frames[i] - test_frames[i-1], i) for i in range(1, len(test_frames))]
min_gap, min_idx = min(gaps, key=lambda x: x[0])
f1, f2 = test_frames[min_idx-1], test_frames[min_idx]
for name, ff in [("before", f1), ("after", f2)]:
    run(["ffmpeg", "-y", "-v", "error", "-i", str(VIDEO), "-vf", f"select=eq(n\\,{ff})", "-vframes", "1", str(FRAMES_DIR / f"gap_{name}_f{ff}.png")])
b1, b2 = FRAMES_DIR / f"gap_before_f{f1}.png", FRAMES_DIR / f"gap_after_f{f2}.png"
print(G(f"Gap={min_gap}f, sizes={b1.stat().st_size}/{b2.stat().st_size} OK") if abs(b1.stat().st_size - b2.stat().st_size) > 0 else "FAIL: identical frames")

for name, ff in [("Three", 363), ("Two", 436), ("One", 509)]:
    if ff <= 1800:
        run(["ffmpeg", "-y", "-v", "error", "-i", str(VIDEO), "-vf", f"select=eq(n\\,{ff})", "-vframes", "1", str(FRAMES_DIR / f"sub_{name}_f{ff}.png")])
        print(G(f"Sub {name}: OK"))

sizes = []
for i in range(min(5, len(test_frames))):
    run(["ffmpeg", "-y", "-v", "error", "-i", str(VIDEO), "-vf", f"select=eq(n\\,{test_frames[i]})", "-vframes", "1", str(FRAMES_DIR / f"div_{i}_f{test_frames[i]}.png")])
    sizes.append((FRAMES_DIR / f"div_{i}_f{test_frames[i]}.png").stat().st_size)
print(G(f"Diversity: {len(set(sizes))}/5 unique OK"))
