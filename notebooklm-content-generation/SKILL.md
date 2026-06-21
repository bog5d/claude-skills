---
name: notebooklm-content-generation
description: Complete pipeline for generating podcast audio, video, and slide-deck from a NotebookLM notebook. Handles auth path fix, language setting, content extraction, parallel generation, and artifact download.
trigger: When the user asks to generate podcast/audio, video, or PPT from a NotebookLM notebook content. Also triggered by "读取笔记本内容生成播客/视频/PPT" or similar requests.
category: productivity
---

# NotebookLM Content Generation Pipeline

## Overview

Full pipeline: NotebookLM notebook → content extraction → parallel artifact generation (audio + video + slide-deck) → download and delivery. All via `notebooklm` CLI.

## Step 0: Auth Path Fix (one-time per profile)

The `notebooklm login` command (browser OAuth) saves `storage_state.json` to `~/.notebooklm/profiles/default/`. But Hermes profiles look under `~/.hermes/profiles/<name>/home/.notebooklm/profiles/default/`. 

**Fix**: copy the file to all active profiles:

```bash
for prof in her-m2 english-tutor default; do
  dir="/Users/mac/.hermes/profiles/$prof/home/.notebooklm/profiles/default"
  mkdir -p "$dir"
  cp ~/.notebooklm/profiles/default/storage_state.json "$dir/"
done
```

Verify with: `notebooklm list` (should show notebooks, not "Not logged in")

## Step 1: Select Notebook & Set Language

```bash
# List all notebooks with metadata
notebooklm list --json

# Set active notebook (partial ID works)
notebooklm use <notebook-id>

# Set output language to Chinese (GLOBAL setting!)
notebooklm language set zh_Hans
```

## Step 1.5: Bulk Notebook Audit

To enumerate ALL notebooks and their source counts at once (useful when deciding what to clean up or generate from):

```python
import json, subprocess

result = subprocess.run(['notebooklm', 'list', '--json'], capture_output=True, text=True)
notebooks = json.loads(result.stdout)['notebooks']

for nb in notebooks:
    subprocess.run(['notebooklm', 'use', nb['id']], capture_output=True)
    src = subprocess.run(['notebooklm', 'source', 'list'], capture_output=True, text=True)
    # Parse the table output to count sources
    count = sum(1 for line in src.stdout.split('\n') if '│' in line and 'ID' not in line)
    print(f"{nb['title']}: {count} sources | created {nb['created_at'][:10]}")
```

This works because `notebooklm source list` outputs a pipe-table; each data row contains `│`.

⚠️ Language is a GLOBAL account setting — it affects ALL notebooks.

## Step 2: Extract & Understand Content

```bash
# List sources in current notebook
notebooklm source list

# Get notebook AI summary
notebooklm summary

# Get full source text (for reference)
notebooklm source fulltext <source-id> -o /tmp/source_content.md

# Read saved content
cat /tmp/source_content.md
```

## Step 3: Parallel Artifact Generation

Start all three generations simultaneously in background:

```bash
# Audio (podcast) — dual-host conversational style, 15-20 min
notebooklm generate audio "<detailed Chinese prompt>" &
PID_AUDIO=$!

# Video — technical explainer, 8-12 min, with subtitles
notebooklm generate video "<detailed Chinese prompt>" &
PID_VIDEO=$!

# Slide-deck — 12-15 slides, dark theme
notebooklm generate slide-deck "<detailed Chinese prompt>" &
PID_SLIDES=$!

wait $PID_AUDIO $PID_VIDEO $PID_SLIDES
```

Each `generate` returns an artifact ID (e.g., `a4667fab-...`). Save these IDs.

**Prompt tips for Chinese content from Chinese sources:**
- Audio: "基于笔记本中的全部内容，生成一期深度中文播客节目。播客风格：两个主持人对话形式，一男一女。时长15-20分钟。讨论要点包括：1) ... 2) ..."
- Video: "基于笔记本内容，生成中文深度解读视频。风格：技术解说+动态图文。内容包括：1) 封面标题 2) 核心观点梳理 3) 架构图解..."
- Slide-deck: "生成中文PPT演示文稿。幻灯片结构（共12-15页）：1) 封面 2) 议程 3) ... 视觉风格：深色主题，蓝色+橙色点缀，配架构图和流程图。"

## Step 4: Wait for Completion

```bash
# Wait for each artifact (NotebookLM renders on server, 3-8 minutes)
notebooklm artifact wait <artifact-id> --timeout 600
```

Check status anytime:
```bash
notebooklm artifact list
notebooklm artifact poll <artifact-id>
```

## Step 5: Download & Deliver

```bash
# Download syntax: --artifact flag, output path is positional (NO -o flag!)
cd /tmp
notebooklm download audio --artifact <artifact-id>        # → auto-named from title
notebooklm download video --artifact <artifact-id>        # → auto-named from title
notebooklm download slide-deck --artifact <artifact-id> --format pptx  # PPTX for editing
```

Filenames are auto-derived from artifact titles (Chinese-friendly). Use `cd /tmp` first to avoid cluttering workspace.

**Video >50MB?** Telegram bot limit is 50MB. Compress:
```bash
ffmpeg -i input.mp4 -vcodec libx264 -crf 28 -preset fast -acodec aac -b:a 64k output.mp4 -y
```

**Delivery**: PPTX/PDF are NOT in Telegram MEDIA whitelist. Use curl Bot API (see `telegram-file-delivery` skill):
```bash
TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d ' ')
# PPTX → sendDocument | Audio → sendAudio | Video → sendVideo
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendDocument" \
  -F chat_id=<CHAT_ID> -F document=@<FILE> -F caption="..."
```

## Troubleshooting: Expired Auth

When `notebooklm list --json` returns `"Authentication expired or invalid"`:

1. **Check if storage_state.json exists**: `ls -la ~/.notebooklm/profiles/default/storage_state.json`
2. **If it exists but auth is expired** → the tokens inside are stale. `notebooklm login` must be re-run.
3. **`notebooklm login` requires interactive OAuth**: it opens a Chromium browser window and waits for you to press ENTER after logging in. This means:
   - It CANNOT run in background mode (`background=true`) — needs PTY + user interaction
   - It CANNOT be fully automated — the Google OAuth page requires manual credential entry
   - If run non-interactively, it hits `EOFError: EOF when reading a line` and aborts
4. **Workaround**: ask the user to run `notebooklm login` themselves in a terminal, then resume the pipeline. Or use the browser tool to manually complete Google Login → NotebookLM homepage → then `notebooklm login` in PTY mode and press ENTER.
5. **Copy to Hermes profiles after re-auth**: once login succeeds, copy `storage_state.json` to all active profiles (see Step 0).

## Pitfalls

1. **Auth path mismatch + token expiration**: Two failure modes exist — (a) file missing/wrong path (Step 0 fix), (b) file present but tokens expired (needs full re-login, see Troubleshooting above). Running `notebooklm login` requires interactive OAuth; cannot be background-automated.

2. **Language is GLOBAL**: `notebooklm language set zh_Hans` affects ALL notebooks, not just the current one. Warn user if they have non-Chinese notebooks.

3. **Source ID is truncated**: `notebooklm source list` shows truncated IDs (e.g., `3237f3ce-4aff-4`). Use the truncated form in commands — CLI matches by prefix.

4. **Fulltext truncation**: `notebooklm source fulltext` without `-o` truncates long content. Always use `-o <file>` for complete content.

5. **Generation is async**: `notebooklm generate` returns immediately with an artifact ID. The actual rendering happens on Google's servers. Must `artifact wait` before downloading.

6. **Video generation may fail for complex prompts**: NotebookLM video generation is beta. If it fails, fall back to audio + slide-deck only, and generate video manually from slides.

7. **Gateway tools already available**: NotebookLM tools are in `_HERMES_CORE_TOOLS` — all gateways (Telegram, Discord, CLI) have them. No code changes needed beyond auth file sync.

8. **CLI `source add` does NOT upload binary files**: The CLI only handles text content, URLs, and YouTube links. For binary files (xlsx, docx, pptx, PDF), you must either use the NotebookLM web UI drag-and-drop, OR convert the content to a text format (markdown, CSV) and upload that instead.

9. **`.xls` is NOT supported — only `.xlsx`**: NotebookLM's full supported format list is: `.cfg, .csv, .docx, .ini, .json, .log, .md, .pdf, .pptx, .py, .sh, .toml, .ts, .txt, .xlsx, .xml, .yaml, .yml, .zip`. Old `.xls` format must be converted to `.xlsx` first (use `openpyxl` + `xlrd` or LibreOffice headless).

10. **Scanned PDFs need OCR before text upload**: If a source is an image-only PDF (0 text characters), the CLI cannot extract meaningful text. Workflow: extract image from PDF with `fitz` (PyMuPDF) → OCR with `tesseract -l chi_sim` → create structured `.md` file → upload as text source. Tesseract Chinese (`chi_sim`) needs `brew install tesseract tesseract-lang`. See `references/ocr-pdf-workflow.md`.
