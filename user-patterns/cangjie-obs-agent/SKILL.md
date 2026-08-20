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
- **分叉（"左 右"非 0 0）用 rebase 收敛，别用 --ff-only 硬拉**：2026-08-14 实测本地 1 条未推送提交（人脉卡更新）+ 远端 30 条（Windows/OBS 同步）分叉，`git pull --ff-only` 报 `Diverging branches can't be fast-forwarded`。处理：`git rebase origin/main`（零冲突）→ `git push origin main` 推回本地独有提交 → 验证回到 "0 0"。自动拉取 cron（`~/.hermes/scripts/pull_obs_notes.sh`）已升级为 `git pull --rebase --autostash` + 检测到本地独有提交时自动回推，不再报错。

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
10. **人脉相关任务另读（V2 规范，2026-08-15 启用）**：`人脉管理/人脉管理V2方法论.md`（八维字段/6视图/互动日志/引荐闭环）→ `人脉管理/AI强制维护协议.md`（互动后强制动作）→ `人脉管理/README.md`（总表+V2导航）。速查见 `references/renmai-v2-spec.md`。

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

## 素材梳理/主题素材包输出（只读出报告模式，2026-08-19 实测）

用户要"梳理知识库中关于主题 X 的全部素材 / 输出素材包 / 做主题调研"时——**只读收集，不改仓库**（区别于 Step 3 的录入流程）：

1. `git pull` 后关键词 grep（search_files files_only；同义词/别名/人名/机构名一起搜，如 `跃壹|雷达|南京|中材|矿山|5G|换股|反投|人名`，两次调用合并去重）。
2. **拆解卡优先**的精读顺序（信息密度排序）：SRC 拆解卡（每张含新增信息/新增认知/待研究课题/未知扫描/行动与回链，是全主题最高价值入口）→ 对应 raw/clean 转写（取原文金句与逐字口径）→ `知识库/实体索引/entities.md`+`relations.md`（PER/ORG/PRJ 代码）→ `evolution.md`（INS 编号+修正历史）→ `待办管理/OPEN.md`（T 编号）→ `副官系统/data/operating_state.json`+主线台账（LINE 编号，含主线状态/决策门/成功定义）→ `交接手记/CURRENT_STATE.md` 更正节 → 工作日志/人脉卡/日程管理（补时间线与接触窗口）。
3. 输出素材包**写 /tmp/ 文件**（本类输出实测 20-40KB，必须文件中转不走对话，呼应 search-generate-separation）：按主题分节；每条事实带来源（文件路径+SRC 编号+日期）；【事实】与【推断】分开；不确定标【待确认】；末尾附"待确认清单＋敏感项＋金句（原文+发言人+日期）＋来源文件清单"。
4. 验证：`wc -l` + `grep -c '【事实】'` 等标记计数，确认落盘。
5. **旧素材口径陷阱**：主题跨多日时，旧 SRC（如 8/11）的机构名/项目名/轮次可能已被后续更正（实测：一保研究院→中材（南京）矿山研究院、民防雷达→矿山边坡雷达、"民防雷达产线"→成熟设备采买+集成承接、B轮/B+轮命名 2026-08-19 统一）。引用旧素材前先对 `CURRENT_STATE.md`「已确认的重要人脉/信息更正」节 + entities.md 别名列，素材包统一用更正后口径，旧名出现处注明"（旧称，已更正）"，避免传播过期术语。
6. 模板与跨模块映射图见 `references/topic-material-pack.md`。

## 知识边界标签

- `KK` 已确认已理解 / `KU` 已知问题答案不明 / `UU` 未知之未知候选（必须标置信度+验证办法，不得写成事实）。
- 合规/法律/税务/医疗/投资结论标"待专业核验"。

## 确认原则

- 明确事实先沉淀；姓名/说话人/日期/金额/身份/合规结论有歧义 → 标待确认。
- 一次最多追问 1—3 个最关键问题，不给代表性原话只问"说话人1是谁"是差评。
- **说话人确认闭环（用户原话要求 2026-08-12）**：批量确认未识别说话人时，逐人列出「推测身份 + 依据 + 原话摘录」再问是谁——"跟我确认的时候，一定要说他说了什么话"。模板与实战案例见 `references/speaker-confirmation.md`。
- **对话内直接称呼是高置信度说话人证据**：确认顺序＝直接称呼 > 自称单位 > 内容特征。例：波总喊"江总"问投屏 → 下一句应答者=江总；对方称"王总"且答问全是泽天融资/实缴细节 → 即波总。被喊姓氏（"张总"）也能锁姓，再与已知人名（张雨竹等）交叉核对。**但该启发式有边界（2026-08-16 纠错实战）**：股权/投资/合作**书面文件**（股权结构表/合同/筹划方案）里的"王总"≠自动=波总——跃壹科技筹划方案 19% 核心股东"王总"是**另一个王总**（波总原话"我指的是另外一个王总，千万不要把这个信息搞错了"）。规则：群聊对答/直接称呼场景的"王总"可锁=波总；**书面股权表/合同里的"X总"一律先标身份待确认**（建占位实体如 PER-068），除非用户明示，绝不写死=已知人物。
- **ASR 会把同一人的连续独白切成两个说话人标签**（2026-08-14 实测）：说话人1 说完"我第一份工作是中信证券"，说话人3 无缝接"第二份工作是…副总，去年去到现在的单位"——职业叙述首尾衔接=同一人（张克成）被切分，不是两个人。判定：相邻标签内容构成连贯单人叙述（我→我第二份→我去年）或一问一答对不上人时，标"说话人1/3 疑为同一人（转写切分）"，在映射表合并标注，**只建一张人脉卡**，不得给切分标签各建卡；用户附带的身份备注（转写末尾"这是X引荐，跟Y，职务，电话"）是最高置信度锁定证据，先读再定映射。
- 用户附带的 AI 摘要（"以上由AI大模型生成，可能包含不准确的信息"）只作参考，入库标"可能不准确"，不得当事实。
- **同一 source 分批发（续段+人物确认）**（2026-08-14 实测 SRC-20260814-007）：会面转写先到，随后用户隔条消息补"这是晚宴和华西证券的团队用餐"并逐说话人确认（2=王宇翔、3=吴琛亮、4=万东梅+执业证书编号/手机/邮箱）。处理：①**续段追加进同一 `_raw.md`**（同 source_id），不另开新 SRC——保证溯源链一条；②续段末尾的身份备注=最高置信度映射证据，直接回写 clean 映射表+既有人脉卡，不必再追问；③联系方式（手机/邮箱/执业证书号）进人脉卡 `特殊细节` 字段；④**清理"说话人N"占位实体**——已确认者更新实体行（PER-058 万东梅补全信息），占位实体改写为确认后人物（PER-061"华西经纪条线说话人2"→吴琛亮）或删除（PER-062"建行说话人3"并入吴琛亮卡），避免僵尸实体与真实人物并存；⑤新增人物建卡（吴琛亮）同步 README 总表（总人数+1）+entities+relations。
- 用户纠正后保留变更痕迹，搜索并同步所有受影响文件。

## 跨 AI 规则（SKILL）更新协议（2026-08-16 用户确认）

- Hermes skills（`~/.hermes/skills/<category>/<skill>/SKILL.md`）是跨 AI 共用的**规则层**（与仓库事实层互补），**规则类更新统一由 Hermes 用 skill_manage 落盘**（版本+patch 追踪），其他 AI 不直接写盘。
- 其他 AI（Codex/Cursor/Claude）发现需固化的规则（踩坑/方法论/流程变更）→ 写提议到仓库 `交接手记/规则更新提议.md`（要更新的 skill 名/要点/依据 source_id 或日期），Hermes 下次会话统一落盘并登记。
- 例外：紧急安全修复（如凭据泄露防护）可立即写盘，但须在 CURRENT_STATE 登记改动内容与时间。
- 已落盘规则修订走 patch 方式，不整文件重写。
- 历史既成事实：2026-08-16 Codex 直接写盘更新的 4 个 skill（cangjie-obs-agent / corporate-due-diligence / enterprise-due-diligence / cloud-browser-download）保留；后续更新一律改走本协议。

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

- `references/recording-intake-formats.md` — 录音转写入库具体格式速查（clean.md/拆解卡/台账/待办/INDEX 字段与 `[confirmed_fact｜KK]` 标注语法、validate 与提交检查清单；§6A 人脉卡含**利他清单（公/私）+ 可合作点双维度**模板，波总 2026-08-14 要求）
- `references/entity-index-evolution.md` — 实体索引+认知演化模块格式与维护（entities/relations/conflicts/evolution 字段与 ID 规则、初版全量扫描流程、每日增量规则、跨文件 ID 校验）
- `references/table-image-rendering.md` — 中文表格 → PNG 图片渲染配方（波总偏好表格出图，禁止 markdown 源码）
- `references/telegram-phone-control-diagnosis.md` — 用户手机 Telegram 遥控通道诊断（代理解析/pairing 授权/getUpdates 冲突陷阱）
- `references/speaker-confirmation.md` — 说话人身份确认闭环（逐人原话摘录模板 + 对话内直接称呼证据法 + 确认后全模块回写清单 + SRC-20260812-001 实战案例）
- `references/renmai-v2-spec.md` — 人脉管理 V2 规范速查（八维字段/6视图/互动日志/引荐闭环/迁移状态/课程映射）
- `references/topic-material-pack.md` — 主题素材包输出模板（只读梳理工作流的跨模块映射图/输出分节 schema/标记约定/2026-08-19 跃壹科技实战骨架）

## 陷阱

- **不要靠 Hermes memory / mem0 获取任务状态**——会过期；以仓库为准。
- 旧 hermes-adjutant（status.json）与 Cangjie_OBS_Notes 是两个不同事实源，别混。用户 2026-08-10 明确指定后者为长期记忆/人脉事实源。
- 过期日程不能自动标完成，先与用户核对实际结果（CURRENT_STATE 有专门待核对清单）。
- `TELEGRAM_ALLOWED_USERS=501` 是 macOS UID 陷阱，与 Telegram ID（9~10 位）不可混；波总 ID `8447296166` 在 pairing store 授权（见 hermes 侧资料）。
- **用户要"人脉表/归档表/总表/故障表"时，先读仓库约定格式再输出**：`人脉管理/README.md` 的 8 字段总表（姓名/角色/职业/地区/行业/影响力/亲密度/黄金人脉圈）+ `交接手记/SCHEMA.md` §3 全息背景卡。不要自创字段或结构。参考 `references/table-image-rendering.md`。
- **话题切换检测**：用户说"我已经不说X了/你没理解"时，立即丢弃旧话题锚点重新确认需求。真实案例（2026-08-10）：把"人脉故障表"误当成刚聊的雅典娜案工具表，实际用户要的是仓库里约定的人脉归档总表。不要因为当前聊天上下文有热点话题就臆断用户指代。
- **人脉档案必须登记进总表**：新建/更新 `人脉管理/<姓名>.md` 后检查 `人脉管理/README.md` 总表行 + 统计（总人数/密友/好友）同步。历史缺口：何福荣/刘锐/郑小康 3 份档案存在但未进总表，2026-08-10 已补录。
- **人脉卡全息字段缺失会被 validate 拦**：全息背景卡表格字段缺一不可（含 `爱好`，未知填 `—（待补充）`），缺了报 `缺少全息字段: <字段名>`（2026-08-14 实测新建刘主任卡漏 `爱好`）。格式见 `references/recording-intake-formats.md` §6A。
- **validate_repo.py 报错先判断是否本次引入**：已知历史遗留 = `obs-wiki/`（含 API key 存档）与 `2026年/` 旧目录约 109 个 ERROR + obs-wiki/raw 缓存 utf-8 解码错误，不阻塞提交。本次引入判定用定向 grep 而非 stash（新文件未跟踪时 stash 无效）：`python3 系统检查/validate_repo.py 2>&1 | grep -E "<本次文件名>"` 无输出，且对每个报错文件跑 `git status --short -- <报错文件>` 无匹配 = 全部历史遗留。**`git add -A` 前先确认未跟踪新增文件里没有密钥/敏感文件会被扫入**（2026-08-11 run 中密钥文件已被跟踪故安全；新增文件一律人工过目再 add）。完整检查清单见 `references/recording-intake-formats.md` §7。
- **用户更正人名/数字/事实 → 全模块传播协议**：用户纠正后（如 2026-08-11 尹建文→尹嘉雯），搜索全库所有出现处（`grep -rn "旧名" --include="*.md" .`），同步改：clean 稿、副官拆解卡、人脉卡、OPEN 待办、工作日志、CURRENT_STATE、处理台账（通常 6-8 个文件）；**`_raw.md` 正文保留原始 ASR 不动**（溯源链完整），只在 frontmatter 场景段加"用户更正"说明行；解除相关 `[待确认]` 标记并注明"用户已确认"。批量替换用 python3 脚本（逐文件 read+replace+write）比 patch 工具可靠，改完 `grep -rn "旧名"` 验证无残留（raw 正文例外，预期保留）再 commit+push。
- **ASR 人名/机构错乱更正（2026-08-14 实战）**：语音转写会把完全不同的词转成音近词——"李主任"→"刘主任"、"中心"→"中信"、"玉松"→"王玉松"。用户常以"应该是我说错了或者语音转文字错了"形式自纠。处理：①用户更正时先**确认是否同一人**（"刘主任"=李华清"李主任"），同人则**删除错误人脉卡（`git rm`）+ 把内容合并进正确卡**（全息字段/互动记录/下一步动作/利他清单/可合作点），而不是保留两张卡；②术语类错乱（中信→中心=西部转化中心直投）影响拆解卡/待办/日志中的业务理解，要逐处重读并同步改写相关行动项（如"中信直投300-700万"→"中心直投"）；③搜索范围除正文外还包括拆解卡标题、台账主题列、INDEX、OPEN 关联人物列。实战：SRC-20260814-005 整卡"刘主任"改写为李华清，删除 `人脉管理/刘主任.md`，8 处引用同步。
- **机构级 ASR 误记 → 网络穿透 + 实体合并（2026-08-16 实战）**：语音机构名"一保研究院"→ 实为"中材（南京）矿山研究院"。处理链：①用户怀疑 ASR 错误时先 web_search 验证机构真实性（"中国矿山研究院 南京"查无此名）；②**三要素匹配法**确认实体：地名（南京）+ 机构名（矿山研究院）+ 业务链（项目材料 29 课题清单单位=中材矿山四大区域公司）唯一命中中材（南京）矿山研究院（2021.11 成立、中材矿山建设全资子公司）；③穿透补实体：新增母公司/集团实体（中材矿山建设 ORG-087、中材国际 600970 ORG-088）+ relations 隶属关系，把碎片单位挂到链条；④**合并实体**：ORG-085（研究院）并入 ORG-038（改名中材（南京）矿山研究院），删除被合并 ID 后 `grep -rn "ORG-085"` 查残留引用并改 relations；⑤**PRJ 改名后 sweep 全部旧名引用**：PRJ-003"民防雷达"→"矿山边坡雷达"，grep 旧名找出 relations 3 处 + 人脉卡（张远）+ OPEN 待办逐处同步，不只改 entities 一行；⑥CURRENT_STATE「已确认的重要人脉/信息更正」节追加更正记录（旧称→实称+依据+日期），待确认清单同步移除已确认项；⑦历史拆解卡（SRC-20260811-001）保留原文不改（档案纪律），修正只写活文档；⑧validate（134 基线不变=零新增）+ commit。认知口径一并修正：数亿订单→立项≠订单（29 课题为立项清单）、自建产线→成熟设备采买+集成承接（商业模式认知修正进 PRJ/OPEN 备注）。
- **同日多素材必须交叉核对数字**：同一天处理第二份 source 前，先读同日已处理的拆解卡/清洗稿（如 SRC-20260811-002 处理前读 SRC-20260811-001），逐项比对金额/估值/年度口径；冲突处**不静默取其一**，双口径并列写进新拆解卡的未知扫描（ai_inference+置信度）与台账/CURRENT_STATE 待确认项。实测冲突（2026-08-11）：投前 5.5亿+3500万=投后 5.85亿 自洽 vs 001 卡"投前 5.45亿"；"去年营收 8400万" vs 001 卡"2025 营收 1.2亿"；今年净利 3300万 vs "2000多万~3000万"。另注意：自洽口径（5.5+0.35=5.85）可以标"自洽、疑为另一卡 ASR 误"，但仍是待确认。
- **待办归档要原子化**：OPEN.md 里跟踪的待办其底层事件一旦落地（如 T-20260811-006"华西约时间"→8/11 交流已发生），归档=**同一编辑里从 OPEN.md 删除行 + 追加到 `待办管理/DONE-YYYY.md`**，并在 DONE 行注明"后续转 T-XXXX 推进"。先追加 DONE 忘删 OPEN 会产生双写，改完 `grep -n "T-20260811-006" 待办管理/*.md` 验证只出现在 DONE。
- **日程疑似同一场事件的处理**：不同 source 描述的同一日期活动（8/13 投资对接会=省内20家+全国24家 vs 8/13 路演=约100人 15+5分钟）**保留两行并互标"疑为同一场待确认"**，不擅自合并；旧行被新信息取代时（如"8/14 后华西可能来访"→8/11 交流已落地）就地改写该行，不留过期行。
- **`_raw.md` 可能是未跟踪文件**：原始稿存在磁盘 ≠ 已在 git 里；提交前 `git status --short` 检查，未跟踪的 `_raw.md` 属本次任务文件一并 `git add -A`，不要以为它早已入库。
- **实体 ID 跨文件一致性（实体索引模块）**：relations.md/conflicts.md 引用的实体 ID（ORG-xxx 等）必须先存在于 entities.md。教训（2026-08-11 初版）：relations 初稿引用了未建卡的 ORG-023*/ORG-077*，被迫回补 ORG-076/077/078。写完 relations 后跑 `grep -oE '(PER|ORG|PRJ|FIN|MET|PLC)-[0-9]{3}' relations.md | sort -u` 与 entities.md 同法输出做 diff，零差集才提交。**追加 relations 前必须按实体名 grep entities.md 查真实 ID，禁止凭印象/上下文猜编号**（2026-08-14 实测：凭感觉把"华西证券"写成 ORG-046、把"绵阳"写成 PLC-006，实际华西证券=ORG-005、绵阳=PLC-003，ORG-046 是上海微小卫星、PLC-006 是广州南沙——错引到别的实体；一律先 `grep -n "实体名" 知识库/实体索引/entities.md` 拿到正确 ID 再写行，写完 `grep -c "ORG-046" relations.md` 复查无残留错误引用）。
- **表格行去重（实体索引模块）**：给 relations.md 追加行前先 grep 该行主键（如 `PER-012 刘锐`）是否已存在，避免 patch 后出现重复行（2026-08-11 实测出现一次，需回删）。
- **兄弟代理并发同库（2026-08-20 实测）**：Cangjie_OBS_Notes 与 hermes-adjutant 都有其他 AI/子代理并行写入（patch 会警告 `was modified by sibling subagent '...'`，git log 出现你没写的 commit——本会话副官 T100、OPEN.md T-027/T-019 御沪落地都被兄弟代理先写入）。对策：①**追加行前先 grep 目标行是否已含要写的内容**，已含就跳过（重复写会双行）；②写完 patch 核对 diff——重复行/误删行即时修复（本会话互动日志孙捷行被重复追加两次，`tail`+patch 去重；替换多行块时 new_string 必须保留所有未改行，曾误删「此前履历」行靠 diff 发现回补）；③**批量 terminal heredoc 写多文件可能触发审批 BLOCKED**（"user has NOT consented"），勿重试勿换命令绕——改用逐文件 patch（markdown 表格行）或单文件小命令，仍被拦就停下来问波总；④提交前 git pull，commit 只 add 本次文件，push 后 git log 复查无遗漏。
- **patch 工具引号转义失败（escape-drift）**：old_string/new_string 含 `\"` 字面量时报 "Escape-drift detected" 拒绝匹配。仓库 md 大量含引号，patch 时去掉反斜杠转义，或改用无引号锚点（如只锚标题行 `## 使用规则`）；仍失败就用 python3 逐文件 read+replace+write（本仓库多 AI 并发下该路径已验证最可靠）。
- **`_raw.md` 必须满足 validate schema**：frontmatter 缺 `source_format/confidentiality/raw_integrity`、`type` 不是 `voice_transcript`、正文缺 `## 原始转写` 标题都会报"缺少原始素材字段"（2026-08-12 实测）。按 `references/recording-intake-formats.md` §0 模板落盘。
- **拆解卡章节标题是 validate 逐字匹配的固定字符串**：必须用阿拉伯数字编号 `## 1. 新增信息` / `## 2. 新增认知` / `## 3. 行业谈资` / `## 4. 待研究课题` / `## 5. 未知扫描` / `## 6. 行动与回链`（一个都不能少、不能改成中文序号"一、"或加副标题），frontmatter 必须含 `type: adjutant_digest`、`event_date`、`processed_at`，否则报"缺少副官拆解字段/type 应为 adjutant_digest/缺少章节"（2026-08-14 实测用中文序号一次报 6 个错，被迫整卡重写）。同理 `_raw.md` 需 `## 场景` + `## 原始转写` 两级标题、`_clean.md` 需 `## 参与人与说话人映射`/`## 事实、观点与推测`/`## 处理去向`——全部按 `references/recording-intake-formats.md` §0-2 模板先对齐再落笔，别等 validate 报错再改。
- **派 Cursor 执行的可用方式（2026-08-16 实测）**：`delegate_task(acp_command=cursor-agent)` 旧写法在当前 schema **不存在**（acp_command/acp_args 参数无效），实测可用的是终端直调：`cd <仓库> && cursor-agent -p --yolo "$(cat /tmp/prompt.md)"`（background=true + notify_on_complete=true）。prompt 文件给全上下文（绝对路径命令+精确 patch 说明+校验+提交+回执要求），已定稿内容注明只落位不改写；大任务 2-8 分钟；完成后必须亲自验证（git log/validate/文件落位）。见 skill `cursor-default-executor`（bundled，不可改，其旧调用描述已过时）。
- **cursor-agent 启动即崩排查（2026-08-20 实测）**：`cursor-agent -p --yolo` 秒退、日志只有 `/Users/mac/.openclaw/completions/openclaw.zsh:3803: command not found: compdef`。根因：`~/.zshrc` 第 5 行**无条件** source openclaw.zsh（130KB 补全脚本，其 3803 行用 `compdef`，非交互 zsh 未跑 compinit 时该函数未定义）；cursor-agent 是 bash wrapper→node（`file /opt/homebrew/bin/cursor-agent` 可见），内部 spawn 的 zsh 照读 ~/.zshrc——`zsh -f` 和 `ZDOTDIR=/tmp/empty` **都绕不过**（node 显式加载用户配置）。修复：~/.zshrc 的 source 行加交互守卫 `if [[ -o interactive ]]; then source ...; fi`（用户 shell 配置，改前备份、需波总同意——2026-08-20 波总选择自行处理）。诊断链：`file /opt/homebrew/bin/cursor-agent` → `grep -rn openclaw ~/.zshrc` → `sed -n '3800,3805p' ~/.openclaw/completions/openclaw.zsh`。启动失败即按降级链 🟢 Hermes 原生跑完全流程（波总 2026-08-20 认可），不要死等 Cursor。
- **接手其他 AI（Codex 等）沙盒未完成的工作（2026-08-15 实战）**：Codex 沙盒无法认证私有仓库时，会把产物留在「持久文件区」=`~/.hermes/cache/documents/`（如 `人脉课程全量整理.md`），会话 rollout 在 `~/.codex/sessions/` 但沙盒内会话可能不落盘。接手流程：①`git status` + `git log` 确认仓库侧到底缺什么（对方汇报的「已完成」可能只在 Notion/沙盒，GitHub 侧一条提交都没有）；②用 mdfind/find 定位产物（搜课程名/素材名而非泛搜，全盘 find 会超时）；③Hermes 出设计稿到 /tmp/（内容设计是监工职责），再派 Cursor 落位+validate+commit+push——本机 git remote URL 自带凭据，push 私有仓库无障碍（Codex 不行是本机可）。未提交内容必须明确「尚未入库」。
- **读取 Codex/另一 AI 的活动与进度（2026-08-16 实测）**：用户问"X 更新到哪一步了/在做什么"时按序定位：①`~/.codex/.codex-global-state.json`（最近线程 ID + `thread-descriptions-v1` 描述 + `prompt-history` 最近提问，判断最近在做什么）；②`~/.codex/sessions/YYYY/MM/DD/*.jsonl`（会话落盘，按 mtime 找当日/近期）；③`~/.codex/rules/default.rules`、`~/.codex/automations/*/automation.toml`（规则与自动化心跳，注意 `status = "PAUSED"` 是已停用）；④**改了什么规则**：`find ~/.hermes/skills -name "SKILL.md" -mmin -600` 看 skills mtime——其他 AI 直接写盘更新 SKILL.md 时这是唯一痕迹（实测 13:30-14:09 Codex 更新 4 个 skill，无 git 历史）；⑤`ps aux | grep codex` + `~/.codex/logs_2.sqlite` mtime（App 是否活跃）；⑥**无痕迹≠没在做**——Codex App 云端会话可能不落盘，查不到时如实说"未发现当日会话文件"，请用户提供进度来源（如 App 界面截图），不要硬编结论。规则更新内容读 SKILL.md 尾部新增条目（通常带日期标注）。
- **非转写类素材（课程/文档/PDF 提取文本）入库**：type 可用 `course_material` 等（validate 只查字段存在性，不查枚举值），但 validate 强制 raw 必有 clean 稿+拆解卡+台账+INDEX 登记，与录音素材同等对待。raw 结构照旧：frontmatter 8 字段 + `## 场景`（说明来源/用途）+ `## 原始转写`（原文全量）；clean 稿的「说话人映射」节改为「参与者/来源映射」（讲师/整理者），事实分层照用 `[confirmed_fact｜课程原文]` 等标注。95K 级大文件直接 `cat 头部 frontmatter + 原文 > _raw.md` 拼接，不要重写。
- **通用头衔身份歧义：书面文件里的"X总"≠自动=已知人物（2026-08-16 纠错）**：跃壹科技筹划方案股权表"王总 19%"被误标为波总，写入拆解卡/clean/entities/relations/OPEN/CURRENT_STATE 共 6 处后用户纠正"是另外一个王总"。处理：①股权结构/合同/筹划文件中的股东名（王总/唐总/刘总）先建占位实体标 `[待确认]`（如 PER-068），**禁止在无明示情况下映射到波总/已知人物**；②用户一旦纠正身份，按「用户更正→全模块传播协议」sweep 全部出现处（`grep -rn "王总（=波总）"` 之类旧写法逐文件改）；③修正脚本必须**幂等**（每处替换前 `if "旧串" not in content` 守卫），避免半途失败重跑时报 NOT FOUND；④改完 `grep -rn "旧写法"` 验证零残留再 commit。
- **合并本地未提交工作到已推进的远端（通用 git 技巧，2026-08-16 实测）**：本地工作区有旧功能改动而远端领先 N commits 时：①`git status --short` 盘点，M 修改与 ?? 未跟踪分开看；②`git stash push -m "wip-<功能>-<日期>" -- <具体M文件>`——**勿用 `git stash -u`**（会把 .codex/、data/、实验残留等未跟踪杂项一起卷进 stash）；③`git pull origin <branch>` → `git stash pop`（改动点不重叠则零冲突）；④功能依赖的新未跟踪文件（被 import 的库/测试）先 `grep -n "模块名" 组件文件` 确认再一并 `git add`；提交前人工过目未跟踪列表，禁止 `git add -A`；⑤先跑功能测试再全量回归再提交。判定"开发完没提交" vs "烂尾"：有配套测试 + 改动自洽 + 符合仓库规范 = 值得救（实测救活 7/2 文字稿上传功能 280 行，零冲突合并 19 commits）。
- **python3 批量更新脚本两个坑（2026-08-16 实测）**：①**中文引号陷阱**——`python3 - <<EOF` heredoc 里 python 双引号字符串嵌入全角引号（"准备测试"）会提前闭合字符串报 SyntaxError；改用 write_file 写脚本文件再 `python3 /tmp/x.py` 执行；②**非幂等脚本重跑陷阱**——替换脚本第一步成功后中断，重跑时第一步的 old 串已不存在 → assert NOT FOUND 抛错，后面步骤全没执行；每步加 `if "marker" not in content` 守卫 + 每步 print 结果，半途失败可安全重跑（或拆成"已完成部分跳过"的两段脚本）。
- **随行落库 + 外部 AI 深度分析模式（波总 2026-08-16 明确）**：波总提供群聊/文件/早期信息时，指令是"先随行落库（raw+clean+拆解卡+实体+待办），再由另一个 AI（Codex 等）引入做全面分析"。处理：①**立即落库防丢**（不等分析完成），落库与交付并行；②同时产出**可复制粘贴的自包含提示词**给 Codex——Codex 无对话上下文，必须自带全部背景（关键数据表/股权结构/金额/时间线/约束）；③提示词结构：任务定义 → 背景全景 → 数据表 → 请分析的决策问题清单（如注册地矩阵/资金闭环/换股条款/行动清单）→ 输出要求（结论先行、事实vs推断标注、3 条最值得记住+3 个待解决问题）；④群回应/谈判类文案若需要，另行起草，不混入分析提示词。
