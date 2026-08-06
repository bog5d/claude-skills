---
name: excel-desensitization
description: 接收加密.xls/.xlsx + 密码 → 解密 → 脱敏 → 加密输出。替换公司名/客户名/金额扰动。
category: devops
trigger: 用户发加密Excel要求脱敏，或"替换公司名""去掉敏感信息"等指令
---

# Excel 脱敏管道

## 触发条件
- 用户发送加密 .xls/.xlsx 文件 + 密码
- 要求脱敏、去掉敏感信息、替换公司名/客户名、金额处理
- 文件需发给第三方但不能暴露原始数据

## 工具链
| 步骤 | 工具 | 作用 |
|------|------|------|
| 解密 | `msoffcrypto.OfficeFile(f).load_key(password=...).decrypt(out)` | 读加密文件 |
| 读取 | `xlrd.open_workbook()` (xls) 或 `openpyxl.load_workbook()` (xlsx) | 解析数据 |
| 脱敏 | Python 内存处理 | 替换实体名 + 扰动金额 |
| 写出 | `openpyxl.Workbook()` | 生成 xlsx |
| 加密 | `msoffcrypto.OfficeFile(f).encrypt(password, outfile)` | 回加密 |

## 脱敏规则

### 1. 实体名替换
- **公司名**：维护固定映射表，主公司和子公司分别替换为 XX公司 / 子公司A / 子公司B
- **客户/供应商名**：用 Python `dict` 做去重映射，首次出现的原名 → 客户1/供应商1，后续同原名用同一个编号
- **签署人**：正则替换为张XX/李XX/王XX（替换法定代表人、主管会计工作负责人、会计机构负责人等）

### 2. 金额扰动
- 扰动因子 `random.uniform(0.70, 1.30)`，保留原始小数精度
- **关键排除项（这些不是金额，绝对不能扰动）：**
  - 年份：`2000 <= val <= 2099` 且是整数
  - **Excel 日期序列号**：`30000 <= val <= 60000` 且是整数（如 46203.0 = 2026-06-30）——这是最常见的误扰动源
  - 序号/小整数：`abs(val) <= 100` 且是整数

### 3. Sheet 名处理
Sheet 名如果含公司名也跟着替换。注意 `openpyxl` Sheet 名最长 31 字符。

## 输出规范
- 密码与原文件保持一致
- 不用样式继承（xlrd→openpyxl 格式跨库转换容易丢），简单输出：宋体/微软雅黑 10pt，冻结首行
- 自动列宽：中文算 2 宽度，上限 40
- 回复中必须附脱敏摘要：几个 Sheet、替换了几个客户名/供应商名
- **必须声明**「金额已随机扰动，仅供脱敏展示，财务勾稽关系不平是正常的」

## 验证步骤
1. 解密后跑一遍读取，确认所有 Sheet 可访问
2. 脱敏后抽查关键 Sheet 的前 15 行，确认：
   - 公司名已全部替换
   - 客户名列已变成客户1/客户2...
   - 日期序列号（如 46203.0）未被动
   - 金额已变化且量级合理
3. 加密后用密码验证可解密

## 陷阱
- `msoffcrypto.encrypt()` 签名是 `encrypt(password, outfile)`，不是 `encrypt(outfile, password)`
- `xlrd` 2.x 不支持 xlsx，只能读 xls；读 xlsx 用 `openpyxl`
- `openpyxl` 不支持密码写入，加密必须走 `msoffcrypto`
- Excel 日期序列号（46203.0 之类）在 xlrd 里读出来是 float，极易被当成金额误扰动
- `xlrd` 和 `openpyxl` 之间的格式不能跨库复制（前者读样式→后者写样式走不通），直接用 openpyxl 写新文件即可
- `openpyxl` 写入的公式没有缓存值，但脱敏场景一般不涉及公式，直接用数据写入即可

## 参考脚本
完整脱敏脚本模板见 `scripts/desensitize_template.py`。
