#!/usr/bin/env python3
"""Progression diagnostic for an exhaustively enumerated (C, plan, order) group (standard library only).

For each of the 24 directed street blocks, a vehicle that crosses the upstream stop line at the first
second of the upstream through green reaches the downstream stop-line cell n-1 after n-1 steps and can
cross at step +n. The block is "in progression" if that step falls inside the downstream through green.
The script relates the number of blocks in progression to total TTS over all 4^9 offset vectors.
Usage: progression_analysis.py C plan order 'runs/exhaust_C_plan_order_*.csv'
"""
import csv, glob, sys
from collections import defaultdict

GREEN = {60: [(18, 8, 18, 8), (22, 6, 18, 6), (16, 7, 22, 7), (20, 9, 16, 7), (16, 7, 20, 9), (21, 5, 21, 5)]}
C, plan, order = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
g = dict(zip('ABCD', GREEN[C][plan - 1]))
seq = 'ABCD' if order == 'lead' else 'BADC'
start = {}; t0 = 0
for p in seq:
    start[p] = t0; t0 += g[p] + 2
# directed blocks: (from, to, cells, through phase)
H = {(0, 1): 32, (1, 2): 26, (3, 4): 22, (4, 5): 36, (6, 7): 28, (7, 8): 24}
V = {(0, 3): 30, (3, 6): 20, (1, 4): 24, (4, 7): 34, (2, 5): 27, (5, 8): 21}
blocks = []
for (a, b), n in H.items(): blocks += [(a, b, n, 'C'), (b, a, n, 'C')]
for (a, b), n in V.items(): blocks += [(a, b, n, 'A'), (b, a, n, 'A')]


def score(offs):
    s = 0
    for a, b, n, ph in blocks:
        tau = (offs[a] + start[ph] + n - offs[b]) % C
        if start[ph] <= tau < start[ph] + g[ph]:
            s += 1
    return s


rows = []
for fn in glob.glob(sys.argv[4]):
    for r in csv.reader(open(fn)):
        offs = [int(x) for x in r[4].split(';')]
        rows.append((score(offs), int(r[8]), offs))
by = defaultdict(list)
for s, tot, _ in rows: by[s].append(tot)
print(f'group C={C} plan={plan} {order}: {len(rows)} offset vectors')
print('blocks in progression -> count, mean total TTS, min total TTS')
for s in sorted(by):
    v = by[s]
    print(f'  {s:2d}: {len(v):6d}  mean {sum(v) / len(v):12,.0f}  min {min(v):12,}')
n = len(rows); mx = sum(s for s, _, _ in rows) / n; my = sum(t for _, t, _ in rows) / n
cov = sum((s - mx) * (t - my) for s, t, _ in rows) / n
vx = sum((s - mx) ** 2 for s, _, _ in rows) / n; vy = sum((t - my) ** 2 for _, t, _ in rows) / n
print(f'correlation(score, total TTS) = {cov / (vx * vy) ** 0.5:.3f}')
best = min(rows, key=lambda r: r[1])
print(f'best offsets {best[2]} total {best[1]:,}: {best[0]} of 24 blocks in progression (group mean {mx:.2f})')
