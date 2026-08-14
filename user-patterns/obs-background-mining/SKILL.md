---
name: obs-background-mining
description: "波总提'后台挖掘/自动建链/LLM Wiki'时用。只读巡检OBS仓库织网+cron日报。"
version: 1.0.0
author: Hermes Agent
platforms: [macos, linux]
metadata:
  hermes:
    tags: [obs, knowledge-base, karpathy, llm-wiki, automation, cron]
    category: user-patterns
---

# OBS 后台自动挖掘（LLM Wiki 模式落地）

波总要求"后台不停自动建立链接、建立联系"——Karpathy LLM Wiki 模式的工程落地。

## 触发条件

- 用户提到"后台挖掘""自动建链""LLM Wiki""知识库网络"
- 用户发来新转写需要归档（归档时增量织网）
- 需要查看知识库关联网络/孤岛/逾期待办

## 核心资产

| 脚本 | 作用 |
|------|------|
| `~/.hermes/scripts/obs_link_miner.py` | 全量网络扫描：实体/关系/人脉互引/拆解卡映射/孤岛/跨场景（一次性看全图） |
| `~/.hermes/scripts/obs_auto_miner.py` | 增量 watchdog：对比昨日快照，检测 A未归档素材 B未建档人名 C孤岛实体 D孤儿卡 E逾期待办 F新链接，**有变化才报**，无变化静默 |

## 铁律（波总明确约束）

1. **白名单只读**：只扫描 `~/AI_Workspaces/Cangjie_OBS_Notes`，绝不写该仓库任何文件（git status 必须保持干净）。
2. **状态文件唯一写点**：`~/.hermes/scripts/obs_link_state.json`（仓库外）。
3. **报告只是建议**：待办/建档等落地动作由副官人工确认后执行，脚本不自动改库。
4. 不污染 OBS 其他项目——仓库路径硬编码，脚本内无任何写仓库逻辑。

## 运维

- Cron: `OBS后台自动挖掘日报`，每天 09:00，no_agent 模式，stdout 非空才投递。
- 重置快照：`rm -f ~/.hermes/scripts/obs_link_state.json` 后重跑即为"首跑"全量报告。
- 自测：`python3 ~/.hermes/scripts/obs_auto_miner.py` 跑两遍，第二遍应静默（无变化时）。
- 修改后必测：先 `rm state` 首跑，再二跑验证静默，最后 `cd ~/AI_Workspaces/Cangjie_OBS_Notes && git status --short` 验证零改动。

## 陷阱

- 人名检测误报多：职务词（一部总/营销总/基金总/新任总/投行总）、公司名片段（盈远董/农商行董）、描述片段（服务了/了解波总）都要加进 `bad_names` 黑名单。
- 已建档卡名必须在黑名单里（张克/王宇/李华…两字前缀），否则自指误报。
- 逾期检测正则只匹配 `YYYY-MM-DD`；"2026-08-10后"这类带后缀的日期也能匹配到（正则不要求整行）。
- entities.md 的 PER-001~010 等早期实体无 relations 行属正常（历史存量），孤岛检测要区分存量与新孤岛，避免刷屏。
