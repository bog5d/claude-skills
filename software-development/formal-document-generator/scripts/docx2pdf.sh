#!/bin/bash
# docx2pdf — docx → PDF 转换（LibreOffice headless）
#
# 为什么需要这个 wrapper：
#   LibreOffice bundle 自带 fontconfig 但无 fonts.conf，headless 模式下字体枚举
#   为零 → PDF 中文全部空白/希伯来字体 fallback（macOS 26 + LO 26.8 实测 2026-08-27）。
#   唯一生效的修复：FONTCONFIG_FILE=/opt/homebrew/etc/fonts/fonts.conf
#   （brew fontconfig 配置含全部 macOS 系统字体目录，fc-list 验证过）
#
# 用法：
#   docx2pdf input.docx                # 输出到当前目录
#   docx2pdf input.docx /tmp/out       # 输出到指定目录
#   docx2pdf "文件 名.docx" ~/Downloads
#
# 验证：输出 PDF 用 `python3 -c "import fitz;d=fitz.open(x);print({f[3] for f in d[0].get_fonts()})"`
#   应看到 PingFangSC/STHeiti 等中文字体被嵌入，而非仅 LinuxLibertineG。
set -euo pipefail

FONTCONFIG_FILE=/opt/homebrew/etc/fonts/fonts.conf
export FONTCONFIG_FILE

INPUT="${1:?用法: docx2pdf <input.docx> [outdir]}"
OUTDIR="${2:-.}"

mkdir -p "$OUTDIR"
soffice --headless --convert-to pdf --outdir "$OUTDIR" "$INPUT" 2>&1 | grep -v "Fontconfig"
echo "✅ PDF: $(basename "${INPUT%.docx}").pdf → $OUTDIR"
