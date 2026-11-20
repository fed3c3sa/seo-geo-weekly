#!/usr/bin/env python3
"""Compare this run's Search Console snapshot with the previous one.
Usage: compare.py <data_dir> [window]   (window = 28d (default, use this for week-over-week) or 3m)
<data_dir> holds dated folders YYYY-MM-DD/<window>/ with totals.csv, pages.csv, queries.csv, targets.csv
(columns: see the skill's "Data files" section). Reads the two most recent dated folders and prints
totals, pages, the previous run's tracked targets with their movement, and new queries."""
import csv, os, sys
root = sys.argv[1]
win = sys.argv[2] if len(sys.argv) > 2 else '28d'
weeks = sorted(d for d in os.listdir(root) if d[:4].isdigit() and os.path.isdir(os.path.join(root, d, win)))
if len(weeks) < 2: sys.exit(f'need two weeks of data, have {weeks}')
prev, cur = weeks[-2], weeks[-1]
def load(w, name, key):
    p = os.path.join(root, w, win, name)
    return {r[key]: r for r in csv.DictReader(open(p, encoding='utf-8-sig'))} if os.path.exists(p) else {}
def f(x):
    """Parse 1234, 1,234, 1.64K, 2M, 6.7%, 6,7% (decimal comma) into a float, or None."""
    s = str(x or '').strip().replace('\u00a0', '').replace(' ', '')
    if not s or s == '-': return None
    mult = 1
    if s[-1:] in 'kK': mult, s = 1000, s[:-1]
    elif s[-1:] in 'mM': mult, s = 1000000, s[:-1]
    s = s.rstrip('%')
    if ',' in s and '.' in s: s = s.replace(',', '')                  # 1,234.5
    elif s.count(',') == 1 and len(s.split(',')[1]) == 3 and mult == 1: s = s.replace(',', '')  # 1,234
    else: s = s.replace(',', '.')                                       # 6,7 (decimal comma)
    try: return float(s) * mult
    except ValueError: return None
def delta(a, b, lower_is_better=False):
    a, b = f(a), f(b)
    if a is None or b is None: return ''
    d = b - a
    good = (d < 0) if lower_is_better else (d > 0)
    return f'{d:+.1f} {"better" if good and d else ("worse" if d else "same")}'
print(f'# {prev} -> {cur} ({win})\n')
t0, t1 = list(load(prev,'totals.csv','window').values()), list(load(cur,'totals.csv','window').values())
if t0 and t1:
    for k in ['clicks','impressions','ctr','position','ai_impressions','indexed_pages','indexed_videos']:
        print(f'{k:16} {t0[0].get(k) or "-":>8} -> {t1[0].get(k) or "-":>8}  {delta(t0[0].get(k), t1[0].get(k), k=="position")}')
print('\n## Pages')
p0, p1 = load(prev,'pages.csv','page'), load(cur,'pages.csv','page')
for k in sorted(set(p0)|set(p1), key=lambda k: -(f(p1.get(k,{}).get('impressions')) or 0)):
    a, b = p0.get(k, {}), p1.get(k, {})
    print(f'{k:45} impr {a.get("impressions","-"):>6}->{b.get("impressions","-"):<6} pos {a.get("position","-"):>5}->{b.get("position","-"):<5} {delta(a.get("position"), b.get("position"), True)}  ai {a.get("ai_impressions","-")}->{b.get("ai_impressions","-")}')
print('\n## Tracked targets (from the previous week)')
q1 = load(cur, 'queries.csv', 'query')
for r in csv.DictReader(open(os.path.join(root, prev, win, 'targets.csv'), encoding='utf-8-sig')) if os.path.exists(os.path.join(root, prev, win, 'targets.csv')) else []:
    now = q1.get(r['query'], {})
    print(f'{r["query"][:60]:60} pos {r["baseline_position"]:>5} -> {now.get("position","not in top rows"):<6} {delta(r["baseline_position"], now.get("position"), True)}')
print('\n## New queries this week (not seen before)')
q0 = load(prev, 'queries.csv', 'query')
for k, r in sorted(q1.items(), key=lambda kv: -(f(kv[1]['impressions']) or 0)):
    if k not in q0: print(f'{k[:70]:70} impr {r["impressions"]:>4} pos {r["position"]}')
