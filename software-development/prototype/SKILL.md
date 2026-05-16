---
name: prototype
title: "多方案原型生成器"
description: "针对需求生成3+变体方案（A/B/C），启动预览，等待选型。适合UI/文档/架构选型场景。"
trigger: "当波总说'出几个方案'、'原型'、'选型'、'变体'、'多版本对比'时"
---

# prototype — 多变体方案生成

## 核心逻辑

收到需求后，不走单线思维——强制出至少3个差异化方案，每个有明确侧重点。

## Phase 1: 需求解析

提取：
- **场景类型**：UI原型 | 文档方案 | 架构设计 | 商业方案
- **差异化维度**：用户指定的侧重方向（如果有），否则自动推断
- **输出格式**：HTML预览 | PPT | Markdown文档 | 代码

## Phase 2: 并行生成（用 delegate_task）

```python
delegate_task(tasks=[
    {"goal": "方案A：侧重[维度1]...", "context": "..."},
    {"goal": "方案B：侧重[维度2]...", "context": "..."},
    {"goal": "方案C：侧重[维度3]...", "context": "..."},
])
```

每个子agent独立生成一个方案，不互相污染。

## Phase 3: 汇总对比

输出对比表（关键差异 + 适用场景 + 风险）→ 直接生成截图图片发送，不用 Markdown 表格源码。

## Phase 4: 启动预览

- UI原型 → 生成单HTML文件，用 `python3 -m http.server` 启动本地预览
- 文档方案 → 生成多版本文档文件供对比
- PPT方案 → 用 guizang-ppt-skill 或 reveal-ppt-skill 渲染

## Phase 5: 等待选型

明确告知波总各方案差异，等选择后再深入开发。

## Pitfalls

- 不要让子agent看到其他方案（避免思维趋同）
- 差异化维度要够大——如果三个方案本质上一样，就失去了意义
- 预览链接用 `localhost`，波总在本地可以直接打开
