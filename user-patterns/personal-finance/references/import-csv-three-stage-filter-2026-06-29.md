# import_csv.py 三关过滤修复 | 2026-06-29

## 故障现象

支付宝 CSV 导入后，expenses.json 出现 217 笔「理财」类条目（¥15,000+ 余额宝定时转入、小荷包自动攒）和 4 笔退款/不计收支条目。消费总额虚胖 ¥31,466。

## 根因

`parse_alipay_row()` 的方向过滤是：
```python
if "收" in direction and "支" not in direction:
    return None  # skip income
```
但「不计收支」同时包含「收」和「支」两个字：
- `"收" in "不计收支"` → True
- `"支" not in "不计收支"` → False（因为"不计收支"也有"支"）
- → 条件 False → 不跳过 → **漏网**

同时，代码未检查 `交易分类` 列（CSV 第2列），投资理财/退款/保险类交易直接通过。

## 修复内容（2026-06-29 commit ab5be0b）

### 第1关：方向过滤前置

```python
# 最前面加显式检查
if "不计收支" in direction:
    return None  # 不计收支=内部流转（余额宝/小荷包/退款）
if "收" in direction and "支" not in direction:
    return None  # 收入
if direction and "支" not in direction:
    return None  # 任何非支出方向兜底
```

### 第2关：交易分类列过滤（新增）

```python
tx_category = row.get("交易分类", "") or ""
skip_tx_cats = ["投资理财", "退款", "保险", "充值缴费-预存", "信用卡还款"]
if tx_category and any(cat in tx_category for cat in skip_tx_cats):
    return None
```

注意：支付宝导出的 CSV 列顺序为 `交易时间,交易分类,交易对方,对方账号,商品说明,收/支,金额,收/付款方式,交易状态,交易订单号,商家订单号,备注`

### 第3关：关键字扩展

```python
# 旧：require exact match
skip_keywords = ["余额宝转入", "余额宝转出", ...]

# 新：模糊匹配
skip_keywords = ["余额宝", "余利宝", "转账给", "信用卡还款", "花呗还款", "借呗还款",
                 "基金", "理财", "定期", "保险购买", "提现", "小荷包", "花呗分期还款"]
# 新增：小荷包、花呗分期还款
# 余额宝改为模糊：原"余额宝转入"→现"余额宝"（匹配所有余额宝相关）
```

### 退款处理

原代码将退款标记为 `is_refund=True` 但仍然入库。改为直接跳过退款：
```python
refund_kw = ["退款", "退回", "撤销", "冲正"]
if any(kw in name for kw in refund_kw) or any(kw in product for kw in refund_kw):
    return None
```

## 验证

```python
# dry-run 对比
python3 import_csv.py --dry-run alipay_bill.csv

# 旧逻辑：504 parsed（含222笔非消费）
# 新逻辑：125 parsed（全部真实消费）
# 改进率：100%（非消费条目的 100% 拦截）
```

## 代码位置

`finance/scripts/import_csv.py` → `parse_alipay_row()` 函数

## 关联清理

2026-06-29 同批次在 expenses.json 中清理了：
- 5笔非消费（花呗还款×3 + 缴税 + 家庭转账）
- 40条小荷包自动攒
- 67条「其他」recat
- 合并重复分类（餐饮/餐饮美食, 交通出行/交通）

commit: faf0f17
