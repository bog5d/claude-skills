#!/usr/bin/env python3
"""波总账单CSV导入器 — 支付宝GBK CSV / 微信xlsx → 自动解析+过滤+分类+去重.

用法:
    python3 import_csv.py alipay_utf8.csv          # 支付宝CSV（已转UTF-8）
    python3 import_csv.py wechat_bill.xlsx          # 微信xlsx
"""

import csv, json, sys, os, re, io, datetime
from pathlib import Path
from collections import defaultdict

_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~")))
if ".hermes/profiles/" in str(_HOME):
    _HOME = Path("/Users/mac")
FINANCE_DIR = Path(os.environ.get("FINANCE_DIR", str(_HOME / ".hermes/adjutant/finance")))
EXPENSES_FILE = FINANCE_DIR / "expenses.json"


def load_expenses():
    with open(EXPENSES_FILE) as f:
        return json.load(f)


def save_expenses(data):
    with open(EXPENSES_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_alipay(filepath):
    """
    Parse Alipay CSV (already UTF-8). Returns list of {date, amount, merchant}.

    🛑 过滤铁律：只要涉及支付宝内部资金流转（理财/余额宝/小荷包/定时转入），都跳过，不管方向字段。
    真实翻车：2026-06-29 余额宝每天¥500定时转入，方向="支出"，217条全被当消费导入。
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    idx = content.find("交易时间,交易分类,交易对方")
    if idx == -1:
        return [], "Alipay header not found"

    data_lines = content[idx:].split("\n")[1:]
    results = []
    skipped = defaultdict(int)

    for line in data_lines:
        line = line.strip()
        if not line or line.startswith("-"):
            continue
        parts = line.split(",")
        if len(parts) < 7:
            continue

        date_str = parts[0].strip()
        tx_category = parts[1].strip() if len(parts) > 1 else ""
        merchant = parts[2].strip()
        desc = parts[4].strip() if len(parts) > 4 else ""
        direction = parts[5].strip()

        try:
            amount = float(parts[6].strip().replace(",", ""))
        except ValueError:
            continue

        # ── 过滤链 ──

        # 1. 零金额跳过
        if amount <= 0:
            skipped["zero_amount"] += 1
            continue

        # 2. 非支出方向跳过
        if direction != "支出":
            skipped["non_expense"] += 1
            continue

        # 3. 投资理财全类跳过（余额宝/基金等，不管方向）
        if tx_category in ("投资理财",):
            skipped["investment"] += 1
            continue

        # 4. 退款类跳过（这是退款本身，不是原始购买）
        if "退款" in tx_category:
            skipped["refund"] += 1
            continue

        # 5. 关键字跳过：支付宝内部资金流转
        skip_keywords = ["个人所得税", "缴税", "余额宝", "基金", "转账", "小荷包"]
        if any(kw in merchant + desc + tx_category for kw in skip_keywords):
            skipped["excluded"] += 1
            continue

        merchant_clean = merchant if merchant and merchant != "/" else desc[:30]

        results.append({
            "date": date_str[:10],
            "amount": amount,
            "merchant": merchant_clean,
        })

    return results, dict(skipped)


def parse_wechat(filepath):
    """Parse WeChat xlsx bill. Returns list of {date, amount, merchant}."""
    try:
        import openpyxl
    except ImportError:
        return [], "openpyxl not installed. Run: pip3 install openpyxl"

    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active
    results = []
    skipped = defaultdict(int)

    for row in ws.iter_rows(min_row=19, values_only=True):
        if not row[0]:
            continue
        date_str = str(row[0]).strip()
        tx_type = str(row[1]).strip() if row[1] else ""
        merchant = str(row[2]).strip() if row[2] else ""
        product = str(row[3]).strip() if row[3] else ""
        direction = str(row[4]).strip() if row[4] else ""

        try:
            amount = float(str(row[5]).replace("¥", "").replace(",", "").strip()) if row[5] else 0
        except (ValueError, TypeError):
            continue

        if direction != "支出":
            skipped["non_expense"] += 1
            continue

        # Skip transfers, red packets, props, repayment
        if tx_type in ("转账", "红包", "零钱充值", "零钱提现", "信用卡还款", "分付还款"):
            skipped["excluded"] += 1
            continue

        desc = product if product and product != "/" else merchant

        results.append({
            "date": date_str[:10],
            "amount": amount,
            "merchant": desc[:60],
        })

    return results, dict(skipped)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 import_csv.py <file>")
        sys.exit(1)

    filepath = sys.argv[1]
    ext = Path(filepath).suffix.lower()

    if ext == ".csv":
        items, stats = parse_alipay(filepath)
        platform = "支付宝"
    elif ext in (".xlsx", ".xls"):
        items, stats = parse_wechat(filepath)
        platform = "微信"
    else:
        print(f"Unsupported format: {ext}")
        sys.exit(1)

    if not items:
        print(f"No items found. Stats: {stats}")
        sys.exit(0)

    # Load existing expenses
    data = load_expenses()
    categories = data.get("categories", {})

    # Dedup and classify
    sys.path.insert(0, str(FINANCE_DIR))
    from scripts.expenses import classify

    added = 0
    dupes = 0

    for item in items:
        cat = classify(item["merchant"], categories)
        dedup_key = f"{item['date']}_{round(item['amount'], 0)}_{item['merchant'][:4]}"

        is_dupe = False
        for existing in data["expenses"]:
            if existing.get("dedup_key") == dedup_key:
                is_dupe = True
                break
            if (existing["date"] == item["date"] and
                abs(existing["amount"] - item["amount"]) <= 1.0):
                from difflib import SequenceMatcher
                if SequenceMatcher(None, existing["merchant"].lower(), item["merchant"].lower()).ratio() > 0.5:
                    is_dupe = True
                    break

        if is_dupe:
            dupes += 1
            continue

        expense = {
            "id": f"E{len(data['expenses']) + added + 1:03d}",
            "date": item["date"],
            "amount": item["amount"],
            "merchant": item["merchant"],
            "category": cat,
            "source": f"{platform}CSV",
            "screenshot_id": Path(filepath).stem,
            "dedup_key": dedup_key,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        data["expenses"].append(expense)
        added += 1

    data["meta"]["total_expenses"] = len(data["expenses"])
    data["meta"]["total_amount"] = round(sum(e["amount"] for e in data["expenses"]), 2)
    data["meta"]["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    save_expenses(data)

    print(json.dumps({
        "platform": platform,
        "file": Path(filepath).name,
        "total_rows": len(items),
        "added": added,
        "duplicates": dupes,
        "new_total": len(data["expenses"]),
        "new_amount": round(data["meta"]["total_amount"], 2),
        "skipped": stats,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
