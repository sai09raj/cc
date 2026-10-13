"""Likely misreads (adjacent-section swaps at every node, log slips) and greedy choice of graded quantities."""
import copy, json, itertools, vent, state, net as N
def secs(): return {r[0]: list(r[3]) for r in N.ROUTES}
def Q(st):
    r = vent.solve(st); q = {"q_" + k: v for k, v in r["flows"].items()}
    q["Q"] = r["Q"]; q["pfan"] = r["p_fan"]; q["power"] = r["power"]
    for k, v in r["reg_dp"].items(): q["dp_" + k] = v
    for k, v in r["p"].items(): q["p_" + k] = v
    return q
def ends(rid, node):
    r = next(x for x in N.ROUTES if x[0] == rid); return [i for i, e in ((0, r[1]), (-1, r[2])) if e == node]
def swaps():
    out = {}
    nodes = {x for r in N.ROUTES for x in r[1:3]}
    for nd in nodes:
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
    allr = {r[0] for r in N.ROUTES}
    m["LOG main fan 0"] = state.final(fan="main 0"); m["LOG main fan +5"] = state.final(fan="main +5")
    m["LOG REG-E 2.8"] = state.final(reg={**state.final()["reg"], "REG-E": 2.8})
    m["LOG REG-T 1.5"] = state.final(reg={**state.final()["reg"], "REG-T": 1.5})
    m["LOG X1 shut"] = state.final(open=allr - {"X1"})
    m["LOG X2 stopping intact"] = state.final(open=allr - {"X2"})
    m["LOG X2 no brattice R"] = state.final(extra_R={})
    return m
def ok(k, a, b):
    if k.startswith("q_"): return abs(a - b) <= max(0.001 * abs(b), 0.02) and (a > 0) == (b > 0)
    return abs(a - b) <= 0.001 * abs(b)
if __name__ == "__main__":
    import sys
    base = Q(state.final()); L = {n: Q(st) for n, st in likely().items()}
    fail = {n: {k for k in base if not ok(k, q.get(k, 0), base[k])} for n, q in L.items()}
    if "-v" in sys.argv:
        for n in sorted(fail, key=lambda n: len(fail[n])): print(f"{len(fail[n]):3d}/{len(base)}  {n}")
    TRAP = [n for n in fail if n.startswith(("J2: I3[0]", "J5: C2[-1] P5 350 <-> R2", "J7: W1[-1] P3 380 <-> X1", "J9: E1[-1] P4 280 <-> X2")) or n.startswith("LOG")]
    cand = [k for k in base if k not in ("q_R1", "q_I1", "q_T1")]; W, NONNUM, NROWS = 4, 15, 24; chosen = []
    def sc(ch, names):
        pos = W * len(ch) + NONNUM; return {n: 100 * (pos - W * len(fail[n] & set(ch))) / pos for n in names}
    while len(chosen) < NROWS:
        best = min((k for k in cand if k not in chosen), key=lambda k: (max(sc(chosen + [k], TRAP).values()), sum(sc(chosen + [k], fail).values())))
        chosen.append(best)
    json.dump(chosen, open("chosen.json", "w"))
    print("chosen:", " ".join(f"{k}={base[k]:.4g}" for k in chosen))
    for n, v in sorted(sc(chosen, fail).items(), key=lambda t: t[1]):
        if v < 100: print(f"  {v:5.1f}  {n}")
