---
name: recruitment
description: Full recruitment pipeline — resume screening, JD-aligned scoring, candidate evaluation, BOSS直聘 automation, and structured report generation. Covers the entire hiring workflow from posting to ranked shortlist.
---

# 招聘全流程自动化与评估

## 核心铁律

**评分模型必须从 JD 重建，禁止使用通用金融/技术岗模型。** 每次评估必须从用户提供的 JD/RFP/评分规则中提取维度、权重和判定标准。

## 工作流概览

### 1. 简历筛选与评估（核心能力）

#### 1.1 标准驱动的结构化评估
- 从 JD 原文逐条提取硬性条件、核心能力、加分信号、排除信号
- 维度命名必须使用文档原文用词，不用 AI 自己的术语
- 权重分配必须反映文档中的优先级顺序
- 每项维度必须有明确的"什么证据算高分"的定义

#### 1.2 简历解析
- 优先用 PyMuPDF (fitz) 直接提取文本（PDF 从 Word/WPS 导出的都可直接读）
- 扫描件才需要 OCR 回退
- 提取字段：姓名、性别、年龄、联系方式、教育背景、工作/实习经历、项目经历、证书、技能、语言

#### 1.3 打分与排名
- 每份简历逐人 JD 对齐评分，每条分数必须附"简历原文依据"
- 动态追加：每个新简历追加进排名表，不重新打分已有候选人
- 推荐度标识：🔥 强推 (≥8.0) / ✅ 推荐 (≥7.0) / 🟡 备选 (≥5.0) / ⚠️ 短板 (≥4.0) / ❌ 不推荐 (<4.0)

#### 1.4 报告生成
- 报告必须包含简历原文引用（标注「原文引用」标签）
- 输出 Word + PDF 双份
- 结构：封面 → 评估模型说明 → 核心结论 → 逐人详析 → 综合排名 → 面试建议
- 中文字体：STHeiti/PingFang SC，weasyprint CSS 必须显式中文字体声明

### 2. BOSS直聘自动化

#### 2.1 工具链
- 推荐：`boss-zhipin-automation` (wensia/boss-zhipin-automation) — FastAPI + React + Playwright
- 安装：`~/.hermes/tools/boss-automation/install.sh`
- 启动：`./start.sh` → localhost:27421

#### 2.2 反爬应对
- ❌ Playwright headless → 白屏
- ❌ AppleScript `open location` → 开新标签丢登录态
- ❌ Chrome CDP 远程调试 → 需 Mac 活跃桌面会话
- ✅ 唯一可行路径：非 headless Chrome + 手机扫码 + REST API 操控

#### 2.3 公网隧道
- 优先：localhost.run SSH 隧道（无注册）
- 备选：ngrok（免费版有警告插页，体验差）
- localhost.run URL 提取：`grep -o 'https://[a-z0-9]*\.lhr\.life' /tmp/boss_tunnel.txt | head -1`

#### 2.4 简历打分引擎
- 脚本：`~/.hermes/scripts/boss_resume_scorer.py`
- 六维：学习力(25%) / 专业力(20%) / 商务力(20%) / 销售属性(15%) / 抗压(10%) / 开放心态(10%)
- 红线淘汰：社恐、排斥社交、玻璃心、应酬耗能型

### 3. 常见翻车场景

| 翻车 | 解法 |
|------|------|
| 用通用模型评所有候选人 | 每次从 JD 重建，维度名用原文 |
| 权重与文档优先级不一致 | 文档中"最重要"的维度必须拿最高权重 |
| 忽略排除信号 | 排除信号设为致命短板/一票否决 |
| 假设用人偏好 | 一切从文档来，不从经验来 |
| 应届岗用社招模型 | 经验相关性在应届岗降权甚至设上限 |
| 证书权重过高 | JD 说"更看重思维而非专业标签"时证书降权 |
| "客户服务"≠"对外开拓" | 银行零售 sales 和投融资 BD 是不同的对外能力 |

### 4. 商用替代方案

| 工具 | 类型 | 说明 |
|------|------|------|
| 影刀 RPA | 桌面客户端 | BOSS 直聘采集 + DeepSeek AI 打分 |
| 八爪鱼 RPA | 桌面客户端 | 有 BOSS 直聘专用模块 |
| Moka | 企业 SaaS | 全流程 AI 招聘 |
| 智聘AI | 云端 SaaS | 远程操作 BOSS |

## Absorbed Sibling Skills

This umbrella has absorbed the following skills as labeled subsections below. Each sibling's unique knowledge was merged rather than left as a separate skill:

| Former Skill | Now In |
|-------------|--------|
| recruitment-automation | §BOSS直聘自动化（详细） |
| recruitment-resume-scoring | §简历打分引擎 |
| candidate-resume-evaluation | §候选人评估（完整流程） |
| candidate-resume-screening | §动态筛选与报告 |
| boss-recruitment-automation | §BOSS直聘自动化（补充） |
| criteria-driven-evaluation | §通用标准驱动评估 |
| jd-aligned-candidate-screening | §JD对齐筛选 |
| resume-evaluation-pipeline | §英文简历管线 |

--- 

## § 简历打分引擎（absorbed from recruitment-resume-scoring）

脚本：`scripts/boss_resume_scorer.py` — 六维打分引擎。

六维：学习力(25%) / 专业力(20%) / 商务力(20%) / 销售属性(15%) / 抗压(10%) / 开放心态(10%)

红线淘汰：社恐、排斥社交、玻璃心、应酬耗能型。

用法：`python3 ~/.hermes/scripts/boss_resume_scorer.py resumes.json`

**关键词库、权重、红线均可在脚本中定制。**

### Pitfalls
- 应届生简历关键词稀疏是正常的，看总分分布不是单维0分淘汰
- 外卖/零售类兼职不算「销售属性」— 需区分主动拓客 vs 被动服务
- 双模切换是核心：能对外「搞人」+ 能静下来做材料
- 学生会/社团经历要看角色：主席/部长才算商务力

---

## § 候选人评估完整流程（absorbed from candidate-resume-evaluation）

### Phase 1：申请 JD
如果用户未发 JD，先问：「请把岗位 JD 发给我，我先理解岗位要什么样的人再建评分模型。」

### Phase 2：解析 JD → 定制评分模型
1. 硬性条件（学历、专业、经验年限）
2. 核心软性要求（如「对外不怵」「学习力强」）
3. 加分信号（JD 明确列出的加分项）
4. 排除信号（JD 明确排除的特征）

**权重分配原则**：JD 中排在最前、用最多篇幅描述 → 最高权重。

### Phase 3：解析简历
用 PyMuPDF (fitz) 提取文本。每份简历提取：姓名、性别、年龄、联系方式、教育背景、工作/实习经历（原文引用）、项目经历、证书、技能。

### Phase 4：逐人 JD 对齐评分
每条分数必须附「简历原文依据」。禁止用通用金融/技术岗模型。

### Phase 5：生成报告
输出 Word + PDF 双份。报告必须包含：封面、评估模型说明、核心结论、逐人详析（≥阈值分）、低分段简表（<阈值分）、综合排名全表、面试建议。

### Phase 6：本地归档
按 `{得分}_{姓名}.pdf` 命名存入 `~/.hermes/cache/documents/候选人简历库/`。

---

## § 动态筛选与报告（absorbed from candidate-resume-screening）

**同一标准，动态追加** — 评分维度和权重全程不变，每个新简历追加进排名表。

报告必须包含简历原文引用（波总要求：「不然要往深看，还不知道内容呢」）。

推荐度标识：🔥 强推 (≥8.0) / ✅ 推荐 (≥7.0) / 🟡 备选 (≥5.0) / ⚠️ 短板 (≥4.0) / ❌ 不推荐 (<4.0)

---

## § BOSS直聘自动化（absorbed from recruitment-automation + boss-recruitment-automation）

### 核心工具：boss-zhipin-automation
GitHub: `wensia/boss-zhipin-automation`（FastAPI + React + Playwright Web UI）

安装路径：`~/.hermes/tools/boss-automation/`

### 反爬铁律
BOSS直聘反headless极严：
- ❌ Playwright headless → 白屏
- ❌ AppleScript `open location` → 开新标签页丢登录态
- ❌ Chrome CDP 远程调试 → 需桌面活跃会话
- ✅ 唯一可行：非 headless Chrome + 手机扫码

### 公网隧道
```bash
ssh -R 80:localhost:27421 nokey@localhost.run
# URL: https://<随机ID>.lhr.life
```
优先 localhost.run（无注册），ngrok 免费版有警告插页。

### REST API 操控（推荐替代 Web UI）
```bash
curl -X POST "http://localhost:27421/api/automation/init?headless=false&manual_mode=false"
```

### 当前限制
boss-zhipin-automation 原生只支持「自动打招呼」，简历下载/打分需二次开发。

---

## § 通用标准驱动评估（absorbed from criteria-driven-evaluation）

适用于评估**任何**候选对象（简历/供应商/方案/项目），不仅限于招聘。

### 铁律
永远不要用通用评分模型。评分维度、权重、判定标准必须从用户提供的标准文档（JD/RFP/评分规则）中逐条提取。

### 维度命名用原文
JD 说「锲而不舍」→ 维度名就是「锲而不舍」，不要翻译成「韧性抗压」。

### 排除信号作为一票否决
JD 说「只做研究不愿对外的不适合」→ 纯后台候选人对应维度直接不及格。

---

## § JD对齐筛选（absorbed from jd-aligned-candidate-screening）

**在拿到 JD 之前，不要开始评分。** 本条来自血泪教训。

### 常见 JD 类型维度模板

| 岗位类型 | 高权重维度 |
|---------|-----------|
| 投融资事务代表（应届） | 对外能量30-35% / 学习力20% / 韧性15-20% |
| 金融分析师 | 分析建模30-35% / 学习力20% / 学历15-20% |

### 陷阱
- 不要用社招模型评应届（经验相关降权甚至设上限）
- 「客户服务能力」≠「对外开拓能力」

---

## § 英文简历管线（absorbed from resume-evaluation-pipeline）

当波总发送英文简历时的评估流程。八维框架：

| 维度 | 权重 |
|------|:----:|
| 学历匹配度 | 10% |
| 工作经验相关性 | 25% |
| 业绩表现 | 20% |
| 专业资质 | 10% |
| 客户服务能力 | 15% |
| 数据分析能力 | 10% |
| 合规意识 | 5% |
| 综合潜力 | 5% |

权重一旦锁定，全轮不变。评分须引用具体简历内容。

---

## 支持文件

- `references/boss-anti-bot-patterns.md` — BOSS直聘反爬对抗实录
- `references/report-template.md` — 评估报告模板
- `references/jd-dimension-mapping.md` — JD → 评估维度映射指南
- `references/2026-06-09-case-study.md` — 应届社招模型错误案例
- `references/boss-integration-reality.md` — BOSS直聘集成现实
- `scripts/boss_resume_scorer.py` — 六维打分引擎