#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中文 PDF 报告生成器骨架（fpdf2, macOS 已验证字体）
复制后：填 EMOJI_MAP 已内置；把 build() 里的章节换成你的内容；
输出到 ~/Downloads/<公司名>_报告.pdf，再 cp 到 ~/.hermes/cache/documents/ 交付。
验证：fitz.open 抽查 get_text() 关键数字/章节（见 SKILL.md）。"""

from fpdf import FPDF
import os

HEI = '/System/Library/Fonts/STHeiti Light.ttc'
SONG = '/System/Library/Fonts/STHeiti Medium.ttc'   # 注意：勿用 Songti.ttc（Python 不可见）

EMOJI_MAP = {
    '✅': '[OK]', '⚠️': '[!!]', '❌': '[X]', '🔴': '[HIGH]',
    '🟠': '[MED]', '🟡': '[LOW]', '🟢': '[CLEAR]', '❗': '[!]',
    '🚨': '[ALERT]', '①': '1)', '②': '2)', '③': '3)',
    '：': ':', '—': '-', '·': '.',
}

def clean(s):
    for k, v in EMOJI_MAP.items():
        s = s.replace(k, v)
    return s

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('HeiTi', '', HEI)
        self.add_font('SongTi', '', SONG)
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        if self.page_no() > 1:
            self.set_font('SongTi', '', 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 6, '报告标题 - 内部机密', align='R')
            self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font('SongTi', '', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f'第 {self.page_no()} 页', align='C')

    def h1(self, t):
        self.ln(3)
        self.set_font('HeiTi', '', 15)
        self.set_text_color(20, 40, 80)
        self.cell(0, 10, clean(t), ln=True)
        self.set_draw_color(20, 40, 80)
        self.set_line_width(0.6)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def h2(self, t):
        self.ln(2)
        self.set_font('HeiTi', '', 12)
        self.set_text_color(40, 60, 120)
        self.cell(0, 8, clean(t), ln=True)
        self.ln(1)

    def body(self, t, bold=False):
        self.set_font('HeiTi' if bold else 'SongTi', '', 10.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.8, clean(t))
        self.ln(1)

    def bullet(self, t):
        self.set_font('SongTi', '', 10.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.8, clean('- ' + t))
        self.ln(0.5)

    def verdict_box(self, title, text, color=(200, 40, 40)):
        self.ln(2)
        self.set_fill_color(*color)
        self.set_draw_color(*color)
        self.set_font('HeiTi', '', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, clean(title), ln=True, fill=True)
        self.set_fill_color(255, 245, 245)
        self.set_text_color(30, 30, 30)
        self.set_font('SongTi', '', 10.5)
        self.multi_cell(0, 5.8, clean(text), fill=True)
        self.ln(2)

    def table(self, headers, rows, widths=None, col_colors=None):
        n = len(headers)
        if widths is None:
            widths = [186 // n] * n
        self.set_fill_color(30, 50, 90)
        self.set_text_color(255, 255, 255)
        self.set_font('HeiTi', '', 9.5)
        for i, h in enumerate(headers):
            self.cell(widths[i], 7, clean(h), border=0, fill=True, align='C')
        self.ln()
        self.set_font('SongTi', '', 9.5)
        for r_i, row in enumerate(rows):
            if r_i % 2 == 0:
                self.set_fill_color(240, 244, 250)
            else:
                self.set_fill_color(255, 255, 255)
            self.set_text_color(30, 30, 30)
            for i, cell in enumerate(row):
                fill = False
                if col_colors and col_colors[i] and r_i < len(col_colors[i]) and col_colors[i][r_i]:
                    self.set_fill_color(*col_colors[i][r_i])
                    fill = True
                self.cell(widths[i], 7, clean(cell), border=0, fill=fill, align='C')
            self.ln()


def build():
    pdf = PDF()
    pdf.set_margins(12, 14, 12)

    # ===== 封面 =====
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font('HeiTi', '', 26)
    pdf.set_text_color(20, 40, 80)
    pdf.cell(0, 14, '评估报告', align='C', ln=True)
    pdf.ln(4)
    pdf.set_font('HeiTi', '', 20)
    pdf.cell(0, 12, '公司名称 (代码)', align='C', ln=True)
    pdf.ln(20)
    pdf.set_font('HeiTi', '', 14)
    pdf.set_text_color(200, 40, 40)
    pdf.cell(0, 10, '最终评级: [HIGH] 示例评级 (X.X/10)', align='C', ln=True)
    pdf.ln(12)
    pdf.set_font('SongTi', '', 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, '数据截至 YYYY-MM-DD | 内部机密', align='C', ln=True)

    # ===== 章节示例 =====
    pdf.add_page()
    pdf.h1('一、排雷速览')
    pdf.table(['#', '检查项', '结果', '标记'], [
        ['1', '审计意见', '标准无保留', '[CLEAR]'],
        ['2', '信披/股权雷', '有监管措施', '[HIGH]'],
    ], widths=[8, 34, 118, 24])
    pdf.verdict_box('[HIGH] 结论', '这里写警示结论。', (200, 40, 40))

    pdf.h1('二、股权穿透')
    pdf.set_font('SongTi', '', 9.5)
    pdf.multi_cell(0, 5.2, clean("""公司 (代码)
|-- [X%] 实控人
|-- [X%] 机构股东
+-- 控制权事件链
    2024-XX 事项A
    2026-XX 事项B"""))

    out = os.path.expanduser('~/Downloads/示例_报告.pdf')
    pdf.output(out)
    print('OK:', out, os.path.getsize(out), 'bytes')

build()
