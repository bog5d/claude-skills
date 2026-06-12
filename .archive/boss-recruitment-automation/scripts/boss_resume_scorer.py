#!/usr/bin/env python3
"""
BOSS 直聘简历自动打分引擎 v1.0
输入：简历文本（从 BOSS 直聘提取或 PDF 解析）
输出：六维打分 + 加权总分 + 排序
"""
import json
import re
import sys
from pathlib import Path
from collections import Counter

# ============================================================
# JD 配置（可调整权重）
# ============================================================

WEIGHTS = {
    "learning":     25,   # 学习力
    "professional": 20,   # 专业力（金融/法务/财务）
    "business":     20,   # 商务力（接待/对外）
    "sales":        15,   # 销售属性（搞定人/搞定事）
    "resilience":   10,   # 抗压/非玻璃心
    "openness":     10,   # 开放心态
}

# 红线关键词（命中直接淘汰）
RED_FLAGS = [
    "社恐", "不喜欢社交", "排斥应酬", "拒绝接待", "讨厌应酬",
    "不善言辞", "不想跟人打交道", "不善交际",
]

# ============================================================
# 六维关键词库
# ============================================================

KEYWORDS = {
    "learning": {
        "strong": ["GPA", "绩点", "自学", "快速上手", "从零到一", "快速学习",
                    "跨专业", "保研", "奖学金", "优秀毕业生", "竞赛获奖",
                    "第一名", "top", "排名", "双学位", "辅修", "进修",
                    "coursera", "MOOC", "考证", "自学成才"],
        "medium": ["学习能力", "主动学习", "新技能", "培训", "钻研"],
    },
    "professional": {
        "strong": ["CFA", "CPA", "司法考试", "法考", "基金从业", "证券从业",
                    "投行", "行研", "尽调", "财务分析", "估值模型", "DCF",
                    "财务报表", "审计", "合规", "公司法", "证券法",
                    "并购", "IPO", "融资", "股权", "债权",
                    "行研报告", "投资分析", "行业研究"],
        "medium": ["金融", "财务", "会计", "法律", "经济学",
                    "材料撰写", "文档", "报告", "PPT", "Excel",
                    "数据分析", "Wind", "Bloomberg", "同花顺"],
    },
    "business": {
        "strong": ["接待", "商务宴请", "客户拜访", "路演", "演讲", "主持",
                    "对外联络", "政府关系", "公关", "品牌", "对外合作",
                    "商务谈判", "会务组织", "大型活动"],
        "medium": ["沟通", "协作", "团队合作", "跨部门", "协调",
                    "社团", "学生会", "组织", "策划", "活动"],
    },
    "sales": {
        "strong": ["销售", "BD", "商务拓展", "客户开发", "拉赞助", "签约",
                    "地推", "陌拜", "渠道", "代理商", "经销商",
                    "搞定", "拿下", "成交", "转化率", "KPI",
                    "校园代理", "创业", "合伙人"],
        "medium": ["谈判", "说服", "推广", "营销", "获客",
                    "实习", "兼职", "赚钱"],
    },
    "resilience": {
        "strong": ["创业公司", "0-1", "高强度", "996", "从无到有",
                    "抗压", "独立负责", "独当一面", "攻坚", "突破",
                    "克服", "困难", "坚持", "韧性"],
        "medium": ["快节奏", "挑战", "高压", "多任务", "并行"],
    },
    "openness": {
        "strong": ["跨领域", "转专业", "跨界", "复合背景", "文理兼修",
                    "工科+金融", "技术+商业", "多元", "AI", "新技术",
                    "开源", "blog", "github", "个人项目", "side project"],
        "medium": ["好奇心", "探索", "尝试", "兴趣广泛", "终身学习"],
    },
}


def score_resume(text: str) -> dict:
    """对简历文本打分"""
    text_lower = text.lower()
    
    # 红线检查
    for flag in RED_FLAGS:
        if flag in text:
            return {"disqualified": True, "reason": f"红线命中: {flag}"}
    
    scores = {}
    details = {}
    
    for dim, tiers in KEYWORDS.items():
        strong_hits = []
        medium_hits = []
        
        for kw in tiers["strong"]:
            if kw.lower() in text_lower:
                strong_hits.append(kw)
        for kw in tiers["medium"]:
            if kw.lower() in text_lower:
                medium_hits.append(kw)
        
        # 计分：强关键词 10 分/个，中等关键词 5 分/个，上限 100
        raw = min(len(strong_hits) * 10 + len(medium_hits) * 5, 100)
        scores[dim] = raw
        details[dim] = {
            "strong": strong_hits,
            "medium": medium_hits,
            "raw": raw,
        }
    
    # 加权总分
    weighted = sum(scores[d] * WEIGHTS[d] / 100 for d in WEIGHTS)
    
    return {
        "disqualified": False,
        "scores": scores,
        "weighted_total": round(weighted, 1),
        "details": details,
    }


def rank_resumes(resume_list: list) -> list:
    """批量打分排序"""
    results = []
    for item in resume_list:
        name = item.get("name", "未知")
        text = item.get("text", "")
        result = score_resume(text)
        result["name"] = name
        results.append(result)
    
    # 排序：淘汰的排最后
    results.sort(key=lambda x: (
        x["disqualified"],
        -x["weighted_total"]
    ))
    
    return results


def print_report(results: list):
    """打印排名报告"""
    print("\n" + "=" * 70)
    print("  BOSS   简历打分报告")
    print("=" * 70)
    
    for i, r in enumerate(results, 1):
        if r["disqualified"]:
            print(f"\n  #{i} {r['name']} — 淘汰 ({r['reason']})")
            continue
        
        s = r["scores"]
        print(f"\n  #{i} {r['name']} — 总分: {r['weighted_total']}/100")
        print(f"    学习力: {s['learning']:>3} | 专业力: {s['professional']:>3} | "
              f"商务力: {s['business']:>3}")
        print(f"    销售:   {s['sales']:>3} | 抗压:   {s['resilience']:>3} | "
              f"开放:   {s['openness']:>3}")
    
    print("\n" + "-" * 70)
    qualified = [r for r in results if not r["disqualified"]]
    disq = [r for r in results if r["disqualified"]]
    print(f"  总计 {len(results)} 份 | 合格 {len(qualified)} | 淘汰 {len(disq)}")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if path.suffix == ".json":
            data = json.loads(path.read_text())
            results = rank_resumes(data)
        else:
            text = path.read_text()
            results = rank_resumes([{"name": path.stem, "text": text}])
        print_report(results)
    else:
        print(__doc__)
        print(f"\n用法: python {sys.argv[0]} resumes.json  # JSON数组")
        print(f"      python {sys.argv[0]} resume.txt    # 单个简历文本")
