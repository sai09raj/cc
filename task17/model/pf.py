"""AC load flow (Newton-Raphson, polar) for KINGSMEAD-11, with AVC tap selection."""
import math, cmath
import numpy as np
import net as N
SB = 10.0                                  # MVA base
VB = {"HV": 33.0, "LV": 11.0}
def zbase(kv): return kv * kv / SB
def route_z(route):                        # ohm
    return sum(complex(N.CABLE[t][0], N.CABLE[t][1]) * L / 1000.0 for t, L in route[3])

def build(state):
    """state: closed (set of route ids in service), tx (set of transformers in service), bs (bool), taps {T: int},
    cap (bool), pv_kw (float), loads (dict, optional)"""
    merge = {"B": "A"} if state["bs"] else {}
    m = lambda b: merge.get(b, b)
    buses = ["SRC", "P33"] + sorted({m(b) for b in ["A", "B"]}) + [f"S{i}" for i in range(1, 13)]
    idx = {b: i for i, b in enumerate(buses)}; n = len(buses)
    Y = np.zeros((n, n), complex)
    def add_branch(a, b, y):
        i, j = idx[a], idx[b]; Y[i, i] += y; Y[j, j] += y; Y[i, j] -= y; Y[j, i] -= y
    add_branch("SRC", "P33", 1 / (N.SRC_Z / zbase(33.0)))
    for t, d in N.TX.items():
        if t not in state["tx"]: continue
        zpu = d["z"] * SB / d["S"]; r = zpu / math.sqrt(1 + d["xr"] ** 2); zt = complex(r, r * d["xr"]); yt = 1 / zt
        a = 1 + N.TAP_STEP * (state["taps"][t] - N.TAP_NOM)
        h, l = idx["P33"], idx[m("A" if t == "T1" else "B")]
        Y[h, h] += yt / a ** 2; Y[l, l] += yt; Y[h, l] -= yt / a; Y[l, h] -= yt / a
    for r_ in state.get("routes", N.ROUTES):
        if r_[0] not in state["closed"]: continue
        add_branch(m(r_[1]), m(r_[2]), 1 / (route_z(r_) / zbase(11.0)))
    if state["cap"]:
        Y[idx[N.CAP["bus"]], idx[N.CAP["bus"]]] += 1j * N.CAP["Q_kvar"] / 1000.0 / SB
    S = np.zeros(n, complex)
    for b, (p, pf) in state.get("loads", N.LOAD).items():
        S[idx[b]] -= complex(p, p * math.tan(math.acos(pf))) / 1000.0 / SB
    pv = state["pv_kw"]
    S[idx[N.PV["bus"]]] += complex(pv, -pv * math.tan(math.acos(N.PV["pf"]))) / 1000.0 / SB
    return buses, idx, Y, S

def solve_fixed(state, tol=1e-12):
    buses, idx, Y, S = build(state); n = len(buses)
    V = np.ones(n, complex); V[0] = N.SRC_KV / 33.0
    pq = list(range(1, n))
    for it in range(60):
        I = Y @ V; Sc = V * np.conj(I); dS = (S - Sc)[pq]
        mis = np.concatenate([dS.real, dS.imag])
        if np.max(np.abs(mis)) < tol: break
        # numerical Jacobian on (angle, |V|) of pq buses
        x = np.concatenate([np.angle(V[pq]), np.abs(V[pq])]); J = np.zeros((2 * len(pq), 2 * len(pq)))
        def F(xx):
            VV = V.copy(); VV[pq] = xx[len(pq):] * np.exp(1j * xx[:len(pq)])
            d = (S - VV * np.conj(Y @ VV))[pq]; return np.concatenate([d.real, d.imag])
        f0 = F(x)
        for k in range(len(x)):
            xp = x.copy(); xp[k] += 1e-7; J[:, k] = (F(xp) - f0) / 1e-7
        dx = np.linalg.solve(J, -f0); x = x + dx
        V[pq] = x[len(pq):] * np.exp(1j * x[:len(pq)])
    else:
        raise RuntimeError("no convergence")
    return dict(buses=buses, idx=idx, Y=Y, V=V, S=S, state=state)

def results(sol):
    st, V, idx = sol["state"], sol["V"], sol["idx"]; m = (lambda b: "A" if (st["bs"] and b == "B") else b)
    kv = {b: abs(V[idx[b]]) * (33.0 if b in ("SRC", "P33") else 11.0) for b in sol["buses"]}
    out = dict(kV=kv, routes={}, tx={})
    for r_ in st.get("routes", N.ROUTES):
        if r_[0] not in st["closed"]: continue
        a, b = m(r_[1]), m(r_[2]); z = route_z(r_) / zbase(11.0)
        i_pu = (V[idx[a]] - V[idx[b]]) / z
        Ia = abs(i_pu) * SB * 1e6 / (math.sqrt(3) * 11e3)
        sa = V[idx[a]] * np.conj(i_pu) * SB * 1000      # kVA at 'from' end
        loss = abs(i_pu) ** 2 * z.real * SB * 1000
        out["routes"][r_[0]] = dict(I_A=Ia, P_from_kW=sa.real, Q_from_kvar=sa.imag, loss_kW=loss,
                                     sections=[(t, L, Ia / N.CABLE[t][2]) for t, L in r_[3]])
    for t, d in N.TX.items():
        if t not in st["tx"]: continue
        zpu = d["z"] * SB / d["S"]; r = zpu / math.sqrt(1 + d["xr"] ** 2); zt = complex(r, r * d["xr"])
        a = 1 + N.TAP_STEP * (st["taps"][t] - N.TAP_NOM); h, l = idx["P33"], idx[m("A" if t == "T1" else "B")]
        i_lv = (V[h] / a - V[l]) / zt; s_lv = V[l] * np.conj(i_lv) * SB
        out["tx"][t] = dict(tap=st["taps"][t], MVA_lv=abs(s_lv), P_lv_MW=s_lv.real, Q_lv_Mvar=s_lv.imag, loss_kW=abs(i_lv) ** 2 * r * SB * 1000)
    s_src = V[0] * np.conj((sol["Y"] @ V)[0]) * SB
    out["source_MW"], out["source_Mvar"] = s_src.real, s_src.imag
    load_p = sum(p for p, _ in st.get("loads", N.LOAD).values()) / 1000.0
    out["losses_kW"] = (s_src.real + st["pv_kw"] / 1000.0 - load_p) * 1000
    return out

def solve(state):
    """AVC: transformers whose tap is 'auto' take the tap (common tap when paralleled) giving section voltage closest to target."""
    autos = [t for t in state["tx"] if state["taps"].get(t) == "auto"]
    if not autos:
        return results(solve_fixed(state)), state
    best = None
    for tap in range(N.TAP_MIN, N.TAP_MAX + 1):
        s = dict(state); s["taps"] = {t: (tap if t in autos else state["taps"][t]) for t in state["tx"]}
        r = results(solve_fixed(s))
        dev = max(abs(r["kV"]["A" if (state["bs"] or t == "T1") else "B"] - N.AVC_TARGET_KV) for t in autos)
        if best is None or dev < best[0] - 1e-12: best = (dev, r, s)
    return best[1], best[2]
