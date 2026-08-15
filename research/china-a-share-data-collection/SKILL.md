---
name: china-a-share-data-collection
description: 查A股公司股东/实控人/财务/监管数据时用。Firecrawl MCP + 搜狐URL工具链。
trigger: "查A股公司股东/实控人/股权/财务/公告/监管数据、做标的/壳/IPO尽调采集数据、'这公司前十大股东是谁''实控人是谁''业绩趋势'"
---

# China A-share Data Collection — 已验证的 A 股数据抓取工具链

## 何时用

任何需要从中国金融网站拉取 A 股上市公司结构化数据（前十大股东、实控人、财务、公告、监管处罚、解禁）的场景。是 shell-company-analysis / shell-control-acquisition / chinese-ipo-research 等评估技能的**底层数据采集层**。

## 抓取工具（按可靠性排序，首选排第一）

1. **Firecrawl MCP `firecrawl_scrape`** — `formats:["markdown"]` + `onlyMainContent:true` + `maxAge:0`
   - 对搜狐证券、网易财经、新浪财经等中文页面有效，**自动处理 GBK 编码**，直接返回可读 Markdown 表格。
   - 2026-08 实战：搜狐证券股东页、网易一季报文章均一次抓取成功。
2. **web_search 引号精确匹配** — 用 `"XX万股" "占总股本"` 从新闻片段抠具体数字（当全文页面抓不到时）。
3. **terminal curl 东方财富 push2 API** — 需带 `Referer: https://quote.eastmoney.com/`，字段名不稳定，每次先试。

## 具体 URL 模式

- **前十大股东（最快入口）**：`https://q.stock.sohu.com/cn/{code}/zygd.shtml`
  → 一次返回完整前十大股东表（持股数量/比例/变化/股本性质）+ 实控人/一致行动说明 + "一年内即将解禁限售股"表。
- **流通股股东**：`https://q.stock.sohu.com/cn/{code}/ltgd.shtml`
- **限售解禁表**：`https://q.stock.sohu.com/cn/{code}/xsjj.shtml`
- **公司概况（法人/董秘/注册资本/上市日期）**：`https://q.stock.sohu.com/cn/{code}/index.shtml`
- **东财实时行情 API**：`https://push2.eastmoney.com/api/qt/stock/get?secid=0.{code}&fields=f43,f57,f58,f60,f84,f85,f116,f117,f162,...`（创业板 secid=0.{code}，沪市=1.{code}）
- **巨潮公告原文（权威 PDF）**：`https://static.cninfo.com.cn/finalpage/{date}/{id}.PDF`

## 股权核验必查数据点清单

1. 前十大股东 + 持股比例/变化
2. 实控人 + 一致行动协议签署方/有效期（**实控人常藏在控股股东里，不出现在前十大**——需穿透控股股东的股权结构）
3. 首发原始股解禁日期 → 判断实控人"卖不卖"的关键窗口
4. 实控人/高管是否被留置、军队采购网处罚、**军采禁入**（对军工产业方尤其致命）
5. 前十大股东/历史股权中是否有**已爆雷资本系族旧人马**（中技系/中植系/明天系等）

## 陷阱

- **`web_extract` 不可用于中国金融网站**（DuckDuckGo 后端仅搜索不提取）——直接跳过，用 Firecrawl。
- **`execute_code` 在 cron/无用户在场模式会被 BLOCKED**（"arbitrary local Python"）；`terminal` curl 也可能超时 BLOCKED。**遇 BLOCKED 不要重试同一命令，直接切 Firecrawl MCP。**
- **不要仅凭市值小/股东分散就下结论**——股权结构要先核到"一致行动关系 + 解禁时点 + 历史资本系族印记"三件事。
