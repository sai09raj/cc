#!/usr/bin/env python3
"""Aggregate the GRID-14 exhaustive sweep (144 part files: 6 cycles x 6 plans x 2 lags x 2 offset halves).

Objective key for the optimum: (total TTS, C, plan, lag, offsets I0..I8) - offset index oi encodes I0 in its most
significant base-4 digit, so ascending oi is the packet's offset tie-break order.
usage: aggregate.py DIR [THRESHOLD ...]
"""
import glob, json, os, sys

D = sys.argv[1]; THR = [int(x) for x in sys.argv[2:]]
files = sorted(glob.glob(os.path.join(D, "chunk_*.json")))
seen = set(); n = 0; s = 0; s_sc = {"AM": 0, "PM": 0, "EVENT": 0}; below = 0; grid = 0
bc, bp, bl = {}, {}, {}; gc = {}; cands = []; hist = {}
for f in files:
    c = json.load(open(f)); key = (c["C"], c["plan"], c["lag"], c["lo"], c["hi"])
    assert key not in seen, f; seen.add(key)
    assert c["n"] == c["hi"] - c["lo"] and sum(c["hist1000"].values()) == c["n"], f
    n += c["n"]; s += c["sum"]; below += c["below"]; grid += c["gridlock"]
    for k in s_sc:
        s_sc[k] += c["sum_" + k]
    bc[c["C"]] = bc.get(c["C"], 0) + c["below"]; bp[c["plan"] + 1] = bp.get(c["plan"] + 1, 0) + c["below"]
    bl[c["lag"]] = bl.get(c["lag"], 0) + c["below"]; gc[c["C"]] = gc.get(c["C"], 0) + c["gridlock"]
    for b, v in c["hist1000"].items():
        hist[int(b)] = hist.get(int(b), 0) + v
    for tot, k in c["top"]:
        lag, oi = k // 262144, k % 262144
        cands.append((tot, c["C"], c["plan"], lag, oi))
expect = {(C, p, l, h * 131072, (h + 1) * 131072) for C in (60, 72, 84, 96, 108, 120) for p in range(6) for l in (0, 1) for h in (0, 1)}
missing = sorted(expect - seen)
cands.sort()
fmt = lambda k: dict(total_tts=k[0], C=k[1], plan=k[2] + 1, order="lag" if k[3] else "lead",
                     offsets=[((k[4] >> (2 * (8 - j))) & 3) * k[1] // 4 for j in range(9)])
out = dict(files=len(files), missing=len(missing), configurations=n, sum_total_tts=s, sum_by_scenario=s_sc,
           below_baseline=below, gridlock=grid, below_by_cycle=dict(sorted(bc.items())), below_by_plan=dict(sorted(bp.items())),
           below_by_order={"lead": bl.get(0, 0), "lag": bl.get(1, 0)}, gridlock_by_cycle=dict(sorted(gc.items())),
           optimum=fmt(cands[0]) if cands else None, top5=[fmt(k) for k in cands[:5]])
if THR:
    out["at_most_bin_approx"] = {t: sum(v for b, v in hist.items() if (b + 1) * 1000 <= t) for t in THR}
if missing:
    out["missing_list"] = [str(m) for m in missing[:40]]
json.dump(out, open(os.path.join(D, "aggregate.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
