---
name: cli-anything-integration
description: "Install and use CLI-Anything (HKUDS) to give Hermes structured CLI access to desktop GUI applications — LibreOffice, GIMP, Blender, and 80+ others. Covers macOS installation quirks, harness discovery, and integration with existing Hermes skills."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [cli, desktop, automation, libreoffice, gimp, blender, devops]
    related_skills: [software-copyright-screenshot-workflow, macos-computer-use, ocr-screenshot-extraction]
    triggers:
      - User mentions CLI-Anything, cli-hub, or HKUDS
      - User needs to automate LibreOffice, GIMP, Blender, or other GUI apps from Hermes
      - User asks "how to give Hermes CLI access to desktop apps"
      - User wants to replace GUI-screenshot-based automation with structured CLI calls
---

# CLI-Anything Integration

CLI-Anything (HKUDS) generates structured CLI wrappers for GUI applications, letting Hermes call them like any other shell tool — no screenshots, no coordinate clicking, no OCR.

**The class of problem it solves:** Hermes can talk to web APIs and run shell commands natively, but desktop GUI apps (LibreOffice, GIMP, Blender) are a blind spot. The old pattern was `macos-computer-use` → screenshot → find coordinates → click → wait → verify. CLI-Anything replaces that entire chain with a single `cli-anything-{app} --json <command>` that returns structured output.

## When to Use

- Any task that currently uses `macos-computer-use` to drive a GUI app
- Document generation workflows (LibreOffice → PDF/DOCX)
- Image processing that doesn't justify a full Python PIL script (GIMP)
- 3D rendering or batch asset processing (Blender)
- Any of the 80+ supported apps listed in `references/harness-catalog.md`

## Quick Start (macOS)

### Prerequisites

CLI-Anything requires Python ≥ 3.12 (f-string backslash syntax). macOS system Python is 3.9 — use homebrew Python 3.13:

```bash
# Install Python 3.13 if not present
brew install python@3.13

# Install CLI-Anything hub (PEP 668 guard requires --break-system-packages)
/opt/homebrew/bin/python3.13 -m pip install --break-system-packages cli-anything-hub

# Verify
/opt/homebrew/bin/cli-hub list
```

### Install a Harness

```bash
# Browse available CLIs (80+ options)
/opt/homebrew/bin/cli-hub list

# Install a specific harness (also needs --break-system-packages)
/opt/homebrew/bin/pip3 install --break-system-packages cli-anything-libreoffice

# Verify
/opt/homebrew/bin/cli-anything-libreoffice --help
```

### Using from Hermes

All harnesses live under `/opt/homebrew/bin/` — call them directly from Hermes' `terminal` tool:

```bash
# Example: LibreOffice document creation
/opt/homebrew/bin/cli-anything-libreoffice --json writer create report.odt
/opt/homebrew/bin/cli-anything-libreoffice --json writer set-text --heading "Q1 Report"
/opt/homebrew/bin/cli-anything-libreoffice --json export pdf report.odt --output report.pdf
```

## Key Harnesses (macOS)

| App | Install Command | Primary Use |
|-----|----------------|-------------|
| LibreOffice | `pip3 install --break-system-packages cli-anything-libreoffice` | Document creation, export to PDF/DOCX |
| GIMP | `pip3 install --break-system-packages cli-anything-gimp` | Image editing, resize, crop, annotate |
| Blender | `pip3 install --break-system-packages cli-anything-blender` | 3D rendering, batch processing |
| Safari | `pip3 install --break-system-packages cli-anything-safari` | Browser automation via safari-mcp |
| QGIS | `pip3 install --break-system-packages cli-anything-qgis` | Geospatial processing |
| Obsidian | Already bundled | Vault automation |

Full catalog: `references/harness-catalog.md`

## Integration with Hermes Skills

### Replacing `macos-computer-use` patterns

**Before** (GUI automation):
```
macos-computer-use → screenshot → find "Export" button → click → wait → verify screenshot
```

**After** (CLI):
```bash
cli-anything-libreoffice --json export pdf input.odt --output output.pdf
```

This is faster, deterministic, and burns zero vision tokens.

### With `software-copyright-screenshot-workflow`

The soft-copyright skill generates PDFs from browser screenshots. With CLI-Anything, you can bypass the screenshot step entirely for document-native content:

```bash
# Instead of: browser → screenshot → OCR → PDF layout
# Do:
cli-anything-libreoffice --json writer create manual.odt
# ... write content programmatically ...
cli-anything-libreoffice --json export pdf manual.odt --output 操作手册.pdf
```

### With `ocr-screenshot-extraction`

For images that still need OCR, use GIMP CLI to preprocess before OCR:

```bash
cli-anything-gimp --json resize input.png --width 1200 --output preprocessed.png
# Then run Tesseract OCR on preprocessed.png
```

## Pitfalls

### Python version mismatch

CLI-Anything uses f-string backslash syntax (`f"{expr\}"`) that requires Python ≥ 3.12. Python 3.11 will fail with `SyntaxError: f-string expression part cannot include a backslash`. Always use homebrew Python 3.13 on macOS.

### PEP 668 "externally-managed-environment"

Homebrew-managed Python refuses `pip install` without `--break-system-packages`. This is intentional — homebrew owns its Python and doesn't want pip competing. Always add the flag:

```bash
/opt/homebrew/bin/python3.13 -m pip install --break-system-packages <package>
```

### Harness installs are per-Python-version

CLI-Anything hub and harnesses must be installed in the same Python environment. If you installed the hub with python3.13, install harnesses with the same python3.13 pip.

### cli-hub path

After installation, `cli-hub` lives at `/opt/homebrew/bin/cli-hub`. It is NOT automatically on Hermes' PATH in some configurations — always use the absolute path in Hermes tool calls.

## Verification

```bash
# Check hub is working
/opt/homebrew/bin/cli-hub list | head -5

# Check a specific harness
/opt/homebrew/bin/cli-anything-libreoffice --help
```

## References

- `references/harness-catalog.md` — Full listing of 80+ available CLIs with categories
