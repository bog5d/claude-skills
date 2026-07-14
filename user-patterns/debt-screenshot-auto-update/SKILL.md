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

## OCR 引擎（v4.2，2026-07-14 迁移至 Qwen/DashScope）

⚠️ `ocr_orchestrator.py`、`ocr_pro.swift`、EasyOCR 均未部署。

### 引擎优先级

| 优先级 | 引擎 | 适用场景 | 备注 |
|--------|------|---------|------|
| 🥇 | **Qwen/DashScope (`alibaba`, `qwen-vl-max-latest`)** | 所有截图（唯一默认） | 通过 `vision_analyze` 工具自动走 `auxiliary.vision` |
| 禁止默认 | **Apple Vision / Tesseract** | 仅波总明确点名时 | 不再作为自动降级；Qwen 失败就报告配置/余额/API 问题 |

**Qwen/DashScope 不可用的情况：**
- 未设置 `DASHSCOPE_API_KEY`
- 余额/配额耗尽
- 模型名不匹配
- 超时（默认 60s 不够，需要 120s）

遇到以上任一 → 直接告诉波总需要配置/充值/修复 API，不要自动降级到 Apple Vision 或 Tesseract。

### 🥇 Qwen/DashScope — 默认首选

#### ⚠️ 架构铁律：vision_analyze 读的是 default config 的 auxiliary.vision

`vision_analyze` 工具读取的是 **`~/.hermes/config.yaml`（默认 config）的 `auxiliary.vision`** 段，**不是**当前 profile 的 `vision` 段。两个位置必须同时配置：

```
~/.hermes/config.yaml                          ← vision_analyze 读这里
  auxiliary.vision: provider=alibaba, model=qwen-vl-max-latest

~/.hermes/profiles/<name>/config.yaml          ← profile 自己的 vision 段
  vision: provider=alibaba, model=qwen-vl-max-latest
```

**诊断 vision 失效时**：先查默认 config 的 `auxiliary.vision`，不要只看 profile config。

**两种 config 同时失效的典型场景**：换了 API 后只更新了 profile 的 `vision`，没更新 default 的 `auxiliary.vision`。

#### 配置方式

只能用 `hermes config set` 命令：
```bash
hermes config set auxiliary.vision.provider alibaba
hermes config set auxiliary.vision.model "qwen-vl-max-latest"
hermes config set auxiliary.vision.base_url ""
hermes config set auxiliary.vision.api_key ""
hermes config set auxiliary.vision.timeout 120
```

⚠️ 不把 API key 写进 config.yaml；凭证放在环境变量 `DASHSCOPE_API_KEY`。如果没有这个变量或余额不足，直接告诉波总配置/充值。

#### 连通性验证

**Step 1 — 文本测试（先确认 API + key 有效）：**
```bash
curl -s https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-vl-max-latest","messages":[{"role":"user","content":"hello"}],"stream":false}'
```

**Step 2 — 图片测试（确认 vision 通路正常）：**
```python
import base64, json, urllib.request
with open('/path/to/test.jpg', 'rb') as f:
    img = base64.b64encode(f.read()).decode()
import os
payload = {"model":"qwen-vl-max-latest","messages":[{"role":"user","content":[
    {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}"}},
    {"type":"text","text":"提取金额数字"}]}]}
req = urllib.request.Request("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Authorization":f"Bearer {os.environ['DASHSCOPE_API_KEY']}","Content-Type":"application/json"})
print(json.loads(urllib.request.urlopen(req, timeout=30).read()))
```

#### 可用模型

| 模型 | 场景 | 备注 |
|------|------|------|
| `qwen-vl-max-latest` | 通用截图 OCR（唯一默认） | DashScope OpenAI-compatible |

### Apple Vision (Swift) — 禁止默认降级

```bash
# 编译一次
swiftc -o /tmp/ocr_vision /tmp/ocr_vision.swift
# 对每个截图运行
/tmp/ocr_vision /path/to/screenshot.jpg
```
- 对微信账单效果最好（日期+金额+商户清晰），对支付宝账单较差（复杂布局+图标干扰）
- ⚠️ 支付宝截图经常乱码，优先让波总口述而非反复 OCR

**批量截图：并行 OCR**

无论用哪个引擎，多张截图必须并行：
```bash
/tmp/ocr_vision /path/to/img1.jpg &
/tmp/ocr_vision /path/to/img2.jpg &
wait
```

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

### Tesseract (`chi_sim`) — 禁止默认使用

```bash
tesseract /path/to/img.jpg stdout -l chi_sim 2>&1
```
- 可尝试 PSM 3/4/6/11 不同模式
- 已知 Bug：数字 5→9、开头 "1" 被吞（19432→9432）
- 对支付宝截图几乎不可用（乱码严重）
- 只有波总明确要求时才允许使用
- ⚠️ Tesseract 提取的金额必须波总肉眼确认，不可直接写入

---

## 触发条件
- 波总发送手机截图（支付平台界面）
- 波总说「看看这个」「更新一下」并附图
- 截图未说明但 OCR 文本包含平台特征

## 工作流

### Step 1: OCR 提取（优先千问 VL，降级 Apple Vision）

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

### Step 1: OCR 提取（优先千问 VL，降级 Apple Vision）

### Step 2: 逐行解析
从 OCR 文本中提取每笔交易：日期 + 金额 + 商户名

### Step 3: 批量导入
```bash
cd ~/.hermes/adjutant/finance
python3 scripts/expenses.py batch --items '[
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

### 多源合并去重（v2.1 新增）

当同时收到微信截图 + 支付宝CSV时，存在跨来源重复（如同一天同一商户出现在两个平台）：

1. **先处理CSV**（数据更准）→ 录入 expenses.json
2. **再处理截图** → 录入时跳过已在CSV中的记录
3. **去重键**：`日期_金额_商户名_来源`，但需注意同一笔交易在不同平台商户名可能不同
4. **支付宝小荷包**（¥0.33等）属于内部转账，不计消费，跳过
5. **不计收支行**（余额宝转入等）跳过
6. 最终做一次全局去重：`日期_金额_商户名` 完全匹配的去重

### 微信/支付宝账单截图

截图包含消费明细时，走 OCR → batch 导入流程：
```bash
# OCR（Apple Vision 临时脚本 — ocr_apple.swift 未部署）
/tmp/ocr_vision screenshot.jpg
# 解析 → 批量入库
python3 scripts/expenses.py batch --items '<JSON>' -s "微信" --sid "wx_bill_20260606"
```

⚠️ CSV 数据质量优于截图 OCR，优先使用 CSV。截图仅作补充（CSV 日期范围不够时）。

## 🆕 石墨文档债务表评论提取（2026-07-05）

波总在石墨文档 `https://shimo.im/sheet/ll1x4P3IDZcSBf5F/` 维护了完整的债务台账。每个债主单元格有**详细评论/备注**，记录每笔借款的时间、地点、背景故事（"来时路"）。

### 评论提取方法（按可靠性排序）

#### 方法1：Shimo SDK 评论 API（首选，但需登录态）

石墨表格页面加载后，`window['@shimo/editor-sdk-sheet']` 可用：

```javascript
// 1. 初始化 SDK
const sdk = await window['@shimo/editor-sdk-sheet'].createSheetSDK(document.body);

// 2. 获取所有评论
// 方法 A: query + 事件监听
sdk.commentModel.query();
sdk.commentModel.on('updateComment', (commentList) => {
  // commentList 包含所有评论数据
});

// 方法 B: Utils 辅助方法（含行列映射）
sdk.comment.Utils.sheetComments();      // 当前 sheet 全部评论
sdk.comment.Utils.editorComments();     // 全部 sheet 评论
sdk.comment.Utils.commentsByRowAndCol(row, col);  // 指定单元格
```

**⚠️ 已知问题：** `sdk.comments.getAll()` 返回 "Method not implemented"；`commentModel` 可能不可用。

#### 方法2：REST API（需登录态的 token + 文件 GUID）

```
GET /api/comment/${guid}
Authorization: Bearer <token>

// GUID 可从页面 URL 或 window.__INITIAL_STATE__ 获取
```

#### 方法3：截图回退（最可靠）⭐ 推荐

当 SDK 和 API 都不可用时（无需登录、公开分享链接场景）：

```
1. 在浏览器中打开石墨表格
2. 点击数字单元格 → 右侧显示评论面板
3. browser_vision 截图 → vision_analyze 提取评论文本
4. 逐条记录到 debts.json 的 notes 字段
```

### 同步工作流

```
收到石墨链接 → 浏览器打开
  ├─ 如可登录 → 方法1/2 批量拉取全部评论
  └─ 如公开分享（只读）→ 方法3 截图逐条提取

提取后：
1. 解析评论中的金额变更、借款时间线
2. 更新 debts.json active/cleared
3. 将完整评论写入对应 creditor 的 notes 字段
4. git push
```

### notes 字段格式

```json
{
  "notes": "2026-07-05 更新: 石墨表同步\n\n📜 来时路·债主名：\n\n2022/5/17 XX事件，XX转账¥X,XXX\n2023/4/20 XX事件，XX转账¥XX,XXX，约定X%利息\n当时正在XX地点（高铁/酒店/老家...）\n\n备注：¥XX,XXX有来源记录，剩余¥X,XXX待补充。"
}
```

### debts.json 金额核对

石墨表总亲友债 vs 系统总亲友债 → 差值为石墨中已清但系统未同步的记录（如小马哥¥5K等），需手动确认。

## 注意事项

### OCR 陷阱（真实案例）
- **⚠️ 铁律：提取金额后必须向波总确认！人眼比 OCR 可靠**
- **OCR 完全失败不追问**：千问 VL + Apple Vision + Tesseract 三引擎都读不出的截图，直接告诉波总"这张读不出"。波总会自己说是什么。**案例**：157×1279 极窄竖条截图（宽高比 1:8），Apple Vision 只能读到碎片（"1900""-18"），Tesseract 全部乱码，6 种增强方法无效——正确做法是直接问波总，不浪费时间
- 度小满：`19432.55` 被 Tesseract 读成 `9432.55`（吞掉开头 "1"）→ 波总纠正
- 拿去花：`5303.51` 被 Tesseract 读成 `9303.51`（5→9 误读）→ 波总纠正
- 拿去花：Apple Vision 正确读出 `5,303.51`，验证了引擎升级的必要性
- `简余待还` = `剩余待还`（Tesseract 中文误读）
- 拿去花页面：区分三个数字——`剩余待还(元)` 总负债 / `累计账单金额` 本期消费 / `剩余应还` 本期扣退款后

### 千问 VL 配置陷阱
- **⚠️ API key 有效性**：DashScope key 格式为 `sk-xxx`，需在 [DashScope 控制台](https://dashscope.console.aliyun.com/apiKey) 获取。若返回 `invalid_api_key` 则 key 已过期/无效，立即降级到 Apple Vision
- **⚠️ home/config.yaml 浅覆盖**：profile 的 `home/config.yaml` 会**替换**（非深合并）主 config.yaml 的 `auxiliary.vision` 整个 dict。若 home 中只写了 `base_url` 和 `provider`，会丢失 `model`、`api_key`、`timeout`。症状：`_get_auxiliary_task_config('vision')` 返回 provider=dashscope 但 model=''、api_key=False。解法：home/config.yaml 的 `auxiliary.vision` 必须包含完整字段（provider + model + api_key + base_url + timeout），或用 `hermes config set` 逐字段写入
- **vision_analyze_tool 路由失败回退链**：dashscope → auto（OpenRouter → Nous → stop）。若三者均不可用 → RuntimeError。此时切换到直接 API 调用方式（`references/qwen-vl-direct-call.py`）或降级 Apple Vision

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

### 参考文件

| 文件 | 用途 |
|------|------|
| `references/visualization-and-gamification-research.md` | 游戏化设计研究 |
| `references/vision-config-architecture.md` | 🆕 vision_analyze 配置架构、API key 截断陷阱、双位置配置指南 |

### 金额更新命令
```bash
# 截图刷新（直接更新金额，非还款记录）
FINANCE_DIR=~/.hermes/adjutant/repo/hermes-adjutant/finance \
  python3 finance/scripts/finance.py update -c "花呗" -a <金额> -s "截图YYYY-MM-DD"
```
