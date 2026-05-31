---
name: chinese-ipo-research
description: Research Chinese A-share IPO companies by sector, retrieve prospectuses (招股说明书) from Chinese financial sites, and extract key sections. Covers searching, PDF retrieval, and deep-reading core sections (financials, competitive positioning, fundraising).
---

# Chinese IPO Research & Prospectus Retrieval

## When to Use
User asks to research Chinese listed companies, find IPO prospectuses, analyze recent IPOs by sector, or deep-read a specific company's 招股说明书.

## The 3 Data Sources (Priority Order)

| Source | Best For | Pattern |
|--------|----------|---------|
| **巨潮资讯网** (cninfo.com.cn) | Official filings, complete PDFs | `static.cninfo.com.cn/finalpage/{date}/{id}.PDF` |
| **新浪财经** (sina.com.cn) | Full-text inline prospectus, PDF download | `file.finance.sina.com.cn/211.154.219.97:9494/MRGG/...` |
| **东方财富** (eastmoney.com) | Company overview data, IPO stats | `data.eastmoney.com/xg/xg/detail/{code}.html` |

## Step-by-Step Workflow

### 1. Search for IPO Companies by Sector
```
web_search("{sector} 2024 2025 IPO 上市 招股说明书 主营业务")
web_search("近两年 {sector} 上市公司 科创板 创业板")
```

### 2. Collect Company Details
Use 东方财富 `data.eastmoney.com/xg/xg/detail/{code}.html` via browser for:
- Stock code, listing date, IPO price, PE ratio
- Industry classification
- The `browser_navigate` approach works well — the page includes a direct link "点击查看招股说明书pdf"

### 3. Retrieve the Prospectus PDF

#### Method A: 巨潮资讯网 (best for official PDFs)
```
curl -L -o "prospectus.pdf" "https://static.cninfo.com.cn/finalpage/{YYYY-MM-DD}/{id}.PDF"
```
⚠️ Pitfall: Some cninfo URLs are blocked by Hermes' network rules. Fall back to Method B.

#### Method B: 新浪财经 (reliable for full PDFs)
1. Navigate to: `https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?stockid={CODE}&id={BULLETIN_ID}`
2. **CRITICAL**: The page renders a PDF viewer (iframe/JS), not a direct download link.
3. Extract the actual PDF URL from page source:
   ```bash
   curl -s "SINA_PAGE_URL" | grep -oE 'file\.finance\.sina[^"]*' | head -1
   ```
4. Download with `curl -L -o "output.pdf" "EXTRACTED_URL"`
5. Verify: `file output.pdf` should report "PDF document, version 1.x, N pages"

#### Method C: 东方财富 (lightweight, for overview data only)
Browser navigate to `data.eastmoney.com/xg/xg/detail/{code}.html` — good for IPO statistics table but not for full prospectus PDF.

### 4. Extract & Interpret Key Sections

After downloading, use PyPDF2 to extract text from the critical pages:

```python
import PyPDF2
reader = PyPDF2.PdfReader('prospectus.pdf')

# Key pages to extract
KEY_SECTIONS = {
    'overview': (0, 35),        # Cover + 概览 + 风险因素
    'business': (85, 95),       # 第五节: 业务与技术
    'financials': (24, 28),     # 财务数据 + 募投项目
}
```

**The 7 sections to always read in a prospectus:**
1. **重大事项提示** (重大风险 + 特有风险) — Page ~11-16
2. **主营业务经营情况** — Page ~18-21
3. **发行人科创板定位** — Page ~22-24
4. **主要财务数据** — Page ~24-25
5. **募集资金用途** — Page ~25-26
6. **业务与技术** (第五节) — Page ~86+
7. **风险因素** (第三节) — Page ~27+

### 5. Present Results to User

**Format preferences:**
- Use labeled key:value pairs (not markdown tables) for Telegram
- Prioritize: 主营业务 → 核心竞争力 → 财务摘要 → 募投项目 → 风险
- Always include the three comparison dimensions: 赛道、军品占比、成长驱动
- Deliver the PDF file via `MEDIA:/absolute/path/to/file.pdf`

## Pitfalls

- **cninfo PDF blocks**: `static.cninfo.com.cn` URLs may fail with "private network" blocks. Immediately fall back to 新浪财经 source.
- **新浪 returns HTML not PDF**: When `curl` from sina returns HTML (`file` reports "HTML document"), you got the page wrapper, not the PDF. Extract the real URL with the grep pattern above.
- **Not all prospectuses are equal**: Registration draft (注册稿) may have placeholder pricing `【】`. The final listing prospectus has actual numbers. Both are useful — cite which version you're using.
- **macOS grep lacks `-P`**: Use `grep -oE` not `grep -oP` on macOS.
- **Bundled/protected skills warning**: `pdftotext` may not be installed. PyPDF2 is more reliable and available via pip.
