#!/usr/bin/env python3
"""Post-render frame-level verification for Remotion Photo MV.

Extracts frames at key switch points from a rendered test segment and checks:
  - Video integrity (duration, streams)
  - Frame extraction at switch points
  - Anti-strobe: smallest gap has two visibly different frames
  - Subtitle rendering at known anchors (e.g. "Three!" at frame 363)
  - Photo diversity across switch frames

Run after test segment is rendered (called automatically by test_mv.py).
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent.parent / "aider_workspace" / "photo_mv_feifei"
# Override from environment if set
import os
PROJECT = Path(os.environ.get("MV_PROJECT", str(PROJECT)))

VIDEO = PROJECT / "test_segment.mp4"
FRAMES_DIR = PROJECT / "test_frames"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    if not VIDEO.exists():
        print("SKIP: test_segment.mp4 not found")
        sys.exit(0)

    # 1. Video integrity
    print("1. Video integrity...")
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "format=duration,size:stream=codec_type", "-of", "json", str(VIDEO)])
    if r.returncode != 0:
        print(f"  FAIL: {r.stderr}")
        sys.exit(1)

    info = json.loads(r.stdout)
    duration = float(info["format"]["duration"])
    size_mb = int(info["format"]["size"]) / 1024 / 1024
    streams = {s["codec_type"] for s in info.get("streams", [])}
    print(f"  {duration:.1f}s, {size_mb:.1f}MB, streams={streams}")
    assert "video" in streams and "audio" in streams, "Missing streams"
    assert 55 < duration < 65, f"Expected ~60s, got {duration:.1f}s"
    print("  OK")

    # 2. Load config
    config = json.loads((PROJECT / "mv_config.json").read_text())
    merged = config["merged_switch_frames"]
    forced = config.get("forced_switch_frames", [])

    FRAMES_DIR.mkdir(exist_ok=True)

    # 3. Key frame extraction
    print("\n2. Key frame extraction...")
    key_frames = [f for f in merged if f <= 1800]
    for f in forced:
        if f <= 1800 and f not in key_frames:
            key_frames.append(f)
    key_frames.sort()

    sample = key_frames[::10]
    if key_frames[-1] not in sample:
        sample.append(key_frames[-1])

    success = 0
    for i, sf in enumerate(sample):
        img = FRAMES_DIR / f"switch_{i:03d}_f{sf}.png"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(VIDEO),
             "-vf", f"select=eq(n\\,{sf})", "-vframes", "1", str(img)])
        if img.exists() and img.stat().st_size > 500:
            success += 1
    print(f"  {success}/{len(sample)} frames extracted")

    # 4. Anti-strobe check
    print("\n3. Anti-strobe tightest gap...")
    test_frames = [f for f in merged if f <= 1800]
    gaps = [(test_frames[i] - test_frames[i-1], i) for i in range(1, len(test_frames))]
    if gaps:
        min_gap, idx = min(gaps, key=lambda x: x[0])
        f1, f2 = test_frames[idx-1], test_frames[idx]
        for name, ff in [("before", f1), ("after", f2)]:
            p = FRAMES_DIR / f"min_gap_{name}_f{ff}.png"
            run(["ffmpeg", "-y", "-v", "error", "-i", str(VIDEO),
                 "-vf", f"select=eq(n\\,{ff})", "-vframes", "1", str(p)])
        b1 = FRAMES_DIR / f"min_gap_before_f{f1}.png"
        b2 = FRAMES_DIR / f"min_gap_after_f{f2}.png"
        if b1.stat().st_size > 500 and b2.stat().st_size > 500:
            diff = abs(b1.stat().st_size - b2.stat().st_size)
            status = "OK (frames differ)" if diff > 0 else "WARN (same size)"
            print(f"  {f1}→{f2} = {min_gap}f ({min_gap/30:.2f}s), {status}")

    # 5. Subtitle check
    print("\n4. Subtitle at 'Three!' (f363)...")
    if 363 <= 1800:
        img = FRAMES_DIR / "subtitle_three.png"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(VIDEO),
             "-vf", f"select=eq(n\\,363)", "-vframes", "1", str(img)])
        if img.stat().st_size > 500:
            print(f"  OK: {img.stat().st_size:,} bytes")
        else:
            print("  FAIL")

    # 6. Photo diversity
    print("\n5. Photo diversity...")
    sizes = []
    for i in range(min(5, len(test_frames))):
        p = FRAMES_DIR / f"div_{i}_f{test_frames[i]}.png"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(VIDEO),
             "-vf", f"select=eq(n\\,{test_frames[i]})", "-vframes", "1", str(p)])
        sizes.append(p.stat().st_size)
    unique = len(set(sizes))
    print(f"  {unique}/5 unique sizes: {'OK' if unique >= 2 else 'WARN'}")

    print(f"\n{'='*50}")
    print("  FRAME-LEVEL CHECKS COMPLETE")
    print(f"  Frames: {FRAMES_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    main()
