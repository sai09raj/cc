#!/usr/bin/env python3
"""Make two deliberately corrupted copies of a GRID-14 trace, to show that checker.py rejects them.

  altered_red_crossing.txt : one stop-line crossing moved one step earlier, into the all-red interval
                             that precedes its green (position snapshot and X record both moved, so the
                             trace stays otherwise self-consistent)
  altered_double_cell.txt  : in one step's position snapshot, a queued vehicle is put into the cell of
                             the vehicle ahead of it on the same link (two vehicles in one cell)

usage: python3 make_altered.py trace_baseline_AM.txt outdir
"""
import os
import re
import sys

src, outdir = sys.argv[1], sys.argv[2]
lines = open(src).read().split('\n')
hdr = next(l for l in lines if l.startswith('# GRID-14'))
C = int(re.search(r'C=(\d+)', hdr).group(1))
links = {}
p_idx = {}
x_list = []
for i, l in enumerate(lines):
    if l.startswith('LINK '):
        p = l.split(); links[int(p[1])] = int(p[3])
    elif l.startswith('P '):
        p_idx[int(l.split()[1])] = i
    elif l.startswith('X '):
        x_list.append(i)

def snap(t):
    return {int(a.split(':')[0]): tuple(int(x) for x in a.split(':')[1:]) for a in lines[p_idx[t]].split()[2:]}

# baseline: plan 1 lead at C=84, offsets 0 -> greens start at tau 0 (A), 28 (B), 42 (C), 70 (D);
# the step before each of these is all-red for every movement.
green_starts = {0, 28, 42, 70}
assert C == 84
red = list(lines)
done = None
for i in x_list:
    _, t, v, fl, tl, j, a, m = lines[i].split()
    t, v, fl, tl = int(t), int(v), int(fl), int(tl)
    if t % C not in green_starts or t < 100:
        continue
    s = snap(t - 1)
    if s.get(v) != (fl, links[fl] - 1):
        continue
    if any(pos == (tl, 0) for pos in s.values()):
        continue
    # move the crossing to step t-1 (an all-red second)
    toks = red[p_idx[t - 1]].split()
    toks = [f'{v}:{tl}:0' if tok.split(':')[0] == str(v) else tok for tok in toks]
    red[p_idx[t - 1]] = ' '.join(toks)
    red[i] = ' '.join(['X', str(t - 1), str(v), str(fl), str(tl), j, a, m])
    done = (t, v, fl, tl)
    break
open(os.path.join(outdir, 'altered_red_crossing.txt'), 'w').write('\n'.join(red))
print(f'red-crossing copy: vehicle {done[1]} crossing link {done[2]} -> {done[3]} moved from step {done[0]} '
      f'(tau={done[0] % C}, green start) to step {done[0] - 1} (tau={(done[0] - 1) % C}, all-red)')

dbl = list(lines)
for t in sorted(p_idx):
    if t < 1000:
        continue
    s = snap(t)
    by = {}
    for v, (l, c) in s.items():
        by.setdefault((l, c), v)
    hit = None
    for v, (l, c) in s.items():
        if c > 0 and (l, c + 1) in by:   # vehicle directly behind another one
            hit = (v, l, c, by[(l, c + 1)])
            break
    if hit:
        v, l, c, w = hit
        toks = dbl[p_idx[t]].split()
        toks = [f'{v}:{l}:{c + 1}' if tok.split(':')[0] == str(v) else tok for tok in toks]
        dbl[p_idx[t]] = ' '.join(toks)
        print(f'double-cell copy: at step {t} vehicle {v} moved from link {l} cell {c} into cell {c + 1}, '
              f'already held by vehicle {w}')
        break
open(os.path.join(outdir, 'altered_double_cell.txt'), 'w').write('\n'.join(dbl))
