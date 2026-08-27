---
name: startup-bp-evaluation
description: 创业公司 BP 评估：核心价值/痛点/市场空间/估值四问，估值反推与 BP 缺口检查，关注项目存档。
version: 1.0.0
author: Hermes Agent (curator)
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [bp, evaluation, investment, valuation, archive]
    related_skills: [cangjie-obs-agent, tech-project-evaluation]
category: project-analysis
trigger: user sends a startup BP PDF and says 存起来/分析/估值怎么样/这个项目怎么样
---

# 创业公司 BP 评估（四问框架）

## When to Use

- 波总发来创业公司 BP PDF（融资材料），要求"先把这个项目存起来""分析一下它的核心价值/痛点/市场空间/估值"
- 早期项目（天使轮→A 轮）投资判断、FA 递来的项目材料、产业链关注项目

区别于 `tech-project-evaluation`（GitHub 开源项目吸纳评估）与 `corporate-due-diligence`（已运营公司的背景/财务尽调）——本技能管**创业 BP 材料的快速评估 + 关注项目存档**。

## 流程

### Step 1: 提取 BP 文本

- `read_file` 直接读 PDF（自动提取文本；长文档分段读，600+ 行级无压力，分段用 offset/limit 续读）
- 提取不全/图片型再兜底：pdftoppm 渲染 + vision 或 OCR（见 ocr-and-documents）
- 读完全文先记：股权结构、融资史、产能/收入数字、客户名单——这些是估值反推的原料

### Step 2: web 交叉核实（防 BP 自述口径）

- `web_search` 公司名 + 赛道 + 融资（如"湃沃斯 PEKK 融资"→命中动脉网/投资界报道：融资金额/领投方/成立时间）
- 再搜赛道市场数据（"PEKK 市场规模 2025"）——BP 里的市占率/成本对比/增长率全部视为**自述口径**，公开报道+常识交叉验证
- 注意：web_extract 在 DuckDuckGo 后端不可用（报 ddgs search-only），只靠 web_search 摘要即可，必要时换 firecrawl

### Step 3: 四问框架（波总标准问法）

1. **核心价值**：卡脖子/稀缺性/技术代差——用量化对比表（分子量/杂质/成本 vs 竞品三项全优这种）、"国内唯一""填补空白"类的独占性表述、平台型技术可复用的产品线
2. **解决的痛点**：供给端（垄断/禁运/国产无产能）+ 需求端（下游被卡的具体场景）+ 替代品固有缺陷（如 PEEK 加工窗口窄、结晶不可控）
3. **市场空间**：全球+中国两档数字、CAGR、进口依存度变化；**分层标注**——3-5 年真实可获取 TAM vs 长期叙事（"千亿蓝海"标为叙事不标为事实）
4. **估值**：
   - **BP 未披露本轮金额/估值 = 最大缺口**，直接明说并给出索取清单（条款清单/近期销售订单/专利清单）
   - 估值反推：已知轮次金额 ÷ 出让比例 ≈ 投后区间（例：数千万天使轮/社会资本 30% → 投后约 1-1.7 亿）
   - 本轮合理区间：可比锚点（同赛道已上市公司市值/收入）+ 阶段锚点（天使后 pre-A/A 通常投前 2-4 亿，视产能里程碑与订单兑现浮动）

### Step 4: 关注项目存档（轻量路径）

- PDF 二进制**不入 git**：`mkdir -p ~/.hermes/cache/documents/<项目名>/ && cp <原始pdf> <该目录>/`
- OBS 写 `知识库/研究/YYYY/MM/YYYY-MM-DD_<项目>BP分析.md`（frontmatter `type: research_note`，含速览表/四问/风险清单/PDF 路径）——**不需要 raw/clean/拆解卡全管线**，validate 零新增
- `知识库/实体索引/entities.md` 登记 PRJ-XXX（含 PDF 路径、估值反推区间、待索条款）
- 若用户要求挂副官盯进度 → 才在 hermes-adjutant status.json 建任务

### Step 5: 输出格式（波总偏好）

- 结论先行，四节分号：1️⃣核心价值 2️⃣痛点 3️⃣市场空间 4️⃣估值
- 每个数字标注来源属性：（BP 自述 / 公开报道 / AI 推算）
- ⚠️ 明示 BP 缺口（如"未披露本轮金额与估值——谈之前必须索取"）
- 结尾给一句推进问句（"要不要挂副官盯进度？"）+ 风险清单（放量慢于叙事的结构风险如医疗/航空验证 5 年、产能放大工程难题、专利纠纷前车之鉴）

## Pitfalls

- BP 是融资材料不是尽调报告：增长/市占率/成本对比都是自述口径，独立核实只用公开报道；销售数据未披露=保留判断
- 股权结构表里的"X总/社会资本"≠已确认人物/机构——按既有规则建占位标待核，不自动映射
- 估值数字不要编：BP 没写就明说没写，只给反推区间+锚点，标 AI 推算
- 医疗/航空类应用验证周期长（动物/临床/注册证 5 年、行标测试）——"订单确定性"要区分已签 vs 意向 vs 方案已评估

## 参考

- 完整工作例：`references/pekk-paiwosi-worked-example.md`（2026-08-27 湃沃斯 PEKK BP：四问答案要点、估值反推计算、缺口清单、PRJ-033 存档实例）
- 存档仓库协议：skill `cangjie-obs-agent`（OBS 素材处理与 validate 规范）
