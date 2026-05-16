---
name: search-generate-separation
description: 所有"搜索 → 生成"工作流的输出长度管理策略。当搜索数据较大(>1500字)时，必须用文件中转，不经过对话输出避免截断。
---

# 搜索+生成分离策略

## 问题定义

当任务涉及"搜索大量数据 → 生成大型产物（PPT/报告/HTML/代码库）"时，如果搜索结果和生成产物都通过对话流传递，会触发 Telegram/CLI 输出长度限制（约 2-4 万字），导致：

- 搜索结果被截断，只获取部分数据
- 生成产物不完整，缺少后半 CSS/JS/内容
- 需要反复重试，浪费大量 token

**核心原因**：搜索数据 + 模板 + 生成内容的总量远超对话输出限。这不是输出限制能被"修大"的技术问题，是**工作流策略问题**——不应该让中间产物经过对话流。

## 通用工作流

### 三阶段分离模式（任何搜索+生成场景强制使用）

```
Phase 1 — 搜索（落地到文件）
Phase 2 — 读文件+拼接（不经过对话）
Phase 3 — 写文件（对话只回复路径）
```

### Phase 1: 搜索落地（必做）

数据超过 1500 字就必须写为文件，不要带回对话：

```python
# 正确 ✅：搜索数据落地到文件
from hermes_tools import write_file, terminal

result = terminal("curl -s 'https://api.example.com/data'")
write_file("/tmp/research-data.json", result["output"])
# 对话里只说"数据已收集到 /tmp/research-data.json"，不展示原始数据

# 错误 ❌：把结果带回对话
result = terminal("curl -s 'https://api.example.com/data'")
print(result["output"])  # 几万字数据涌入对话，几乎必然截断
```

如果搜索量级大（多个并行搜索），落地到多个独立文件：

```python
from hermes_tools import write_file
write_file("/tmp/rwa-trends.md", trends_result)
write_file("/tmp/rwa-policy.md", policy_result)
write_file("/tmp/rwa-projects.md", projects_result)
```

### Phase 2: 读文件+拼接

从文件读取数据拼接生成产物，不要经过对话：

```python
# 正确 ✅：execute_code 里读取文件拼接
from hermes_tools import read_file, write_file

research = read_file("/tmp/research-data.md")
template = open(os.path.expanduser("~/.hermes/skills/xxx/template.html"), "r").read()

slides = generate_slides_from_data(research["content"])
result = template.replace("SLIDES_HERE", slides)
write_file("~/Desktop/ppt/index.html", result)

# 错误 ❌：把模板和 slides 内容打印到对话
template = read_file(...)  # template 30KB 直接涌入对话
```

### Phase 3: 对话只回复文件路径

对话回复中**只能包含**：
- 文件路径（如 `MEDIA:~/Desktop/ppt/index.html`）
- 摘要（文件结构、页数、主题等元数据）
- 操作提示（"用浏览器打开"、"可用 ← → 翻页"）

**绝对不能在对话回复中包含**：
- 完整的 HTML/CSS/JS 代码块
- 大于 2000 字的搜索结果展示
- 完整的模板内容

## 决策树（每次任务开头过一遍）

```
任务涉及搜索 + 生成？
  ├── 否 → 正常流程
  └── 是 → 必须用三阶段分离模式

搜索数据预计超过 1500 字？
  ├── 否 → 仍建议写文件，防止搜索实际返回量超出预期
  └── 是 → 强制写文件

生成产物是 HTML/大型文本（>10KB）？
  ├── 否 → 可以对话输出
  └── 是 → 强制写文件，对话只给路径

产物可能需要反复迭代修改？
  ├── 否 → 一次性写文件足够
  └── 是 → 首次写文件后，后续用 patch 工具直接修改文件，不走对话流
```

## 与其他技能的配合

- **guizang-ppt-skill**: Step 5 已明确写文件策略
- **web3-research-to-ppt**: Step 1 已增加搜索数据落地要求
- **photo-slideshow-mv**: Remotion 项目文件大，绝不要对话输出

## 验证清单

- [ ] 搜索结果是否写入了文件而不是打印到对话？
- [ ] 生成产物是否写入了文件而不是对话输出？
- [ ] 对话回复只包含文件路径 + 摘要 + 操作提示？
- [ ] 如果有多轮迭代，是否用 patch 直接改文件而不是重写对话？
