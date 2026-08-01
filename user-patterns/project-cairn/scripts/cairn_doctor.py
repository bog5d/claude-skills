#!/usr/bin/env python3
"""Cairn 体检脚本 — 扫描项目 cairn/ 目录的健康状况。

用法:
    python3 cairn_doctor.py [项目路径]
    （省略路径时扫描当前目录）

输出:
    - 目录结构是否完整 (log.md / roadmap.md / topics/ / reference/)
    - topics/ 文档是否含 OKF v0.2 front matter (type/title/status/sources)
    - 指针链接是否失效（相对路径引用的文件不存在）
    - log.md 单条是否超 20 行（朝后看要求轻快）
    - roadmap.md 是否含三大类信息
    - status: draft 的积压主题（待毕业候选）
"""
import sys, os, re, pathlib

def check_cairn(root: pathlib.Path) -> int:
    problems = 0
    cairn = root / "cairn"
    if not cairn.is_dir():
        print(f"✗ {root}: 无 cairn/ 目录（未初始化）")
        return 1

    required = ["log.md", "roadmap.md"]
    for name in required:
        p = cairn / name
        print(f"{'✓' if p.is_file() else '✗'} {name}")
        if not p.is_file():
            problems += 1
    for name in ["topics", "reference"]:
        p = cairn / name
        print(f"{'✓' if p.is_dir() else '✗'} {name}/")
        if not p.is_dir():
            problems += 1

    # log.md 单条长度检查（按空行分段，任一段 >20 行警告）
    logp = cairn / "log.md"
    if logp.is_file():
        text = logp.read_text(encoding="utf-8", errors="replace")
        entries = re.split(r"\n\s*\n", text)
        for i, e in enumerate(entries):
            lines = e.count("\n") + 1
            if lines > 20:
                print(f"⚠ log.md 第{i+1}段 {lines} 行，超过 20 行（建议拆进 topics/）")
                problems += 1

    # roadmap 三大类
    rp = cairn / "roadmap.md"
    if rp.is_file():
        t = rp.read_text(encoding="utf-8", errors="replace")
        for sec in ["里程碑", "当前焦点", "未解决"]:
            if sec not in t:
                print(f"⚠ roadmap.md 缺「{sec}」区块")
                problems += 1

    # topics 检查
    topics = cairn / "topics"
    if topics.is_dir():
        md_files = sorted(topics.glob("*.md"))
        print(f"\ntopics/ 共 {len(md_files)} 个主题文档")
        for f in md_files:
            t = f.read_text(encoding="utf-8", errors="replace")
            front = re.match(r"^---\n(.*?)\n---", t, re.S)
            if not front:
                print(f"  ✗ {f.name}: 缺 YAML front matter")
                problems += 1
                continue
            fm = front.group(1)
            for field in ["type", "title", "status", "sources"]:
                if not re.search(rf"^{field}:", fm, re.M):
                    print(f"  ✗ {f.name}: 缺 OKF 字段 {field}")
                    problems += 1
            if re.search(r"^status:\s*draft", fm, re.M):
                print(f"  ○ {f.name}: draft（待验证/待毕业候选）")
            # 失效指针检查
            for m in re.finditer(r"\[\[([^\]]+)\]\]", t):
                target = m.group(1).split("|")[0]
                if not target.endswith(".md"):
                    target += ".md"
                if not (topics / target).exists() and not (cairn / ".." / target).exists():
                    print(f"  ⚠ {f.name}: 双链失效 → {target}")
                    problems += 1
    return problems

if __name__ == "__main__":
    root = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path.cwd()
    print(f"🔍 Cairn 体检: {root}\n")
    n = check_cairn(root)
    print(f"\n{'✅ 体检通过，cairn 状态健康' if n == 0 else f'⚠ 发现 {n} 个问题，建议修复'}")
    sys.exit(0 if n == 0 else 1)
