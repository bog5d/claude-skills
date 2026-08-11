# 实体索引 + 认知演化模块（初版全量扫描与增量维护）

对应 `交接手记/SCHEMA.md` §9（实体索引）/ §10（认知演化）/ §11（日报）。2026-08-11 完成初版全量扫描（commit e46efde9，7 文件 +714 行）；**之后只做增量，不重扫全库**。

## 四个文件

| 文件 | 作用 |
|---|---|
| `知识库/实体索引/entities.md` | 实体主表，按类型分组 |
| `知识库/实体索引/relations.md` | 实体关系表 |
| `知识库/实体索引/conflicts.md` | 跨素材矛盾登记 |
| `知识库/认知演化/evolution.md` | 认知演化记录 |

## entities.md — 实体主表

- 按 type 分组（person/org/project/finance_tool/metric/place），每组一个表格，表头含 type 列。
- 列：`id | type | name | aliases（ASR/OCR 变体）| first_seen | last_updated | sources | 备注`
- ID 前缀：`PER-`/`ORG-`/`PRJ-`/`FIN-`/`MET-`/`PLC-` + 3 位序号，全文件唯一。
- **aliases 必填 ASR/OCR 变体**（关联发现的关键输入，遗漏会导致后续实体无法合并）。仓库实测别名：华一证券→华西证券、长发展→川发展、天府金云/天府新语、唐总/谭总→唐津、陈昊→陈昱、青区→青羊区、尹建文/尹君文→尹嘉雯、硕神（刘硕微信名）、零（徐江微信名）、客户715（中船715所）。
- 未确认实体照收：名称标 `[待确认]`（说话人3/4/5/6、夏红建、莆田、小边、陈飞、吴总、兴业随行人员等），不得因信息不足直接丢弃——后续关联发现靠这些锚点。
- `first_seen` = 首次出现的 source_id/日期；`last_updated` 每次触碰即更新；`sources` 可写 source_id 或仓库相对路径。

## relations.md — 关系表

- 分组：person→org（任职/合作）、person↔person（引荐/交流/协作）、org→project（投资/承接）、metric→org（财务口径）、org→org（股东/体系/关联）。
- 列：`type | from | to | source | confidence | 备注`。
- confidence 规则：用户确认/名片确认/工商核验=**高**；单方会议口径或明确待确认=**中**；推测/ASR 存疑=**低**。
- from/to 用实体 ID（PER-xxx/ORG-xxx），比裸名称更利于机器关联；未建卡实体同样要先在 entities.md 建条目。

## conflicts.md — 矛盾登记

- 条目编号 `C-NNN`（C-001 起），状态 `open`/`in_progress`/`resolved`。
- 每个矛盾：双口径都保留、各标 source；写明判断（如"两素材投后一致、投前差 500 万"）与验证动作（"以投资协议为准"）。
- 解决后移入"历史已解决项"留档，不删除。
- 初版扫描时把 CURRENT_STATE/拆解卡已知待确认项全部捞入（2026-08-11 初版：C-001~C-025，覆盖投前估值 5.45/5.5 亿、2025 营收 1.2亿/1.3亿/8400万、净利 -1800万/3300万/2000多万~3000万、实缴 675/700/721万、注册资本、王玉松任职单位、股改税务递延口径、8/13 两会是否同一场、ASR 名称等）。

## evolution.md — 认知演化

- 条目 `INS-YYYYMMDD-NNN`：日期为**登记日**（跨素材统一顺排，不按认知来源日）；必填：insight_id、状态、一句话认知、首次来源、修正历史。
- 状态机：`active`（当前有效）/ `revised`（被纠正，旧表述保留）/ `confirmed`（推测被新素材证实）/ `superseded`（被完全取代）。
- 触发登记：新素材认知与旧认知不一致、被用户纠正、被专业核验推翻 → revised/superseded，**旧表述保留不删**，修正历史记日期/新表述/修正原因/来源。
- 金融/税务/合规类认知即使被会议纠正，新口径仍是"会议观点待专业核验"，登记时注明（例：INS-20260811-023 股改税务"递延到退出"→"与退出无关"，指向 conflicts.md C-010 与待办 T-20260810-003/T-20260811-012）。
- 认知卡（`知识库/认知/`）与演化记录互链：认知卡 frontmatter 可加 `evolution: INS-xxx`。

## 初版全量扫描流程（2026-08-11 实测）

1. 协议读取：START_HERE → CURRENT_STATE → 跨AI协作协议 → SCHEMA（**重点 §9/§10/§11 新增规范**）→ 副官拆解 INDEX → 处理台账。
2. 数据源扫描：全部拆解卡（SRC-*，新增认知/新增信息是实体富矿）→ 全部人脉卡 → 金融工具卡 → 认知卡 → 工作日志 → OPEN/UPCOMING → 关键方案。**raw/clean 稿用于查 ASR 原貌**（"华一证券""长发展"等别名只在 raw 里出现，clean 已纠正——别名表必须回 raw 挖）。
3. 冲突清单先行：把已知矛盾/待确认项先列进 conflicts.md 草稿，再回填 entities/relations（保证口径不遗漏）。
4. 实体去重归并：同一实体跨素材出现（川发展 vs 四川省科创投、说话人3 跨两场会议）建一条实体、aliases 收变体，关系指向同一 ID。
5. 书写顺序：entities.md → relations.md（**引用的 ID 必须已在 entities 中**）→ conflicts.md → evolution.md。
6. 同步登记：SCHEMA §9/§10 补"实施状态"行（不改核心结构）、处理台账加"模块初始化动作登记"节、CURRENT_STATE 系统状态补一条。
7. 校验：`validate_repo.py` 109 个历史 ERROR 是 obs-wiki/API key 旧目录，与本次无关；定向 `grep -E "实体索引|认知演化|SCHEMA|处理台账|CURRENT_STATE"` 确认自己文件零报错。
8. 提交：`git add -A && git commit -m "add: 初始化实体索引+认知演化模块（全量初版）" && git push origin main`。

## 每日增量维护规则

- 每份新拆解卡/人脉卡/知识卡处理完后：新增实体入 entities.md（first_seen=该 source_id）；新关系入 relations.md；新矛盾/新待确认入 conflicts.md；拆解卡"新增认知"提炼入 evolution.md（INS 按登记日顺排）。
- 修订已有认知 → evolution.md 标 revised + 修正历史，同时视情况在 conflicts.md 加 C-XXX。
- 更新实体时同步刷 last_updated；每日日报"新认知"栏目从 evolution.md + 当日拆解卡取数（SCHEMA §11）。

## 陷阱

- **跨文件 ID 一致性**：写完 relations/conflicts 后跑
  `grep -oE '(PER|ORG|PRJ|FIN|MET|PLC)-[0-9]{3}' relations.md | sort -u` 与 entities.md 同法输出 diff，零差集才提交（2026-08-11 初版实测：relations 引用了未建卡的 ORG-023*/ORG-077*，回补 ORG-076/077/078）。
- **追加表行前去重**：grep 主键确认不存在再 patch（2026-08-11 实测出现重复行需回删）。
- 不编造实体/关系：无来源的标 confidence=低 + `[待确认]`；人名按用户已确认写法，未确认标 `[待确认]`。
- ASR 别名表遗漏 = 后续实体无法合并，宁可多收、标待确认。
- 秘密绝不写入（沿用仓库安全铁律：Token/密码/证件/银行卡）。
