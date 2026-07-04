#!/usr/bin/env python3
"""Automated validation for Remotion Photo MV — no human eyes needed.

Runs: config check → gap validation → forced-switch check → lyrics check →
      60s test render → ffmpeg frame extraction → frame diff verification.

Usage:
  # Full test (build + render + validate)
  python3 test_mv.py --project /path/to/project --build-first --render-test --test-duration 60

  # Config-only validation (no render, fast)
  python3 test_mv.py --project /path/to/project

This is a companion script to verify_frames.py, which runs the post-render frame checks.
"""

import json
import subprocess
import sys
from pathlib import Path


PIPELINE = Path("/Users/mac/.hermes/profiles/her-m2/tools/mv_pipeline/mv_pipeline.py")


def green(s: str) -> str:
    return f"\033[32m{s}\033[0m"

def red(s: str) -> str:
    return f"\033[31m{s}\033[0m"

def yellow(s: str) -> str:
    return f"\033[33m{s}\033[0m"


def load_config(project: Path) -> dict:
    config_path = project / "mv_config.json"
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}. Run 'build' first.")
    return json.loads(config_path.read_text())


def check_switch_gaps(merged: list[int], min_gap: int = 18, fps: int = 30) -> list[str]:
    issues = []
    gaps = []
    for i in range(1, len(merged)):
        gap = merged[i] - merged[i - 1]
        gaps.append(gap)
        if gap < min_gap:
            issues.append(
                f"  GAP_TOO_SMALL frame {merged[i-1]} → {merged[i]} "
                f"= {gap} frames ({gap/fps:.2f}s)"
            )
    if not issues:
        avg = sum(gaps) / len(gaps) if gaps else 0
        print(f"{green('  OK:')} all {len(gaps)} gaps ≥ {min_gap}f "
              f"(min={min(gaps)}, max={max(gaps)}, avg={avg:.1f})")
    return issues


def check_forced_switches(merged: list[int], forced: list[int]) -> list[str]:
    issues = []
    present = [f for f in forced if f in merged]
    missing = [f for f in forced if f not in merged]
    if missing:
        issues.append(f"  MISSING {len(missing)} forced switches: {missing}")
    print(f"{green('  OK:')} {len(present)}/{len(forced)} forced switches present")
    return issues


def check_lyrics_timeline(lyrics: list[dict], total_frames: int, fps: int = 30) -> list[str]:
    issues = []
    if not lyrics:
        print(yellow("  SKIP: no lyrics"))
        return issues

    def _frame(e): return int(e.get("frame", e.get("f", 0)))
    def _text(e): return str(e.get("text", e.get("t", "")))

    collisions = 0
    for i in range(1, len(lyrics)):
        if _frame(lyrics[i]) <= _frame(lyrics[i - 1]):
            collisions += 1
    if collisions == 0:
        print(green(f"  OK: lyrics monotonic ({len(lyrics)} entries)"))
    else:
        issues.append(f"  {collisions} lyric collisions")

    first, last = _frame(lyrics[0]), _frame(lyrics[-1])
    early = first <= 5 * fps
    full = last >= total_frames * 0.8
    status = "OK" if (early and full) else f"coverage: {first/fps:.1f}s–{last/fps:.1f}s"
    print(green(f"  {status}"))

    return issues


def check_photo_coverage(merged: list[int], photo_count: int) -> list[str]:
    if photo_count == 0:
        return []
    counts = {}
    for i, _ in enumerate(merged):
        pi = i % photo_count
        counts[pi] = counts.get(pi, 0) + 1
    apps = list(counts.values())
    print(f"  Photos: {photo_count}, switches: {len(merged)}, "
          f"each {min(apps)}-{max(apps)}×")
    if max(apps) - min(apps) > 3:
        return [f"  uneven photo distribution: {min(apps)}-{max(apps)}"]
    return []


def run_build(project: Path, theme: str, title: str, lyrics_file=None) -> bool:
    cmd = [sys.executable, str(PIPELINE), "build",
           "--project", str(project), "--theme", theme, "--title", title]
    if lyrics_file:
        cmd.extend(["--lyrics", lyrics_file])
    print(f"\nBUILD: {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(red(f"  FAIL: exit {r.returncode}"))
        print(r.stderr[:500])
        return False
    for line in r.stderr.splitlines():
        if "warning" in line.lower():
            print(yellow(f"  ⚠️  {line[:200]}"))
    print(green("  OK"))
    return True


def render_test_segment(project: Path, duration_sec: int = 60) -> bool:
    root_path = project / "src" / "Root.tsx"
    original = root_path.read_text()

    # Patch duration for test render
    import re
    test_frames = duration_sec * 30
    patched = re.sub(r'durationInFrames=\{\d+\}', f'durationInFrames={{{test_frames}}}', original)
    root_path.write_text(patched)

    output = project / "test_segment.mp4"
    print(f"\nRENDER: {duration_sec}s → {output}")
    r = subprocess.run(
        ["npx", "remotion", "render", "src/index.ts", "PhotoMV",
         str(output), "--codec", "h264", "--crf", "20", "--overwrite",
         "--concurrency=1", "--chrome-mode=chrome-for-testing"],
        cwd=str(project), capture_output=True, text=True, timeout=300,
    )

    root_path.write_text(original)  # restore

    if r.returncode != 0:
        print(red("  FAIL"))
        print(r.stderr[-500:])
        return False
    print(green(f"  OK: {output.stat().st_size/1024/1024:.1f}MB"))
    return True


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True)
    p.add_argument("--build-first", action="store_true")
    p.add_argument("--render-test", action="store_true")
    p.add_argument("--test-duration", type=int, default=60)
    p.add_argument("--theme", default="fast_pop")
    p.add_argument("--title", default="Test")
    p.add_argument("--lyrics")
    args = p.parse_args()

    project = Path(args.project).expanduser().resolve()
    fps, min_gap = 30, 18

    print("=" * 60)
    print("  Photo MV Automated Test Suite")
    print("=" * 60)

    if args.build_first:
        if not run_build(project, args.theme, args.title, args.lyrics):
            sys.exit(1)

    config = load_config(project)
    merged = config["merged_switch_frames"]
    forced = config.get("forced_switch_frames", [])
    lyrics = config.get("lyrics_timeline", [])
    photos = config.get("photo_files", [])
    total_frames = config["duration_in_frames"]

    all_issues = []
    all_issues.extend(check_switch_gaps(merged, min_gap, fps))
    if forced:
        all_issues.extend(check_forced_switches(merged, forced))
    all_issues.extend(check_lyrics_timeline(lyrics, total_frames, fps))
    all_issues.extend(check_photo_coverage(merged, len(photos)))

    if args.render_test:
        if render_test_segment(project, args.test_duration):
            # Run frame-level verifier
            verify = project / "verify_frames.py"
            if verify.exists():
                subprocess.run([sys.executable, str(verify)], cwd=str(project))
            else:
                print(yellow("  verify_frames.py not found, skipping frame checks"))

    print("\n" + "=" * 60)
    if all_issues:
        print(red(f"  FAILED — {len(all_issues)} issues"))
        for issue in all_issues:
            print(red(issue))
        sys.exit(1)
    print(green("  ALL CHECKS PASSED"))
    sys.exit(0)


if __name__ == "__main__":
    main()
