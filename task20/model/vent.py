"""Steady incompressible network solve: airways p = R Q|Q|, regulators as orifices, fan curve on the upcast."""
import math
import numpy as np
import net as N

def sec_R(p, L):
    _, A, per, k = N.PROF[p]; return k * L * per / A ** 3
def reg_R(area): return N.RHO / (2 * (N.CC * area) ** 2)
def route_R(st, rid):
    secs = st["routes"].get(rid, dict((r[0], r[3]) for r in N.ROUTES)[rid])
    R = sum(sec_R(p, L) for p, L in secs)
    if rid in N.REG: R += reg_R(st["reg"][N.REG[rid]])
    R += st.get("extra_R", {}).get(rid, 0.0)
    return R

def solve(st):
    """st: open (set of route ids), routes (section overrides), reg (areas), fan (curve key), extra_R.
    Node pressures are gauge relative to surface (0); flow + from 'from' to 'to' (m^3/s)."""
    br = [(rid, a, b, route_R(st, rid)) for rid, a, b, _ in N.ROUTES if rid in st["open"]]
    br += [("DS", "SURF", "PB", N.R_DS)]
    a0, b1, b2 = N.FAN[st["fan"]]
    nodes = sorted({x for _, a, b, _ in br for x in (a, b)} - {"SURF"}); idx = {n: i for i, n in enumerate(nodes)}; n = len(nodes)
    def fanQ(p_ub):           # flow UB -> SURF through upcast + fan, given p(UB) (negative gauge)
        d = -p_ub              # fan must lift d = a0 - b1 Q - b2 Q^2 - R_US Q^2
        if d >= a0: return 0.0
        c2 = b2 + N.R_US; return (-b1 + math.sqrt(b1 * b1 + 4 * c2 * (a0 - d))) / (2 * c2)
    def flows_of(p):
        P = lambda x: 0.0 if x == "SURF" else p[idx[x]]
        f = {}
        for rid, a, b, R in br:
            d = P(a) - P(b); f[rid] = math.copysign(math.sqrt(abs(d) / R), d)
        f["FAN"] = fanQ(P("UB")); return f
    def resid(p):
        F = np.zeros(n); f = flows_of(p)
        for rid, a, b, R in br:
            if a != "SURF": F[idx[a]] -= f[rid]
            if b != "SURF": F[idx[b]] += f[rid]
        F[idx["UB"]] -= f["FAN"]; return F, f
    # linear seed
    K = np.zeros((n, n)); rhs = np.zeros(n)
    for rid, a, b, R in br:
        g = 1.0 / (R * 100.0)
        for x, y in ((a, b), (b, a)):
            if x != "SURF": K[idx[x], idx[x]] += g; (K.__setitem__((idx[x], idx[y]), K[idx[x], idx[y]] - g) if y != "SURF" else None)
    K[idx["UB"], idx["UB"]] += 1.0 / 30.0; rhs[idx["UB"]] -= 2000.0 / 30.0
    p = np.linalg.solve(K, rhs)
    r, f = resid(p)
    for it in range(300):
        if np.max(np.abs(r)) < 1e-10: break
        J = np.zeros((n, n)); eps = 1e-4
        for j in range(n):
            q = p.copy(); q[j] += eps; J[:, j] = (resid(q)[0] - r) / eps
        dx = np.linalg.solve(J, -r); lam = 1.0
        while True:
            p2 = p + lam * dx; r2, f2 = resid(p2)
            if np.linalg.norm(r2) < np.linalg.norm(r) or lam < 1e-8: break
            lam /= 2
        p, r, f = p2, r2, f2
    else:
        raise RuntimeError("no convergence")
    Q = f["FAN"]; pf = a0 - b1 * Q - b2 * Q * Q
    out = dict(flows={k: v for k, v in f.items() if k not in ("FAN", "DS")}, Q=Q, p_fan=pf, power=pf * Q / 1000.0,
               p={x: p[idx[x]] for x in nodes}, reg_dp={N.REG[r]: route_R(st, r) and reg_R(st["reg"][N.REG[r]]) * f[r] * abs(f[r]) for r in N.REG if r in f})
    out["face"] = {k: f[v] for k, v in N.FACE.items()}
    return out
