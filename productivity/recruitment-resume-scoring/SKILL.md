---
name: recruitment-resume-scoring
description: 招聘简历自动打分排序——定义维度、关键词匹配打分、六维加权排名。适用于 BOSS直聘等平台的简历批量评估。
version: 1.0.0
---

# 简历自动打分引擎

为招聘岗位建立打分维度体系，批量解析简历文本，自动评分排序。

## 使用场景

- 波总发布了招聘岗位，需要从大量简历中筛出最匹配的候选人
- 岗位需求已明确，需要建立可复用的评分标准
- 需要给候选人排名 + 每份简历的详细评分明细

## 方法论：六维框架

分析岗位需求，拆解为 6 个评分维度，每个维度配关键词库：

| 维度 | 含义 | 典型关键词 |
|------|------|-----------|
| **learning** | 学习力 | GPA、自学、跨专业、奖学金、竞赛 |
| **professional** | 专业力 | CFA/CPA、尽调、行研、财务分析、估值 |
| **business** | 商务力 | 接待、演讲、主持、对外合作、路演 |
| **sales** | 销售属性 | BD、客户开发、拉赞助、签约、谈判 |
| **resilience** | 抗压 | 创业公司、高强度、攻坚、独立负责 |
| **openness** | 开放心态 | 跨领域、转专业、复合、新技术、个人项目 |

每个维度的关键词分两级：
- **strong**（强信号）：10 分/命中
- **medium**（弱信号）：5 分/命中

维度得分上限 100，加权总分 = Σ(维度分 × 权重/100)。

## 脚本

打分引擎脚本：`scripts/boss_resume_scorer.py`

位于 `~/.hermes/scripts/boss_resume_scorer.py`。

### 用法

```bash
# JSON 批量（推荐）
python3 ~/.hermes/scripts/boss_resume_scorer.py resumes.json

# 单个简历文本
python3 ~/.hermes/scripts/boss_resume_scorer.py resume.txt

# JSON 格式：[{"name": "张三", "text": "简历全文..."}, ...]
```

### 权重配置

脚本中 `WEIGHTS` 字典可调整，默认配置：

```python
WEIGHTS = {
    "learning":      25,  # 学习力
    "professional":  20,  # 专业力
    "business":      20,  # 商务力
    "sales":         15,  # 销售属性
    "resilience":    10,  # 抗压
    "openness":      10,  # 开放心态
}
```

### 红线机制

`RED_FLAGS` 列表包含硬性淘汰关键词，命中直接标记 `disqualified`。

## 工作流

```
1. 用户描述岗位需求 → 确定六维权重
2. 补充关键词库（根据岗位特有的术语）
3. 用户提供简历文件（PDF/TXT）
4. 运行 OCR 提取 PDF 文字（如需）
5. 运行打分引擎 → 输出排名表
6. 人工复核 Top N 候选人
```

## 关键经验

- **应届生/1-2年经验**的简历，关键词稀疏是正常的。不要因为某维度 0 分就淘汰，要看总分和综合分布
- 外卖/零售类兼职不算"销售属性"——需要区分主动拓客 vs 被动服务
- 学生会/社团经历要具体看角色：主席/部长才算商务力，普通成员不算
- BOSS 直聘反 headless 极严，自动化登录几乎不可行。建议路径：用户手动下载简历 PDF → 发给 Hermes → 自动解析打分

## 相关脚本

- `scripts/boss_resume_scorer.py`：六维打分引擎
- `scripts/boss_login_headless.py`：BOSS 直聘 headless 登录（大概率被反爬拦截）

## Pitfalls

- BOSS 直聘的网页端对 headless browser 零容忍（白屏/5KB空白图），不要浪费时间尝试。走手动下载路线。
- 打分引擎依赖简历文字质量。如果 OCR 提取 PDF 有噪音，先清洗再打分。
- 权重需要根据岗位调整。对同一个候选人的两份不同 JD，得分可能有显著差异——这是正常的，不是 bug。
