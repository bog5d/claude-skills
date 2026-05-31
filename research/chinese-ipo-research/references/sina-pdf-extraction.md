# Extracting PDF URLs from Sina Finance Prospectus Pages

## Problem
新浪财经 renders prospectuses in a JavaScript PDF viewer — the page itself is HTML, and `curl`ing the page URL returns HTML, not PDF. You need the actual underlying PDF URL.

## Solution

### Step 1: Get the page source
```bash
curl -s "https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?stockid={CODE}&id={BULLETIN_ID}"
```

### Step 2: Extract the PDF URL
```bash
curl -s "SINA_URL" | grep -oE 'file\.finance\.sina[^"]*'
```

Returns something like:
```
file.finance.sina.com.cn/211.154.219.97:9494/MRGG/CNSESH_STOCK/2023/2023-4/2023-04-25/9092675.PDF
```

### Step 3: Download
```bash
curl -L -o "output.pdf" "http://EXTRACTED_URL"
```

### Step 4: Verify
```bash
file output.pdf
# Should report: "PDF document, version 1.x, N pages"
```

## Notes
- The host `211.154.219.97:9494` is consistent across filings — just the path varies.
- On macOS, use `grep -oE` not `grep -oP` (no Perl regex).
- If `grep` returns empty, fall back to browser navigation and use the PDF viewer's download button via `browser_click`.
