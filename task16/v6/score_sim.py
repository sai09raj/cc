"""Score each plausible single misread against the v2 rubric thresholds (all other items assumed right)."""
import importlib, copy, json
import plant as P
def final():
    import geom, hyd, timeline
    for m in (geom, hyd, timeline): importlib.reload(m)
    s = hyd.solve(timeline.STATES[-1][1]); return s[0] if len(s) == 1 else None
ORIG = copy.deepcopy(P.LINES); base = final()
W = {"Qp_P-201A": 5, "Qp_P-201B": 5, "PI": 5, "Q203": 5, "Q205": 5, "Q206": 5, "Q207": 5, "Q209": 5, "Q204": 5, "QG": 5, "Q211": 5, "zt": 5,
     "Qr0": 4, "Qr1": 4, "Qr2": 4, "Qr3": 4, "Qr4": 4, "Qr5": 4}
POS = 109
def score(v):
    lost = 0
    for k, w in W.items():
        if k == "PI": bad = abs(v["PI100_barg"] - base["PI100_barg"]) > 0.002
        elif k == "zt": bad = abs(v["zt"] - base["zt"]) > 0.002
        elif k == "Qr2": bad = abs(v[k] - base[k]) > 0.00002
        else: bad = abs(v[k] - base[k]) > 0.001 * abs(base[k])
        lost += w * bad
    if v["regime"][0] != base["regime"][0]: lost += 2
    return 100 * (POS - lost) / POS
def mod(lid, items):
    for i, L in enumerate(P.LINES):
        if L[0] == lid: P.LINES[i] = (L[0], L[1], L[2], items)
CASES = {
 "swap 18000/19000": [("CW-208", [("D", 3000), ("W", 13000), ("D", 18000), ("N", 6000), "N5"]), ("CW-211", [("W", 3000, "GV"), ("U", 19000), ("W", 9000), ("D", 30000), ("W", 4000), "POND"])],
 "detail E leg as drop": [("CW-207", [("S", 4000, "HV-204"), ("D", 1000), ("S", 3000, "HX:E-204"), "D204"])],
 "detail F leg as rise": [("CW-209", [("E", 3000, "GV"), ("U", 1000), ("E", 2000, "HX:E-205"), "D205"])],
 "detail A leg 2000 read as 1500": [("CW-203", [("W", 4000, "FV-201"), ("D", 1500), ("W", 3000, "HX:E-201"), "D201"])],
 "ring rise missed": [("CW-202", [("N", 20000), "Ta", ("N", 30000), ("E", 40000), "Tb", ("E", 50000), ("S", 25000), "Tc", ("S", 25000), ("W", 45000), "Td", ("W", 25000), "Te", ("W", 20000), "R1"]),
                       ("CW-204", [("N", 3000, "GV"), ("U", 22000), ("N", 5000), "TK1IN"])],
 "riser one elbow too many (D leg)": [("CW-204", [("N", 3000, "GV"), ("U", 18500), ("N", 5000), ("D", 1000), "TK1IN"])],
}
print("base score", score(base))
for name, mods in CASES.items():
    P.LINES[:] = copy.deepcopy(ORIG)
    for lid, it in mods: mod(lid, it)
    v = final(); print(f"{name:34s}", "no unique solution" if v is None else f"{score(v):5.1f}")
P.LINES[:] = copy.deepcopy(ORIG)
