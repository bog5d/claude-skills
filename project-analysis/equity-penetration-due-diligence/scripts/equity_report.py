#!/usr/bin/env python3
"""
ENScan 股权穿透 PDF 报告生成器
用法: python3 equity_report.py 小米
      python3 equity_report.py 小米 --deep 3 --invest 51
"""

import sys
import json
import os
import subprocess
import argparse
import tempfile
from datetime import datetime

ENSCAN_BIN = os.path.expanduser("~/.hermes/tools/enscan/enscan")
OUT_DIR = os.path.expanduser("~/.hermes/cache/documents")

def run_enscan(company, deep=2, invest=51, timeout=120):
    """运行 ENScan 获取 JSON 结果"""
    args = [
        ENSCAN_BIN, "-n", company,
        "-deep", str(deep),
        "-invest", str(invest),
        "-json",
        "--branch",
        "-field", "icp,app,wechat,weibo,copyright"
    ]
    
    print(f"[ENScan] 正在查询: {company} (穿透{deep}层, 控股>{invest}%)")
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    
    # ENScan outputs JSON mixed with ANSI/banner, extract JSON part
    stdout = result.stdout
    # Try to find JSON array in output
    json_start = stdout.find("[{")
    if json_start < 0:
        json_start = stdout.find("{\"")
    if json_start < 0:
        json_start = stdout.find("[{")
    
    if json_start >= 0:
        try:
            return json.loads(stdout[json_start:])
        except json.JSONDecodeError:
            pass
    
    # Fallback: save raw output
    print(f"[ENScan] Could not parse JSON, saving raw output")
    return {"raw": stdout, "stderr": result.stderr, "company": company}

def build_report_html(data, company, deep, invest):
    """构建 HTML 报告"""
    companies = data if isinstance(data, list) else [data]
    
    # Extract info
    main_info = {}
    for item in companies:
        if isinstance(item, dict):
            name = item.get("company_name", item.get("name", ""))
            if company in name or not main_info:
                main_info = item
    
    name = main_info.get("company_name", main_info.get("name", company))
    pid = main_info.get("pid", "")
    legal_person = main_info.get("legal_person", main_info.get("legalPerson", ""))
    reg_capital = main_info.get("reg_capital", main_info.get("regCapital", ""))
    status = main_info.get("status", "")
    establish_date = main_info.get("establish_date", main_info.get("fromTime", ""))
    
    rows = ""
    for item in companies:
        if isinstance(item, dict):
            n = item.get("company_name", item.get("name", "?"))
            p = item.get("percent", item.get("ratio", ""))
            r = item.get("reg_capital", item.get("regCapital", ""))
            s = item.get("status", "")
            rows += f"<tr><td>{n}</td><td>{p}</td><td>{r}</td><td>{s}</td></tr>"
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{name} 股权穿透报告</title>
<style>
@page {{ size: A4; margin: 2cm 1.5cm; }}
body {{ font-family: "PingFang SC","STHeiti",sans-serif; font-size: 11pt; color:#222; line-height:1.7; }}
.cover {{ text-align:center; padding:6em 0 4em; page-break-after:always; }}
.cover h1 {{ font-size:28pt; margin-bottom:.3em; }}
.cover .sub {{ color:#888; font-size:14pt; }}
.cover .date {{ color:#aaa; margin-top:2em; }}
.section {{ margin:2em 0; }}
.section h2 {{ font-size:16pt; border-bottom:2px solid #2563eb; padding-bottom:.3em; color:#1e40af; }}
.info-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:.5em 2em; }}
.info-grid .label {{ color:#666; }}
.info-grid .value {{ font-weight:bold; }}
table {{ width:100%; border-collapse:collapse; margin:1em 0; font-size:10pt; }}
th {{ background:#2563eb; color:#fff; padding:.5em; text-align:left; }}
td {{ padding:.4em .5em; border-bottom:1px solid #e5e7eb; }}
tr:nth-child(even) {{ background:#f8fafc; }}
.footer {{ text-align:center; color:#aaa; font-size:9pt; margin-top:3em; border-top:1px solid #e5e7eb; padding-top:1em; }}
.warn {{ background:#fef3c7; border-left:3px solid #f59e0b; padding:.8em 1em; margin:1em 0; }}
</style>
</head>
<body>

<div class="cover">
    <h1>{name}</h1>
    <div class="sub">股权穿透尽调报告</div>
    <div class="date">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 穿透层级: {deep} | 控股阈值: ≥{invest}%</div>
    <div class="date">数据来源: 爱企查 / 天眼查 | 工具: ENScan_GO v2.0.5</div>
</div>

<div class="section">
    <h2>一、企业基本信息</h2>
    <div class="info-grid">
        <div><span class="label">企业名称</span><br><span class="value">{name}</span></div>
        <div><span class="label">企业 PID</span><br><span class="value">{pid}</span></div>
        <div><span class="label">法定代表人</span><br><span class="value">{legal_person}</span></div>
        <div><span class="label">注册资本</span><br><span class="value">{reg_capital}</span></div>
        <div><span class="label">经营状态</span><br><span class="value">{status}</span></div>
        <div><span class="label">成立日期</span><br><span class="value">{establish_date}</span></div>
    </div>
</div>

<div class="section">
    <h2>二、股权穿透结构 (控股≥{invest}% | 穿透{deep}层)</h2>
    <div class="warn">⚠️ 以下为按持股比例筛选的控股/被控股公司结构，不含小股东及代持信息。</div>
    <table>
        <tr><th>公司名称</th><th>持股比例</th><th>注册资本</th><th>状态</th></tr>
        {rows}
    </table>
</div>

<div class="section">
    <h2>三、数据来源与声明</h2>
    <p>本报告数据来源于爱企查/天眼查公开企业信息，通过 ENScan_GO 工具自动采集。</p>
    <p>股权穿透仅反映公开工商登记信息，不包含代持协议、VIE结构、信托安排等非公开权益关系。</p>
    <p>报告仅供参考，不构成法律或投资建议。</p>
</div>

<div class="footer">
    本报告由 Hermes ENScan 自动生成 | {datetime.now().strftime('%Y-%m-%d')}
</div>

</body>
</html>"""
    return html

def html_to_pdf(html, output_path):
    """Convert HTML to PDF using weasyprint"""
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(output_path)
        return True
    except ImportError:
        # Fallback to pandoc
        with tempfile.NamedTemporaryFile(suffix='.html', mode='w', delete=False) as f:
            f.write(html)
            html_path = f.name
        subprocess.run([
            "pandoc", html_path, "--pdf-engine=weasyprint",
            "-o", output_path
        ], check=True, timeout=60)
        os.unlink(html_path)
        return True

def main():
    parser = argparse.ArgumentParser(description="股权穿透 PDF 报告生成器")
    parser.add_argument("company", help="公司名称")
    parser.add_argument("--deep", type=int, default=2, help="穿透层级 (默认2)")
    parser.add_argument("--invest", type=int, default=51, help="控股比例阈值 (默认51)")
    parser.add_argument("--timeout", type=int, default=120, help="查询超时秒数")
    args = parser.parse_args()
    
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # Step 1: Run ENScan
    data = run_enscan(args.company, args.deep, args.invest, args.timeout)
    
    # Step 2: Build HTML
    html = build_report_html(data, args.company, args.deep, args.invest)
    
    # Step 3: Save PDF
    safe_name = args.company.replace("/", "_").replace(" ", "_")
    pdf_path = os.path.join(OUT_DIR, f"{safe_name}_股权穿透报告.pdf")
    html_to_pdf(html, pdf_path)
    
    # Also save JSON for reference
    json_path = os.path.join(OUT_DIR, f"{safe_name}_raw.json")
    with open(json_path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 报告已生成:")
    print(f"   PDF: {pdf_path}")
    print(f"   原始数据: {json_path}")

if __name__ == "__main__":
    main()
