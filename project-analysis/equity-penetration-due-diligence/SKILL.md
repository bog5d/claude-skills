---
name: equity-penetration-due-diligence
description: 中国企业股权穿透尽调——输入公司名称，自动穿透多层股权结构，生成结构化PDF报告。覆盖开源工具(ENScan_GO)、商业API、Cookie配置、PDF报告生成全链路。
trigger: "波总说'查一下这家公司的股权结构'、'穿透一下'、'股权尽调'、'股东穿透'、'谁是实控人'"
---

# 股权穿透尽调 — 全链路

## 工具选型速查

| 方案 | 成本 | 穿透深度 | 适用 |
|---|---|---|---|
| **ENScan_GO** ⭐4.4k | 免费（需Cookie） | 多层（`--deep N`） | 个人尽调、快速穿透 |
| 企查查开放平台 | 5-20万/年（面议） | 完整 + UBO | 机构级、合规 |
| 天眼查开放平台 | 面议 | 完整 | 机构级 |
| 爱企查 | 相对最实惠 | 基本 | ENScan_GO默认源 |

**推荐路径**: ENScan_GO + 爱企查 Cookie → 足够覆盖90%的尽调需求。

---

## Step 1: 安装 ENScan_GO

### 方式A：下载预编译二进制（推荐，macOS ARM64）

```bash
# 下载最新版
curl -sL -o /tmp/enscan.tar.gz \
  'https://github.com/wgpsec/ENScan_GO/releases/download/v2.0.5/enscan-v2.0.5-darwin-arm64.tar.gz'
tar xzf /tmp/enscan.tar.gz -C /tmp
mkdir -p ~/.hermes/tools/enscan
mv /tmp/enscan-v2.0.5-darwin-arm64 ~/.hermes/tools/enscan/enscan
chmod +x ~/.hermes/tools/enscan/enscan
```

### 方式B：源码编译（需Go 1.22+）

```bash
cd /tmp && git clone https://github.com/wgpsec/ENScan_GO.git
cd ENScan_GO && go build -o ~/.hermes/tools/enscan/enscan .
```

### 初始化配置

```bash
~/.hermes/tools/enscan/enscan -v
# 生成 ~/.hermes/tools/enscan/config.yaml
```

---

## Step 2: 配置数据源 Cookie

### 2.1 获取爱企查 Cookie（推荐首选，免费）

1. Chrome 打开 [aiqicha.baidu.com](https://aiqicha.baidu.com)
2. 微信/百度账号扫码登录
3. F12 → **Application** → Cookies → `aiqicha.baidu.com`
4. ⚠️ **不要用 `document.cookie`**——会漏掉 httpOnly 字段导致登录态不完整
5. 推荐：Chrome 插件 **EditThisCookie** 一键导出完整 Cookie 字符串
6. 填写到 `config.yaml`:

```yaml
cookies:
  aiqicha: '你的完整Cookie字符串'
```

### 2.2 其他数据源（可选）

| 数据源 | 配置字段 | 获取方式 |
|---|---|---|
| 天眼查 | `tianyancha` + `tycid` + `auth_token` | capi.tianyancha.com 登录后抓包 |
| 风鸟 | `risk_bird` | 登录后取 Cookie |
| 七麦数据 | `qimai` | 登录后取 Cookie |

---

## Step 3: 测试查询

```bash
# 基本查询
~/.hermes/tools/enscan/enscan -n 小米 -type aqc

# 控股穿透（控股≥51% + 分支机构 + 2层孙公司）
~/.hermes/tools/enscan/enscan -n 小米 -invest 51 --branch --deep 2 -type aqc -json

# 多字段查询
~/.hermes/tools/enscan/enscan -n 小米 -invest 51 -field icp,app,wechat,copyright -json
```

### 关键参数

| 参数 | 说明 | 示例 |
|---|---|---|
| `-n` | 公司名关键词 | `-n 小米` |
| `-invest` | 控股比例阈值 | `-invest 51` (≥51%) |
| `--deep` | 穿透层级 | `--deep 3` |
| `--branch` | 含分支机构 | |
| `-field` | 获取字段 | `icp,app,wechat,copyright` |
| `-json` | JSON输出 | |
| `-type` | 数据源 | `aqc`(爱企查) `tyc`(天眼查) `all` |
| `--mcp` | 开启MCP服务 | 监听 localhost:8080 |

---

## Step 4: 生成 PDF 报告

使用内置报告脚本 `equity_report.py`（见 `scripts/equity_report.py`）：

```bash
python3 ~/.hermes/tools/enscan/equity_report.py 小米 --deep 3 --invest 51
# → 输出: ~/.hermes/cache/documents/小米_股权穿透报告.pdf
```

报告包含：
- 企业基本信息（名称/PID/法人/注册资本/状态/成立日期）
- 股权穿透结构表（按持股比例排序）
- 数据来源与免责声明

依赖：`weasyprint` → 如不可用则 fallback 到 `pandoc --pdf-engine=weasyprint`。

---

## 与其他技能的关系

- **shell-company-analysis**: 覆盖A股壳公司财务/合规评估，本技能覆盖股权结构数据抓取。两者可组合：ENScan 抓股权 → 喂给壳分析框架
- **chinese-ipo-research**: IPO公司研究，侧重点不同

---

## 陷阱

1. **Cookie是刚需**：不用Cookie完全无法查询，不登录爱企查什么都跑不了
2. **不要用 `document.cookie`**：会丢失 httpOnly 字段，导致登录态不完整
3. **MIIT插件需要额外配置**：`miit_api` URL 需填写 HG-ha 的 ICP_Query 服务地址，否则 MIIT 查询会报 `unsupported protocol scheme ""`
4. **请求频率**：建议加 `-delay 3` 防止触发反爬，爱企查风控敏感
5. **数据完整性**：工商数据仅反映公开登记，不含代持/VIE/信托等非公开权益
6. **商业API价格**：企查查/天眼查开放平台大部分接口"面议"，实际报价通常5-20万/年起
