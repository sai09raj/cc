#!/usr/bin/env python3
"""Aggregate the exhaustive COHERE-12 v4 enumeration (448 chunk JSON files).

Each file chunk_{d0}{d1}_Q{q}_B{b}.json (written by cohere_fast.c `chunk`) covers the
65,536 line maps of one (d0, d1, Q, B): makespan sum, makespan histogram, and the 20
best (makespan, messages, line map). Objective key: (makespan, messages, d0, d1, Q, B, h).

usage: aggregate_v4.py DIR BASELINE_MAKESPAN [THRESHOLD ...]
"""
import glob, json, os, sys

D = sys.argv[1]
BASE = int(sys.argv[2])
THR = [int(x) for x in sys.argv[3:]]
files = sorted(glob.glob(os.path.join(D, "chunk_*.json")))
seen = set()
total = 0
msum = 0
below = 0
below_q, below_b = {}, {}
atmost = {t: 0 for t in THR}
hist = {}
cands = []
for f in files:
    c = json.load(open(f))
    key = (c["d0"], c["d1"], c["Q"], c["B"])
    assert key not in seen, f
    seen.add(key)
    assert c["nops"] == 2400 and c["n"] == 65536, f
    h = {int(k): v for k, v in c["hist"].items()}
    assert sum(h.values()) == 65536 and sum(k * v for k, v in h.items()) == c["sum"], f
    total += c["n"]; msum += c["sum"]
    nb = sum(v for k, v in h.items() if k < BASE)
    below += nb
    below_q[c["Q"]] = below_q.get(c["Q"], 0) + nb
    below_b[c["B"]] = below_b.get(c["B"], 0) + nb
    for t in THR:
        atmost[t] += sum(v for k, v in h.items() if k <= t)
    for k, v in h.items():
        hist[k] = hist.get(k, 0) + v
    for ms, msg, lm in c["top"]:
        cands.append((ms, msg, c["d0"], c["d1"], c["Q"], c["B"], lm))
expect = {(a, b, q, bb) for a in range(8) for b in range(a + 1, 8) for q in (1, 2, 3, 4) for bb in (1, 2, 4, 8)}
missing = sorted(expect - seen)
cands.sort()
fmt = lambda k: dict(makespan=k[0], messages=k[1], d0=k[2], d1=k[3], Q=k[4], B=k[5], linemap=k[6])
ks = sorted(hist)
cum, quant = 0, {}
for k in ks:
    cum += hist[k]
    for p in (0.001, 0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9):
        if p not in quant and cum >= p * total:
            quant[p] = k
out = dict(files=len(files), missing=len(missing), total=total, makespan_sum=msum,
           baseline=BASE, below_baseline=below,
           below_baseline_per_Q={q: below_q[q] for q in sorted(below_q)},
           below_baseline_per_B={b: below_b[b] for b in sorted(below_b)},
           at_most={t: atmost[t] for t in THR}, min=ks[0] if ks else None, max=ks[-1] if ks else None,
           quantiles={str(p): v for p, v in quant.items()},
           optimum=fmt(cands[0]) if cands else None, top10=[fmt(k) for k in cands[:10]])
if missing:
    out["missing_list"] = ["%d%d_Q%d_B%d" % m for m in missing[:60]]
json.dump(out, open(os.path.join(D, "aggregate_v4.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
