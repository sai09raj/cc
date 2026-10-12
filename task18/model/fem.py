"""Linear-elastic 2D frame analysis (direct stiffness) for HOLLOWAY-18."""
import copy, math
import numpy as np
import frame as F

GAUSS = np.polynomial.legendre.leggauss(6)

def config(**over):
    c = {k: copy.deepcopy(getattr(F, k)) for k in
         ("E", "G_ACC", "SPACING", "SEC", "GRID_X", "LEVEL_Y", "SPLICE", "COL", "BASE", "BEAM", "BRACE", "BRACE_SEC",
          "AREA", "STORAGE", "PLANT", "WIND")}
    c["self_weight"] = True
    c["col_override"] = {}           # (grid, storey index 0..3) -> section, applied after splice logic
    for k, v in over.items():
        c[k] = v
    return c

def geometry(c):
    lv = list(c["LEVEL_Y"]); ys = c["LEVEL_Y"]
    nodes, idx = [], {}
    def node(key, x, y):
        if key not in idx: idx[key] = len(nodes); nodes.append((x, y))
        return idx[key]
    els = []
    ysp = ys["L2"] + c["SPLICE"]
    for g, x in c["GRID_X"].items():
        pts = [(l, ys[l]) for l in lv]
        chain = []
        for (l, y) in pts:
            if y > ysp and not any(k == "SP" for k, _ in chain):
                chain.append(("SP", ysp))
            chain.append((l, y))
        for (k1, y1), (k2, y2) in zip(chain, chain[1:]):
            n1 = node((g, k1), x, y1); n2 = node((g, k2), x, y2)
            low, up = c["COL"][g]
            sec = low if y2 <= ysp + 1e-9 else up
            st = next(i for i in range(4) if ys[lv[i]] - 1e-9 <= y1 < ys[lv[i + 1]] - 1e-9)
            sec = c["col_override"].get((g, st, k1), c["col_override"].get((g, st), sec))
            els.append(dict(id=f"C{g}:{k1}-{k2}", kind="col", n=(n1, n2), sec=sec, rel=(False, False), loads=[]))
    gl = list(c["GRID_X"])
    for (l, bay), (sec, el, er) in c["BEAM"].items():
        g1, g2 = bay.split("-")
        n1 = node((g1, l), c["GRID_X"][g1], ys[l]); n2 = node((g2, l), c["GRID_X"][g2], ys[l])
        els.append(dict(id=f"B{l}:{bay}", kind="beam", n=(n1, n2), sec=sec, rel=(el == "S", er == "S"), loads=[]))
    for bid, (ga, la), (gb, lb) in c["BRACE"]:
        n1 = node((ga, la), c["GRID_X"][ga], ys[la]); n2 = node((gb, lb), c["GRID_X"][gb], ys[lb])
        els.append(dict(id=bid, kind="brace", n=(n1, n2), sec=c["BRACE_SEC"], rel=(True, True), loads=[]))
    return nodes, idx, els

def add_loads(c, nodes, idx, els):
    nodal = {}
    by = {e["id"]: e for e in els}
    for e in els:
        A, I, m = c["SEC"][e["sec"]]
        L = length(nodes, e)
        if c["self_weight"] and e["kind"] in ("col", "beam"):
            e["loads"].append(("udl", (0.0, -m * c["G_ACC"] / 1000.0), 0.0, L))
    for (l, bay), _ in c["BEAM"].items():
        e = by[f"B{l}:{bay}"]; L = length(nodes, e)
        e["loads"].append(("udl", (0.0, -c["AREA"][l] * c["SPACING"]), 0.0, L))
    s = c["STORAGE"]
    if s:
        e = by[f"B{s['level']}:{s['bay']}"]
        e["loads"].append(("udl", (0.0, -s["q"] * c["SPACING"]), s["a"], s["b"]))
    p = c["PLANT"]
    if p:
        e = by[f"B{p['level']}:{p['bay']}"]
        e["loads"].append(("pt", (0.0, -p["P"]), p["a"], None))
    for l, H in c["WIND"].items():
        nodal[idx[("1", l)]] = nodal.get(idx[("1", l)], np.zeros(3)) + np.array([H, 0.0, 0.0])
    return nodal

def length(nodes, e):
    (x1, y1), (x2, y2) = nodes[e["n"][0]], nodes[e["n"][1]]
    return math.hypot(x2 - x1, y2 - y1)

def rot(nodes, e):
    (x1, y1), (x2, y2) = nodes[e["n"][0]], nodes[e["n"][1]]
    L = math.hypot(x2 - x1, y2 - y1); cs, sn = (x2 - x1) / L, (y2 - y1) / L
    r = np.array([[cs, sn, 0], [-sn, cs, 0], [0, 0, 1.0]])
    T = np.zeros((6, 6)); T[:3, :3] = r; T[3:, 3:] = r
    return T, r, L

def k_local(EA, EI, L):
    a = EA / L; b = 12 * EI / L**3; cc = 6 * EI / L**2; d = 4 * EI / L; h = 2 * EI / L
    return np.array([[a, 0, 0, -a, 0, 0], [0, b, cc, 0, -b, cc], [0, cc, d, 0, -cc, h],
                     [-a, 0, 0, a, 0, 0], [0, -b, -cc, 0, b, -cc], [0, cc, h, 0, -cc, d]])

def shape(xi, L):
    """axial N1,N2 and Hermite H1..H4 at s = xi*L"""
    return (1 - xi, xi, 1 - 3 * xi**2 + 2 * xi**3, L * (xi - 2 * xi**2 + xi**3), 3 * xi**2 - 2 * xi**3, L * (-xi**2 + xi**3))

def p_equiv(e, r, L):
    """equivalent nodal load vector in local coordinates"""
    p = np.zeros(6)
    for kind, (gx, gy), a, b in e["loads"]:
        wl = r[:2, :2] @ np.array([gx, gy])        # local (axial, transverse)
        if kind == "udl":
            xs, ws = GAUSS
            for x, w in zip(xs, ws):
                s = a + (b - a) * (x + 1) / 2; jac = (b - a) / 2
                N1, N2, H1, H2, H3, H4 = shape(s / L, L)
                p += jac * w * np.array([N1 * wl[0], H1 * wl[1], H2 * wl[1], N2 * wl[0], H3 * wl[1], H4 * wl[1]])
        else:
            N1, N2, H1, H2, H3, H4 = shape(a / L, L)
            p += np.array([N1 * wl[0], H1 * wl[1], H2 * wl[1], N2 * wl[0], H3 * wl[1], H4 * wl[1]])
    return p

def condense(k, p, rel):
    r = [i for i, f in zip((2, 5), rel) if f]
    if not r: return k, p, None
    cdofs = [i for i in range(6) if i not in r]
    krr = k[np.ix_(r, r)]; krc = k[np.ix_(r, cdofs)]; kcr = k[np.ix_(cdofs, r)]
    kc = np.zeros((6, 6)); pc = np.zeros(6)
    kc[np.ix_(cdofs, cdofs)] = k[np.ix_(cdofs, cdofs)] - kcr @ np.linalg.solve(krr, krc)
    pc[cdofs] = p[cdofs] - kcr @ np.linalg.solve(krr, p[r])
    return kc, pc, (r, cdofs, krr, krc, p[r])

def solve(c):
    nodes, idx, els = geometry(c)
    nodal = add_loads(c, nodes, idx, els)
    n = len(nodes); K = np.zeros((3 * n, 3 * n)); P = np.zeros(3 * n)
    for i, f in nodal.items(): P[3 * i:3 * i + 3] += f
    for e in els:
        A, I, m = c["SEC"][e["sec"]]
        T, r, L = rot(nodes, e)
        k = k_local(c["E"] * A * 1e-4, c["E"] * I * 1e-8, L)
        p = p_equiv(e, r, L)
        kc, pc, cinfo = condense(k, p, e["rel"])
        e.update(T=T, r=r, L=L, k=k, p=p, kc=kc, pc=pc, cinfo=cinfo)
        dofs = [3 * e["n"][0] + j for j in range(3)] + [3 * e["n"][1] + j for j in range(3)]
        K[np.ix_(dofs, dofs)] += T.T @ kc @ T
        P[dofs] += T.T @ pc
        e["dofs"] = dofs
    fixed = []
    for g, b in c["BASE"].items():
        i = idx[(g, "G")]
        fixed += [3 * i, 3 * i + 1] + ([3 * i + 2] if b == "fixed" else [])
    free = [d for d in range(3 * n) if d not in fixed]
    U = np.zeros(3 * n)
    U[free] = np.linalg.solve(K[np.ix_(free, free)], P[free])
    R = K @ U - P
    for e in els:
        ul = e["T"] @ U[e["dofs"]]
        f = e["kc"] @ ul - e["pc"]
        if e["cinfo"]:
            rr, cd, krr, krc, pr = e["cinfo"]
            ul[rr] = np.linalg.solve(krr, pr - krc @ ul[cd])
            f = e["k"] @ ul - e["p"]
        e["f"] = f          # local end forces ON the element: N1,V1,M1,N2,V2,M2 (anticlockwise +)
        e["ul"] = ul
    return dict(c=c, nodes=nodes, idx=idx, els=els, U=U, R=R)

def moment_along(e, s):
    """bending moment at local s (sagging +, i.e. tension on the local -y face for a beam drawn left to right)"""
    N1, V1, M1 = e["f"][:3]
    M = -M1 + V1 * s
    for kind, (gx, gy), a, b in e["loads"]:
        wl = (e["r"][:2, :2] @ np.array([gx, gy]))[1]
        if kind == "udl":
            if s > a:
                sb = min(s, b); M += wl * (sb - a) * (s - (a + sb) / 2)
        else:
            if s > a: M += wl * (s - a)
    return M
