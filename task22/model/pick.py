"""Likely misreads (adjacent-section swaps at every node, demand-chart slips, rule slips) and greedy choice of graded quantities."""
import json, itertools, sys, eps, state, net as N
def secs(): return {p[0]: list(p[3]) for p in N.PIPES}
def Q(st):
    r = eps.simulate(st); q = {}
    for x in r["rows"]:
        if x["t"] % 60 == 0 and x["t"] > 0: q[f"lev_{x['t'] // 60:02d}"] = x["level"]
    q["lev_24"] = r["final"]; q["energy"] = r["energy"]; q["cost"] = r["cost"]; q["minlev"] = r["minlevel"]; q["pmin"] = float(r["pmin"][0])
    snap = r["rows"][8 * 4]
    for pid, v in snap["flows"].items():
        if pid not in ("L1", "L2"): q["q08_" + pid] = v
    q["qp08"] = snap["qpump"]
    for sp in N.SETPOINTS:
        r2 = eps.simulate(dict(st, ctrl={"P-1": (sp, N.CTRL["P-1"][1]), "P-2": N.CTRL["P-2"]}))
        q[f"dc_{sp:.2f}"] = r2["cost"]; q[f"dm_{sp:.2f}"] = r2["minlevel"]
    q["_events"] = [(t, p, e) for t, p, e in r["events"]]; q["_pminat"] = (r["pmin"][1], r["pmin"][2])
    return q
def ends(pid, node):
    p = next(x for x in N.PIPES if x[0] == pid); return [i for i, e in ((0, p[1]), (-1, p[2])) if e == node]
def swaps():
    out = {}
    for nd in {x for p in N.PIPES for x in p[1:3]}:
        ps = [p[0] for p in N.PIPES if nd in p[1:3]]
        for a, b in itertools.combinations(ps, 2):
            for i in ends(a, nd):
                for j in ends(b, nd):
                    s = secs(); x, y = s[a][i], s[b][j]
                    if x == y or x[0] != y[0]: continue
                    s[a][i], s[b][j] = y, x; out[f"{nd}: {a}[{i}] {x[0]} {x[1]} <-> {b}[{j}] {y[0]} {y[1]}"] = state.base(pipes=s)
    return out
def likely():
    m = dict(swaps())
    for h in range(24):
        for d in (-0.05, 0.05):
            pat = list(N.PATTERN); pat[h] = round(pat[h] + d, 2); m[f"CHART h{h:02d} {d:+.2f}"] = state.base(pattern=pat)
    return m
def ok(k, a, b):
    if k.startswith("lev") or k.startswith("dm_") or k == "minlev": return abs(a - b) <= 0.005
    if k == "pmin": return abs(a - b) <= 0.05
    if k.startswith(("q08", "qp08")): return abs(a - b) <= max(0.001 * abs(b), 0.05)
    return abs(a - b) <= 0.001 * abs(b)
if __name__ == "__main__":
    base = Q(state.base()); L = {n: Q(st) for n, st in likely().items()}
    keys = [k for k in base if not k.startswith("_")]
    fail = {n: {k for k in keys if not ok(k, q[k], base[k])} for n, q in L.items()}
    evd = {n: q["_events"] != base["_events"] for n, q in L.items()}
    json.dump({"base": {k: base[k] for k in keys}, "fail": {n: sorted(v) for n, v in fail.items()}, "evd": evd}, open("sens.json", "w"))
    for n in sorted(fail, key=lambda n: -len(fail[n])): print(f"{len(fail[n]):3d}/{len(keys)} ev{'*' if evd[n] else ' '} {n}")
