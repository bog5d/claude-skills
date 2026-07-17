# Subagent File Delivery Pitfalls

## 问题

`delegate_task` 的子代理运行在**隔离上下文**中。子代理写的文件在主代理看来不存在。

## 症状

- 子代理说"文件已生成在 /path/to/file.pptx"，但主代理 `read_file` 返回 "file not found"
- 主代理不得不从零重新生成文件

## 解决方案

### 方案A：指定共享路径（推荐）

在 goal 中明确指示子代理写到已知共享目录：

```
"Write output to ~/.hermes/cache/documents/filename.ext"
```

然后主代理可以用 `read_file("~/.hermes/cache/documents/filename.ext")` 读取。

前提：
- 主代理和子代理在同一台机器上（共享文件系统）✅
- 子代理的 workdir 不受限 ✅
- 子代理确实写到了指定路径（在 goal 中明确要求）✅

### 方案B：小文件嵌入摘要

对于 markdown/text 文件 < 5KB，让子代理把内容直接放在最终摘要里。

### 方案C：子代理报告文件元数据

要求子代理报告：文件路径、文件大小(bytes)、行数/页数。

## 预防清单

派发子代理前：
1. 在 goal 中明确指定输出路径
2. 使用共享缓存目录 `~/.hermes/cache/documents/`
3. 子代理返回后验证文件是否存在
4. 文件不存在时，要求子代理在摘要中包含内容，或重新生成

## 教训

- 2026-06-17 会话：三个并行 delegate_task (T100/PPT, T101/Q&A, T102/Research)。T100 的 PPTX 写到了子代理临时目录，主代理找不到，被迫重新生成。教训：始终指定共享输出路径。
- T101/T102 产出 markdown，子代理在摘要中包含了内容——完美工作。教训：文本输出嵌入摘要即可，二进制/大文件用共享路径。
