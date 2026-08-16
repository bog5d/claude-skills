---
name: enterprise-due-diligence
description: Use when 波总要搜索/尽调一家企业。先建框架再派 Cursor CLI，Hermes 总调度验证。
version: 1.0.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [due-diligence, research, enterprise, cursor, framework]
    related_skills: [equity-penetration-due-diligence, tech-project-evaluation, criteria-driven-evaluation, china-a-share-data-collection]
category: research
trigger: 用户要求"搜一下XX公司/机构，出详细报告"；尽调合作方/投资标的/客户背景；用户说"未来搜索企业时可参考的框架"
priority: normal
---

# 企业深度尽调（Enterprise Due Diligence）

## When to Use

- 波总说"搜索/尽调/摸底 XX 公司/机构，给我一份详细报告"（合作方、投资标的、客户、竞争分析）
- 用户要求建立"未来搜索企业时可参考"的尽调框架
- 实战案例（2026-08-16）：中材（南京）矿山研究院尽调——为矿山边坡雷达/5G专网合作摸底对方底牌

## 分工铁律（波总 2026-08-16 明确要求）

- **务必使用 Cursor CLI 执行搜索+报告撰写**：`cursor-agent -p --yolo "$(cat /tmp/prompt.md)"`（background=true + notify_on_complete=true）
- **Hermes 是总调度**：设计框架（内容设计是监工职责）→ 写执行 prompt → 派发 → 进度通报（`🔴 [Cursor 执行中]` / `🔴 [Cursor 完成]`）→ **亲自核验产出**（子代理自报不可信，关键数字必须验证）→ 交付
- 报告产出到 `~/.hermes/cache/documents/`（不入私有仓库，除非用户要求归档）

## 工作流

1. **框架先行**：复用 `templates/enterprise-dd-framework.md`（12 维度）或仓库 `知识库/调研框架/企业深度尽调框架.md`。首个案例完成后框架入库（v0.1 → 后续迭代），未来搜任何企业直接套用。
2. **写 Cursor 执行 prompt**（`/tmp/prompt.md`），必须包含：
   - 背景：为什么尽调（合作语境/决策用途），让对方知道要什么
   - 目标公司 + 优先级链（如：目标公司 → 母公司 → 集团上市公司 → 行业）
   - 搜索方法：本环境无专用 web_search 时用 `curl -s "https://www.bing.com/search?q=..."` 抓搜索引擎 HTML + 官网 curl + 百科 + 财经站点（东方财富/新浪财经/雪球抓 600970 类上市公司财务/高管/市值）
   - 铁律：**禁止编造任何数字/人名/事件**；每条关键数据标注来源 + 获取日期 + 可信度（高/中/低）；多源冲突并列呈现；查不到标"未公开/待核实"并给出获取路径
   - 输出路径 + 结构 + 报告末尾固定收尾（3 条最值得记住的信息 + 3 个待核实问题）
   - 回执要求：路径/字节数/每维度有效信息条数/待核实缺口
3. **派发**：`cd <任意目录> && cursor-agent -p --yolo "$(cat /tmp/prompt.md)"` 后台 + notify_on_complete
4. **验证**：报告生成后抽查关键数字（高管姓名、营收、市值、成立时间）与公开信息比对；确认无幻觉数据
5. **交付**：报告（+ 决策要点 3 条 + 待核实缺口 3 条）；合作类尽调附"对我们决策的意义"

## 企业尽调 12 维度（速查，全文见 templates/enterprise-dd-framework.md）

0. 基础身份（全称/注册/法人/股权穿透/关联公司）→ 1. 业务（商业模式/收入结构/客户/订单）→ 2. 产品（产品线/参数/价格/竞品对比）→ 3. 技术（专利/研发投入/壁垒/产学研）→ 4. 团队（实控人/高管履历/技术班底）→ 5. 市场（TAM/SAM/SOM/格局/驱动）→ 6. 空间（天花板/成长性/扩张路径/风险）→ 7. 估值（融资史/财务/倍数/可比公司）→ 8. 解决痛点（量化客户价值）→ 9. 行业素材（政策/动态/上下游/出海）→ 10. 谈资故事（里程碑/创始人故事/数据金句）→ 11. 信息源与可信度（一手/二手/第三方分层 + 标注）→ 12. 报告规范（表格优先/数字带源/结尾 3+3）

## 信息源分层

- 一手：官网、年报、公告、招股书、官方公众号（可信度高）
- 二手：百科、财经媒体、券商研报、行业协会（中）
- 第三方：企查查/天眼查/信用中国（工商实锤，但常反爬，能拿多少算多少）
- 上市公司优先挖 A 股公告/财报（600970 类：市值、营收、净利、高管名单、股东结构都是公开可查的硬数据）

## 陷阱

- **Cursor 自报不可信**：它说"查到了 X"不代表真查到了。交付前亲自核对 2-3 个关键数字（用 web_search 独立验证）。
- **机构名 ASR/简称错乱**：尽调对象名称可能来自语音转写或群聊简称（"一保研究院"实为"中材（南京）矿山研究院"）。开工前先用"地名+机构名+业务链"三要素确认目标实体，别把错名当目标搜。
- **立项≠订单**：企业内部课题清单/立项项目不等于确定订单，报告里金额口径必须区分（"数亿确定订单" vs "29 个立项课题"完全不同量级）。
- 禁止把推测写成事实：AI 推断（如"XX 疑为集团研发中心"）必须标置信度+验证办法。

## 参考文件

- `templates/enterprise-dd-framework.md` — 12 维度尽调框架全文（复制即用）
- 仓库版：`Cangjie_OBS_Notes/知识库/调研框架/企业深度尽调框架.md`（v0.1 已入库，2026-08-16）
- 相关：`equity-penetration-due-diligence`（股权穿透专项）、`criteria-driven-evaluation`（按标准文档评估排序）
