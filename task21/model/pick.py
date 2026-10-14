"""Likely misreads (adjacent-section swaps at every node, log slips) and greedy choice of graded quantities."""
import copy, json, itertools, sys, dc, state, net as N
def secs(): return {r[0]: list(r[3]) for r in N.ROUTES}
def Q(st):
    r = dc.solve(st); q = {"q_" + k: v for k, v in r["flows"].items() if abs(v) > 1e-6}
    q.update({"v_" + k: v for k, v in r["Vt"].items()}); q.update({"i_" + k: v for k, v in r["I_tss"].items() if v > 0}); q["loss"] = r["loss"]
    return q
def ends(rid, node):
    r = next(x for x in N.ROUTES if x[0] == rid); return [i for i, e in ((0, r[1]), (-1, r[2])) if e == node]
def swaps():
    out = {}
    for nd in {x for r in N.ROUTES for x in r[1:3]}:
        rs = [r[0] for r in N.ROUTES if nd in r[1:3]]
        for a, b in itertools.combinations(rs, 2):
            for i in ends(a, nd):
                for j in ends(b, nd):
                    s = secs(); x, y = s[a][i], s[b][j]
                    if x == y: continue
                    s[a][i], s[b][j] = y, x; out[f"{nd}: {a}[{i}] {x[0]} {x[1]} <-> {b}[{j}] {y[0]} {y[1]}"] = s
    return out
def likely():
    m = {n: state.final(routes=s) for n, s in swaps().items()}
    allr = {r[0] for r in N.ROUTES}; f = state.final()
    m["LOG TSS-B in service"] = state.final(tss=f["tss"] | {"TSS-B"})
    m["LOG TSS-D tap 0"] = state.final(tap={})
    m["LOG TSS-D tap -1"] = state.final(tap={"TSS-D": -1})
    m["LOG TSS-C tap +1 made"] = state.final(tap={"TSS-D": 1, "TSS-C": 1})
    m["LOG X1 still isolated"] = state.final(open=allr - {"X1"})
    m["LOG T150 at depot drawing"] = state.final(trams={**f["trams"], "T150": ("A", 300.0)})
    return m
def ok(k, a, b):
    if k.startswith(("q_", "i_")): return abs(a - b) <= max(0.001 * abs(b), 0.5) and (a > 0) == (b > 0)
    if k.startswith("v_"): return abs(a - b) <= 0.1
    return abs(a - b) <= 0.001 * abs(b)
if __name__ == "__main__":
    base = Q(state.final()); L = {n: Q(st) for n, st in likely().items()}
    fail = {n: {k for k in base if not ok(k, q.get(k, 0), base[k])} for n, q in L.items()}
    if "-v" in sys.argv:
        for n in sorted(fail, key=lambda n: -len(fail[n])): print(f"{len(fail[n]):3d}/{len(base)}  {n}")
    TRAP = [n for n in fail if n.startswith(("N4: M1[-1] K3 360 <-> M2", "N9: N9R[-1]", "N6: S3[-1] K3 470 <-> S4", "N7: S5[0] K2 330 <-> S6", "LOG"))]
    cand = [k for k in base if k not in ("q_L1", "q_S5")]; W, NONNUM, NROWS = 4, 15, 24; chosen = []
    def sc(ch, names):
        pos = W * len(ch) + NONNUM; return {n: 100 * (pos - W * len(fail[n] & set(ch))) / pos for n in names}
    while len(chosen) < NROWS:
        best = min((k for k in cand if k not in chosen), key=lambda k: (max(sc(chosen + [k], TRAP).values()), sum(sc(chosen + [k], fail).values())))
        chosen.append(best)
    json.dump(chosen, open("chosen.json", "w"))
    print("chosen:", " ".join(f"{k}={base[k]:.4g}" for k in chosen))
    for n, v in sorted(sc(chosen, fail).items(), key=lambda t: t[1]):
        if v < 100: print(f"  {v:5.1f}  {n}")
