"""Sensitivity: how many graded values fail (0.5 %) under each plausible misread."""
import importlib, sys, copy
import plant as P
TOL = float(sys.argv[1]) if len(sys.argv) > 1 else 0.005
KEYS = ["Qp_P-201A", "Qp_P-201B", "Q203", "Q205", "Q206", "Q207", "Q209", "Q204", "QG", "Q211", "Qr0", "Qr1", "Qr2", "Qr3", "Qr4", "Qr5"]
def final():
    import geom, hyd, timeline
    for m in (geom, hyd, timeline): importlib.reload(m)
    sols = hyd.solve(timeline.STATES[-1][1]); assert len(sols) == 1, len(sols)
    return sols[0]
def mod_line(lid, new_items):
    for i, L in enumerate(P.LINES):
        if L[0] == lid: P.LINES[i] = (L[0], L[1], L[2], new_items)
ORIG = copy.deepcopy(P.LINES)
base = final()
def report(name):
    v = final(); fails = []
    for k in KEYS:
        a, b = base[k], v[k]
        if abs(b - a) > max(TOL * abs(a), 0.00005): fails.append(k)
    lv = abs(v["zt"] - base["zt"]) > 0.002; pi = abs(v["PI100_barg"] - base["PI100_barg"]) > 0.002
    print(f"{name:34s} fails {len(fails)+lv+pi:2d}/18  level {v['zt']:.3f} PI {v['PI100_barg']:.3f} regime {v['regime'][:2]} {fails}")
print("base", {k: round(base[k]*1000, 2) for k in KEYS}, round(base["zt"], 4), round(base["PI100_barg"], 3), base["regime"])
mod_line("CW-208", [("D", 3000), ("W", 13000), ("D", 18000), ("N", 6000), "N5"]); mod_line("CW-211", [("W", 3000, "GV"), ("U", 19000), ("W", 9000), ("D", 30000), ("W", 4000), "POND"])
import hyd
try: report("swap 18000/19000")
except AssertionError as e: print("swap: no unique", e)
P.LINES[:] = copy.deepcopy(ORIG)
mod_line("CW-207", [("S", 4000, "HV-204"), ("D", 1000), ("S", 3000, "HX:E-204"), "D204"]); report("detail E drop instead of rise")
P.LINES[:] = copy.deepcopy(ORIG)
mod_line("CW-209", [("E", 3000, "GV"), ("U", 1000), ("E", 2000, "HX:E-205"), "D205"]); report("detail F rise instead of drop")
P.LINES[:] = copy.deepcopy(ORIG)
mod_line("CW-202", [("N", 20000), "Ta", ("N", 30000), ("E", 40000), "Tb", ("E", 50000), ("S", 25000), "Tc", ("S", 25000), ("W", 45000), "Td", ("W", 25000), "Te", ("W", 20000), "R1"])
mod_line("CW-204", [("N", 3000, "GV"), ("U", 22000), ("N", 5000), "TK1IN"]); report("ring offsets missed (riser to same inlet)")
P.LINES[:] = copy.deepcopy(ORIG)
