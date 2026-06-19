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

## 支持文件

- `references/boss-anti-bot-patterns.md` — BOSS直聘反爬对抗实录
- `references/report-template.md` — 评估报告模板
- `references/jd-dimension-mapping.md` — JD → 评估维度映射指南
- `scripts/boss_resume_scorer.py` — 六维打分引擎