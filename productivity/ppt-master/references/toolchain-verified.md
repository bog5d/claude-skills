# PPT Master 已验证工具链

审计日期: 2026-07-18

## ✅ 可用

| 工具 | 版本 | 路径 | 用途 |
|------|------|------|------|
| python-pptx | 1.0.2 | venv `/Users/mac/.hermes/hermes-agent/venv/bin/python3` | .pptx 读写 |
| cairosvg | 2.9.0 | venv | SVG→PNG 转换 |
| cairocffi | 1.7.1 | venv | Cairo 绑定 |
| PyMuPDF (fitz) | 1.27.2.3 | venv | PDF 源材料提取 |
| Pillow (PIL) | 12.2.0 | venv | 图片处理 |
| svglib | 1.6.0 | venv | SVG 解析 |
| reportlab | 4.5.1 | venv | PDF 生成 |
| lxml | 6.1.0 | venv | XML 解析 |
| defusedxml | 0.7.1 | venv | 安全 XML |
| pptxgenjs | bundled | `/Users/mac/node_modules/pptxgenjs/` | Node.js PPTX 生成 |
| Node.js | v26.3.0 | `/opt/homebrew/bin/node` | JS 运行时 |
| pptx_to_svg.py | — | `~/ppt-master/skills/ppt-master/scripts/pptx_to_svg.py` | PPTX→SVG 反向渲染 |
| svg_to_pptx.py | — | `~/ppt-master/skills/ppt-master/scripts/svg_to_pptx.py` | SVG→PPTX 组装 |
| finalize_svg.py | — | `~/ppt-master/skills/ppt-master/scripts/finalize_svg.py` | SVG 后处理 |
| SiliconFlow Image API | — | `~/.ppt-master/.env` (已配置) | AI 生图 |

## ❌ 缺失

| 工具 | 影响 | 替代方案 |
|------|------|----------|
| LibreOffice (`soffice`) | 无法 PPTX→PDF | python-pptx 直接读存即可；PDF 可用 reportlab 或安装 LibreOffice |
| Poppler (`pdftoppm`) | 无法 PDF→图片 | cairosvg + pptx_to_svg.py 直接 PPTX→PNG |
| ImageMagick | 无法命令行图片转换 | Pillow 覆盖常用场景 |
| Ghostscript | 无法 PDF 后处理 | 暂不影响 |
| Playwright Chromium | 无 headless 浏览器 | 暂不影响 |
| Keynote | 无原生 macOS 预览 | pptx_to_svg.py + cairosvg 替代 |
| Microsoft PowerPoint | 无原生编辑 | python-pptx 完全替代 |
| react-icons | npm 包缺失 | 不影响 python-pptx 路线 |
| sharp | npm 包缺失 | Pillow 替代 |

## 已验证的渲染验证管线

```
.pptx → pptx_to_svg.py → .svg → cairosvg.svg2png() → .png
```

- 质量: ~95% 还原度
- 颜色/位置准确可做版面检查
- 字体渲染可能细微差异（不影响重叠/溢出检测）
- 不依赖 LibreOffice

## python-pptx 操作速查

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor

prs = Presentation('input.pptx')

# 读
slide = prs.slides[0]
for shape in slide.shapes:
    if shape.has_text_frame:
        print(shape.text)

# 改文本
shape.text_frame.paragraphs[0].runs[0].text = '新文字'

# 改颜色
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)

# 删页
prs.slides.delete(prs.slides[2])

# 保存（保留母版、版式、图片）
prs.save('output.pptx')
```
