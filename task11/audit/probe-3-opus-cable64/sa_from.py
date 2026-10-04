"""Run SA from a given start layout. usage: sa_from.py SCEN start(.txt bnb output | .json with parent) runs iters seed0"""
import sys, json
from common import Instance
from heur import anneal
from greedy_sweep import sweep_prim
scen, start = sys.argv[1], sys.argv[2]
runs, iters, seed0 = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
I = Instance(scen)
if start == 'sweep':
    p = sweep_prim(I)[1]
elif start.endswith('.json'):
    p = json.load(open(start))['parent']
else:
    lines = open(start).read().split('\n')
    p = [None]*I.n
    for ln in lines:
        t = ln.split()
        if len(t) == 2 and t[0].isdigit(): p[int(t[0])] = int(t[1])
c0, _ = I.evaluate(p); print('start', c0, flush=True)
best, bp = c0, p
for r in range(seed0, seed0+runs):
    c, q = anneal(I, p, iters=iters, seed=r)
    print(' SA run', r, c, flush=True)
    if c is not None and c < best: best, bp = c, q
try:
    old = json.load(open(f'ub_{scen}.json'))
    if old['cost'] <= best: best, bp = old['cost'], old['parent']
except Exception: old = {}
old.update({'scenario': scen, 'cost': best, 'parent': bp})
json.dump(old, open(f'ub_{scen}.json', 'w'))
print(scen, 'best', best)
