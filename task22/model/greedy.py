"""Greedy choice of graded numeric quantities from sens.json (W=4 per row, NONNUM non-numeric points)."""
import json, sys
d = json.load(open("sens.json")); base, fail = d["base"], {n: set(v) for n, v in d["fail"].items()}
TRAP = [n for n in fail if n.startswith(("J3: A2[-1] DI200 360 <-> C1", "J5: B2[0]", "J6: B2[-1]", "J7: C1[-1]", "J3: A2[-1] DI200 360 <-> A3", "J3: A3[0]"))]
EXCL = {"lev_10", "dc_2.20", "dm_2.20", "dc_2.40", "dm_2.40", "q08_C2", "q08_D2", "qp08"}
cand = [k for k in base if k not in EXCL and not (k.startswith("q08") and k not in ("q08_A2", "q08_B2", "q08_C1", "q08_C3", "q08_TK", "q08_B3"))]
W, NONNUM, NROWS = 4, 21, int(sys.argv[1]) if len(sys.argv) > 1 else 22
chosen = ["energy", "cost", "pmin", "dc_2.00", "dc_2.80", "dm_2.80", "minlev"]
def sc(ch, names):
    pos = W * len(ch) + NONNUM; return {n: 100 * (pos - W * len(fail[n] & set(ch))) / pos for n in names}
while len(chosen) < NROWS:
    best = min((k for k in cand if k not in chosen), key=lambda k: (max(sc(chosen + [k], TRAP).values()), sum(sc(chosen + [k], fail).values())))
    chosen.append(best)
json.dump(chosen, open("chosen.json", "w"))
print("chosen:", " ".join(f"{k}={base[k]:.4g}" for k in chosen))
s = sc(chosen, fail)
for n in TRAP: print(f"  TRAP {s[n]:5.1f}  {n}")
ch = sorted(v for n, v in s.items() if n.startswith("CHART")); print("chart slips: n", len(ch), "max", round(ch[-1], 1), "<=40:", sum(v <= 40 for v in ch), "50+:", sum(v >= 50 for v in ch))
