"""Solve the v4 system for a given operating state, enumerating physics regimes and keeping the consistent one."""
import itertools, math
from model import *

def newton(f, x0, it=300):
    x = list(x0)
    for _ in range(it):
        r = f(x)
        if max(abs(v) for v in r) < 1e-10: return x, True
        n = len(x); J = []
        for j in range(n):
            h = 1e-8 * max(1.0, abs(x[j])); xp = list(x); xp[j] += h; rp = f(xp); J.append([(rp[i] - r[i]) / h for i in range(n)])
        A = [[J[j][i] for j in range(n)] + [-r[i]] for i in range(n)]
        for c in range(n):
            p = max(range(c, n), key=lambda i: abs(A[i][c])); A[c], A[p] = A[p], A[c]
            if abs(A[c][c]) < 1e-30: return x, False
            for i in range(n):
                if i != c:
                    m = A[i][c] / A[c][c]; A[i] = [a - m * b for a, b in zip(A[i], A[c])]
        dx = [A[i][n] / A[i][i] for i in range(n)]
        x = [a + 0.6 * d for a, d in zip(x, dx)]
    r = f(x); return x, max(abs(v) for v in r) < 1e-8

def solve(state):
    """state: running pumps (list), fv ('auto' or % open), hv204 open (bool)"""
    run = state["pumps"]
    results = []
    for overflow, separated in itertools.product((True, False), (True, False)):
        # unknowns: Q per running pump, H2, Q1, Q2, QR, zt, Qw (if overflow), Q3, Q4, Q5, H4
        names = [f"Q_{p}" for p in run] + ["H2", "Q1", "Q2", "QR", "zt", "Q3", "Q4", "Q5", "H4"] + (["Qw"] if overflow else [])
        def f(x):
            v = dict(zip(names, x)); r = []
            Qp = [v[f"Q_{p}"] for p in run]; QL1 = sum(Qp)
            for p in run:
                H0, k = PUMPS[p]; q = v[f"Q_{p}"]
                H1 = SUMP + H0 - k * q * abs(q) - K_PUMP_DISCH * vh(q, "DN150")
                r.append(H1 - loss("L1", QL1) - v["H2"])
            if state["fv"] == "auto":
                r.append(v["Q1"] - FC_SETPOINT)     # controller holds the setpoint (valve not saturated)
            else:
                r.append(v["H2"] - loss("C1", v["Q1"], KHX["C1"] + FV_K[state["fv"]]) - Z["C1"])
            r.append(v["H2"] - loss("C2", v["Q2"], KHX["C2"]) - Z["C2"])
            r.append(v["H2"] - loss("R", v["QR"]) - Z["R"])
            r.append(QL1 - v["Q1"] - v["Q2"] - v["QR"])
            Qg = v["Q3"] + v["Q4"] + v["Q5"]
            if overflow:
                r.append(v["zt"] - WEIR_Z - (max(v["Qw"], 1e-12) / (CW * WEIR_L)) ** (2 / 3))
                r.append(v["QR"] - Qg - v["Qw"])
            else:
                r.append(v["QR"] - Qg)
            r.append(v["zt"] - loss("G", Qg) - v["H4"])
            r.append(v["H4"] - loss("C3", v["Q3"], KHX["C3"]) - Z["C3"])
            if state["hv204"]: r.append(v["H4"] - loss("C4", v["Q4"], KHX["C4"]) - Z["C4"])
            else: r.append(v["Q4"])
            if separated: r.append(v["H4"] - loss("O_up", v["Q5"]) - Z["crest"] - vh(v["Q5"], "DN100") - HV)
            else: r.append(v["H4"] - loss("O_up", v["Q5"]) - loss("O_dn", v["Q5"]) - Z["pond"])
            return r
        x0 = [0.03] * len(run) + [30.0, 0.015, 0.02, 0.04, 26.5, 0.01, 0.01, 0.02, 20.0] + ([0.01] if overflow else [])
        x, ok = newton(f, x0)
        if not ok: continue
        v = dict(zip(names, x))
        crest = v["H4"] - loss("O_up", v["Q5"]) - Z["crest"] - vh(v["Q5"], "DN100")   # gauge head at crest
        cons = all(v[n] > -1e-9 for n in names if n.startswith("Q"))
        if state["fv"] == "auto":   # controller must be able to achieve setpoint: required K >= fully open K
            req = (v["H2"] - Z["C1"] - loss("C1", v["Q1"], KHX["C1"])) / vh(v["Q1"], "DN100")
            cons &= req >= FV_K[100]; v["FV_K_required"] = req
        cons &= (v["zt"] >= WEIR_Z - 1e-9) if overflow else (v["zt"] <= WEIR_Z + 1e-9)
        cons &= (crest <= HV + 1e-9) if separated else (crest >= HV - 1e-9)
        v["crest_kPa_abs"] = (crest * RHO * G + PATM) / 1000
        v["regime"] = ("overflow" if overflow else "below weir") + ", " + ("separated" if separated else "full")
        if cons: results.append(v)
    return results

if __name__ == "__main__":
    import json, sys
    for label, st in [("naive: A+B+C, FV auto, HV-204 open", dict(pumps=["P-101A", "P-101B", "P-101C"], fv="auto", hv204=True)),
                      ("naive2: A+B, FV auto, HV-204 open", dict(pumps=["P-101A", "P-101B"], fv="auto", hv204=True)),
                      ("log: A+C, FV manual 45%, HV-204 closed", dict(pumps=["P-101A", "P-101C"], fv=45, hv204=False))]:
        res = solve(st)
        print(label, "->", len(res), "consistent solution(s)")
        for v in res:
            print("  ", v["regime"], {k: (round(v[k] * 1000, 2) if k.startswith("Q") else round(v[k], 3)) for k in v if k != "regime"})
