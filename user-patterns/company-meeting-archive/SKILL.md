---
name: company-meeting-archive
description: 公司会议数字档案库——接收转写文字、入库SQLite、解析说话人、提取金句、关联照片。当波总发送会议录音/转写文字/现场照片时使用。
version: 1.0.0
triggers:
  - 波总发送会议转写文字（"说话人1 00:00:01 ..."格式）
  - 波总发送现场照片
  - 波总要求"建库""入库""整理会议"
  - 波总发送音频文件（待transcribe）
---

# 公司会议数字档案库

## 档案库位置

```
/Users/mac/company-archive/
├── audio/              # 原始录音 (.m4a/.mp3/.wav)
├── photos/             # 现场照片，命名: YYYY-MM-DD_主题_序号.jpg
├── transcripts/        # 转写文字，命名: YYYY-MM-DD_主题.md
├── exports/            # 导出产物（摘要/金句集锦/PDF报告）
├── index.db            # SQLite 索引库
├── scripts/            # 辅助脚本
│   ├── init_db.py      # 初始化数据库表结构
│   ├── seed_meeting.py # 单会议入库
│   └── seed_all.py     # 批量入库
└── README.md
```

## SQLite 表结构

| 表 | 用途 | 关键字段 |
|----|------|---------|
| meetings | 会议元数据 | id(YYYY-MM-DD_主题), date, title, attendees, tags |
| speakers | 说话人档案 | name(唯一), role, voice_profile, sample_count |
| segments | 发言片段 | meeting_id, speaker_name, start_time, content, is_quote |
| quotes | 金句 | segment_id, speaker_name, quote_text, category |
| photos | 照片索引 | meeting_id, file_path, people_in_frame, is_key_photo |

## 入库流程

### Step 1: 接收素材

波总通过 Telegram 发送：
- 转写文字（通常是"说话人N HH:MM:SS\n内容..."格式）
- 照片（直接发送图片）
- 音频文件（后续处理）

### Step 2: 保存文件

**⚠️ 关键陷阱：大文本必须完整保存，不能只写头部元数据！**

```bash
# 转写文字
write_file /Users/mac/company-archive/transcripts/YYYY-MM-DD_会议主题.md

# 照片（从 image_cache 复制）
cp ~/.hermes/profiles/her-m2/image_cache/img_xxx.jpg \
   /Users/mac/company-archive/photos/YYYY-MM-DD_主题_序号.jpg
```

### Step 3: 识别说话人

根据内容特征判断谁是谁：
- **上下文锚点**：谁在提问/回答？谁在长篇大论？
- **已知事实匹配**：提到"5年千万10年过亿"→ 波总；提到"中医/脾胃"→ 可能是邓老师
- **语气风格**：导师语气、警告资本风险 → 邓老师/唐总；乐观讨论资金方 → 波总
- **人名引用**：说话人提到"唐总""洪斌"→ 排除自己是唐总/洪斌

**铁律：不确定的说话人必须先问波总确认，不要猜！**

### Step 4: 解析转写文字

正则匹配模式：
```python
pattern = r'说话人(\d+)\s+(\d{1,2}:\d{2}:\d{2})\n(.*?)(?=\n说话人\d+|\Z)'
```

每个匹配返回 (说话人编号, 时间戳, 内容文本)。

### Step 5: 插入 SQLite

```bash
# 使用 seed 脚本
/Users/mac/.hermes/hermes-agent/venv/bin/python3 \
  /Users/mac/company-archive/scripts/seed_all.py
```

或逐个 INSERT：
```sql
INSERT INTO meetings (id, date, title, description, tags) VALUES (...);
INSERT INTO speakers (name, role) VALUES (...) ON CONFLICT(name) DO UPDATE ...;
INSERT INTO segments (meeting_id, speaker_name, start_time, content) VALUES (...);
INSERT INTO quotes (meeting_id, speaker_name, quote_text, category) VALUES (...);
INSERT INTO photos (meeting_id, file_path) VALUES (...);
```

### Step 6: 提取金句

从 segments 中筛选有洞察力、可引用的发言，标注 category：
- 战略 — 关于公司方向、IPO路径
- 价值观 — 关于做人做事的原则
- 管理 — 关于团队、人才、流程
- 幽默 — 轻松有趣的发言
- 决策 — 明确的决定或结论

金句存入 quotes 表，同时将对应 segment 的 is_quote 字段设为 1。

## 查询示例

```sql
-- 查某人的所有发言
SELECT m.title, s.start_time, s.content 
FROM segments s JOIN meetings m ON s.meeting_id=m.id 
WHERE s.speaker_name='唐总' ORDER BY m.date, s.start_time;

-- 查某次会议的金句
SELECT speaker_name, quote_text FROM quotes WHERE meeting_id='2026-06-13_务虚会';

-- 查含关键词的片段
SELECT * FROM segments WHERE content LIKE '%IPO%';
```

## 已知说话人档案

| 人名 | 角色 | 特征 |
|------|------|------|
| 唐总 | 创始人/实控人 | 长篇自我反思、军工苹果愿景、引用易经/曾国藩 |
| 刘总 | 高管/改革推手 | 铁三角流程、人才密度、直言不讳 |
| 洪斌/红斌 | 投资/融资 | 三驾马车理论、资本逻辑、14亿人2000个实控人 |
| 孙总 | 原研发→市场 | 从美的出来的案例、年收入突破经历 |
| 波总 | 资本方向 | 5年千万10年过亿、投资视角、30倍PE计算 |
| 邓老师 | 外部导师 | Plan A IPO导向、警告对赌风险、中医养生 |
| 老李 | 市场 | 一线拿项目 |

## 注意事项

1. **大文本保存**：Telegram 消息中的超长转写文字必须完整写入文件，不能只写头部摘要！
2. **说话人确认**：没把握的说话人必须先问波总，不要擅自标注
3. **会议命名**：`YYYY-MM-DD_会议主题.md`，主题用简洁中文
4. **照片入库**：从 `image_cache` 复制到 `photos/`，同时 INSERT 到 photos 表
5. **数据库备份**：`index.db` 目前仅本地存储，后续考虑 Google Drive 备份
