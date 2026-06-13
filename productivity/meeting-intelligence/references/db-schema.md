# Company Archive Database Schema

## 5 Tables + ER

```
meetings (1) ──< segments (N) ──> speakers (N)
   │                  │
   │                  └── quotes (N)
   │
   └── photos (N)
```

## meetings
```sql
CREATE TABLE meetings (
    id TEXT PRIMARY KEY,              -- "YYYY-MM-DD_主题"
    date TEXT NOT NULL,               -- ISO date
    title TEXT NOT NULL,
    description TEXT,
    attendees TEXT,                   -- JSON array
    audio_files TEXT,                 -- JSON array of paths
    photo_files TEXT,                 -- JSON array of paths
    transcript_path TEXT,
    summary TEXT,
    tags TEXT,                        -- "战略,融资,产品"
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
```

## speakers
```sql
CREATE TABLE speakers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,        -- 统一名称
    role TEXT,                        -- "创始人/CEO"
    voice_profile TEXT,               -- 声纹特征
    sample_count INTEGER DEFAULT 0,
    first_seen TEXT,
    last_seen TEXT
);
```

## segments
```sql
CREATE TABLE segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL,
    speaker_id INTEGER,
    speaker_name TEXT,
    start_time TEXT,                  -- "00:03:22"
    end_time TEXT,
    content TEXT NOT NULL,
    is_quote BOOLEAN DEFAULT 0,
    tags TEXT,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id),
    FOREIGN KEY (speaker_id) REFERENCES speakers(id)
);
```

## quotes
```sql
CREATE TABLE quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id INTEGER NOT NULL,
    meeting_id TEXT NOT NULL,
    speaker_name TEXT NOT NULL,
    quote_text TEXT NOT NULL,         -- 完整原文
    context TEXT,
    category TEXT,                    -- "决策/价值观/战略/幽默/反思"
    photo_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (segment_id) REFERENCES segments(id),
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
);
```

## photos
```sql
CREATE TABLE photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    taken_at TEXT,
    description TEXT,
    people_in_frame TEXT,             -- JSON
    is_key_photo BOOLEAN DEFAULT 0,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
);
```

## Indexes
```sql
CREATE INDEX idx_segments_meeting ON segments(meeting_id);
CREATE INDEX idx_segments_speaker ON segments(speaker_name);
CREATE INDEX idx_quotes_meeting ON quotes(meeting_id);
CREATE INDEX idx_quotes_speaker ON quotes(speaker_name);
CREATE INDEX idx_meetings_date ON meetings(date);
```

## 常用查询

```sql
-- 所有金句（最近优先）
SELECT m.date, q.speaker_name, q.quote_text
FROM quotes q JOIN meetings m ON q.meeting_id = m.id
ORDER BY q.created_at DESC;

-- 某人发言时间线
SELECT m.date, s.start_time, s.content
FROM segments s JOIN meetings m ON s.meeting_id = m.id
WHERE s.speaker_name = '邓老师'
ORDER BY m.date, s.start_time;

-- 关键词跨会议搜索
SELECT DISTINCT m.title, m.date
FROM segments s JOIN meetings m ON s.meeting_id = m.id
WHERE s.content LIKE '%对赌%';

-- 每次会议金句比例
SELECT m.id, COUNT(*) AS total,
       SUM(CASE WHEN s.is_quote THEN 1 ELSE 0 END) AS quotes,
       ROUND(100.0*SUM(CASE WHEN s.is_quote THEN 1 ELSE 0 END)/COUNT(*),1) AS quote_pct
FROM segments s JOIN meetings m ON s.meeting_id = m.id
GROUP BY m.id;
```
