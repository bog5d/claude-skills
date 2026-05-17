---
name: anki-import-parser
description: 解析 Anki 导出的 TXT/TSV 文件，提取词汇并匹配考研核心词库。支持 Anki 标准 tab-separated 格式及个性化学词卡片。
category: productivity
trigger: 用户导出 Anki txt 文件要求导入词库时
---

# Anki Import Parser — 词库导入标准流程

## 目的
将 Anki 导出的 txt 文件解析为结构化词库数据，自动匹配考研核心词，写入 `words.json` 并更新进度。

## 输入格式
Anki 默认导出格式（tab-separated，UTF-8）：

```
#separator:tab
#html:true
#guid column:1
#notetype column:2
#deck column:3
#tags column:6
<guid>	问答题	考研英语game	<front>	<back>	<tags>
```

字段索引：
- Field[3] = front（正面：单词/句子/短语）
- Field[4] = back（背面：中文释义+解析）

## 执行步骤

### Step 1: 读取并解析（注意 csv 陷阱）

⚠️ 不要用 Python 的 csv.reader！Anki 导出字段内含双引号，csv.reader 会错误解析引号内的制表符。

```python
with open(path) as f:
    content = f.read()
lines = content.split('\n')
data_lines = [l for l in lines if not l.startswith('#')]

cards = []
for line in data_lines:
    parts = line.split('\t')
    if len(parts) >= 6:
        cards.append({'front': parts[3], 'back': parts[4]})
```

### Step 2: 分类卡片类型

Anki 卡片有三种，需分别处理：

| 类型 | 特征 | 处理方式 |
|------|------|----------|
| 单词卡 | front 以英文单词开头 | 提取单词本体 |
| 句法卡 | front 含 "Kaoyan Syntax"/"同位语"/"公式"/"结构逻辑" | 跳过，不提取为单词 |
| 长难句卡 | front 以中文标点（括号等）开头 | 跳过，不提取为单词 |

```python
import re
f_clean = re.sub(r'<[^>]+>', '', front).strip()
f_clean = f_clean.strip('"').strip()

# 跳过
if re.match(r'^[（(]', f_clean): continue  # 中文开头 = 长难句卡
if any(k in front for k in ['Kaoyan Syntax', '同位语', '结构逻辑']): continue

# 提取单词
first_line = f_clean.split('\n')[0].strip()
m = re.match(r'^([a-zA-Z][a-zA-Z\s\-/()]+?)\s*(?:/\S+?/)?\s*(?:Kaoyan|<br>|$)', first_line)
if m:
    word = m.group(1).strip()
    word = re.sub(r'\s*/\S+?/\s*$', '', word)  # 去掉残留音标
    word = re.sub(r'\s*<br>\s*$', '', word)
    word = re.sub(r'\s+Kaoyan\s+Target.*$', '', word).strip()
    words.append(word.lower())
```

### Step 3: 去重 + 匹配核心词

```python
unique_words = sorted(set(words))

# 匹配考研核心词表（内置 1500 词匹配）
# is_core & core_level 自动赋值
kaoyan_core = {...}  # 考研核心词字典
```

### Step 4: Merge + 写入 words.json

```python
# 读现有 words.json
existing = json.loads(read_file("/path/to/words.json")['content'])
existing_set = {w['word'].lower() for w in existing['words']}

# 仅添加新词
new_entries = []
for w in unique_words:
    if w not in existing_set:
        new_entries.append({
            "word": w, "phonetic": "", "meaning": meaning(w),
            "is_core": w in kaoyan_core,
            "core_level": kaoyan_core.get(w, 0),
            "source": "anki_import",
            "mastery": 0.0, ...
        })

existing['words'].extend(new_entries)
# 写入
```

### Step 5: 更新 progress.json

```python
s = progress['snapshot']
s['total_words'] = new_total
s['core_words_covered'] = new_core
s['coverage_pct'] = round(new_core / 1500 * 100, 1)

progress['history'].append({
    "timestamp": now,
    "action": "anki_import",
    "words": len(new_entries),
    "core_words": core_count
})
```

## 已知陷阱

1. **不要用 csv.reader** — Anki 的引号会打乱列解析，用 line.split('\t') 替代
2. **HTML 标签要先 strip** — Anki 字段中 `<br>`、`<b>` 等干扰正则匹配
3. **引号前缀** — 有些卡 front 以 `"` 开头，需要先 `strip('"')`
4. **卡片分类** — 长难句卡（中文开头）和句法卡（Kaoyan Syntax）必须跳过，它们是句子分析卡不是单词卡
5. **音标残留** — front 中可能有 `/ˈwɜːrd/` 音标，需要正则去除
6. **短语类** — "hair dryer"、"electric razor" 等短语是非核心词但也要保留
7. **大小写归一化** — 统一转为小写匹配，避免 duplicate

## 回导出 Anki 兼容格式

```python
# CSV/TSV 格式兼容 Anki 导入
with open("anki_export.tsv", "w") as f:
    f.write("#separator:tab\n#html:true\n")
    for w in words:
        f.write(f"{w['word']}\t中文：{w['meaning']}\n")
```
