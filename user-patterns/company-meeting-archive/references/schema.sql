-- company-archive index.db Schema
-- Created: 2026-06-13
-- Location: /Users/mac/company-archive/index.db

CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,           -- YYYY-MM-DD_主题 (e.g. "2026-06-13_务虚会")
    date TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    attendees TEXT,                -- JSON array
    audio_files TEXT,
    photo_files TEXT,
    transcript_path TEXT,
    summary TEXT,
    tags TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS speakers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,     -- "唐总" / "波总" / "刘总"
    role TEXT,                     -- "创始人/实控人"
    voice_profile TEXT,            -- 声纹特征（后期积累）
    sample_count INTEGER DEFAULT 0,
    first_seen TEXT,
    last_seen TEXT
);

CREATE TABLE IF NOT EXISTS segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL,
    speaker_id INTEGER,
    speaker_name TEXT,
    start_time TEXT,               -- "00:03:22"
    end_time TEXT,
    content TEXT NOT NULL,
    is_quote BOOLEAN DEFAULT 0,
    tags TEXT,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id),
    FOREIGN KEY (speaker_id) REFERENCES speakers(id)
);

CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id INTEGER DEFAULT 0,  -- 0 = 未关联具体segment
    meeting_id TEXT NOT NULL,
    speaker_name TEXT NOT NULL,
    quote_text TEXT NOT NULL,
    context TEXT,
    category TEXT,                 -- "战略"/"价值观"/"管理"/"决策"/"幽默"
    photo_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
);

CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    taken_at TEXT,
    description TEXT,
    people_in_frame TEXT,          -- JSON array
    is_key_photo BOOLEAN DEFAULT 0,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_segments_meeting ON segments(meeting_id);
CREATE INDEX IF NOT EXISTS idx_segments_speaker ON segments(speaker_name);
CREATE INDEX IF NOT EXISTS idx_quotes_meeting ON quotes(meeting_id);
CREATE INDEX IF NOT EXISTS idx_quotes_speaker ON quotes(speaker_name);
CREATE INDEX IF NOT EXISTS idx_meetings_date ON meetings(date);

-- Confirmed speakers (as of 2026-06-13)
-- 唐总    — 创始人/实控人，长篇自我反思，军工苹果愿景
-- 刘总    — 高管/改革推手，铁三角流程，人才密度，直言不讳  
-- 洪斌    — 投资/融资，三驾马车理论，14亿人中2000个实控人
-- 孙总    — 研发→市场，美的经历，年收入突破
-- 波总    — 资本方向，5年千万10年过亿，30倍PE计算
-- 邓老师  — 外部导师，Plan A IPO导向，警告对赌风险
-- 老李    — 市场，一线拿项目
