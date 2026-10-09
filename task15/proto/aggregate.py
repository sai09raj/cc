#!/usr/bin/env python3
"""Aggregate the FIRE-15 sweep (196 part files: crew 1 station x crew 2 station).  usage: aggregate.py DIR"""
import glob, json, os, sys
D = sys.argv[1]; NST, NCREW = 14, 7
files = sorted(glob.glob(os.path.join(D, "chunk_*.json")))
seen = set(); n = s = sh = below = below_all = 0; ssc = [0] * 4
bb = [[0] * NST for _ in range(NCREW)]; sb = [[0] * NST for _ in range(NCREW)]; cands = []; hist = {}
for f in files:
    c = json.load(open(f)); key = (c["s1"], c["s2"]); assert key not in seen, f; seen.add(key)
    assert c["n"] == NST ** 5 and sum(c["hist100"].values()) == c["n"], f
    n += c["n"]; s += c["sum"]; sh += c["sum_houses"]; below += c["below"]; below_all += c["below_all"]
    for i in range(4): ssc[i] += c["sum_sc"][i]
    for k in range(NCREW):
        for j in range(NST): bb[k][j] += c["below_by"][k][j]; sb[k][j] += c["sum_by"][k][j]
    cands += [tuple(t) for t in c["top"]]
    for b, v in c["hist100"].items(): hist[int(b)] = hist.get(int(b), 0) + v
missing = sorted({(a, b) for a in range(1, 15) for b in range(1, 15)} - seen)
cands.sort()
dec = lambda k: [(k // NST ** (6 - i)) % NST + 1 for i in range(7)]
out = dict(files=len(files), missing=len(missing), plans=n, sum_total_loss=s, sum_by_scenario=ssc, sum_house_cells=sh,
           below_baseline=below, below_baseline_all_four=below_all, below_by_crew_station=bb,
           mean_by_crew_station=[[round(sb[k][j] / (n / NST), 1) if n else None for j in range(NST)] for k in range(NCREW)],
           optimum=dict(total_loss=cands[0][0], plan=dec(cands[0][1])) if cands else None,
           top10=[dict(total_loss=v, plan=dec(k)) for v, k in cands[:10]])
if missing: out["missing_list"] = [str(m) for m in missing[:60]]
json.dump(out, open(os.path.join(D, "aggregate.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ("below_by_crew_station", "mean_by_crew_station")}, indent=1))
