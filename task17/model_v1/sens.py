"""Single-misread sensitivity: count graded values outside tolerance."""
import copy, sys, pf, state, net as N
TOL = float(sys.argv[1]) if len(sys.argv) > 1 else 0.001
VT = float(sys.argv[2]) if len(sys.argv) > 2 else 0.002
def key(r, s):
    k = {f"V {b}": v for b, v in r["kV"].items() if (b.startswith("S") and b != "SRC") or b in ("A", "B")}
    k.update({f"I {rid}": v["I_A"] for rid, v in r["routes"].items()})
    k.update({"T1 MVA": r["tx"]["T1"]["MVA_lv"], "T2 MVA": r["tx"]["T2"]["MVA_lv"], "src MW": r["source_MW"], "src Mvar": r["source_Mvar"], "loss": r["losses_kW"]})
    k["T2 tap"] = s["taps"]["T2"]; return k
base_r, base_s = pf.solve(state.final()); B = key(base_r, base_s)
ORIG = copy.deepcopy(N.ROUTES)
MODS = {}
def mod(rid, secs): MODS[rid] = secs
def run(name, fn=None, **over):
    MODS.clear()
    if fn: fn()
    rs = [(r[0], r[1], r[2], MODS.get(r[0], r[3])) for r in over.pop("routes", state.routes())]
    r, s = pf.solve(state.final(routes=rs, **over)); K = key(r, s)
    bad = [k for k in B if (k not in K) or (K[k] != B[k] if k == "T2 tap" else abs(K[k] - B[k]) > (VT if k.startswith("V ") else TOL * abs(B[k])))]
    print(f"{name:42s} {len(bad):2d}/{len(B)}  {bad if len(bad) < 8 else ''}")
    N.ROUTES[:] = copy.deepcopy(ORIG)
run("F1-3 repair ignored", routes=state.routes(False))
run("F1-3 repair length 380 kept", lambda: mod("F1-3", [("185", 640), ("185", 380)]))
run("F2-2 1240 read as 1420", lambda: mod("F2-2", [("185", 1420)]))
run("F4-2 1060 read as 1600", lambda: mod("F4-2", [("95", 1600)]))
run("IC-1 1480 read as 1840", lambda: mod("IC-1", [("185", 1840)]))
run("F3-2 sections swapped type 95", lambda: mod("F3-2", [("185", 690), ("95", 510)]))
run("NOP-1 left open (log misread)", closed=state.final()["closed"] - {"NOP-1"})
run("NOP-2 left open", closed=state.final()["closed"] - {"NOP-2"})
run("cap off", cap=False)
run("PV 4000", pv_kw=4000.0)
run("T1 auto too", taps={"T1": "auto", "T2": "auto"})
run("T1 tap 8 misread", taps={"T1": 8, "T2": "auto"})
run("BS closed (log misread)", bs=True)
run("IC-2 1630 read as 1360", lambda: mod("IC-2", [("185", 1360)]))
run("F1-1 300 section read 185", lambda: mod("F1-1", [("185", 1150), ("185", 420)]))
run("F2-3 70 section read as 95", lambda: mod("F2-3", [("95", 770), ("95", 450)]))
