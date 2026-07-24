---
name: meeting-intelligence
description: 会议录音/转写→结构化情报库。识别说话人、秒级分段、提取金句、建SQLite索引、支持语音声纹匹配。当波总发送会议音频、转写文字、或说"会议入库""建档案"时使用。
---

# Meeting Intelligence — 会议转写→结构化情报

## 触发条件

- 波总发送会议录音文件（.m4a/.mp3/.wav）
- 波总发送转写文字（含说话人标签 + 时间戳）
- 说"入库""建档""存档""记录下来"
- 说"这个对话里有几个要点帮我提取"

## 参考文件

- `references/db-schema.md` — 完整数据库 Schema（5 表 + ER 关系 + 常用 SQL 查询）
- `references/speaker-profiles.md` — 已知说话人档案（特征、风格、识别线索）
- `/Users/mac/company-archive/scripts/init_db.py` — 数据库建表脚本（可复用于新库初始化）
- `/Users/mac/company-archive/scripts/seed_meeting.py` — 单会议入库脚本（传入转写路径+meeting_id+说话人映射JSON）
- `/Users/mac/company-archive/scripts/seed_all.py` — 批量入库脚本

## 目录结构

```
/Users/mac/company-archive/
├── audio/              # 原始录音
├── photos/             # 现场照片
├── transcripts/        # 转写文字 (.md)
├── exports/            # 导出：会议摘要、金句集锦、PDF
├── index.db            # SQLite 主索引库
├── scripts/            # 辅助脚本
└── README.md
```

## 入库流程

### 1. 收到转写文字时

先存原始文件到 `transcripts/YYYY-MM-DD_主题.md`，然后：

```
1. 识别说话人 → 波总确认
2. 逐段解析：说话人 + 时间戳 + 内容
3. 标记金句（is_quote=1）
4. 写入 segments 表（秒级时间戳）
5. 金句同步写入 quotes 表
6. 更新 speakers 表统计
```

### 2. 收到音频文件时

```
1. 存到 audio/ 目录
2. 如果已有转写 → 直接入库
3. 如果没有转写 → 用 Whisper 转写 → 再做入库
4. 声纹匹配：对比已有 speakers 的声纹特征，自动标注说话人
```

### 3. 分段规则

- 每次说话人切换 = 一个 segment
- 保留原始时间戳（HH:MM:SS 格式）
- 超过 300 字的长段发言可以考虑再切分
- 短于 15 字的回应通常不计入 quotes

### 4. 金句判定标准

标记为金句（is_quote=1）的条件（满足任一即可）：
- 包含明确的战略/决策表述（"Plan A 是……"）
- 包含价值观宣示（"最重要的是……"）
- 包含独特比喻或浓缩观点（"资本市场都是喝血的"）
- 包含行动承诺（"我现在就去……"）
- 包含自我批评/反思

## 关键约束

- 金句表每个 entry 的 quote_text 必须完整，不截断（用原文原句）
- segment 的 start_time/end_time 保留原始时间戳格式
- 所有文件命名为 `YYYY-MM-DD_主题.扩展名`
- 每次入库后打印统计确认（segments × 数量，quotes × 数量）
- 说话人识别时，同一个人跨会议必须用统一名称（不能"邓老师"和"老邓"混用）

## 查询示例

```sql
-- 查某人的所有金句
SELECT * FROM quotes WHERE speaker_name = '邓老师' ORDER BY created_at;

-- 查某次会议的全部发言
SELECT speaker_name, start_time, content FROM segments WHERE meeting_id = '2026-06-13_资产注入路径讨论';

-- 跨会议关键词检索
SELECT m.title, s.speaker_name, s.content FROM segments s
JOIN meetings m ON s.meeting_id = m.id
WHERE s.content LIKE '%借壳%';
```

## Absorbed Skills

| Former Skill | Now In |
|-------------|--------|
| meeting-transcript-archive | `references/meeting-transcript-archive.md` |

## Pitfalls

- **大文本保存**：Telegram 消息中的超长转写文字必须完整写入文件，不能只写头部/摘要！本次 session 曾把会议3的完整转写写成1091字节的元数据头部，导致入库脚本读到0段。
- B站的搜索API返回的results结构可能为空但numResults>0，需要二次探测实际数据路径
- 不同会议的"说话人1/2"编号不固定对应同一人，每次都需要重新确认
- 金句太多（>50%发言）说明标准太松，正常比例~20-30%
- 中西方对比类讨论容易跑题，只入库产业相关部分
- 照片从 Telegram 收到后，从 ~/.hermes/profiles/her-m2/image_cache/ 复制到 company-archive/photos/，同时 INSERT 到 photos 表