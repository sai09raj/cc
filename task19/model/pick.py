"""Likely misreads of the route plan and log, and greedy choice of graded quantities (flows with direction, dp, loss, temperatures)."""
import copy, json, hyd, state, net as N
def secs():
    d = {r[0]: list(r[3]) for r in N.ROUTES}; d.update(copy.deepcopy(state.REPAIR)); return d
def Q(st):
    r = hyd.solve(st); q = {}
    for k, v in r["flows"].items():
        if abs(v) > 1e-6: q["m_" + k] = v
    for k, v in r["T"].items(): q["T_" + k] = v
    q["dp"] = r["dp_pump"]; q["loss"] = r["loss"]; q["qec"] = r["q_ec"]; q["mtot"] = r["mtot"]
    return q
def likely():
    s = secs(); m = {}
    for a, i, b, j, name in [("A1", 0, "C1", 0, "EC: A1/C1 first sections swapped"), ("A1", 0, "B1", 0, "EC: A1/B1 first sections swapped"),
                             ("A1", -1, "A2", 0, "H1: A1/A2 sections swapped"), ("A2", -1, "A3", 0, "H2: A2/A3 sections swapped"),
                             ("A2", -1, "X3", 0, "H2: A2/X3 sections swapped"), ("B1", -1, "B2", 0, "H5: B1/B2 sections swapped"),
                             ("B2", -1, "X3", -1, "H6: B2/X3 470 sections swapped"), ("B2", -1, "B3", 0, "H6: B2/B3 sections swapped"),
                             ("C1", -1, "C2", 0, "H8: C1/C2 sections swapped"), ("C2", -1, "C3", 0, "H9: C2/C3 sections swapped"),
                             ("D1", -1, "D2", 0, "H11: D1/D2 sections swapped"), ("D2", -1, "L2", -1, "H12: D2/L2 sections swapped"),
                             ("A4", -1, "L1", 0, "H4: A4/L1 sections swapped"), ("C3", -1, "L1", -1, "H10: C3/L1 sections swapped")]:
        d = copy.deepcopy(s); d[a][i], d[b][j] = d[b][j], d[a][i]; m[name] = state.final(routes=d)
    d = copy.deepcopy(s); d["B2"] = d["B2"] + [d["X3"][-1]]; d["X3"] = d["X3"][:-1]; m["GAP H6: X3 470 given to B2 (seen x2)"] = state.final(routes=d)
    d = copy.deepcopy(s); d["A4"] = d["A4"] + [d["L1"][0]]; d["L1"] = d["L1"][1:]; m["GAP H4: L1 640 given to A4"] = state.final(routes=d)
    d = copy.deepcopy(s); d["A2"] = d["A2"] + [d["X3"][0]]; d["X3"] = d["X3"][1:]; m["GAP H2: X3 460 given to A2"] = state.final(routes=d)
    d = copy.deepcopy(s); d["X3"] = d["X3"] + [d["B2"][0]]; d["B2"] = d["B2"][1:]; m["GAP H5-H6: B2 510 given to X3"] = state.final(routes=d)
    d = copy.deepcopy(s); d["A3"] = [("DN125", 450), ("DN100", 260)]; m["LOG repair ignored"] = state.final(routes=d)
    d = copy.deepcopy(s); d["A3"] = [("DN125", 450), ("DN100", 260), ("DN125", 290)]; m["LOG repair added in series"] = state.final(routes=d)
    m["LOG X3 closed"] = state.final(open={r[0] for r in N.ROUTES} - {"X3"})
    m["LOG L2 closed"] = state.final(open={r[0] for r in N.ROUTES} - {"L2"})
    m["LOG H7 in service"] = state.final(loads=dict(N.LOAD))
    m["LOG setpoint 90"] = state.final(T_ec=90.0); m["LOG setpoint 86"] = state.final(T_ec=86.0)
    return m
def ok(k, a, b):
    if k.startswith("T_"): return abs(a - b) <= 0.005
    if k.startswith("m_"): return abs(a - b) <= max(0.001 * abs(b), 0.002) and (a > 0) == (b > 0)
    return abs(a - b) <= 0.001 * abs(b)
if __name__ == "__main__":
    base = Q(state.final()); L = {n: Q(st) for n, st in likely().items()}
    cand = [k for k in base if k not in ("m_L2",)]           # L2 carries the same flow as B3 (H7 out)
    fail = {n: {k for k in cand if not ok(k, q.get(k, 0), base[k])} for n, q in L.items()}
    W, NONNUM, NROWS = 4, 14, 26
    chosen = []
    def sc(ch):
        pos = W * len(ch) + NONNUM; return {n: 100 * (pos - W * len(fail[n] & set(ch))) / pos for n in fail}
    while len(chosen) < NROWS:
        best = min((k for k in cand if k not in chosen), key=lambda k: (max(sc(chosen + [k]).values()), sum(sc(chosen + [k]).values())))
        chosen.append(best)
    json.dump(chosen, open("chosen.json", "w"))
    for k in chosen: print(f"  {k:8s} {base[k]:.4f}")
    for n, v in sc(chosen).items(): print(f"  {n:34s} {v:5.1f}")
