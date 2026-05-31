# Military IPO Case Studies (2023-2025)

## 航天南湖 (688552.SH) — "军工雷达第一股"

- **Listed**: 2023-05-18, SSE STAR Market
- **IPO Price**: 21.17 CNY | **Raised**: 17.85B CNY
- **Business**: Air defense early-warning radar R&D, production, sales, service
- **Products**: Surveillance radar, target indication radar, radar components
- **Military share**: >94%
- **Controlling shareholder**: CASIC Second Academy No. 23 Institute
- **Core edge**: Only listed air-defense radar integrator in China, 30+ year track record
- **Prospectus PDF**: `static.cninfo.com.cn/finalpage/2023-05-17/1216831256.PDF` (79 pages)
- **东方财富**: `data.eastmoney.com/xg/xg/detail/688552.html`

## 国科军工 (688543.SH) — 导弹弹药核心供应商

- **Listed**: 2023-06-21, SSE STAR Market
- **IPO Price**: 43.67 CNY | **Raised**: ~1.6B CNY
- **Business**: Missile/rocket solid-fuel engine power & control products + ammunition equipment
- **Products**: Solid engine modules, ammunition, missile control systems
- **Military share**: >96%
- **Controlling shareholder**: Jiangxi Provincial SASAC (via Jiangxi Military Industry Holding)
- **Core edge**: One of few domestic solid-engine module producers; first-to-market on 3 fuze types; 25 core technologies; 24 serial-production products; 24 R&D programs
- **Prospectus PDF (注册稿)**: Sina source — `file.finance.sina.com.cn/211.154.219.97:9494/MRGG/CNSESH_STOCK/2023/2023-4/2023-04-25/9092675.PDF` (351 pages)
- **2022 Revenue**: 837M CNY | **Net profit**: 113M CNY
- **Key risk**: Pre-audit pricing on main products DJ022/JK and DJ014/XF; 486M CNY long-dated AR from client F2

## Key Comparison

| Dimension | 航天南湖 | 国科军工 |
|-----------|---------|----------|
| Segment | Radar (defense detection) | Ammunition + propulsion (offense) |
| Military ratio | >94% | >96% |
| 2022 Revenue | ~950M | 837M |
| Growth driver | Export + new model deployment | Missile production ramp + new bid wins |
| Parent | CASIC (central SOE) | Jiangxi SASAC (local SOE) |

## Prospectus Retrieval Notes

- 航天南湖 PDF downloaded directly from cninfo.com.cn — fast and clean.
- 国科军工 注册稿 needed the Sina `file.finance.sina.com.cn` extraction method (cninfo only had 4-page notice, not full prospectus).
- The Sina page has a 351-page embedded PDF viewer; "下载" button triggers browser-level download that's hard to catch programmatically. The `grep -oE` method is more reliable.
