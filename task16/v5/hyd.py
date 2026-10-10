"""CW-200 steady-state solver: regime enumeration + Newton. State: running pumps, FV modes, HV positions."""
import itertools, math
import plant as P
from geom import build
NODES, LINES = build()
HVAP = (P.PV - P.PATM) / (P.RHO * P.G)
def area(dn): return math.pi * P.ID[dn] ** 2 / 4
def vh(Q, dn): return (Q / area(dn)) ** 2 / (2 * P.G)
def fric(Q, dn, L):
    q = abs(Q)
    if q < 1e-12: return 0.0
    d = P.ID[dn]; v = q / area(dn); Re = v * d / P.NU
    f = 0.25 / math.log10(P.EPS / (3.7 * d) + 5.74 / Re ** 0.9) ** 2
    return f * L / d * v * v / (2 * P.G)
def piece(lid, i=0): return LINES[lid][i]
def kfit(pc, state, extra=0.0):
    k = extra + pc["elbows"] * P.K["ell"]
    for f in pc["fit"]:
        if f == "GV": k += P.K["gv"]
        elif f.startswith("HV"): k += P.K["hv_open"]
        elif f.startswith("HX:"): k += P.HX[f[3:]]
        elif f.startswith("FV"):
            m = state["fv"][f]
            if m != "auto": k += P.FV_CHAR[m]
    return k
def loss(pc, Q, state, extra=0.0):
    return fric(Q, pc["dn"], pc["L"]) + kfit(pc, state, extra) * vh(Q, pc["dn"])
def sloss(pc, Q, state): return math.copysign(loss(pc, Q, state), Q)
def z(node): return NODES[node][2] / 1000.0
RING = [p for p in LINES["CW-202"]]          # R1-Ta, Ta-Tb, Tb-Tc, Tc-Td, Td-Te, Te-R1
BR = {"CW-203": "Ta", "CW-205": "Tc", "CW-206": "Td", "CW-207": "Te"}
def solve(state, want_all=False):
    run = state["pumps"]; sols = []
    regimes = itertools.product((True, False), (True, False), (True, False), *[(False, True)] * len([f for f, m in state["fv"].items() if m == "auto"]))
    autos = [f for f, m in state["fv"].items() if m == "auto"]
    for reg in regimes:
        overflow, separated, riser_on = reg[0], reg[1], reg[2]; sat = dict(zip(autos, reg[3:]))
        if not riser_on and overflow: continue
        names = [f"Qp_{p}" for p in run] + ["HM", "Q201"] + [f"Hn_{n}" for n in ("R1", "Ta", "Tb", "Tc", "Td", "Te", "N5")] + \
                [f"Qr{i}" for i in range(6)] + ["Q203", "Q204", "Q205", "Q206", "Q207", "QG", "Q209", "Q210", "Q211", "zt"] + (["Qw"] if overflow else [])
        def F(x):
            v = dict(zip(names, x)); r = []; H = lambda n: v[f"Hn_{n}"]
            for p in run:
                H0, k = P.PUMPS[p]; q = v[f"Qp_{p}"]
                r.append(H0 - k * q * abs(q) - P.K_PUMP * vh(q, 150) - v["HM"])
            r.append(sum(v[f"Qp_{p}"] for p in run) - v["Q201"])
            r.append(v["HM"] - loss(piece("CW-201"), v["Q201"], state) - H("R1"))
            seq = ["R1", "Ta", "Tb", "Tc", "Td", "Te", "R1"]
            for i in range(6): r.append(H(seq[i]) - sloss(RING[i], v[f"Qr{i}"], state) - H(seq[i + 1]))
            r.append(v["Q201"] + v["Qr5"] - v["Qr0"])                      # R1
            r.append(v["Qr0"] - v["Qr1"] - v["Q203"])                      # Ta
            r.append(v["Qr1"] - v["Qr2"] - v["Q204"])                      # Tb (riser)
            r.append(v["Qr2"] - v["Qr3"] - v["Q205"])                      # Tc
            r.append(v["Qr3"] - v["Qr4"] - v["Q206"])                      # Td
            r.append(v["Qr4"] - v["Qr5"] - v["Q207"])                      # Te
            for lid, qn in (("CW-203", "Q203"), ("CW-205", "Q205"), ("CW-206", "Q206"), ("CW-207", "Q207")):
                pc = piece(lid); node = BR[lid]
                fv = next((f for f in pc["fit"] if f.startswith("FV")), None); hv = next((f for f in pc["fit"] if f.startswith("HV")), None)
                if hv and not state["hv"][hv]: r.append(v[qn]); continue
                if fv and state["fv"][fv] == "auto" and not sat[fv]: r.append(v[qn] - state["sp"][fv]); continue
                kx = P.K["branch"] + P.K["exit"] + (P.FV_CHAR[100] if fv and state["fv"][fv] == "auto" else 0.0)
                r.append(H(node) - loss(pc, v[qn], state, kx) - z(pc["to"]))
            if riser_on: r.append(H("Tb") - loss(piece("CW-204"), v["Q204"], state, P.K["branch"] + P.K["exit"]) - z("TK1IN"))
            else: r.append(v["Q204"])
            if state.get("header_only"):
                r += [v["QG"] - v["Q204"], v["zt"] - 27.0, v["Hn_N5"] - 10.0, v["Q209"], v["Q210"], v["Q211"]] + ([v["Qw"]] if overflow else [])
                return r
            if overflow:
                r.append(v["zt"] - P.WEIR_CREST - (max(v["Qw"], 0.0) / (P.WEIR_C * P.WEIR_L)) ** (2 / 3))
                r.append(v["Q204"] - v["QG"] - v["Qw"])
            else:
                r.append(v["Q204"] - v["QG"])
            r.append(v["zt"] - loss(piece("CW-208"), v["QG"], state, P.K["ent"]) - H("N5"))
            r.append(v["QG"] - v["Q209"] - v["Q210"] - v["Q211"])
            r.append(H("N5") - loss(piece("CW-209"), v["Q209"], state, P.K["branch"] + P.K["exit"]) - z("D205"))
            if state["hv"]["HV-206"]: r.append(H("N5") - loss(piece("CW-210"), v["Q210"], state, P.K["branch"] + P.K["exit"]) - z("D206"))
            else: r.append(v["Q210"])
            pc = piece("CW-211")
            if separated: r.append(H("N5") - crest_loss(v["Q211"], state) - CREST_Z - vh(v["Q211"], pc["dn"]) - HVAP)
            else: r.append(H("N5") - loss(pc, v["Q211"], state, P.K["branch"] + P.K["exit"]) - z("POND"))
            return r
        x0 = [0.05] * len(run) + [40.0, 0.05 * len(run)] + [35.0] * 6 + [10.0] + [0.03, 0.01, 0.0, -0.01, -0.03, -0.04] + \
             [0.015, 0.04, 0.02, 0.015, 0.02, 0.04, 0.012, 0.01, 0.02, 28.0] + ([0.005] if overflow else [])
        x, ok = newton(F, x0)
        if not ok: continue
        v = dict(zip(names, x)); v["regime"] = (overflow, separated, riser_on, dict(sat))
        if not riser_on and v["Hn_Tb"] > z("TK1IN") + 1e-9: continue
        good = all(v[n] > -1e-9 for n in names if n.startswith("Qp") or n in ("Q203", "Q204", "Q205", "Q206", "Q207", "QG", "Q209", "Q210", "Q211", "Qw"))
        if state.get("header_only"):
            v["PI100_barg"] = (v["Hn_R1"] - z("R1") - vh(v["Qr0"], 200)) * P.RHO * P.G / 1e5
            if (not overflow) and separated and good: sols.append(v)
            continue
        good &= (v["zt"] >= P.WEIR_CREST - 1e-9) if overflow else (v["zt"] <= P.WEIR_CREST + 1e-9)
        v["tank_ok"] = v["zt"] >= P.TK1_OUTLET[2] / 1000 + 0.5
        cp = v["Hn_N5"] - crest_loss(v["Q211"], state) - CREST_Z - vh(v["Q211"], pc11["dn"]); v["crest_kPa"] = (cp * P.RHO * P.G + P.PATM) / 1000
        good &= (cp <= HVAP + 1e-9) if separated else (cp >= HVAP - 1e-9)
        for f in autos:
            pc = piece("CW-203" if f == "FV-201" else "CW-206"); node = BR["CW-203" if f == "FV-201" else "CW-206"]
            q = v["Q203" if f == "FV-201" else "Q206"]
            req = (v[f"Hn_{node}"] - z(pc["to"]) - loss(pc, q, state, P.K["branch"] + P.K["exit"])) / vh(q, pc["dn"])
            v[f"{f}_Kreq"] = req
            good &= (q <= state["sp"][f] + 1e-12) if sat[f] else (req >= P.FV_CHAR[100] - 1e-9)
        v["PI100_barg"] = (v["Hn_R1"] - z("R1") - vh(v["Qr0"], 200)) * P.RHO * P.G / 1e5
        if good: sols.append(v)
    return sols
# outfall crest: end of the W 9000 run at EL 21; crest loss includes branch tee, GV, elbows up to and including the crest-end elbow
pc11 = piece("CW-211"); CREST_Z = 21.0
def crest_loss(Q, state):
    mv = pc11["moves"][:3]; L = sum(m[1] for m in mv) / 1000; ell = 2 + 1     # W->U, U->W, crest-end W->D
    k = P.K["branch"] + P.K["gv"] + ell * P.K["ell"]
    return fric(Q, pc11["dn"], L) + k * vh(Q, pc11["dn"])
def newton(f, x0, it=400):
    x = list(x0)
    for _ in range(it):
        r = f(x)
        if max(abs(t) for t in r) < 1e-10: return x, True
        n = len(x); A = []
        J = []
        for j in range(n):
            h = 1e-7 * max(1.0, abs(x[j])); xp = list(x); xp[j] += h; rp = f(xp); J.append([(rp[i] - r[i]) / h for i in range(n)])
        A = [[J[j][i] for j in range(n)] + [-r[i]] for i in range(n)]
        for c in range(n):
            p = max(range(c, n), key=lambda i: abs(A[i][c])); A[c], A[p] = A[p], A[c]
            if abs(A[c][c]) < 1e-30: return x, False
            for i in range(n):
                if i != c and A[i][c] != 0:
                    m = A[i][c] / A[c][c]; A[i] = [a - m * b for a, b in zip(A[i], A[c])]
        dx = [A[i][n] / A[i][i] for i in range(n)]
        x = [a + 0.5 * d for a, d in zip(x, dx)]
    return x, max(abs(t) for t in f(x)) < 1e-8
def show(v):
    out = {k: (round(val * 1000, 2) if k.startswith("Q") else round(val, 3)) for k, val in v.items() if k != "regime" and not isinstance(val, dict)}
    return v["regime"], out
