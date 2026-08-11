# 录音转写入库——具体格式速查（2026-08-11 SRC-20260811-001 实战校准）

波总录音/口述转写入 Cangjie_OBS_Notes 时各产出文件的确切字段与标注语法。以本文件 + 仓库 `原始素材/模板/录音清洗稿模板.md` 为准。

## 1. 清洗稿 `*_clean.md`

frontmatter：

```yaml
---
source_id: SRC-YYYYMMDD-NNN
type: cleaned_transcript
status: cleaned
event_date: YYYY-MM-DD
cleaned_at: YYYY-MM-DD HH:MM Asia/Shanghai
review_status: unreviewed
---
```

正文固定节：`## 清洗说明` → `## 参与人与说话人映射` → `## 清洗后文本` → `## 事实、观点与推测` → `## 处理去向`。

- 说话人映射表列：`| 说话人 | 推测身份 | 依据 | 置信度 | 用户确认 |`（用户确认列必须显式写"是/否"）。
- 清洗说明规则：只修正明显 ASR 错字/断句/已确认姓名；不确定数字/人名/机构名保留原意并标 `[待确认]`；AI 推测标 `[推测｜置信度：低/中/高]`。
- 用户纠正/补充：原始稿 frontmatter 保留"用户补充/用户纠正"原话；清洗稿正文在纠正处标 `（用户纠正）`。
- 无法还原的 ASR 碎片（人名、金额、机构名）：按原意保留 + `[待确认]`，不猜写。碎片过多时可在段落后加 `> 说明：…` 汇总"可确认信息 vs 存疑信息"。
- 对话末尾用户确认句（如"这是我和XX的对话"）保留在正文末尾。

## 2. 副官拆解卡 `知识库/副官拆解/YYYY/MM/SRC-*.md`

frontmatter：

```yaml
---
source_id: SRC-YYYYMMDD-NNN
type: adjutant_digest
status: processed
event_date: YYYY-MM-DD
processed_at: YYYY-MM-DD Asia/Shanghai
---
```

六段式固定标题：`## 1. 新增信息` / `## 2. 新增认知` / `## 3. 行业谈资` / `## 4. 待研究课题` / `## 5. 未知扫描` / `## 6. 行动与回链`。

标注语法（每段每条前缀）：

- `[confirmed_fact｜KK]` 已确认事实（对话中明确、用户确认或双方一致）
- `[third_party_view｜KU]` 他人观点（如银行/券商人员口径）
- `[user_judgment｜KK/KU]` 王波判断（KK=已确认、KU=待验证）
- `[ai_inference｜UU｜置信度]` AI 推测（未知之未知候选，**必须带置信度 + 验证动作**）

第 5 段每条写 `[ai_inference｜UU｜中置信度] … 验证：<具体动作>`。第 6 段以"- "列出行动项并写 `同步：<文件路径>；<文件路径>…` 回链。

INDEX.md 行格式（数字 = 各段条目数）：

```
| 日期 | source_id | 场景 | 新增信息 | 新增认知 | 谈资 | 待研究 | 未知候选 | 拆解卡 |
| 2026-08-11 | SRC-20260811-001 | 浙商银行张远办公室交流 | 11 | 7 | 6 | 6 | 5 | [查看](2026/08/SRC-20260811-001.md) |
```

## 3. 处理台账行格式

| source_id | 日期 | 主题 | 原始稿 | 清洗/分析稿 | 状态 | derived | 待确认/缺口 | 最后处理 |

- `derived` 写全部产出文件路径（分号分隔）；`待确认/缺口` 列必须列全存疑项，方便后续核对。

## 4. 待办 OPEN.md 行格式

`| ID | 优先级 | 事项 | 截止时间 | 状态 | 下一步动作 | 关联人物 | 来源 |`；ID = `T-YYYYMMDD-NNN`（按当日续号）；来源列 = source_id 链（如 `SRC-20260811-001`）。frontmatter `as_of` 同步刷新。

## 5. 日程 UPCOMING.md

- frontmatter `as_of` 刷新；新行程一律 `暂定`（`confirmed/tentative/cancelled/completed` 四态），未确认的对话提及行程（如"明天下午XX要过来"）按对话日期推算并标"日期/人员待确认"。

## 6. CURRENT_STATE.md 刷新

- `as_of` 刷新；新增素材节（已完成同步列表 + 待确认项清单 + 风险说明）；`接手下一步` 更新为当前待确认问题清单；已确认的人脉/信息更正追加进对应节。

## 7. 校验与提交检查清单（2026-08-11 实战校准）

已知历史遗留（不阻塞提交）：`obs-wiki/`（含 API key 存档，约 109 个 ERROR + `.graphify` 缓存 utf-8 解码错误）与 `2026年/` 旧目录。

本次引入判定（比 stash 后重跑更精准，新文件未跟踪时 stash 无效）：

```bash
python3 系统检查/validate_repo.py 2>&1 | grep -E "<本次文件名|SRC-20260811" || echo "本次文件零错误"
python3 系统检查/validate_repo.py 2>&1 | grep -oE "^ERROR: [^:]+: [^ ]+" | awk '{print $NF}' | while read f; do git status --short -- "$f" | grep -q . && echo "本次变更含: $f"; done
```

- 第二段无输出 = 报错文件均不在本次变更集 → 可提交。
- **`git add -A` 前检查**：确认未跟踪新增文件里没有密钥/敏感文件会被扫入；本次 run 中密钥文件早已被 git 跟踪（`git ls-files` 可查），安全。
- commit message 惯例：`update: SRC-YYYYMMDD-NNN <主题>处理（清洗稿+副官拆解+日志/人脉/待办/日程/知识卡同步）`；只提交本次任务文件。
- 回执中如实说明"校验 N 个 ERROR 均为历史遗留，本次文件零错误"。

## 8. 高风险表述处理

原始稿保留原话 → 清洗稿标注性质（如"属银行风控知识，仅作谈资，不构成操作建议"）→ 知识卡写"不得作为操作方案；只接受银行书面合规路径" → 待办不出现"取现/回流"类可执行描述。涉及规避监管/隐匿资金的说法永不加工成步骤。
