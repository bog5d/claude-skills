---
name: encrypted-excel-ddd-clean
description: 接收加密Excel→解密→DDD大宽表清洗→加密输出xlsx。适用于投资尽调订单重构、多段式表格合并等场景。
category: devops
trigger: 用户发送加密.xls/.xlsx + 密码 + DDD清洗指令
---

# 加密 Excel → DDD 大宽表清洗 → 加密输出

## 触发条件
- 用户发送加密 Excel 文件（.xls/.xlsx）+ 密码
- 用户要求重构多段式表格为单一宽表
- 涉及 L1/L2/L3 订单分级

## 核心工具链
| 步骤 | 工具 | 作用 |
|------|------|------|
| 解密 | `msoffcrypto.OfficeFile(f).load_key(password='...').decrypt(out)` | 读加密文件 |
| 读取 | `xlrd.open_workbook()` (xls) 或 `openpyxl.load_workbook()` (xlsx) | 解析数据 |
| 清洗 | Python 内存处理 | DDD 规则映射 |
| 写出 | `openpyxl.Workbook()` | 生成 xlsx |
| 加密 | `msoffcrypto.OfficeFile(f).encrypt(password, outfile)` | 回加密 |

## msoffcrypto 关键 API

```python
import msoffcrypto, io

# 解密
dec = io.BytesIO()
with open(src, 'rb') as f:
    of = msoffcrypto.OfficeFile(f)
    of.load_key(password='18')
    of.decrypt(dec)
dec.seek(0)

# 加密（注意签名：encrypt(self, password, outfile) — password是第一个位置参数）
with open(plain, 'rb') as f:
    of = msoffcrypto.OfficeFile(f)
    with open(out, 'wb') as outf:
        of.encrypt('18', outf)  # password 在前，outfile 在后
```

## 标准清洗规则

### 订单级别映射
- 上半段（已签合同行）→ L1
- 下半段 已外借/已发货/部分发货 → L2
- 下半段 未发货 + 投产函/中标 → L3

### 字段映射
| 输出字段 | L1来源 | L2/L3来源 |
|----------|--------|-----------|
| 订单级别 | L1 | L2/L3 |
| 客户名称 | col[4] | col[4] |
| 产品型号 | col[6]（空则用col[5]合同名回填） | col[5] |
| 核心确收凭证 | 正式合同 | 外借出库单/发货单/投产函/中标通知书 |
| 凭证编号/备注 | col[3]合同编号 | 投产函X套 + col[11]备注 |
| 总金额(万元) | col[7]元÷10000 | col[8]万元（不变） |
| 当前业务进度 | 已收X万/待回款 | col[6]发货情况 |

### Excel日期转换
```python
from datetime import datetime, timedelta
base = datetime(1899, 12, 30)
date = (base + timedelta(days=int(serial))).strftime('%Y-%m-%d')
```

## 输出格式
- Sheet 名称保持与原始一致
- 三级颜色分层：L1绿 #E2EFDA / L2黄 #FFF2CC / L3橙 #FCE4D6
- 表头深蓝 #2F5496 白字
- 首行冻结 + 自动筛选
- 末尾附加汇总行
- 密码与原文件保持一致

## 陷阱
- xlrd 不支持加密文件，必须先 msoffcrypto 解密
- xlrd 2.x 不支持 xlsx，只能读 xls
- xlrd 在 Python 3.11+ 读 xlsx 有 `getiterator` 兼容问题，验证用 openpyxl
- msoffcrypto.encrypt() 签名是 `encrypt(password, outfile)` 不是 `encrypt(outfile, password)`
- openpyxl 不支持密码写入，加密必须走 msoffcrypto
- 原始 xls 的金额单位是元，需 ÷10000 转为万元
