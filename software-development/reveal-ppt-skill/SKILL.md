---
name: reveal-ppt-skill
description: 基于 Reveal.js 5.x + Chart.js 4.5 的商务数据PPT生成方案。单HTML文件、深色专业风格、支持柱状图/雷达图/折线图/数据表格/KPI卡片、横向翻页。当用户需要"商务风PPT"、"数据对比图表"、"专业研究报告"风格的HTML幻灯片时使用。
---

# Reveal.js 商务数据PPT Skill

## 什么时候用

- 用户说"做个商务风的PPT"、"数据展示PPT"、"公司报告PPT"
- 需要大量数据图表（柱状图、雷达图、折线图、对比表格）
- 需要深色/专业/稳重风格的展示
- 之前 guizang-ppt-skill 觉得太文科生/杂志风，想要更商务通用

## 模板文件

模板在 `assets/template.html`，包含：

- **Reveal.js 5.2.1** 核心框架（CDN引用）
- **Chart.js 4.5.0**（CDN引用）
- **3个Reveal.js插件**：highlight、zoom、notes
- **深色商务风格**（black主题），一键切换浅色（white主题）
- **8个布局骨架**（注释内，SLIDES_HERE 标记处占位）
- **55+占位符**（`<%- NAME %>` 格式）

## 工作流

### Step 1: 规划页面

先列出所有页面和主题切换节奏（建议暗/亮交替），例如：

| 页 | 主题 | 内容 | 布局 |
|----|------|------|------|
| 1 | dark | 封面 | 大标题+副标题+品牌条纹 |
| 2 | light | KPI大字报 | 4个数据卡片 |
| 3 | dark | 对比表格 | 表头高亮+条纹+百分比条 |
| 4 | light | 柱状图 | Chart.js bar |
| 5 | dark | 雷达图 | Chart.js radar |
| 6 | light | 折线趋势 | Chart.js line |
| 7 | dark | 双列对比 | 优缺点/中美对比 |
| 8 | light | 总结 | CTA+要点 |

暗色主题使用 `data-background-color="#0a0a1a"` 或直接默认黑色
亮色主题使用 `data-background-color="#ffffff"` 或浅灰背景

### Step 2: 拷贝模板

```bash
mkdir -p ~/Desktop/xxx-ppt
cp ~/.hermes/skills/reveal-ppt-skill/assets/template.html ~/Desktop/xxx-ppt/index.html
```

### Step 3: 替换占位符

**搜索 `<%- ` 找到所有占位符**，逐一替换为实际内容。

关键占位符列表：

| 占位符 | 含义 |
|--------|------|
| `PPT_TITLE` | 浏览器标签标题 |
| `SLIDE1_COVER_TITLE` | 封面大标题 |
| `SLIDE1_COVER_SUBTITLE` | 封面子标题 |
| `SLIDE1_DATE` | 封面日期 |
| `SLIDE2_KPI_*` | 4个KPI卡片（数字+标签） |
| `SLIDE3_TABLE_*` | 对比表格数据（表头、行） |
| `SLIDE4_CHART_TITLE` | 柱状图标题 |
| `SLIDE4_CHART_LABELS` | 柱状图X轴标签 |
| `SLIDE4_CHART_DATA1/2` | 柱状图数据集1/2 |
| `SLIDE5_RADAR_*` | 雷达图标题/labels/数据集 |
| `SLIDE6_LINE_*` | 折线图标题/labels/数据集 |
| `SLIDE7_LEFT/RIGHT_*` | 双列对比内容 |
| `SLIDE8_*` | 总结页内容 |

### Step 4: 生成和验证

```bash
open ~/Desktop/xxx-ppt/index.html
```

验证：
- ← → 翻页正常
- 所有Chart.js图表渲染正确
- 深色/浅色切换按钮工作
- ESC总览正常
- 数据内容完整无截断

### Step 5: 迭代

直接通过 `patch` 工具修改 `~/Desktop/xxx-ppt/index.html` 中的内容/样式，不需要重写整个文件。

## 关键原则

1. **写文件，不对话输出** — 模板685行、Chart.js JS块，绝对不能在对话中直接输出
2. **所有数据占位符必须搜索 `<%- ` 全部替换完**，不能留任何未替换的占位符
3. **Chart.js canvas 必须放在 IIFE（`(function(){...})()`）中初始化**，不能用 `DOMContentLoaded` 监听器（Reveal.js 的 slide 切换会重新渲染）
4. **商务风规约**：深色背景为主、冷色调（深蓝/靛青/银灰）、衬线标题只用于封面、其他标题用非衬线加粗、数据表格用渐变表头
5. **替换占位符时注意转义**：模板中的 `%>` 可能被写成 `%\>`（字面反斜杠+%>），替换时需要用字符串 `"%>"` 和 `"%\\>"` 都覆盖，或者直接用 bytes 模式检查
6. **Chart.js JS 代码中不能使用 f-string** — JS 的大括号 `{}` 会被 Python f-string 误解析。用字符串拼接（`str1 + data + str2`）或 `.format()` 或模板字符串
7. **用 write_file 先写 Python 脚本到 /tmp/，再 terminal 执行** — 直接在 terminal heredoc 里写长 Python 脚本会有引号转义问题

## 样式规范（必读）

波总已确认偏好：**浅色商务风格**。所有 PPT 生成必须遵循以下规范：

### 颜色规则
- **底色**：纯白 `#ffffff` 或浅灰 `#f5f6fa`（不要深色背景）
- **文字**：深灰 `#1e2026` 为主要文字色，辅助文字 `#646e82`
- **卡片**：白色卡片 + 浅灰边框 `#dce1eb`
- **表头**：蓝色 `#1976d2` 白字
- **表格行**：浅灰 `#f0f5fa` 交替白底
- **强调色**（少量点缀，不影响阅读）：
  - 蓝色 `#1976d2` — 主要强调
  - 绿色 `#2e7d32` — KPI/KR
  - 橙色 `#ed6c02` — 警示/对比
  - 紫色 `#6a1b9a` — 分类标记
- **禁用**：深色背景 + 深色文字的组合，会造成看不清

### 布局规则
- 所有内容块放在白色圆角卡片内（带浅边框）
- 标题左对齐，24-28pt
- KPI 数字 36pt 加粗使用强调色
- 正文 12-14pt
- 表格 10-11pt

## 与 guizang-ppt-skill 的区别

| 维度 | guizang-ppt-skill | reveal-ppt-skill |
|------|-------------------|------------------|
| 框架 | 自定义CSS+JSWGL | Reveal.js 5.x |
| 风格 | 杂志×电子墨水 | 商务数据 |
| 图表 | 无内置 | Chart.js 4.5 |
| 主题 | 5套（墨水/靛蓝/森林/牛皮/沙丘） | 深色black+白色white双主题 |
| 适用场景 | 个人分享、文化内容、AI产品发布 | 研究报告、数据对比、公司汇报 |
| 字体 | 衬线+非衬线+等宽 | 非衬线加粗为主 |
