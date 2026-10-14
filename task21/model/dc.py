"""Steady DC load flow: resistive network, constant-power trams I = P/V, substations E - R I with rectifier diodes (no reverse current)."""
import numpy as np
import net as N
def sec_R(c, L): return N.COND[c][1] * L / 1000.0
def route_R(st, rid):
    secs = st["routes"].get(rid, dict((r[0], r[3]) for r in N.ROUTES)[rid]); return sum(sec_R(c, L) for c, L in secs)
def solve(st):
    br = [(rid, a, b, route_R(st, rid)) for rid, a, b, _ in N.ROUTES if rid in st["open"]]
    nodes = sorted({x for _, a, b, _ in br for x in (a, b)}); idx = {n: i for i, n in enumerate(nodes)}; n = len(nodes)
    tss = {k: (N.TSS[k][0], N.TSS[k][1] + N.TAP[st["tap"].get(k, 0)], N.TSS[k][2]) for k in st["tss"]}
    load = {}
    for t, (nd, P) in st["trams"].items(): load[nd] = load.get(nd, 0.0) + P * 1000.0
    G = np.zeros((n, n))
    for _, a, b, R in br:
        i, j = idx[a], idx[b]; g = 1 / R; G[i, i] += g; G[j, j] += g; G[i, j] -= g; G[j, i] -= g
    active = set(tss)
    for outer in range(50):
        V = np.full(n, 750.0)
        for it in range(100):
            Gs = G.copy(); rhs = np.zeros(n)
            for k in active:
                nd, E, Ri = tss[k]; Gs[idx[nd], idx[nd]] += 1 / Ri; rhs[idx[nd]] += E / Ri
            # constant power: I = P/V linearised  I ~ P/V0 + (-P/V0^2)(V - V0) -> current leaving node
            J = Gs.copy(); f = Gs @ V - rhs
            for nd, P in load.items():
                i = idx[nd]; f[i] += P / V[i]; J[i, i] += -P / V[i] ** 2
            dV = np.linalg.solve(J, -f); V += dV
            if np.max(np.abs(dV)) < 1e-10: break
        I_tss = {k: (tss[k][1] - V[idx[tss[k][0]]]) / tss[k][2] for k in active}
        rev = {k for k, i in I_tss.items() if i < 0}
        blocked = {k for k in set(tss) - active if tss[k][1] > V[idx[tss[k][0]]]}
        if not rev and not blocked: break
        active = (active - rev) | blocked
    flows = {rid: (V[idx[a]] - V[idx[b]]) / R for rid, a, b, R in br}
    loss = sum((V[idx[a]] - V[idx[b]]) ** 2 / R for rid, a, b, R in br) / 1000.0
    Vt = {t: V[idx[nd]] for t, (nd, P) in st["trams"].items()}
    return dict(V={x: V[idx[x]] for x in nodes}, flows=flows, I_tss={k: I_tss.get(k, 0.0) for k in tss}, blocked=sorted(set(tss) - active),
                Vt=Vt, loss=loss, P_tss={k: tss[k][1] * I_tss.get(k, 0.0) / 1000 for k in tss})
