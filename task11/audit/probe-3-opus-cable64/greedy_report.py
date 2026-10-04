"""Greedy baselines, validated with the independent checker. Writes evidence/greedy.json"""
import json, subprocess, sys, os
from common import Instance
from heur import esau_williams
from greedy_sweep import sweep_prim, sweep_any
os.makedirs('layouts/greedy', exist_ok=True)
out = {}
for s in ['S1', 'S2', 'S3', 'S4']:
    I = Instance(s); res = {}
    p, c, ok = esau_williams(I)
    res['esau_williams'] = c if ok else f'infeasible (ended with {sum(1 for v in p if v == I.root)} feeders > {I.K})'
    b = sweep_prim(I); res['sweep_equal_sectors'] = b[0] if b else 'no feasible rotation'
    b2 = sweep_any(I); res['sweep_random_sector_sizes'] = b2[0] if b2 else None
    _, load = I.evaluate(b2[1])
    cab = {I.names[i]: {'to': 'SUB' if b2[1][i] == I.root else I.names[b2[1][i]], 'type': I.tname(load[i])} for i in range(I.n)}
    path = f'layouts/greedy/{s}_sweep.json'
    json.dump({'scenario': s, 'cost': b2[0], 'cables': cab}, open(path, 'w'), indent=1)
    res['checker'] = subprocess.run([sys.executable, 'checker.py', path], capture_output=True, text=True).stdout.strip()
    out[s] = res; print(s, res, flush=True)
json.dump(out, open('evidence/greedy.json', 'w'), indent=1)
