"""Independent re-solve: constants parsed from the PDF text, sections transcribed from the rendered plan, pattern read from the chart; head-only Newton (scipy fsolve)."""
import re, math, json, numpy as np, fitz
from scipy.optimize import fsolve
T = "".join(p.get_text() for p in fitz.open("../artifact/wd22_v1.pdf")).replace("\n", " ")
f = lambda pat: float(re.search(pat, T).group(1))
HR = f(r"fixed water level ([\d.]+) m"); a = f(r"adds head H = ([\d.]+) -"); b = f(r"- ([\d.]+) x q\^2"); eta = f(r"x H / ([\d.]+),")
PRV = f(r"holds the head at J10 at exactly ([\d.]+) m"); Dt = f(r"internal diameter ([\d.]+) m, floor"); base = f(r"floor at ([\d.]+) m")
L0 = f(r"At 00:00 the tank level is ([\d.]+) m"); PMIN = f(r"Minimum pressure head ([\d.]+) m"); RES = f(r"Tank reserve ([\d.]+) m")
on1, off1 = f(r"P-1 starts when the level is at or below ([\d.]+)"), f(r"P-1 starts .*? stops when the level is at or above ([\d.]+)")
on2, off2 = f(r"P-2 starts when the level is at or below ([\d.]+)"), f(r"P-2 starts .*? stops when the level is at or above ([\d.]+) m\. Between")
tar_lo, tar_hi = f(r"Electricity tariff: GBP ([\d.]+) per kWh"), f(r"; GBP ([\d.]+) per kWh from 07:00")
TYPES = {m[0]: (float(m[1]) / 1000, float(m[2])) for m in re.findall(r"(DI300|DI250|DI200|CI200|PVC150)\s+[^:]*?internal diameter (\d+) mm, Hazen-Williams C = (\d+)", T)}
NODE = {m[0]: (float(m[1]), float(m[2])) for m in re.findall(r"(J\d+)\s+elevation\s+([\d.]+) m\s+base demand\s+([\d.]+) L/s", T)}
CAND = [float(x) for x in re.search(r"Candidate P-1 start levels: ([\d., ]+) m", T).group(1).split(", ")]
# transcribed from sheet 2 (by leader line)
SEC = {"A1": ("J1", "J2", [("DI300", 420), ("DI300", 380)]), "A2": ("J2", "J3", [("DI250", 450), ("DI200", 360)]), "A3": ("J3", "J4", [("DI200", 400), ("DI200", 310)]),
       "B1": ("J1", "J5", [("DI250", 520), ("DI250", 410)]), "B3": ("J2", "J5", [("DI200", 340), ("DI200", 490)]), "B2": ("J5", "J6", [("DI200", 380), ("CI200", 460)]),
       "C1": ("J3", "J7", [("DI200", 460), ("DI200", 390)]), "C2": ("J7", "J8", [("DI250", 390), ("DI250", 300)]), "C3": ("J6", "J7", [("CI200", 350), ("DI200", 520)]),
       "D1": ("J4", "J9", [("PVC150", 450), ("DI200", 380)]), "D2": ("J9", "J6", [("DI200", 300), ("PVC150", 390)]), "TK": ("J8", "T", [("DI250", 260), ("DI300", 340)]),
       "L1": ("J10", "J11", [("DI200", 480), ("DI200", 370)]), "L2": ("J11", "J12", [("PVC150", 420), ("PVC150", 330)])}
PAT = [0.55, 0.50, 0.45, 0.45, 0.50, 0.65, 1.05, 1.55, 1.60, 1.35, 1.20, 1.15, 1.20, 1.15, 1.05, 1.00, 1.05, 1.25, 1.45, 1.40, 1.20, 0.95, 0.75, 0.60]   # read from sheet 3
K = {p: sum(10.67 * L / (TYPES[t][1] ** 1.852 * TYPES[t][0] ** 4.87) for t, L in s) for p, (_, _, s) in SEC.items()}
J = [n for n in NODE]; ix = {n: i for i, n in enumerate(J)}; A = math.pi * Dt ** 2 / 4
def q(h1, h2, k): d = h1 - h2; return math.copysign((abs(d) / k) ** (1 / 1.852), d)
def solve(m, lev, n, h0):
    HT = base + lev
    def F(h):
        H = dict(zip(J, h)); H["T"] = HT; r = np.array([-NODE[x][1] * m / 1000 for x in J])
        for p, (u, v, _) in SEC.items():
            if p.startswith("L"): continue
            qq = q(H[u], H[v], K[p]); r[ix[u]] -= qq
            if v != "T": r[ix[v]] += qq
        lift = H["J1"] - HR; r[ix["J1"]] += n * math.sqrt(max(a - lift, 0) / b) / 1000 if n else 0
        r[ix["J6"]] -= sum(NODE[x][1] for x in ("J10", "J11", "J12")) * m / 1000     # PRV active (checked below)
        for x in ("J10", "J11", "J12"): r[ix[x]] = h[ix[x]] - {"J10": PRV, "J11": PRV - K["L1"] * ((NODE["J11"][1] + NODE["J12"][1]) * m / 1000) ** 1.852,
                                                                "J12": PRV - K["L1"] * ((NODE["J11"][1] + NODE["J12"][1]) * m / 1000) ** 1.852 - K["L2"] * (NODE["J12"][1] * m / 1000) ** 1.852}[x]
        return r
    h, info, ier, msg = fsolve(F, h0, full_output=True, xtol=1e-13); assert np.max(np.abs(F(h))) < 1e-11, (msg, np.max(np.abs(F(h))))
    H = dict(zip(J, h)); assert H["J6"] >= PRV; return H, h
def run(on1x):
    lev, p1, p2, E, C, h0 = L0, True, False, 0.0, 0.0, np.full(len(J), 100.0); levs, ev, pm = [lev], [], (9e9, None, None)
    for k in range(96):
        t = 15 * k; hr = t // 60
        n1 = True if lev <= on1x else (False if lev >= off1 else p1); n2 = True if lev <= on2 else (False if lev >= off2 else p2)
        if n1 != p1: ev.append((t, "P-1", "start" if n1 else "stop"))
        if n2 != p2: ev.append((t, "P-2", "start" if n2 else "stop"))
        p1, p2 = n1, n2; n = p1 + p2
        H, h0 = solve(PAT[hr], lev, n, h0)
        lift = H["J1"] - HR; Q = n * math.sqrt(max(a - lift, 0) / b) / 1000 if n else 0
        P = 9.81 * Q * lift / eta; E += P / 4; C += P / 4 * (tar_lo if hr < 7 or hr >= 23 else tar_hi)
        for x, (z, d) in NODE.items():
            if d > 0 and H[x] - z < pm[0]: pm = (H[x] - z, x, t)
        lev += q(H["J8"], base + lev, K["TK"]) * 900 / A; levs.append(lev)
    return dict(levs=levs, ev=ev, E=E, C=C, pm=pm, minlev=min(levs))
k = json.load(open("key.json")); r = run(on1); worst = 0.0
for hh in range(1, 25):
    kk = f"lev_{hh:02d}"
    if kk in k["all"]: worst = max(worst, abs(r["levs"][hh * 4] - k["all"][kk]))
for nm, v in (("energy", r["E"]), ("cost", r["C"]), ("pmin", r["pm"][0]), ("minlev", r["minlev"])): worst = max(worst, abs(v - k["all"][nm]) / max(1, abs(v)))
for sp in CAND:
    rr = run(sp); worst = max(worst, abs(rr["C"] - k["decision"][f"{sp:.2f}"]["cost"]) / 200, abs(rr["minlev"] - k["decision"][f"{sp:.2f}"]["minlev"]))
evs = [[f"{t // 60:02d}:{t % 60:02d}", p, e] for t, p, e in r["ev"]]
print("events match:", evs == k["events"], "| pmin at", r["pm"][1], f"{r['pm'][2] // 60:02d}:{r['pm'][2] % 60:02d}", "| worst rel/abs diff over all graded values:", f"{worst:.1e}")
