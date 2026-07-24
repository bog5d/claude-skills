---
name: meeting-transcript-archive
description: "Build and maintain a searchable SQLite-based meeting transcript archive with speaker identification, quote extraction, and photo indexing."
category: productivity
---

# 会议转写数字档案库

## 触发条件

波总发送会议转写文字，要求"入库""存档""建库"或"能搜"。

## 目录结构

```
company-archive/
├── audio/       # 原始录音
├── photos/      # 现场照片
├── transcripts/ # 转写文字 (.md)
├── exports/     # 导出产物
├── index.db     # SQLite索引库
└── scripts/     # 入库脚本
```

## 入库流程

1. 建库：创建目录 + 初始化SQLite (5表: meetings/speakers/segments/quotes/photos)
2. 收转写：波总发文字 → 存为 `transcripts/YYYY-MM-DD_标题.md`
3. 确认说话人：向波总确认每个"说话人N"的真实姓名
4. 解析入库：正则匹配 `说话人N HH:MM:SS` + 内容，INSERT到segments
5. 提取金句：手动标注或AI筛选 → INSERT到quotes
6. 照片关联：photos表注册

## 解析正则 (Python)

```python
pattern = r'说话人(\d+)\s+(\d{1,2}:\d{2}:\d{2})\n(.*?)(?=\n说话人\d+|\Z)'
for m in re.finditer(pattern, text, re.DOTALL):
    speaker_num, timestamp, content = m.group(1), m.group(2), m.group(3).strip()
```

## 注意事项

- 30K+字符的大文件用 `write_file` 不要用终端heredoc
- 每场会议说话人编号独立，需逐个确认映射
- 增量入库先DELETE旧segments再INSERT
- quotes的segment_id找不到时填0

## 查询示例

```sql
-- 某人所有发言
SELECT meeting_id, start_time, substr(content,1,200) FROM segments WHERE speaker_name='唐总';
-- 关键词搜索
SELECT * FROM segments WHERE content LIKE '%IPO%';
-- 金句
SELECT speaker_name, quote_text FROM quotes WHERE meeting_id='X';
```
