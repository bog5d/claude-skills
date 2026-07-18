---
name: ppt-master
description: AI 生成可编辑 PPTX。SVG → DrawingML 转换，输出的每个形状/文本框/渐变都是原生 PowerPoint 对象，可点击编辑。适合正式外发、投资人路演等需要 .pptx 的场景。
---

# PPT Master

## 是什么

AI 驱动的 PPT 生成系统。走 SVG → PowerPoint DrawingML 路线，不是 HTML 渲染。输出每一个元素都是原生 PowerPoint 对象，点哪里改哪里。

**路径：** `~/ppt-master`
**Python：** `~/.hermes/hermes-agent/venv/bin/python3`

## 当前 PPT 方案对比

| 方案 | 输出 | 场景 |
|------|------|------|
| guizang-ppt-skill | .html 翻页 | 网页展示/Telegram |
| reveal-ppt-skill | .html 数据PPT | 内部分享/快速出稿 |
| **ppt-master (本 skill)** | **.pptx 可编辑** | **正式外发/投资人** |

## 核心工作流

```
源材料(PDF/DOCX/URL/MD) → 创建项目 → 策略师确认设计 → 生成SVG → 质量检查 → svg_to_pptx → .pptx
```

完整流程见 `~/ppt-master/skills/ppt-master/SKILL.md`（权威工作流文档）。

## 修改现有PPTX（不重新生成）

当已有完整 PPTX、只需定向修改部分页面时，走这条路径而非从零生成。

### 为什么不用 SVG → DrawingML 路线

从零生成走的是 `手写 SVG → finalize_svg.py → svg_to_pptx.py`。如果已有成品 PPTX，这条路线意味着要把原 PPTX 的所有设计（母版、品牌色、图片、版式）全部手工翻译成 SVG — 工作量巨大且必然丢失细节。

**正确做法：python-pptx 直接读 → 改 → 存，保留 95%+ 原有元素不变。**

### 核心工具

| 工具 | 路径 | 用途 |
|------|------|------|
| python-pptx | venv 已装 (pptx 1.0.2) | 读/改/写 .pptx，保留母版和现有元素 |
| pptx_to_svg.py | `~/ppt-master/skills/ppt-master/scripts/pptx_to_svg.py` | 逐页渲染为 SVG，用于视觉检查 |
| cairosvg | venv 已装 (2.9.0) | SVG → PNG 转换，生成逐页预览 |
| finalize_svg.py | 不需要 | 这是从零生成路线用的，改现有 PPTX 不用 |

### 工作流：修改现有 PPTX

```
1. 渲染全景 → 逐页 SVG → cairosvg 转 PNG → 波总确认修改范围
2. 对每页目标：
   a. python-pptx 读取 slide → 定位要改的元素
   b. 直接修改（文本、位置、颜色、删除/新增形状）
   c. prs.save() 保存 → pptx_to_svg.py 重渲染该页 → 对比检查
3. 交付：修改后 .pptx + 逐页 PNG 预览 + 修改日志
```

### 命令速查

```bash
PY=/Users/mac/.hermes/hermes-agent/venv/bin/python3

# Step 1: 渲染全景（pptx → 逐页 SVG）
$PY ~/ppt-master/skills/ppt-master/scripts/pptx_to_svg.py <input.pptx> -o svg_output/

# Step 2: SVG → PNG 预览（可选，用于 Telegram 查看）
for f in svg_output/*.svg; do
  $PY -c "import cairosvg; cairosvg.svg2png(url='$f', write_to='${f%.svg}.png')"
done

# Step 3: 逐页修改（示例：替换第3页的文本）
$PY -c "
from pptx import Presentation
prs = Presentation('input.pptx')
slide = prs.slides[2]  # 第3页（0-indexed）
for shape in slide.shapes:
    if shape.has_text_frame and '旧文字' in shape.text:
        shape.text = shape.text.replace('旧文字', '新文字')
prs.save('output.pptx')
"

# Step 4: 重渲染修改后的页面验证
$PY ~/ppt-master/skills/ppt-master/scripts/pptx_to_svg.py output.pptx -o svg_verify/
```

### 修改日志格式

每项修改记录：
```
页号 | 元素类型 | 修改前 | 修改后 | 验证截图
```

### ⚠️ 修改现有 PPTX 的注意事项

1. **母版和版式完全保留** — python-pptx 的 `prs.save()` 不丢母版，不丢 slide layouts
2. **图片保留原样** — 除非显式替换 shape，否则图片元素不变
3. **字体保留原始指定** — python-pptx 不改字体名称，渲染差异只在预览工具
4. **图表数据可修改** — 如果是原生 PowerPoint 图表（非图片），可改底层数据
5. **删除页用 `prs.slides.delete(prs.slides[i])`** — 不要用 XML 操作
6. **插入页需要先有版式** — 用 `slide_layout = prs.slide_layouts[idx]` 选版式

### 渲染验证：LibreOffice 缺失时的替代方案

本机未安装 LibreOffice。`powerpoint` skill 的 `soffice → PDF → pdftoppm` 路线不可用。

**替代路径已验证可用**：
- `pptx_to_svg.py` — 直接读 OOXML，不依赖 LibreOffice
- `cairosvg.svg2png()` — SVG 转 PNG
- 质量：95% 还原度，颜色/位置准确，细微字体渲染差异不影响版面检查

如需 PDF 最终交付，需先 `brew install --cask libreoffice`。

## 常用命令

```bash
# Python 前缀
PY=~/.hermes/hermes-agent/venv/bin/python3

# 源材料转换
$PY ~/ppt-master/skills/ppt-master/scripts/source_to_md/pdf_to_md.py <PDF>
$PY ~/ppt-master/skills/ppt-master/scripts/source_to_md/doc_to_md.py <DOCX>
$PY ~/ppt-master/skills/ppt-master/scripts/source_to_md/web_to_md.py <URL>

# 项目管理
$PY ~/ppt-master/skills/ppt-master/scripts/project_manager.py init <name> --format ppt169
$PY ~/ppt-master/skills/ppt-master/scripts/project_manager.py import-sources <project> <files> --move

# SVG 质量检查 + 后处理
$PY ~/ppt-master/skills/ppt-master/scripts/svg_quality_checker.py <project>
$PY ~/ppt-master/skills/ppt-master/scripts/finalize_svg.py <project>

# 导出 PPTX
$PY ~/ppt-master/skills/ppt-master/scripts/svg_to_pptx.py <project>
```

## 实战工作流（研究 → PPTX）

已验证的完整路径：

```
1. 搜集资料 → 写 source.md（Markdown，含所有数据/图表/文字）
2. project_manager.py init <name> --format ppt169
3. 直接写 sources/ 目录（跳过 import-sources）
4. 写 spec_lock.md（配色/字体/页数/节奏）
5. 逐页手写 SVG → svg_output/
6. finalize_svg.py <project>（矩形→Path 转换，必须跑）
7. svg_to_pptx.py <project>（导出 .pptx）
8. 验证：from pptx import Presentation; prs = Presentation("xxx.pptx")
```

## ⚠️ 常见踩坑

### 1. 配图与文字重叠（最高频Bug）
**根因**：
- AI生图后忘记在SVG里加 `<image href="../images/xxx.png"/>` → 图在PPT外面
- SVG里两个相邻 `<text>` 元素（如 ⭐⭐⭐ + 标题）坐标估算不准 → 重叠
- 密集卡片网格页强塞配图 → 必然重叠

**铁律**：
- emoji/符号 + 文字**必须放在同一个 `<text>` 元素里**，禁止拆分
- 封面/概念页可以配图，卡片网格/表格页不配图
- 图文的 y 间距至少留 40px（>卡片内部行间距），不能靠 10px 缝隙

### 2. SVG 中 `&` 必须转义为 `&amp;`
svg_to_pptx.py 会因 XML 解析错误（`not well-formed (invalid token)`）失败。中文标题中"总结 & 行动建议"的`&`是高频触发点。
**修复：** `grep -n ' & ' svg_output/*.svg | grep -v '&amp;'` 查找后逐一替换。

### 2b. Python生成SVG时禁止单字母变量名
**踩坑实录**：用Python脚本批量生成SVG时，如果定义了`H()`函数但变量`H=720`也在作用域内，`f'viewBox="0 0 {W} {H}"'`会输出`<function H at 0x...>`而非`720`。
**铁律**：生成SVG的Python代码中，辅助函数用`hdr()`/`tbar()`/`ftr()`多字母命名，禁止`H()`/`T()`/`F()`等单字母。

### 3. Emoji 文字排版陷阱
Emoji（如 ⭐⭐⭐）在 PowerPoint 里的渲染宽度和浏览器不一样。如果拆成两个 `<text>` 元素（一个放 emoji，一个放标题文字），人工估算的坐标必定出错，PowerPoint 中会重叠。
**铁律：** 含 emoji 的行，emoji + 文字必须放在**同一个 `<text>` 元素**内，让 SVG 引擎自己处理间距，禁止人工估算拆分。

### 4. Pillow C 扩展不兼容
`cannot import name '_imaging' from 'PIL'`
**修复：** `pip uninstall -y Pillow && pip install --no-cache-dir Pillow`

### 5. 系统 Python 3.9 无法编译 cairosvg
Meson 需要 3.10+。必须用 venv Python 3.11。
**同步 cron job 时也记得切 Python 路径。**

### 6. finalize_svg 必须先于 svg_to_pptx
否则圆角矩形不会被转换为 Path 元素，PowerPoint 渲染异常。

## AI 生图配置（硅基流动）

已配置 SiliconFlow 作为 IMAGE_BACKEND：
- 配置文件：`~/.ppt-master/.env`
- API Key：已配置（硅基流动 sk-...）
- 默认模型：Qwen/Qwen-Image
- 用法：
```bash
PY=~/.hermes/hermes-agent/venv/bin/python3
# 单张测试
$PY skills/ppt-master/scripts/image_gen.py "prompt" \
    --aspect_ratio 16:9 --image_size 1K -o project/images/
# 批量生产（PPT 工作流内）
$PY skills/ppt-master/scripts/image_gen.py --manifest project/images/image_prompts.json
```

## 配图方案（零 API）

PPT Master 两条不需要 API key 的配图路径：

### 路径一：SVG 矢量绘制（推荐）
- 直接在手写 SVG 里画地图、柱状图、流程图、热力图、关系箭头
- 零网络依赖 · 零版权问题 · 无限缩放 · ppt里逐元素可编辑
- 适合：数据可视化、战区示意图、逻辑框架图、抽象概念
- 示例：`svg_output/demo_slide_with_visuals.svg`（中东热力图）

### 路径二：网页搜图
- `image_search.py` — 零配置源: openverse(CC协议) + wikimedia
- 搜到图后嵌入 SVG → finalize_svg 嵌入 → svg_to_pptx
- 注意：CC协议图片需要标注来源（attribution）
- 适合：实景照片、新闻配图
```bash
PY=~/.hermes/hermes-agent/venv/bin/python3
$PY skills/ppt-master/scripts/image_search.py "关键词" \
    --filename name.jpg --orientation landscape -o project/images/
```

### 配图整合流程（⚠️ 关键：图必须嵌入PPT里）

图片不能单独发送——必须嵌入 SVG 然后通过 finalize → svg_to_pptx 打进 PPTX。

### 完整配图整合三步

```
1. AI生图/搜图 → images/目录（image_gen.py / image_search.py）
2. 手写SVG时用 <image href="../images/filename.png" /> 引用图片
3. finalize_svg.py（嵌入图片到SVG）→ svg_to_pptx.py（导出含图PPTX）
```

### SVG 中引用图片的正确写法
```xml
<image href="../images/cover_huawei.png" x="650" y="100" 
       width="580" height="380" preserveAspectRatio="xMidYMid slice" opacity="0.9"/>
```
- 路径：`../images/filename.png`（从 svg_output/ 到 images/ 的相对路径）
- 必须跑 `finalize_svg.py` 才会真正嵌入图片到 SVG
- 图片较大时文件大小会明显增长（如 63KB→3MB），说明嵌入成功

### 配图策略 — 页面类型 × 配图决策

| 页面类型 | 能否配图 | 怎么配 | 为什么 |
|----------|---------|--------|--------|
| 封面 | ✅ | 右半区 hero 大图，左半文字 | 自然分区，互不干扰 |
| 概念/引言页 | ✅ | 全幅低透明度背景纹理 (opacity 0.04-0.08) | 不覆盖任何文字 |
| 卡片网格（2/3/4列等分） | ❌ | 不要塞图 | 版面已占满，无处可放 |
| 数据对比表 | ❌ | 纯矢量 | 矢量本身就是最好配图 |
| 引用/名言页 | ⚠️ | 小图放在版心之外 | 仅空白区域 |

### ⚠️ 配图避坑清单

1. **SVG 引用图片的正确写法**：`<image href="../images/xxx.png" x="..." y="..." width="..." height="..." preserveAspectRatio="xMidYMid slice"/>`（从 svg_output/ 到 images/ 的相对路径）
2. **卡片网格页面绝对不要塞图** — 四等分卡已占满 x:80-1200 横向空间，任何图都会重叠
3. **图与文字至少留 30px 缝隙** — PowerPoint 渲染时图片边缘会溢出，10px 不够
4. **不要在图片上叠彩色渐变矩形** — `fill="url(#gradient)" opacity="0.12"` 会扭曲图片颜色
5. **验证图片是否嵌入 PPTX**：`from pptx import Presentation; [s.shape_type for s in slide.shapes]` — PICTURE=13 表示图在文件里
6. **文件大小验证**：纯矢量 PPTX ~60KB，嵌入 2 张 AI 图后 ~3MB，说明图确实打进去了

## ⚠️ Hermes Profile 环境注意事项

在 Hermes Agent profile 环境下（`~` 被重定向到 profile home）：
- **必须用绝对路径**：`/Users/mac/ppt-master/` 而非 `~/ppt-master/`
- venv Python：`/Users/mac/.hermes/hermes-agent/venv/bin/python3`
- 批量生成SVG时，避免用 execute_code 写含中文的脚本（编码问题），改用 write_file + terminal 执行

## 已知限制

- 逐页串行生成，10页≈15分钟（手写SVG部分）
- 图表是视觉形状，非 Excel 数据绑定
- 需要 AI 编辑器（Claude Code/Cursor/VS Code Copilot）驱动
- 首次配置需要装依赖（已完成）
- 策略师确认步骤（八项确认）在 Telegram 异步场景可用 `clarify` 工具替代
- 本机已验证工具链状态见 `references/toolchain-verified.md`

## 安装记录

- 安装日期: 2026-05-16
- 路径: ~/ppt-master
- Python: ~/.hermes/hermes-agent/venv/bin/python3 (3.11)
- 关键依赖: python-pptx, cairosvg, svglib, Pillow, PyMuPDF
- 已装 cairo (brew) + pkg-config (brew)
- ⚠️ 已知坑：安装后若报 `cannot import name '_imaging' from 'PIL'`，需 `pip uninstall -y Pillow && pip install --no-cache-dir Pillow` 重装 Pillow C 扩展
- 系统 Python 3.9 无法编译 cairosvg（Meson 需要 3.10+），必须用 venv Python 3.11
