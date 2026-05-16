---
name: web3-research-to-ppt
description: 对 Web3 / RWA / AI+Web3 方向进行深度研究并直接生成 HTML PPT。使用 delegate_task 做并行 web research → 结构化输出 → 直接用 guizang-ppt-skill 模板生成翻页幻灯片。核心教训：用户说"做成PPT"时必须 skip markdown 中间步骤，直接生成 HTML slides。
---

# Web3 Research → HTML PPT 工作流

## 什么时候用

用户要求研究 Web3 / 区块链 / RWA / AI+Web3 / 数字资产 / 加密货币等方向，并输出为 PPT / 幻灯片 / 分享材料。

## 核心教训（血泪经验）

**当用户说"做成PPT"时，绝对不能先输出 markdown 再转格式。** 用户要的是"看起来像 PPT 的东西"——可翻页、有视觉风格、能直接打开的 HTML 文件。先给 markdown 等于告诉用户"我做了但没做完"，会被纠正。

## 工作流

### Step 1: 并行研究（delegate_task）

用 `delegate_task` 做 1 个全面研究任务，toolsets 带 `web`。覆盖：

1. Web3 2025-2026 最新发展趋势（DeFi、Layer2、RWA 代币化、AI Agent 经济）
2. 中国政策环境与合规路径
3. AI + Web3 结合方向（zkML、Bittensor、数据 DAO）
4. 个人学习路径（从零到变现）
5. 变现/赚钱方向（合规角度）
6. 可买入的数字资产类型（风险分层）
7. 可实践的动手项目

prompt 要求：结构化输出、每个方向含核心技术点/学习资源/所需技能栈/变现评估/中国大陆可行性。用中文。

**搜索数据落地规则**：如果单个搜索返回的数据超过 1500 字，不要把它带回对话上下文——先用 `write_file` 写入一个临时文件（如 `/tmp/rwa-research-1.json`），然后继续下一步。所有搜索数据全部落地到文件后，Step 2 直接读取这些文件拼接 PPT。

### Step 2: 直接生成 HTML PPT

不要先写 markdown！直接用 guizang-ppt-skill 模板生成。

1. 选主题：AI/科技类推荐 🌊 靛蓝瓷（--ink:#0a1f3d, --paper:#f1f3f5）
2. 规划页面节奏（15-20 页）：封面 → 大字报(what) → 趋势(why) → 中国政策 → AI+Web3 → 学习路径 → 变现 → 项目推荐 → 资产 → 行动路线 → 总结
3. 边写边注意：
   - `h-hero` 衬线大标题
   - `h-xl` 衬线副标题
   - `lead` 引导段
   - `stat-card` 数据卡片
   - `grid-2-7-5` / `grid-2-6-6` 分栏
   - `callout` 引用框
   - `pipeline` 流水线
   - 按节奏规划表交替 `light` / `dark` / `hero light` / `hero dark`

### Step 3: 本地打开验证

```bash
open "/Users/mac/.hermes/hermes-agent/web3-ppt/index.html"
```

### PPT 内容组织参考

| 页 | 主题 | 布局 | 内容 |
|----|------|------|------|
| 1 | Cover | `hero dark` | Web3 / RWA 学习、实践与变现 |
| 2 | 三个互联网时代 | `light` grid-2-6-6 | Web1→Web2→Web3 对比 |
| 3-4 | 六大趋势 | `light` stat-card | DeFi、Layer2、RWA、AI Agent、zkML、DID |
| 5 | 中国政策地图 | `hero dark` | 红线/灰色/机会区域 |
| 6-7 | AI+Web3 交叉 | `light` callout | zkML、Agent 经济、数据 DAO |
| 8-9 | 学习路径 | `light` pipeline | Phase 1-5 |
| 10-11 | 变现方向 | `light` stat-card | 短期/中期/长期收入预期 |
| 12 | 数字资产 | `light` rowline | 风险分层表格 |
| 13 | 波总专属行动路线 | `light` pipeline | 第一周/月/三月/六月 |
| 14 | 动手项目 | `light` grid-3 | 5 个项目卡 |
| 15 | 总结 | `hero dark` | 一句话金句 |

### 坑点

- **用户说"做成PPT"≠ markdown**：直接生成 HTML slides，不要先给 markdown 底稿
- **主题色选靛蓝瓷**：AI/科技/区块链方向最适合
- **节奏规划必须在写 slide 之前完成**：画好 15 页的 light/dark 交替表
- **不要用 emoji**：全部用 Lucide icons
- **中文大标题 ≤ 5 字时 nowrap**
