# 中文表格 → PNG 图片渲染（波总偏好：表格出图，不出现 markdown 源码）

波总明确偏好：所有表格/对比/多维度数据直接生成截图图片发送，更直观。**禁止在回复中贴 markdown 表格源码。**

## 已验证配方（matplotlib + STHeiti 中文字体）

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch
import os

# 1. 中文字体（macOS）
font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
fm.fontManager.addfont(font_path)
prop = fm.FontProperties(fname=font_path)
plt.rcParams["font.family"] = prop.get_name()

# 2. 画布：坐标轴关闭，用 FancyBboxPatch 画单元格
fig, ax = plt.subplots(figsize=(15, 10.5), dpi=160)
ax.set_xlim(0, 15); ax.set_ylim(0, 10.5); ax.axis("off")
fig.patch.set_facecolor("#F7F5F0")

# 3. 表头深色带 + 数据行交替底色 + 层级色块（红/橙/黄风险分级等）
#    长文本列（描述/应对）用小字号 + wrap，确保不截断

# 4. 保存到 MEDIA 白名单目录（Telegram 可投递）
out_dir = os.path.expanduser("~/.hermes/cache/images")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "<文件名>_YYYYMMDD.png")
fig.savefig(out_path, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close(fig)
```

## 自测铁律（用户极度反感未自测就发）

**必须**：用 `vision_analyze(image_url=out_path, question="检查表格对齐/完整/重叠/乱码")` 自测通过后才发给用户。
2026-08-10 实测：23 行 × 8 列总表渲染后经 vision 检查无重叠、无截断、无乱码。

## 排版要点

- `figsize` 按行数调整：约 20+ 行用 (16.5, 13.8)；行多则加高
- 单元格底色交替（`i % 2 == 0`）提升可读性
- 重要值着色：强=红、密友=紫、好友=绿，加 fontweight="bold"
- 新补/变更行用浅黄底 `#FFF8E1` 高亮
- 底部图例 + 使用规则 + 统计数字（总人数/分类数）
- 存 `~/.hermes/cache/images/`（MEDIA 白名单子目录），根目录和 /tmp 不在白名单

## 关联

- 用户偏好出处：`USER PROFILE`「讨厌表格以Markdown源码形式展示」
- 仓库 schema：`交接手记/SCHEMA.md` §3 人脉八字段
- 人脉总表源文件：`人脉管理/README.md`
