---
name: debt-screenshot-auto-update
description: 波总发送花呗/拿去花/度小满/借呗等平台截图时，自动 OCR 识别 + 平台检测 + 更新 debts.json
trigger: 波总发送截图 且 提及"花呗""拿去花""度小满""借呗""还款"或直接发图未说明
category: user-patterns
---

# 债务截图自动识别 & 更新

## OCR 引擎（铁律：优先 Apple Vision）

**🥇 Apple Vision OCR（macOS 系统级，必用）：**
```bash
swift /Users/mac/.hermes/scripts/ocr_apple.swift /path/to/screenshot.jpg
```
- 和系统「实况文本」同一引擎，数字 5/9/1 不会混淆
- 中文识别精准，1-2 秒出结果，无需下载模型
- 脚本位置：`~/.hermes/scripts/ocr_apple.swift`

**🥈 Tesseract 备选（仅 Apple Vision 不可用时）：**
```bash
python3 -c "import pytesseract; from PIL import Image; print(pytesseract.image_to_string(Image.open('/path/to/img.jpg'), lang='chi_sim+eng'))"
```
- ⚠️ 已知 Bug：数字 5 误读为 9、开头 "1" 被吞掉（如 19432→9432）
- ⚠️ 用 Tesseract 提取的金额必须波总肉眼确认，不可直接写入

---

## 触发条件
- 波总发送手机截图（支付平台界面）
- 波总说「看看这个」「更新一下」并附图
- 截图未说明但 OCR 文本包含平台特征

## 工作流

### Step 1: OCR 提取（优先 Apple Vision）

### Step 2: 平台识别

**借呗 (Alipay Jiebei) — 置信度 ≥3 即判定：**
1. "剩余未还本金（元）" — 页面核心数字，独有文案
2. "查账还款" — 支付宝借呗顶部导航
3. "共X笔" — 借款笔数统计
4. "先息后本" 或 "等额本息" — 还款方式标识
5. "提前还款" — 借呗操作按钮
6. "全部待还" + "含利息" — 总览行（本金+利息拆分）

**借呗金额提取：**
- ⚠️ 区分两个数字！「剩余未还本金」才是债务金额，「全部待还」含利息不要用
- 正则：`剩余未还本金[\\(（]元[\\)）]\s*[^\d]*([\d,]+\\.?\d*)`
- 附加信息：借款日期（如"2025年9月24日 借20,000.00元"）、还款方式（先息后本）、剩余期数

**花呗 (Alipay Huabei) — 置信度 ≥3 即判定：**
1. "全部待还" — 独有总览文案
2. "未入账" — 花呗独有（交易确认后入账）
3. "淘宝" 或 "天猫" — 支付宝生态关联
4. "还款日" + 多月分期 — 账单调特征
5. 金额紧随"全部待还(元)" — 格式特征

**拿去花 (携程拿去花) — 置信度 ≥3 即判定：**
1. "剩余待还(元)" — 页面顶部总览
2. "累计账单金额" — 本期消费合计
3. "记账周期 X月X日-X月X日" — 账单周期
4. "已退款" — 退款追踪
5. "用拿去花订酒店" — 产品标语
6. "携程" — 携程关联

**拿去花金额提取：**
- ⚠️ 注意区分三个数字！只有最上面的「剩余待还(元)」才是总负债
- 「累计账单金额」和「剩余应还」都只是本期数据，不要用
- 正则：`剩余待还[\(（]元[\)）]\s*[^\d]*([\d,]+\.?\d*)`

**度小满 (Duxiaoman) — 置信度 ≥3 即判定：**
1. "查账" + "还款" — App 顶部导航栏独有
2. "近7日待还" — 度小满首页概览
3. "自动扣款" 或 "自动还款" — 度小满扣款描述
4. "共X笔借款" — 借款笔数统计
5. "待还本金" — 本金余额显示
6. "每月还款计划" + 多月份横向排列 — 度小满分期展示

**度小满金额提取：**
- 正则：`待还本金[:\s]*([\d,]+\.?\d*)`
- 取第一个匹配的数字（这是总待还本金）

### Step 3: 金额提取

花呗：
- 正则：`全部待还[\(（]元[\)）]\s*\n?\s*([\d,]+\.?\d*)`
- 取第一个匹配的数字

### Step 4: 更新 debts.json
```bash
cd ~/.hermes/adjutant/repo/hermes-adjutant
python3 finance/scripts/finance.py update-debt -c "花呗" -a <提取金额> --source "截图更新 YYYY-MM-DD"
```

### Step 5: Git push
```bash
git add -A && git commit -m "finance: 花呗截图更新 ¥XXX" && git push origin main
```

## 反馈模板

识别成功时：
```
📸 识别：花呗截图
💰 金额：¥X,XXX.XX
📅 更新时间：YYYY-MM-DD HH:MM
✅ debts.json 已更新 + Git 已推送
```

## 注意事项

### OCR 陷阱（真实案例）
- **⚠️ 铁律：提取金额后必须向波总确认！人眼比 OCR 可靠**
- 度小满：`19432.55` 被 Tesseract 读成 `9432.55`（吞掉开头 "1"）→ 波总纠正
- 拿去花：`5303.51` 被 Tesseract 读成 `9303.51`（5→9 误读）→ 波总纠正
- 拿去花：Apple Vision 正确读出 `5,303.51`，验证了引擎升级的必要性
- `简余待还` = `剩余待还`（Tesseract 中文误读）
- 拿去花页面：区分三个数字——`剩余待还(元)` 总负债 / `累计账单金额` 本期消费 / `剩余应还` 本期扣退款后

### 游戏化隐喻规则（铁律）
- **🚫 禁止使用对立/攻击隐喻**：Boss、讨伐、击杀、斩灭、英灵殿——借钱的是亲友恩人
- **✅ 使用「归途·星火」框架**：
  - 债主 = 归途驿站/星火使者（不是 Boss）
  - 还款 = 践约/归还（不是攻击）
  - 还清 = 星火已燃/驿站抵达（不是击杀）
  - 已清列表 = 星火台（不是英灵殿）
  - 总进度 = 归途进度（不是 Boss 击杀数）
- 参考文件：`references/visualization-and-gamification-research.md`

### 文件发送（铁律）
- **🥇 curl 直调 Telegram Bot API**（100% 可靠，绕过 Hermes 白名单）
- **🥈 MEDIA 标签**（不可靠，需白名单 + gateway 重启才生效）
- 详见 `media-file-delivery` 技能

### 金额更新命令
```bash
# 截图刷新（直接更新金额，非还款记录）
FINANCE_DIR=~/.hermes/adjutant/repo/hermes-adjutant/finance \
  python3 finance/scripts/finance.py update -c "花呗" -a <金额> -s "截图YYYY-MM-DD"
```
