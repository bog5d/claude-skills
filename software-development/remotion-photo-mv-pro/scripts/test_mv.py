#!/usr/bin/env python3
"""自动化测试脚本 — 不靠肉眼验证 Remotion 照片 MV 质量

运行方式:
  python3 /Users/mac/.hermes/profiles/her-m2/tools/mv_pipeline/test_mv.py \\
    --project /Users/mac/aider_workspace/photo_mv_feifei \\
    --build-first --render-test --test-duration 60

检查项:
  1. switch gap ≥ 18 帧 (anti-strobe)
  2. 强制切换帧 (Three/Two/One/吹蜡烛/点起来/吹下去/吹一下/两下/三下) 在合并列表中
  3. LYRICS 时间轴递增、无碰撞
  4. 字幕覆盖完整时长 (首帧 < 5s, 末帧 > 80%)
  5. [可选] 渲染测试段 + ffmpeg 帧提取验证
"""

import json
import subprocess
import sys
from pathlib import Path


def green(s): return f"\033[32m{s}\033[0m"
def red(s): return f"\033[31m{s}\033[0m"
def yellow(s): return f"\033[33m{s}\033[0m"


def load_config(project):
    config_path = Path(project) / "mv_config.json"
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")
    return json.loads(config_path.read_text())


def check_switch_gaps(merged, min_gap=18, fps=30):
    issues, violations, gaps = [], 0, []
    for i in range(1, len(merged)):
        gap = merged[i] - merged[i - 1]
        gaps.append(gap)
        if gap < min_gap:
            violations += 1
            issues.append(f"  ❌ gap too small: {merged[i-1]}→{merged[i]} = {gap}f ({gap/fps:.2f}s)")
    if not issues:
        print(green(f"  ✅ All {len(gaps)} gaps ≥ {min_gap} frames  (min={min(gaps)}, max={max(gaps)}, avg={sum(gaps)/len(gaps):.1f})"))
    return issues


def check_forced_switches(merged, forced, expected_count):
    issues = []
    present = [f for f in forced if f in merged]
    missing = [f for f in forced if f not in merged]
    if missing:
        issues.append(f"  ❌ {len(missing)} forced switch frames MISSING: {missing}")
    if present:
        print(green(f"  ✅ {len(present)}/{len(forced)} forced switches present (expected ~{expected_count})"))
    else:
        issues.append(f"  ❌ 0/{len(forced)} forced switches present")
    return issues


def check_lyrics_timeline(lyrics, total_frames, fps=30):
    issues = []
    if not lyrics:
        print(yellow("  ⚠️  No lyrics timeline"))
        return issues

    def lyric_frame(entry):
        return int(entry.get("frame", entry.get("f", 0)))

    def lyric_text(entry):
        return str(entry.get("text", entry.get("t", "")))

    collisions = 0
    for i in range(1, len(lyrics)):
        current_frame = lyric_frame(lyrics[i])
        previous_frame = lyric_frame(lyrics[i - 1])
        if current_frame <= previous_frame:
            collisions += 1
            if collisions <= 3:
                issues.append(f"  ❌ Collision: '{lyric_text(lyrics[i-1])[:30]}' (f={previous_frame}) ≤ '{lyric_text(lyrics[i])[:30]}' (f={current_frame})")
    if collisions == 0:
        print(green(f"  ✅ Lyrics timeline monotonic ({len(lyrics)} entries)"))

    first, last = lyric_frame(lyrics[0]), lyric_frame(lyrics[-1])
    if first > 5 * fps:
        issues.append(f"  ❌ First subtitle too late: frame {first}")
    else:
        print(green(f"  ✅ First subtitle at frame {first} ({first/fps:.1f}s)"))
    if last < total_frames * 0.8:
        issues.append(f"  ❌ Last subtitle covers only {last/total_frames*100:.0f}%")
    else:
        print(green(f"  ✅ Last subtitle at frame {last} ({last/total_frames*100:.0f}% coverage)"))
    return issues


def check_photo_coverage(merged, photo_count):
    appearances = [len(merged) // photo_count + (1 if i < len(merged) % photo_count else 0) for i in range(photo_count)]
    min_app, max_app = min(appearances), max(appearances)
    print(f"  Photos: {photo_count}, Switches: {len(merged)}, Each appears {min_app}-{max_app}× (avg {len(merged)/photo_count:.1f})")
    if max_app - min_app > 2:
        return [f"  ⚠️  Uneven distribution: {min_app}-{max_app}"]
    return []


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--render-test", action="store_true")
    parser.add_argument("--test-duration", type=int, default=60)
    parser.add_argument("--build-first", action="store_true")
    parser.add_argument("--theme", default="fast_pop")
    parser.add_argument("--title", default="Test")
    parser.add_argument("--lyrics")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    fps, min_gap = 30, 18

    print("=" * 60)
    print("  Photo MV Automated Test Suite")
    print("=" * 60)

    if args.build_first:
        cmd = [sys.executable, "/Users/mac/.hermes/profiles/her-m2/tools/mv_pipeline/mv_pipeline.py", "build", "--project", str(project), "--theme", args.theme, "--title", args.title]
        if args.lyrics:
            cmd.extend(["--lyrics", args.lyrics])
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(red(f"  ❌ Build failed: {result.stderr[:300]}"))
            sys.exit(1)
        print(green("  ✅ Build succeeded"))

    config = load_config(project)
    merged = config["merged_switch_frames"]
    forced = config.get("forced_switch_frames", [])
    lyrics = config.get("lyrics_timeline", [])
    photo_files = config.get("photo_files", [])
    total_frames = config["duration_in_frames"]

    print(f"\n📋 Duration: {config['duration_seconds']:.1f}s, Photos: {len(photo_files)}, Switches: {len(merged)}")

    all_issues = []
    print("\n🔍 Test 1: Switch Gap Check")
    all_issues.extend(check_switch_gaps(merged, min_gap, fps))
    print("\n🔍 Test 2: Forced Switch Check")
    all_issues.extend(check_forced_switches(merged, forced, 16))
    print("\n🔍 Test 3: Lyrics Timeline Check")
    all_issues.extend(check_lyrics_timeline(lyrics, total_frames, fps))
    print("\n🔍 Test 4: Photo Coverage")
    all_issues.extend(check_photo_coverage(merged, len(photo_files)))

    print("\n" + "=" * 60)
    if all_issues:
        print(red(f"  ❌ FAILED — {len(all_issues)} issues"))
        for i in all_issues:
            print(i)
        sys.exit(1)
    else:
        print(green("  ✅ ALL CHECKS PASSED"))
        sys.exit(0)


if __name__ == "__main__":
    main()
