import math, net as N

def fsolve(f, x0, args=(), xtol=1e-12):
    x = list(x0)
    for _ in range(200):
        r = f(x, *args)
        if max(abs(v) for v in r) < 1e-11: break
        J = []
        for j in range(len(x)):
            h = 1e-7; xp = list(x); xp[j] += h; rp = f(xp, *args); J.append([(rp[i] - r[i]) / h for i in range(len(x))])
        # solve J^T dx = -r (J stored column-wise)
        n = len(x); A = [[J[j][i] for j in range(n)] + [-r[i]] for i in range(n)]
        for c in range(n):
            p = max(range(c, n), key=lambda i: abs(A[i][c])); A[c], A[p] = A[p], A[c]
            for i in range(n):
                if i != c:
                    m = A[i][c] / A[c][c]; A[i] = [a - m * b for a, b in zip(A[i], A[c])]
        dx = [A[i][n] / A[i][i] for i in range(n)]
        x = [max(1e-6, a + 0.7 * d) for a, d in zip(x, dx)]
    return x
def segs(line):
    lid, dn, frm, items = line; out = []; prev = None; L = 0; z0 = None
    return items
def friction(Q, D, L):
    A = math.pi * D * D / 4; v = abs(Q) / A
    if v == 0: return 0.0
    Re = v * D / N.NU; f = 0.25 / math.log10(N.EPS / (3.7 * D) + 5.74 / Re ** 0.9) ** 2
    return f * L / D * v * v / (2 * N.G)
def vh(Q, D): A = math.pi * D * D / 4; return (Q / A) ** 2 / (2 * N.G)
def path_loss(Q, dn, moves, k_extra):
    """moves: list of (dir, len_mm, fitting?) ; returns head loss (m) and elbow count"""
    D = N.ID[dn]; L = sum(m[1] for m in moves) / 1000; ell = sum(1 for a, b in zip(moves, moves[1:]) if a[0] != b[0])
    gv = sum(1 for m in moves if len(m) > 2 and m[2] == "GV")
    k = k_extra + ell * N.K["ell"] + gv * N.K["gv"]
    return friction(Q, D, L) + k * vh(Q, D)
# header pieces
H = N.LINES[0][3]
h_up_T1 = H[:3]; h_T1_T2 = [H[4]]; h_T2_T3 = [H[6]]; h_T3_O4 = [H[8], H[9]]
br = {1: N.LINES[1][3][:-1], 2: N.LINES[2][3][:-1], 3: N.LINES[3][3][:-1]}
zO = {1: 15.0, 2: 17.0, 3: 0.0, 4: 16.0}; Htank = N.TANK_LEVEL / 1000
def heads(Q1, Q2, Q3, Q4):
    q01 = Q1 + Q2 + Q3 + Q4; q12 = Q2 + Q3 + Q4; q23 = Q3 + Q4
    # elbow between tank leg and T1 (D,E,D,N): 3 elbows; entrance loss
    HT1 = Htank - path_loss(q01, 150, h_up_T1, N.K["ent"])
    HT2 = HT1 - path_loss(q12, 150, h_T1_T2, N.K["tee_run"])
    HT3 = HT2 - path_loss(q23, 150, h_T2_T3, N.K["tee_run"])
    return HT1, HT2, HT3
def residual(x, mode):
    Q1, Q2, Q3, Q4 = x; HT1, HT2, HT3 = heads(Q1, Q2, Q3, Q4)
    r1 = HT1 - path_loss(Q1, 80, br[1], N.K["tee_branch"] + N.K["exit"] + N.KHX[1]) - zO[1]
    r2 = HT2 - path_loss(Q2, 80, br[2], N.K["tee_branch"] + N.K["exit"] + N.KHX[2]) - zO[2]
    r4 = HT3 - path_loss(Q4, 150, h_T3_O4, N.K["tee_run"] + N.K["exit"] + N.KHX[4]) - zO[4]
    if mode == "full":
        r3 = HT3 - path_loss(Q3, 80, br[3], N.K["tee_branch"] + N.K["exit"]) - zO[3]
    else:   # crest at vapour pressure: H_T3 - losses(T3->crest end) - z_crest - v^2/2g = (Pv-Patm)/(rho g)
        up = br[3][:3]   # E 2000 GV, U 26000, E 6000 (crest run)
        r3 = HT3 - path_loss(Q3, 80, up, N.K["tee_branch"] + N.K["ell"]) - 31.0 - vh(Q3, N.ID[80]) - (N.PV - N.PATM) / (N.RHO * N.G)
    return [r1, r2, r3, r4]
def crest_p(x):
    Q1, Q2, Q3, Q4 = x; HT3 = heads(*x)[2]
    hp = HT3 - path_loss(Q3, 80, br[3][:3], N.K["tee_branch"] + N.K["ell"]) - 31.0 - vh(Q3, N.ID[80])
    return hp * N.RHO * N.G + N.PATM
for mode in ("full", "separated"):
    pass
for mode in ("full", "separated"):
    x = fsolve(residual, [0.01] * 4, args=(mode,), xtol=1e-12)
    print(mode, "flows L/s", [round(q * 1000, 3) for q in x], "total", round(sum(x) * 1000, 3),
          "crest abs pressure kPa", round(crest_p(x) / 1000, 2), "resid", max(abs(r) for r in residual(x, mode)),
          "header v m/s", round(sum(x) / (3.14159 * N.ID[150] ** 2 / 4), 2), "v3", round(x[2] / (3.14159 * N.ID[80] ** 2 / 4), 2))

if __name__ == "__main__":
    import json
    x = fsolve(residual, [0.01] * 4, args=("separated",), xtol=1e-12)
    HT1, HT2, HT3 = heads(*x); q23 = x[2] + x[3]
    pT3 = (HT3 - 14.0 - vh(q23, N.ID[150])) * N.RHO * N.G + N.PATM
    key = dict(flows_Ls={f"O{i + 1}": round(q * 1000, 3) for i, q in enumerate(x)}, total_Ls=round(sum(x) * 1000, 3),
               crest_kPa=round(crest_p(x) / 1000, 3), T3_kPa=round(pT3 / 1000, 2))
    xf = fsolve(residual, [0.01] * 4, args=("full",), xtol=1e-12)
    key["naive_full_pipe"] = dict(flows_Ls={f"O{i + 1}": round(q * 1000, 3) for i, q in enumerate(xf)}, total_Ls=round(sum(xf) * 1000, 3),
                                  crest_kPa=round(crest_p(xf) / 1000, 2))
    json.dump(key, open("key.json", "w"), indent=1); print(json.dumps(key))
