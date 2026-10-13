"""Steady-state hydraulic + thermal solution of the DH-19 supply network."""
import math
import numpy as np
import net as N

def route_secs(state, rid):
    return state.get("routes", {}).get(rid, dict((r[0], r[3]) for r in N.ROUTES)[rid])

def sec_dp(t, L, m):
    """kPa pressure drop of one pipe section of type t, length L (m) carrying m kg/s (sign follows m)."""
    D = N.PIPE[t][0] / 1000.0; A = math.pi * D * D / 4; v = abs(m) / (N.RHO * A)
    if v == 0: return 0.0
    Re = N.RHO * v * D / N.MU
    f = 0.25 / math.log10(N.ROUGH / (3.7 * D) + 5.74 / Re ** 0.9) ** 2
    return math.copysign(f * L / D * N.RHO * v * v / 2 / 1000.0, m)

def route_dp(state, rid, m): return sum(sec_dp(t, L, m) for t, L in route_secs(state, rid))

def hydraulics(state, demand):
    """demand: kg/s withdrawn at each consumer. Returns route flows (kg/s, + from 'from' to 'to') and node pressures (kPa below EC)."""
    routes = [r for r in N.ROUTES if r[0] in state["open"]]
    nodes = ["EC"] + sorted({n for r in routes for n in r[1:3]} - {"EC"})
    idx = {n: i for i, n in enumerate(nodes)}; n = len(nodes)
    def residual(h):
        F = np.array([-demand.get(x, 0.0) for x in nodes]); flows = {}
        for rid, a, b, _ in routes:
            m = invert(state, rid, h[idx[b]] - h[idx[a]]); flows[rid] = m; F[idx[a]] -= m; F[idx[b]] += m
        return F[1:], flows
    # linear start: dp = k m with k = route_dp at 5 kg/s / 5
    K = np.zeros((n, n)); rhs = np.array([-demand.get(x, 0.0) for x in nodes])
    for rid, a, b, _ in routes:
        g = 5.0 / route_dp(state, rid, 5.0); i, j = idx[a], idx[b]
        K[i, i] += g; K[j, j] += g; K[i, j] -= g; K[j, i] -= g
    h = np.zeros(n); h[1:] = np.linalg.solve(K[1:, 1:], -rhs[1:])
    r, flows = residual(h)
    for it in range(200):
        if np.max(np.abs(r)) < 1e-11: break
        J = np.zeros((n, n))
        for rid, a, b, _ in routes:
            g = dmdh(state, rid, flows[rid]); i, j = idx[a], idx[b]
            J[i, i] += g; J[j, j] += g; J[i, j] -= g; J[j, i] -= g
        dx = np.linalg.solve(J[1:, 1:], -r); lam = 1.0
        while True:
            h2 = h.copy(); h2[1:] += lam * dx; r2, f2 = residual(h2)
            if np.linalg.norm(r2) < np.linalg.norm(r) or lam < 1e-6: break
            lam /= 2
        h, r, flows = h2, r2, f2
    else:
        raise RuntimeError("hydraulics did not converge")
    return flows, {x: h[idx[x]] for x in nodes}

def invert(state, rid, dh):
    if dh == 0: return 0.0
    lo, hi = 0.0, 1.0
    while route_dp(state, rid, hi) < abs(dh): hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if route_dp(state, rid, mid) < abs(dh): lo = mid
        else: hi = mid
    return math.copysign((lo + hi) / 2, dh)

def dmdh(state, rid, m):
    m0 = max(abs(m), 1e-6); d = m0 * 1e-6
    return 2 * d / (route_dp(state, rid, m0 + d) - route_dp(state, rid, m0 - d))

def thermal(state, flows, h):
    """Supply temperatures: exponential loss along every section, flow-weighted mixing at nodes. Returns node temps and route heat loss (kW)."""
    T = {"EC": state["T_ec"]}; loss = {}
    order = sorted(h, key=lambda n: h[n])                 # pressure falls along the flow direction
    inflow = {n: [] for n in h}
    for rid, a, b, _ in [r for r in N.ROUTES if r[0] in state["open"]]:
        m = flows[rid]
        if abs(m) < 1e-9: continue
        src, dst = (a, b) if m > 0 else (b, a); inflow[dst].append((rid, src, abs(m)))
    for n in order:
        if n == "EC": continue
        num = den = 0.0
        for rid, src, m in inflow[n]:
            if src not in T: continue
            Tin = T[src]; secs = route_secs(state, rid)
            secs = secs if src == [r for r in N.ROUTES if r[0] == rid][0][1] else list(reversed(secs))
            q = 0.0
            for t, L in secs:
                Tout = N.T_GROUND + (Tin - N.T_GROUND) * math.exp(-N.PIPE[t][1] * L / (m * N.CP * 1000.0))
                q += m * N.CP * (Tin - Tout); Tin = Tout
            loss[rid] = q; num += m * Tin; den += m
        if den > 0: T[n] = num / den
    return T, loss

def solve(state):
    """state: open (set of route ids carrying flow), T_ec (C), loads (kW per consumer in service), routes (optional section overrides)."""
    loads = state["loads"]
    T = {n: state["T_ec"] for n in loads}
    for it in range(200):
        demand = {n: q / (N.CP * (T[n] - N.T_RET)) for n, q in loads.items()}
        flows, h = hydraulics(state, demand)
        Tn, loss = thermal(state, flows, h)
        new = {n: Tn[n] for n in loads}
        if max(abs(new[n] - T[n]) for n in loads) < 1e-12: T = new; break
        T = new
    else:
        raise RuntimeError("thermal iteration did not converge")
    demand = {n: q / (N.CP * (T[n] - N.T_RET)) for n, q in loads.items()}
    mtot = sum(demand.values())
    index = max(loads, key=lambda n: h[n])
    dp_pump = 2 * h[index] + N.DP_MIN
    q_ec = mtot * N.CP * (state["T_ec"] - N.T_RET)
    return dict(flows=flows, h=h, T=T, demand=demand, mtot=mtot, index=index, dp_pump=dp_pump, q_ec=q_ec, loss=sum(loss.values()),
                route_loss=loss)
