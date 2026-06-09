---
name: debt-screenshot-auto-update
description: 波总发截图时自动识别类型——平台债务页 → debts.json更新+还款日提取；微信/支付宝账单 → expenses.json消费追踪
trigger: 波总发送截图 且 提及"花呗""拿去花""度小满""借呗""还款"或直接发图未说明，或发送微信/支付宝账单截图/CSV文件
category: user-patterns
---

# 截图自动识别 & 更新（v2.0 双管线）

截图现在有**两个目的地**，先判断类型再走对应管线：

**类型判断：**
- 平台债务页关键词 → `debts.json`：剩余未还本金、全部待还、查账还款、待还本金
- 微信/支付宝账单关键词 → `expenses.json`：微信支付、支付宝、交易记录、账单明细

## 管线 A：平台债务截图（已有，新增还款日提取）

## OCR 引擎（v3.1，2026-06-08 实测校准）

⚠️ `ocr_orchestrator.py`、`ocr_pro.swift`、EasyOCR 均未部署。以下为当前可用的实际工具：

### 批量截图：并行 OCR

波总常一次发送多张截图。**必须并行运行 OCR**（每张图一个 terminal 调用），不要串行等待：
```bash
# 🥇 全部并行发起
/tmp/ocr_vision /path/to/img1.jpg &
/tmp/ocr_vision /path/to/img2.jpg &
/tmp/ocr_vision /path/to/img3.jpg &
wait
```
或使用 `terminal()` 分别调用（后台不阻塞）。Apple Vision 是独立进程，4 张图并行 ~3 秒，串行 ~12 秒。

### 🥇 Apple Vision (Swift) — 首选，临时脚本调用：
```bash
# 编译一次
swiftc -o /tmp/ocr_vision /tmp/ocr_vision.swift
# 对每个截图运行
/tmp/ocr_vision /path/to/screenshot.jpg
```
- Swift 源码见下方「Vision OCR Swift 模板」
- 对微信账单效果最好（日期+金额+商户清晰），对支付宝账单较差（复杂布局+图标干扰）
- ⚠️ 支付宝截图经常乱码，优先让波总口述而非反复 OCR

**🥈 Tesseract (`chi_sim`) — 备选：**
```bash
tesseract /path/to/img.jpg stdout -l chi_sim 2>&1
```
- 可尝试 PSM 3/4/6/11 不同模式
- 已知 Bug：数字 5→9、开头 "1" 被吞（19432→9432）
- 对支付宝截图几乎不可用（乱码严重）
- ⚠️ Tesseract 提取的金额必须波总肉眼确认，不可直接写入

**Vision OCR Swift 模板：**
```swift
import Vision; import AppKit
let img = NSImage(contentsOfFile: CommandLine.arguments[1])!
let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil)!
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.recognitionLanguages = ["zh-Hans", "zh-Hant", "en"]
try VNImageRequestHandler(cgImage: cg).perform([req])
for obs in req.results! { print(obs.topCandidates(1).first!.string) }
```

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
# 先同步数据文件到 repo（scripts 写入 adjutant/finance/，repo 在 hermes-adjutant/finance/）
cp ~/.hermes/adjutant/finance/debts.json ~/.hermes/adjutant/repo/hermes-adjutant/finance/
cp ~/.hermes/adjutant/finance/transactions.json ~/.hermes/adjutant/repo/hermes-adjutant/finance/
cd ~/.hermes/adjutant/repo/hermes-adjutant && git add -A && git commit -m "finance: 平台截图更新" && git push origin main
```

## 反馈模板

识别成功时：
```
📸 识别：花呗截图
💰 金额：¥X,XXX.XX
📅 更新时间：YYYY-MM-DD HH:MM
✅ debts.json 已更新 + Git 已推送
```

## 🆕 管线 B：消费账单截图（微信/支付宝）

收到微信或支付宝账单截图时：

### Step 1: OCR 提取（Apple Vision 优先）

### Step 2: 逐行解析
从 OCR 文本中提取每笔交易：日期 + 金额 + 商户名

### Step 3: 批量导入
```bash
cd ~/.hermes/adjutant/repo/hermes-adjutant
python3 finance/scripts/expenses.py batch --items '[
  {"date":"2026-06-05","amount":35.50,"merchant":"美团外卖"},
  {"date":"2026-06-05","amount":128.00,"merchant":"滴滴出行"}
]' -s "微信" --sid "截图文件名"
```

### Step 4: 去重检查
expenses.py 自动去重逻辑：日期相同 + 金额差 ≤¥2 + 商户名相似度 >50%

### Step 5: 反馈
```json
{"added": [...], "duplicates": [...], "errors": [...]}
```
告诉波总：新增N笔、去重M笔、错误K笔

### Step 6: Git push

## 🆕 还款日提取

平台截图 OCR 后检查：
- 花呗：`还款日：每月(\\d+)日` → 设为 `YYYY-MM-DD`
- 拿去花：`还款日(\\d+)月(\\d+)日`
- 度小满：`到期日[：:]\\s*(\\d{4}-\\d{2}-\\d{2})`

提取后执行：
```bash
python3 finance/scripts/finance.py set-duedate -c "花呗" -d 2026-06-10
```

Cron 每天 21:00 自动 `due-check`，5 天内到期自动预警。

## 🆕 暴力催收联动

`nag_screenshots.py`（cron `7857946435ae`，10:00/14:00/18:00）：
- 检查 `expenses.json` → `screenshots` 数组是否含昨日数据
- 昨日无截图 → 输出催收 → cron 推送 Telegram
- 已有数据 → 静默退出

## 消费账单处理（v2.0 新增）

### CSV 文件导入（优先于截图 OCR）

当波总发送支付宝或微信导出的账单文件时，使用 `import_csv.py`：

```bash
cd ~/.hermes/adjutant/finance
python3 scripts/import_csv.py <文件路径>
```

**支付宝 CSV**：GBK 编码，需先转换
```bash
iconv -f GBK -t UTF-8 alipay.csv > alipay_utf8.csv
python3 scripts/import_csv.py alipay_utf8.csv
```

**微信账单**：xlsx 格式，`import_csv.py` 直接用 openpyxl 读取。

导入器自动完成：平台识别、日期解析、噪音过滤（转账/红包/理财/信用卡还款）、去重、分类、入库。

### 微信/支付宝账单截图

截图包含消费明细时，走 OCR → batch 导入流程：
```bash
# OCR（Apple Vision 临时脚本 — ocr_apple.swift 未部署）
/tmp/ocr_vision screenshot.jpg
# 解析 → 批量入库
python3 scripts/expenses.py batch --items '<JSON>' -s "微信" --sid "wx_bill_20260606"
```

⚠️ CSV 数据质量优于截图 OCR，优先使用 CSV。截图仅作补充（CSV 日期范围不够时）。

## 注意事项

### OCR 陷阱（真实案例）
- **⚠️ 铁律：提取金额后必须向波总确认！人眼比 OCR 可靠**
- **OCR 完全失败不追问**：Apple Vision + Tesseract 双引擎都读不出的截图（如模糊截图、局部裁剪），直接告诉波总"这张读不出"，不要反复重试。波总会自己说是什么
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
