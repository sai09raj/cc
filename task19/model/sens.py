"""Misread sensitivity for DH-19."""
import copy, hyd, state, net as N
def Q(st):
    r = hyd.solve(st); q = {}
    for k, v in r["flows"].items():
        if abs(v) > 1e-6: q["m_" + k] = v
    for k, v in r["T"].items(): q["T_" + k] = v
    q["dp"] = r["dp_pump"]; q["qec"] = r["q_ec"]; q["loss"] = r["loss"]; q["mtot"] = r["mtot"]
    return q
def secs():
    d = {r[0]: list(r[3]) for r in N.ROUTES}; d.update(state.REPAIR); return d
def with_secs(**ch):
    d = secs(); d.update(ch); return state.final(routes=d)
def misreads():
    s = secs(); m = {}
    # swap the adjacent sections of two routes meeting at a node (attribution)
    pairs = [("A2", -1, "A3", 0), ("A3", -1, "A4", 0), ("A1", -1, "A2", 0), ("B1", -1, "B2", 0), ("B2", -1, "B3", 0), ("B2", -1, "X3", -1),
             ("A2", -1, "X3", 0), ("C1", -1, "C2", 0), ("C2", -1, "C3", 0), ("A4", -1, "L1", 0), ("C3", -1, "L1", -1), ("D1", -1, "D2", 0), ("A1", 0, "B1", 0), ("C1", 0, "D1", 0)]
    for a, i, b, j in pairs:
        d = copy.deepcopy(s); d[a][i], d[b][j] = d[b][j], d[a][i]
        m[f"swap {a}[{i}]<->{b}[{j}]"] = state.final(routes=d)
    # length digit misreads: each section +/-
    return m
if __name__ == "__main__":
    base = Q(state.final()); print(len(base), "quantities")
    moved = {k: 0 for k in base}
    for n, st in misreads().items():
        q = Q(st); ch = [k for k in base if abs(q.get(k, 0) - base[k]) > max(0.001 * abs(base[k]), 0.005)]
        for k in ch: moved[k] += 1
        print(f"{n:28s} moves {len(ch):2d}/{len(base)}")
    for k, v in sorted(moved.items(), key=lambda t: -t[1]): print(f"  {k:8s} {v:2d}  {base[k]:.4f}")
