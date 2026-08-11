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
9. 本次任务相关的人脉档案、日志、原始素材和知识卡

回答"今天/接下来见谁"时：时间地点 → 人物背景 → 上次聊了什么 → 双方承诺 → 未完成事项 → 本次注意事项（按 `跨AI协作协议.md` 的检索顺序）。

## Step 3: 素材处理八步流程（录音/口述/会议/截图转写）

1. **保存原始稿**：`原始素材/录音转写/YYYY/MM/*_raw.md`，生成唯一 `source_id`（`SRC-YYYYMMDD-NNN`），**原文不删减、不覆盖**。
2. **登记台账**：`原始素材/处理台账.md`，状态 `received`。
3. **清洗稿**：`*_clean.md`，修正明显 ASR 错误；不确定片段保留原文并标 `[待确认]`，**不得把猜测写成事实**。
4. **分层提取**：客观事实 / 王波判断 / 他人观点 / AI 推测，四层分开。
5. **副官拆解卡**：`知识库/副官拆解/YYYY/MM/SRC-*.md`，固定六维（新增信息/新增认知/行业谈资/待研究课题/未知扫描/行动与回链），更新 `INDEX.md`。
6. **同步正式模块**：工作日志、人脉档案、日程、待办、知识/认知卡按需更新。
7. **回链**：正式记录写 `source_id`；台账列全 `derived`。
8. **校验提交**：`python 系统检查/validate_repo.py` 通过后 `git commit + push`。

清洗稿与拆解卡的具体字段/表格/标注语法（说话人映射表列、frontmatter、`[confirmed_fact｜KK]` 等标注、台账/待办/INDEX 行格式、校验与提交检查清单）见 `references/recording-intake-formats.md`——录音转写入库时先读该文件，格式与仓库模板对齐再落笔。

## 知识边界标签

- `KK` 已确认已理解 / `KU` 已知问题答案不明 / `UU` 未知之未知候选（必须标置信度+验证办法，不得写成事实）。
- 合规/法律/税务/医疗/投资结论标"待专业核验"。

## 确认原则

- 明确事实先沉淀；姓名/说话人/日期/金额/身份/合规结论有歧义 → 标待确认。
- 一次最多追问 1—3 个最关键问题，不给代表性原话只问"说话人1是谁"是差评。
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
- `references/table-image-rendering.md` — 中文表格 → PNG 图片渲染配方（波总偏好表格出图，禁止 markdown 源码）
- `references/telegram-phone-control-diagnosis.md` — 用户手机 Telegram 遥控通道诊断（代理解析/pairing 授权/getUpdates 冲突陷阱）

## 陷阱

- **不要靠 Hermes memory / mem0 获取任务状态**——会过期；以仓库为准。
- 旧 hermes-adjutant（status.json）与 Cangjie_OBS_Notes 是两个不同事实源，别混。用户 2026-08-10 明确指定后者为长期记忆/人脉事实源。
- 过期日程不能自动标完成，先与用户核对实际结果（CURRENT_STATE 有专门待核对清单）。
- `TELEGRAM_ALLOWED_USERS=501` 是 macOS UID 陷阱，与 Telegram ID（9~10 位）不可混；波总 ID `8447296166` 在 pairing store 授权（见 hermes 侧资料）。
- **用户要"人脉表/归档表/总表/故障表"时，先读仓库约定格式再输出**：`人脉管理/README.md` 的 8 字段总表（姓名/角色/职业/地区/行业/影响力/亲密度/黄金人脉圈）+ `交接手记/SCHEMA.md` §3 全息背景卡。不要自创字段或结构。参考 `references/table-image-rendering.md`。
- **话题切换检测**：用户说"我已经不说X了/你没理解"时，立即丢弃旧话题锚点重新确认需求。真实案例（2026-08-10）：把"人脉故障表"误当成刚聊的雅典娜案工具表，实际用户要的是仓库里约定的人脉归档总表。不要因为当前聊天上下文有热点话题就臆断用户指代。
- **人脉档案必须登记进总表**：新建/更新 `人脉管理/<姓名>.md` 后检查 `人脉管理/README.md` 总表行 + 统计（总人数/密友/好友）同步。历史缺口：何福荣/刘锐/郑小康 3 份档案存在但未进总表，2026-08-10 已补录。
- **validate_repo.py 报错先判断是否本次引入**：已知历史遗留 = `obs-wiki/`（含 API key 存档）与 `2026年/` 旧目录约 109 个 ERROR + obs-wiki/raw 缓存 utf-8 解码错误，不阻塞提交。本次引入判定用定向 grep 而非 stash（新文件未跟踪时 stash 无效）：`python3 系统检查/validate_repo.py 2>&1 | grep -E "<本次文件名>"` 无输出，且对每个报错文件跑 `git status --short -- <报错文件>` 无匹配 = 全部历史遗留。**`git add -A` 前先确认未跟踪新增文件里没有密钥/敏感文件会被扫入**（2026-08-11 run 中密钥文件已被跟踪故安全；新增文件一律人工过目再 add）。完整检查清单见 `references/recording-intake-formats.md` §7。
