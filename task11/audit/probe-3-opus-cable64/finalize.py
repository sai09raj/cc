"""Write best layouts in checker format, run the independent checker, export B&B models.
usage: python3 finalize.py"""
import json, subprocess, sys, os
from common import Instance
from export_model import export
os.makedirs('layouts', exist_ok=True); os.makedirs('models', exist_ok=True)
for s in ['S1', 'S2', 'S3', 'S4']:
    I = Instance(s)
    cands = []
    for t in ['S1', 'S2', 'S3', 'S4']:     # any layout feasible for s is a valid candidate
        try: cands.append(json.load(open(f'ub_{t}.json'))['parent'])
        except Exception: pass
    best = None
    for p in cands:
        c, load = I.evaluate(p)
        if c is None: continue
        if sum(1 for v in p if v == I.root) > I.K: continue
        used = {I.eid[(i, p[i])] for i in range(I.n)}
        if any(I.cross[e] & used for e in used): continue
        if any(p[i] != I.root and I.L[i][p[i]] > 1300 for i in range(I.n)): continue
        if best is None or c < best[0]: best = (c, p, load)
    c, p, load = best
    cab = {I.names[i]: {'to': 'SUB' if p[i] == I.root else I.names[p[i]], 'type': I.tname(load[i]),
                        'load': load[i], 'length_m': I.L[i][p[i]]} for i in range(I.n)}
    json.dump({'scenario': s, 'cost': c, 'feeders': sum(1 for v in p if v == I.root), 'cables': cab},
              open(f'layouts/{s}.json', 'w'), indent=1)
    export(s, c, f'models/{s}.txt')
    r = subprocess.run([sys.executable, 'checker.py', f'layouts/{s}.json'], capture_output=True, text=True)
    print(s, c, r.stdout.strip())
