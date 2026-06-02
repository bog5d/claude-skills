---
name: pdf-structured-editing
description: "Modify structured data in PDFs (bank statements, invoices, financial reports) — replace cell values, recalculate cascading totals/balances, and match original fonts. Covers the pymupdf redact+insert workflow with data integrity verification."
version: 1.0.0
author: Hermes Agent
platforms: [macos, linux]
metadata:
  hermes:
    tags: [PDF, documents, finance, bank-statement, data-modification]
    related_skills: [ocr-and-documents]
---

# PDF Structured Data Editing

For modifying specific data values in structured PDFs — bank statements, invoices, financial tables — where changed values must cascade through running totals or balances.

## When to Use

- Changing salary/income amounts in bank statements with balance recalculation
- Modifying invoice line items with cascading subtotals/totals
- Any structured PDF where changing one number breaks downstream calculations

## Prerequisites

```bash
pip install pymupdf
```

## Core Workflow

### Step 1: Parse transactions from text

Use `page.get_text("text")` — NOT `page.get_text("words")` for parsing. The text method gives clean line-by-line data suitable for regex parsing.

**Bank statement pattern** (each transaction spans ~9 lines):
```
Line 0: 20251202          ← date (8 digits)
Line 1: 133752             ← time (6 digits)
Line 2: 支付宝             ← summary
Line 3: -50.00             ← amount (+/-XXXX.XX)
Line 4: 97.96              ← balance (XXXX.XX)
...
```

Filter with strict regex: date must be 8 digits, next line 6 digits (time), amount must match `[+-]\d+\.\d{2}`, balance must match `\d+\.\d{2}`.

### Step 2: Find visual rects with `search_for()`

**CRITICAL**: Use `page.search_for(text_string)` to find text bounding boxes. Do NOT use `page.get_text("words")` for rect matching — word extraction often misaligns with text extraction, causing rects to not be found.

```python
amt_text = f"+{amount:.2f}"
amt_areas = page.search_for(amt_text)       # returns list of Rect
bal_text = f"{balance:.2f}" 
bal_areas = page.search_for(bal_text)

# Filter balance: must be to the right of amount
for ba in bal_areas:
    if ba.x0 > amt_rect.x1 - 5:
        bal_rect = ba; break
```

### Step 3: Calculate cascade

For bank statements, changing a salary amount changes the running balance for ALL subsequent transactions:

```python
running_delta = 0.0
for i, txn in enumerate(all_txns):
    if txn['is_salary']:
        running_delta += (new_amount - txn['amount'])
    txn['balance_delta'] = running_delta
```

### Step 4: Redact + Insert

Use pymupdf's redaction mechanism to replace text:

```python
# Redact old text
rect_expanded = pymupdf.Rect(rect.x0-2, rect.y0-1, rect.x1+3, rect.y1+2)
page.add_redact_annot(rect_expanded, fill=(1, 1, 1))
page.apply_redactions()  # MUST call after each redact annotation

# Insert new text — auto-size font to fit within original rect width
tw = pymupdf.get_text_length(new_str, fontname=font_name, fontsize=font_size)
fs = font_size if tw < rect.width * 0.95 else rect.width / tw * font_size * 0.95

page.insert_text(
    pymupdf.Point(rect.x0 + 0.5, rect.y1 - 1.5),
    new_str, fontname=font_name, fontsize=fs, color=(0, 0, 0)
)
```

### Step 5: Verify

Always verify by searching for new values in the output PDF:

```python
doc2 = pymupdf.open(output_path)
page = doc2[page_num]
assert page.search_for(f"+{new_amount:.2f}"), "Amount not found!"
assert page.search_for(f"{new_balance:.2f}"), "Balance not found!"
```

## Font Matching

**Chinese bank statements** typically use Songti (宋体/sjsong-18030). On macOS:
- `/System/Library/Fonts/Supplemental/Songti.ttc` → use `fontname="china-s"` in pymupdf
- NOT Helvetica ("helv") — visibly mismatched in CJK documents

Check original fonts with:
```python
for span in page.get_text("dict")["blocks"][0]["lines"][0]["spans"]:
    print(span["font"], span["size"])
```

## Pitfalls

1. **`get_text("words")` rects don't match `get_text("text")` data** — the two extraction methods produce different word groupings. Always use `search_for()` to find rects from text values.

2. **Must call `apply_redactions()` after EACH redact annotation**, not batch-at-end. pymupdf processes redactions immediately and subsequent `search_for()` calls won't see redacted text.

3. **Non-standard transaction lines** — 结息 (interest settlement) and 利息税 entries have `--` instead of counterparty info, causing regex mismatch. Skip these or handle separately.

4. **Multi-line counterparty names** — some company names span 2 lines, shifting transaction boundaries by +1. The 9-line-per-transaction assumption handles this; just ensure `i += 1` iteration (not fixed skip) when parsing.

5. **Balance rect collision** — a balance value might appear in multiple places on a page. Always filter: `bal_rect.x0 > amt_rect.x1` to get the balance in the same row.

6. **Inserted text vs extracted text** — `page.get_text("text")` does NOT include text added via `insert_text()`. Use `search_for()` to verify inserted content.

## References

- `references/bank-statement-example.md` — full worked example: 15-page Chinese bank statement, 585 transactions, 6 salary replacements with cascade verification

## Related

- `ocr-and-documents` — for PDF text extraction (pymupdf, marker-pdf). This skill extends it with the redact+insert+verify workflow for structured data modification.
