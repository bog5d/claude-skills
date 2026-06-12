---
name: fos-project-analysis-workflow
title: "仓颉 FOS 项目分析工作流"
description: "对仓颉 FOS（融资作战系统）项目进行结构化理解的标准化流程"
trigger: "当波总要求理解/分析/评估仓颉 FOS、或让 Cursor 理解 FOS 项目时"
---

## Phase 1: 信息采集

### 1.1 拉取最新代码
```bash
cd /Users/mac/cangjie-fos && git fetch origin && git pull origin master
```
- 先 fetch 看远程是否有更新
- 再 pull 合并
- 不要默认只读本地版本

### 1.2 三路并行读取
同时读三个关键入口文档（不要串行，浪费时间）：
- `AGENTS.md` — AI 协作手册（当前版本状态、测试基线、禁止行为）
- `CHANGELOG.md` — 版本历史与 [Unreleased] 待做项
- `MASTER_PRD.md` — 产品灵魂与架构红线

### 1.3 代码结构扫描
```bash
find backend/src -name "*.py" | sort
find frontend/src -name "*.tsx" -o -name "*.ts" | sort
```
理解模块边界——看 services/ 和 api/routes/ 就能知道实现了什么能力。

### 1.4 测试基线验证
```bash
cd backend && python -m pytest tests/ -q --tb=no 2>&1 | tail -10
```
记录 passed/failed 数量。计算方式：
```python
dots = output.replace('\n', '')
passed = dots.count('.')
failed = dots.count('F')
```

### 1.5 Git 历史阅读
```bash
git log --oneline -20
git branch -a
```
看最近提交、分支策略、发布节奏。

## Phase 2: 架构理解

### 2.1 三体架构法
用三句话提炼系统本质：
- **一句话本质**：FOS 是做什么的（融资作战系统 = 虚拟资本合伙人）
- **核心架构**：FOS 和外部依赖的关系（FOS 编排 + Pitch_Coach 评估引擎 → 双系统）
- **当前阶段**：当前 Phase + 版本号

### 2.2 能力矩阵
输出表格：模块 | 状态(✅/🟡/🔴) | 说明

## Phase 3: 现状评估

### 3.1 识别关键数字
- 测试总数、passed/failed
- 前端测试数、build 状态
- commit 数量、分支结构
- CI 配置要求

### 3.2 问题分类
把 FAILED test 分成几类：
1. FSS 依赖（Pitch_Coach 路径找不到）
2. 环境配置（ffmpeg 没装）
3. 真正的代码 bug

## Phase 4: 路线规划

### 4.1 三阶段输出法
不要一上来就给长篇大论。结构如下：
1. **理解确认**：「我读完了，核心理解是XXX，对吗？」
2. **现状快照**：「当前 225/246 passed，12 failed 原因分类」
3. **路线建议**：「建议分X个Phase，每步预期产出」

### 4.2 行动清单优先级排序
- P0: 修复测试基线（让 CI 绿）
- P1: 落地 [Unreleased] 待做项
- P2: 后续增强

## Phase 5: 沉淀与同步

### 5.1 出结果前先问
**关键教训**：不要想当然地规划好了就开始干。
- 先问波总：「这个优先级你同意吗？」
- 波总说先沉淀就沉淀，说先干就干。

### 5.2 CHANGELOG 同步
每个变更都更新 CHANGELOG.md 的 [Unreleased] 区

### 5.3 知识沉淀
session 结束后记录新的观察：
- 学到了什么项目结构知识
- 波总的沟通偏好
- 踩了什么坑

---

## 已知 Pitfalls

### DO NOT
- 不 git pull 就开干（本地可能落后远程）
- 默认只读 AGENTS.md 不看 CHANGELOG（CHANGELOG 有最新待做项）
- 规划完成后直接开始编码（必须先问波总）
- 忽略 FAILED tests 的状态（它们反应真实问题）
