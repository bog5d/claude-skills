---
name: resume-evaluation-pipeline
description: Dynamic resume evaluation pipeline — extract, score, rank, and report. Use when the user sends resume PDFs for candidate screening with consistent multi-dimensional scoring.
---

# Resume Evaluation Pipeline

When a user is screening candidates and sending resume PDFs one by one, build a **dynamic evaluation table** that grows with each resume. End goal: a final ranked report with cited resume evidence, ready to share with decision-makers.

## Trigger

User sends resume PDFs sequentially with instructions like:
- "按同一个标准整理、维度打分，动态增加"
- "最后输出报告，引用简历原文"
- "排序优先推荐度"

## Workflow

### Phase 1: Extract

Use PyMuPDF (`fitz`) to extract text from PDF resumes:

```bash
python3 -c "
import fitz
doc = fitz.open('<path>')
for page in doc:
    print(page.get_text())
doc.close()
"
```

If PyMuPDF fails, fall back to `pdftotext` or OCR pipeline.

### Phase 2: Score — 8-Dimension Framework

| Dimension | Weight | What to evaluate |
|-----------|:------:|------------------|
| 学历匹配度 | 10% | Education relevance to target role, school tier |
| 工作经验相关性 | 25% | Direct experience match with job requirements |
| 业绩表现 | 20% | Quantifiable achievements, numbers, scale |
| 专业资质 | 10% | Certifications, licenses |
| 客户服务能力 | 15% | Client-facing skills, conversion, relationship management |
| 数据分析能力 | 10% | Tools (Python/Excel/SQL), analytical thinking |
| 合规意识 | 5% | Compliance/risk control background |
| 综合潜力 | 5% | Growth potential, learning ability, soft skills |

**Hard rules:**
- Weights NEVER change between candidates in the same round
- Score honestly — if info is missing, mark it as unknown (e.g., "无" / "未注明")
- Each score must have a **one-line reason** citing specific resume content
- Scale: 1-10 (10 = exceptional match)

### Phase 3: Present — Dynamic Table

After each candidate, output:
1. Their individual scoring card (dimension + score + reason)
2. Updated full ranking table

Table format (Telegram-compatible):
```
| # | 姓名 | 得分 | 推荐度 | 核心竞争力 |
|:--:|------|:--:|:--:|------|
| 1 | 张三 | 8.5 | 🔥 强推 | 核心卖点一句话 |
```

Label recommendations consistently:
- 8.0+: 🔥 强推
- 7.0-7.9: ✅ 推荐
- 5.0-6.9: 🟡 备选
- <5.0: ⚠️ 短板明显

### Phase 4: Final Report

When user says stop, produce:
1. **Ranked table** (all candidates)
2. **Per-candidate analysis** — 3-5 bullet reasons, **citing real resume content** (quote specific achievements, numbers, roles)
3. **Recommended invitation list** — who to call for interviews and why
4. **Gap analysis** — what's missing from the candidate pool

Report must be: shareable with partners, self-contained (they don't see the raw resumes), evidence-backed.

## Pitfalls

- **Weights drift**: If you start changing dimension weights mid-stream, earlier candidates become incomparable. Lock weights on first candidate.
- **Halo effect**: Don't let one strong dimension inflate unrelated scores. A great school doesn't make someone great at client service.
- **Missing info ≠ low score**: If a candidate simply didn't list certifications, that's "unknown" not "0". But if they list none and the role requires them, score accordingly.
- **Telegram format**: No markdown tables — use labeled key:value format or the pipe format which auto-converts to row-group bullets.

## Example Scoring Card Output

```
### #3 王五 — 综合评分：6.5 / 10

| 维度 | 得分 | 依据 |
|------|:--:|------|
| 学历匹配 | 7/10 | 金融学硕士，211院校 |
| 经验相关 | 8/10 | 3年PE投研，直接对口 |
| 业绩表现 | 5/10 | 无量化业绩数据 |
| ... | ... | ... |

**综合**: 6.5 — 🟡 备选
**一句话**: PE投研背景对口但业绩模糊，需面试验证。
```
