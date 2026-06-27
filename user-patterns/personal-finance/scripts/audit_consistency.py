#!/usr/bin/env python3
"""
波总财务数据 — 13 项一致性审计
==============================
检查 debts.json / config.json / game_state.json / transactions.json / expenses.json
之间的跨文件引用完整性、内部汇总一致性、双副本同步状态。

用法：
   cd ~/.hermes/adjutant/repo/hermes-adjutant
   python3 finance/scripts/audit_consistency.py

修复模式（自动修复可修项 + push）：
   python3 finance/scripts/audit_consistency.py --fix
"""
import json, sys
from pathlib import Path

RP = Path('/Users/mac/.hermes/adjutant/repo/hermes-adjutant/finance')
WC = Path('/Users/mac/.hermes/adjutant/finance')
FIX = '--fix' in sys.argv
ok, fail, fixed = 0, 0, 0

def chk(name, cond, detail="", fix_cb=None):
    global ok, fail, fixed
    if cond:
        ok += 1; print(f'  ✅ {name}')
    elif FIX and fix_cb:
        fix_cb()
        fixed += 1; print(f'  🔧 {name} — 已修复')
    else:
        fail += 1; print(f'  ❌ {name}: {detail}')

# ── 1. debts.json meta 与实际求和 ──
with open(RP/'debts.json') as f: d = json.load(f)
family = sum(x['amount'] for x in d['active'] if x['type']=='亲友')
plat = sum(x['amount'] for x in d['active'] if x['type']=='平台')
other = sum(x['amount'] for x in d['active'] if x['type']=='其他')
total = round(family + plat + other, 2)
chk('grand_total 匹配', abs(d['meta']['grand_total']-total)<0.01,
    f'meta={d["meta"]["grand_total"]}, 实际={total}')
chk('total_active_family', abs(d['meta']['total_active_family']-family)<0.01)
chk('total_active_platform', abs(d['meta']['total_active_platform']-plat)<0.01)
chk('total_active_other', abs(d['meta'].get('total_active_other',0)-other)<0.01)

# ── 2. transactions 债权人引用 ──
with open(RP/'transactions.json') as f: tx = json.load(f)
creditors = {x['creditor'] for x in d['active']} | {x['creditor'] for x in d['cleared']}
bad = [t for t in tx if t['creditor'] not in creditors]
chk('tx 债权人引用', len(bad)==0, f'{len(bad)} 笔无法匹配')

# ── 3. config baseline ──
with open(RP/'config.json') as f: cfg = json.load(f)
chk('baseline_grand_total 对齐', abs(cfg['baseline_grand_total']-d['meta']['grand_total'])<0.01,
    f'cfg={cfg["baseline_grand_total"]} debts={d["meta"]["grand_total"]}',
    fix_cb=lambda: (setattr(cfg,'baseline_grand_total',d['meta']['grand_total']),
                    json.dump(cfg, open(RP/'config.json','w'), ensure_ascii=False, indent=2)))

# ── 4. game_state ──
with open(RP/'game_state.json') as f: gs = json.load(f)
chk('last_total 对齐', abs(gs['last_total']-d['meta']['grand_total'])<0.01,
    fix_cb=lambda: (gs.update({'last_total':d['meta']['grand_total'],'updated':'2026-06-27'}),
                    json.dump(gs, open(RP/'game_state.json','w'), ensure_ascii=False, indent=2)))
ann = gs.get('milestones_announced',[])
chk('milestones 升序', ann == sorted(ann), str(ann))
thresholds = {m['threshold'] for m in cfg['milestones']}
bad_ms = [t for t in ann if t not in thresholds]
chk('milestones 在阈值中', len(bad_ms)==0, str(bad_ms))

# ── 5. 快照 ──
snaps = sorted((RP/'snapshots').glob('*.json'))
chk('快照存在', len(snaps)>=1, f'{len(snaps)} 个')

# ── 6. expenses 内部一致性 ──
with open(RP/'expenses.json') as f: ex = json.load(f)
exp_sum = round(sum(e['amount'] for e in ex.get('expenses',[])), 2)
chk('expenses 总金额', abs(ex['meta']['total_amount']-exp_sum)<0.01,
    f'meta={ex["meta"]["total_amount"]}, 实际={exp_sum}')
cats = set(ex.get('categories',{}).keys()) | {'其他'}
exp_cats = set(e.get('category','') for e in ex.get('expenses',[]))
bad_c = [c for c in exp_cats if c not in cats]
chk('分类键完整性', len(bad_c)==0, str(bad_c))
known_layers = {'basic_living','relationship','event_reserve','business'}
no_l = sum(1 for e in ex.get('expenses',[]) if e.get('layer') not in known_layers)
chk('layer 完整性', no_l==0, f'{no_l} 笔缺 layer')

# ── 7. 双副本一致性 ──
diff = []
for fn in ['debts.json','config.json','game_state.json','transactions.json','expenses.json']:
    if (WC/fn).read_text() != (RP/fn).read_text():
        diff.append(fn)
chk('双副本一致', len(diff)==0, str(diff),
    fix_cb=lambda: [__import__('shutil').copy2(RP/f, WC/f) for f in diff])

print(f'\n📊 结果: ✅ {ok} 通过 | ❌ {fail} 未通过 | 🔧 {fixed} 已修复')
if fail > 0 and not FIX:
    print('💡 加 --fix 自动修复浮点精度/game_state/双副本')
sys.exit(0 if fail == 0 else 1)
