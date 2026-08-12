---
name: cangjie-obs-agent
description: 波总长期记忆/人脉Agent：拉取Cangjie_OBS_Notes仓库按序读交接文件并处理素材。
version: 1.0.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [adjutant, memory, contacts, cangjie, obs, notes, workflow]
    related_skills: [adjutant-boot, adjutant-system]
category: user-patterns
trigger: session start as memory/contact agent; user asks who to meet; user sends voice transcript, meeting notes, or long dictation
priority: critical
---

# Cangjie OBS Notes — 长期记忆/人脉 Agent 协议

## When to Use

- 用户以"长期工作记忆与人脉管理 Agent"角色启动会话（事实源 = Cangjie_OBS_Notes 仓库）
- 用户问"今天/接下来见谁""最近在做什么""项目状态"
- 用户发送语音转写、会议记录、截图转写或长篇口述
- 用户说"记一下""记录下来""有个任务"

波总（王波）指定的长期事实源是私有 GitHub 仓库 `bog5d/Cangjie_OBS_Notes` 的 `main` 分支（本地 `~/AI_Workspaces/Cangjie_OBS_Notes`）。**聊天窗口不是事实库。** 每次开工先拉库并按序读交接文件。

⚠️ 区别于旧 hermes-adjutant 副官仓库（status.json 单点）：本仓库是**多模块仓库**（交接手记/原始素材/知识库/人脉管理/日程管理/待办管理/收件箱/系统检查），协议在仓库自带的 `交接手记/START_HERE.md`，本 skill 是它的速记版。以仓库文件为准。

## Step 1: 拉库 + 并发检查

```bash
cd ~/AI_Workspaces/Cangjie_OBS_Notes && git pull origin main
# 写入前确认远端最新（多 AI 并发铁律）
git fetch origin main && git rev-list --left-right --count HEAD...origin/main   # "0 0" = 同步
ls -la .git/*.lock 2>/dev/null || echo "无锁文件，无进行中的写入"
```
- 远端有新提交 → 重新读取相关文件再合并；**禁止强推、禁止旧文件覆盖新文件**。
- 每次提交只含本次任务相关文件，commit 写清来源日期和处理内容。

## Step 2: 按序读取交接文件（必须按序）

1. `交接手记/START_HERE.md`（接手入口 + 三条最高规则）
2. `交接手记/CURRENT_STATE.md`（当前状态 + 待核对项）
3. `交接手记/跨AI协作协议.md`（权威顺序 + 写入边界）
4. `交接手记/WORKFLOW.md`（八步流程）
5. `原始素材/处理台账.md`（source_id 台账）
6. `知识库/副官拆解/README.md` 与 `知识库/副官拆解/INDEX.md`
7. `日程管理/UPCOMING.md`
8. `待办管理/OPEN.md`
9. 本次任务相关的人脉档案、日志、原始素材和知识卡；**同一天已处理过的拆解卡/清洗稿必读**（同日多素材数字交叉核对，防信息冲突，见陷阱节）

回答"今天/接下来见谁"时：时间地点 → 人物背景 → 上次聊了什么 → 双方承诺 → 未完成事项 → 本次注意事项（按 `跨AI协作协议.md` 的检索顺序）。

## Step 3: 素材处理八步流程（录音/口述/会议/截图转写）

> **执行引擎（2026-08-11 波总约定，已实测）**：录音/长口述/会议转写处理，Hermes 是总调度，**优先派遣 Cursor CLI 执行全部完成动作**（清洗→拆解→同步→台账→validate→push）。理由：Cursor 订阅月额度大量未用完，DeepSeek 按量计费；重活放 Cursor，DeepSeek 只花"原始稿入库+调度验证"的几千 token。调度标注用 `🔴 [Cursor 执行中]` → delegate → 验证 → `🔴 [Cursor 完成]`；Cursor 不可用才降级 Hermes 原生（🟢）。**实测**：SRC-20260811-001 原始稿 46KB → Cursor 产出 11 文件 +2247 行 → commit+push 成功。
>
> **分工铁律**：原始稿必须 Hermes 自己写（转写文本在对话上下文里，子代理看不到）；写完 `_raw.md` 后再 delegate 剩余步骤。delegate 返回后**必须验证侧效应**（git log 看提交、search_files 确认文件落位、grep 台账/OPEN 行），不信子代理自报。**原生降级路径已实测完整可用**（2026-08-11 SRC-20260811-002：Hermes 原生全流程 14 文件 +1063 行 + commit/push 成功，清洗稿 46KB 级也扛得住）——Cursor 不可用时无需犹豫，直接原生跑完。

1. **保存原始稿**：`原始素材/录音转写/YYYY/MM/*_raw.md`，生成唯一 `source_id`（`SRC-YYYYMMDD-NNN`），**原文不删减、不覆盖**。
2. **登记台账**：`原始素材/处理台账.md`，状态 `received`。
3. **清洗稿**：`*_clean.md`，修正明显 ASR 错误；不确定片段保留原文并标 `[待确认]`，**不得把猜测写成事实**。
4. **分层提取**：客观事实 / 王波判断 / 他人观点 / AI 推测，四层分开。
5. **副官拆解卡**：`知识库/副官拆解/YYYY/MM/SRC-*.md`，固定六维（新增信息/新增认知/行业谈资/待研究课题/未知扫描/行动与回链），更新 `INDEX.md`。
6. **同步正式模块**：工作日志、人脉档案、日程、待办、知识/认知卡按需更新。
7. **回链**：正式记录写 `source_id`；台账列全 `derived`。
8. **校验提交**：`python 系统检查/validate_repo.py` 通过后 `git commit + push`。

清洗稿与拆解卡的具体字段/表格/标注语法（说话人映射表列、frontmatter、`[confirmed_fact｜KK]` 等标注、台账/待办/INDEX 行格式、校验与提交检查清单）见 `references/recording-intake-formats.md`——录音转写入库时先读该文件，格式与仓库模板对齐再落笔。

## 实体索引与认知演化模块（SCHEMA §9/§10，2026-08-11 初始化完成）

- 文件：`知识库/实体索引/entities.md`（实体主表）、`relations.md`（关系表）、`conflicts.md`（矛盾登记）；`知识库/认知演化/evolution.md`（认知演化）。
- 实体 ID 前缀：`PER-`/`ORG-`/`PRJ-`/`FIN-`/`MET-`/`PLC-`；关系必带 source + confidence（高/中/低）；矛盾双口径都保留、各标来源。
- **日常是增量，不是全量重扫**：每日加工只扫新增拆解卡/人脉卡/知识卡（按 source_id 或 mtime），把新实体/新关系/新冲突/新认知追加进四个文件；初版全量扫描（2026-08-11 已完成）只做一次。
- 认知演化状态机：`active`/`revised`/`confirmed`/`superseded`；被纠正的认知旧表述保留、修正历史记日期/新表述/原因/来源（例：股改税务"递延到退出"→"与退出无关"，INS-20260811-023 revised；两个口径均为会议观点，仍需专业核验）。
- 初版扫描的完整流程、格式样板、增量维护规则与校验坑见 `references/entity-index-evolution.md`。

## 知识边界标签

- `KK` 已确认已理解 / `KU` 已知问题答案不明 / `UU` 未知之未知候选（必须标置信度+验证办法，不得写成事实）。
- 合规/法律/税务/医疗/投资结论标"待专业核验"。

## 确认原则

- 明确事实先沉淀；姓名/说话人/日期/金额/身份/合规结论有歧义 → 标待确认。
- 一次最多追问 1—3 个最关键问题，不给代表性原话只问"说话人1是谁"是差评。
- **说话人确认闭环（用户原话要求 2026-08-12）**：批量确认未识别说话人时，逐人列出「推测身份 + 依据 + 原话摘录」再问是谁——"跟我确认的时候，一定要说他说了什么话"。模板与实战案例见 `references/speaker-confirmation.md`。
- **对话内直接称呼是高置信度说话人证据**：确认顺序＝直接称呼 > 自称单位 > 内容特征。例：波总喊"江总"问投屏 → 下一句应答者=江总；对方称"王总"且答问全是泽天融资/实缴细节 → 即波总。被喊姓氏（"张总"）也能锁姓，再与已知人名（张雨竹等）交叉核对。
- 用户附带的 AI 摘要（"以上由AI大模型生成，可能包含不准确的信息"）只作参考，入库标"可能不准确"，不得当事实。
- 用户纠正后保留变更痕迹，搜索并同步所有受影响文件。

## 安全铁律

- 不记录 Token/密码/Cookie/身份证/银行卡秘密。
- 无仓库权限时停止正式写入，回复中说明"尚未入库"，让用户通过密钥管理/环境变量/GitHub 授权配置，**不要要求用户粘贴 Token**。
- 涉及规避监管或隐匿资金路径的原话只做风险识别，不改写成操作指南。
- 私人日记不自动入库，除非用户明确要求。

## 中断保护（额度不足时）

按优先级：原始稿 → 处理台账 → 副官拆解卡骨架 → `CURRENT_STATE.md` → 其余提炼。未提交内容必须明确告诉用户"尚未入库"。

## 处理回执（最后回复必须包含）

1. 已入库的原始素材（路径）
2. 已更新的正式模块
3. 未确认/待处理项
4. 下一步提醒
5. 提交结果或"尚未入库"的明确状态

## 参考文件

- `references/recording-intake-formats.md` — 录音转写入库具体格式速查（clean.md/拆解卡/台账/待办/INDEX 字段与 `[confirmed_fact｜KK]` 标注语法、validate 与提交检查清单）
- `references/entity-index-evolution.md` — 实体索引+认知演化模块格式与维护（entities/relations/conflicts/evolution 字段与 ID 规则、初版全量扫描流程、每日增量规则、跨文件 ID 校验）
- `references/table-image-rendering.md` — 中文表格 → PNG 图片渲染配方（波总偏好表格出图，禁止 markdown 源码）
- `references/telegram-phone-control-diagnosis.md` — 用户手机 Telegram 遥控通道诊断（代理解析/pairing 授权/getUpdates 冲突陷阱）
- `references/speaker-confirmation.md` — 说话人身份确认闭环（逐人原话摘录模板 + 对话内直接称呼证据法 + 确认后全模块回写清单 + SRC-20260812-001 实战案例）

## 陷阱

- **不要靠 Hermes memory / mem0 获取任务状态**——会过期；以仓库为准。
- 旧 hermes-adjutant（status.json）与 Cangjie_OBS_Notes 是两个不同事实源，别混。用户 2026-08-10 明确指定后者为长期记忆/人脉事实源。
- 过期日程不能自动标完成，先与用户核对实际结果（CURRENT_STATE 有专门待核对清单）。
- `TELEGRAM_ALLOWED_USERS=501` 是 macOS UID 陷阱，与 Telegram ID（9~10 位）不可混；波总 ID `8447296166` 在 pairing store 授权（见 hermes 侧资料）。
- **用户要"人脉表/归档表/总表/故障表"时，先读仓库约定格式再输出**：`人脉管理/README.md` 的 8 字段总表（姓名/角色/职业/地区/行业/影响力/亲密度/黄金人脉圈）+ `交接手记/SCHEMA.md` §3 全息背景卡。不要自创字段或结构。参考 `references/table-image-rendering.md`。
- **话题切换检测**：用户说"我已经不说X了/你没理解"时，立即丢弃旧话题锚点重新确认需求。真实案例（2026-08-10）：把"人脉故障表"误当成刚聊的雅典娜案工具表，实际用户要的是仓库里约定的人脉归档总表。不要因为当前聊天上下文有热点话题就臆断用户指代。
- **人脉档案必须登记进总表**：新建/更新 `人脉管理/<姓名>.md` 后检查 `人脉管理/README.md` 总表行 + 统计（总人数/密友/好友）同步。历史缺口：何福荣/刘锐/郑小康 3 份档案存在但未进总表，2026-08-10 已补录。
- **validate_repo.py 报错先判断是否本次引入**：已知历史遗留 = `obs-wiki/`（含 API key 存档）与 `2026年/` 旧目录约 109 个 ERROR + obs-wiki/raw 缓存 utf-8 解码错误，不阻塞提交。本次引入判定用定向 grep 而非 stash（新文件未跟踪时 stash 无效）：`python3 系统检查/validate_repo.py 2>&1 | grep -E "<本次文件名>"` 无输出，且对每个报错文件跑 `git status --short -- <报错文件>` 无匹配 = 全部历史遗留。**`git add -A` 前先确认未跟踪新增文件里没有密钥/敏感文件会被扫入**（2026-08-11 run 中密钥文件已被跟踪故安全；新增文件一律人工过目再 add）。完整检查清单见 `references/recording-intake-formats.md` §7。
- **用户更正人名/数字/事实 → 全模块传播协议**：用户纠正后（如 2026-08-11 尹建文→尹嘉雯），搜索全库所有出现处（`grep -rn "旧名" --include="*.md" .`），同步改：clean 稿、副官拆解卡、人脉卡、OPEN 待办、工作日志、CURRENT_STATE、处理台账（通常 6-8 个文件）；**`_raw.md` 正文保留原始 ASR 不动**（溯源链完整），只在 frontmatter 场景段加"用户更正"说明行；解除相关 `[待确认]` 标记并注明"用户已确认"。批量替换用 python3 脚本（逐文件 read+replace+write）比 patch 工具可靠，改完 `grep -rn "旧名"` 验证无残留（raw 正文例外，预期保留）再 commit+push。
- **同日多素材必须交叉核对数字**：同一天处理第二份 source 前，先读同日已处理的拆解卡/清洗稿（如 SRC-20260811-002 处理前读 SRC-20260811-001），逐项比对金额/估值/年度口径；冲突处**不静默取其一**，双口径并列写进新拆解卡的未知扫描（ai_inference+置信度）与台账/CURRENT_STATE 待确认项。实测冲突（2026-08-11）：投前 5.5亿+3500万=投后 5.85亿 自洽 vs 001 卡"投前 5.45亿"；"去年营收 8400万" vs 001 卡"2025 营收 1.2亿"；今年净利 3300万 vs "2000多万~3000万"。另注意：自洽口径（5.5+0.35=5.85）可以标"自洽、疑为另一卡 ASR 误"，但仍是待确认。
- **待办归档要原子化**：OPEN.md 里跟踪的待办其底层事件一旦落地（如 T-20260811-006"华西约时间"→8/11 交流已发生），归档=**同一编辑里从 OPEN.md 删除行 + 追加到 `待办管理/DONE-YYYY.md`**，并在 DONE 行注明"后续转 T-XXXX 推进"。先追加 DONE 忘删 OPEN 会产生双写，改完 `grep -n "T-20260811-006" 待办管理/*.md` 验证只出现在 DONE。
- **日程疑似同一场事件的处理**：不同 source 描述的同一日期活动（8/13 投资对接会=省内20家+全国24家 vs 8/13 路演=约100人 15+5分钟）**保留两行并互标"疑为同一场待确认"**，不擅自合并；旧行被新信息取代时（如"8/14 后华西可能来访"→8/11 交流已落地）就地改写该行，不留过期行。
- **`_raw.md` 可能是未跟踪文件**：原始稿存在磁盘 ≠ 已在 git 里；提交前 `git status --short` 检查，未跟踪的 `_raw.md` 属本次任务文件一并 `git add -A`，不要以为它早已入库。
- **实体 ID 跨文件一致性（实体索引模块）**：relations.md/conflicts.md 引用的实体 ID（ORG-xxx 等）必须先存在于 entities.md。教训（2026-08-11 初版）：relations 初稿引用了未建卡的 ORG-023*/ORG-077*，被迫回补 ORG-076/077/078。写完 relations 后跑 `grep -oE '(PER|ORG|PRJ|FIN|MET|PLC)-[0-9]{3}' relations.md | sort -u` 与 entities.md 同法输出做 diff，零差集才提交。
- **表格行去重（实体索引模块）**：给 relations.md 追加行前先 grep 该行主键（如 `PER-012 刘锐`）是否已存在，避免 patch 后出现重复行（2026-08-11 实测出现一次，需回删）。
- **patch 工具引号转义失败（escape-drift）**：old_string/new_string 含 `\"` 字面量时报 "Escape-drift detected" 拒绝匹配。仓库 md 大量含引号，patch 时去掉反斜杠转义，或改用无引号锚点（如只锚标题行 `## 使用规则`）；仍失败就用 python3 逐文件 read+replace+write（本仓库多 AI 并发下该路径已验证最可靠）。
- **`_raw.md` 必须满足 validate schema**：frontmatter 缺 `source_format/confidentiality/raw_integrity`、`type` 不是 `voice_transcript`、正文缺 `## 原始转写` 标题都会报"缺少原始素材字段"（2026-08-12 实测）。按 `references/recording-intake-formats.md` §0 模板落盘。
