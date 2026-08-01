---
name: tech-project-evaluation
description: 值不值得吸纳：structured GitHub project evaluation and decision.
category: project-analysis
---

# 技术项目吸纳评估

波总从公众号/推文/GitHub 发现新项目时，要求快速判断「值不值得投入」。

## 触发条件

- "研究一下这个值不值得吸纳"
- 发来 GitHub 链接或公众号文章推荐的开源项目
- "这个项目怎么样"

## 评估流程

### Phase 1: 并行信息收集

对每个候选项目同时抓取：
1. **公众号原文** → Firecrawl scrape（微信公众号用 Firecrawl，不要用 web_extract——DuckDuckGo 后端不支持）
2. **GitHub 仓库页** → Firecrawl scrape（stars、license、语言占比、最近 commit、贡献者数、README 全文）
3. **补充搜索** → web_search 找第三方评测/新闻（中文+英文各搜一次）

### Phase 2: 多维评分矩阵

每个项目至少覆盖：

| 维度 | 数据来源 |
|---|---|
| Stars / 活跃度 | GitHub |
| 作者背景 | 公司/独立开发者？GitHub profile |
| **许可协议** | 第一优先级！GPLv3 传染性直接限制商业化；MIT/Apache 无顾虑 |
| 技术栈匹配度 | 与波总现有栈的重叠度（Hermes、Cursor、公众号管线、PPT 栈） |
| 部署/集成成本 | 一小时能跑通 vs 需要运维基建 |
| 可拆解价值 | 能否只取部分模块而不全量依赖？ |
| 生态成熟度 | 真开源 vs 镜像仓库？是否接受 PR？社区活跃度？ |

### Phase 3: 定位对比

如果有同类项目在波总栈里，做差异化分析：
- 新项目填补了什么空白？
- 是否会替代现有工具？还是互补？
- 提取独有的核心技术点（自研引擎、独特算法）

### Phase 4: 决策输出格式

```
每个项目：❌不吸纳 / 🟡战略关注 / ✅强烈吸纳

表格总结：
| 项目 | 吸纳 | 核心理由 |
```

对 ✅ 项目给出**即刻可执行的下一步**（clone → build → 验证）。

## 代码执行

评估为 ✅ 的项目，波总说"立刻跑起"时：
1. `git clone` 到 `/Users/mac/<项目名>/`
2. 读 AGENTS.md / CLAUDE.md 了解项目规范
3. 安装依赖 + build
4. 浏览器打开产物验证
5. 读文档研究集成方案（agents.md、format.md、architecture.md）
6. 输出技术解剖 + 与现有栈的对比定位 + 集成路线图

## 评估优先级原则

- **许可 > 技术**：GPLv3 直接警告，MIT 优先
- **可拆解 > 全量依赖**：宁可取模块，不引入新基建
- **填补空白 > 同类替换**：新能力比换工具更有价值
- **AI-native > 传统工具**：JSON 数据驱动、Agent 可编程的设计是加分项

## Pitfalls

- 微信公众号页面用 Firecrawl scrape（设置 `waitFor: 3000`），不要用 web_extract
- GitHub 仓库页 scrape 可能很大，会被持久化到文件，用 read_file 分段读取
- 评估报告不要写成"计划做"的列表——波总要的是决策和可执行动作
