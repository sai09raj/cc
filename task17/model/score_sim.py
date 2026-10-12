"""Rubric score under single misreads (everything else assumed right)."""
import copy, pf, state, net as N
def vals(over):
    r, s = pf.solve(state.final(**over))
    v = {f"V{b}": r["kV"][b] for b in ("A", "B", "S2")}
    for rid in [x[0] for x in N.ROUTES]:
        x = r["routes"].get(rid); v[f"I{rid}"] = (x["I_A"], x["P_from_kW"] > 0) if x else (0.0, True)
    v.update(T1MVA=r["tx"]["T1"]["MVA_lv"], T1Q=r["tx"]["T1"]["Q_lv_Mvar"], T2MVA=r["tx"]["T2"]["MVA_lv"], T2Q=r["tx"]["T2"]["Q_lv_Mvar"], tap=s["taps"]["T2"],
             MW=r["source_MW"], Mvar=r["source_Mvar"], loss=r["losses_kW"], C1=1200 * (r["kV"]["S6"] / 11) ** 2 if over.get("cap", True) else 0)
    secs = sorted(((u, rid, k) for rid, x in r["routes"].items() for k, (t, L, u) in enumerate(x["sections"])), reverse=True)
    v["maxsec"] = (secs[0][1], secs[0][2]); v["maxpct"] = 100 * secs[0][0]
    return v
W = dict(VA=2, VB=2, VS2=3, T1MVA=3, T1Q=4, T2MVA=4, T2Q=4, tap=3, MW=1, Mvar=1, loss=5, C1=1, maxsec=2, maxpct=2)
W.update({f"I{r[0]}": 4 for r in N.ROUTES})
POS = 119; base = vals({})
def ok(k, a, b):
    if k.startswith("V"): return abs(a - b) <= 0.002
    if k.startswith("I"): return abs(a[0] - b[0]) <= 0.001 * b[0] and a[1] == b[1]
    if k in ("tap", "maxsec"): return a == b
    if k == "loss": return abs(a - b) <= 0.4
    if k == "C1": return abs(a - b) <= 1.0
    if k == "maxpct": return abs(a - b) <= 0.1
    return abs(a - b) <= 0.001 * abs(b)
def score(over):
    v = vals(over); lost = sum(w for k, w in W.items() if not ok(k, v[k], base[k])); return 100 * (POS - lost) / POS
def mod(rid, secs, base_routes=None):
    rs = base_routes or state.routes(); return [(r[0], r[1], r[2], secs if r[0] == rid else r[3]) for r in rs]
def mods(d):
    rs = state.routes(); return [(r[0], r[1], r[2], d.get(r[0], r[3])) for r in rs]
CASES = {
 "J10 510 section given to F3-3 (as 59-run)": dict(routes=mods({"F3-2": [("185", 690)], "F3-3": [("95", 510), ("95", 480), ("185", 400)]})),
 "S1 corner: 420/520 labels swapped": dict(routes=mods({"F1-1": [("300", 820), ("300", 330), ("185", 520)], "F1-2": [("185", 420), ("95", 340)]})),
 "F1-1 last section given to F1-2": dict(routes=mods({"F1-1": [("300", 820), ("300", 330)], "F1-2": [("185", 420), ("185", 520), ("95", 340)]})),
 "S8 corner: F3-1 420 given to NOP-1": dict(routes=mods({"F3-1": [("300", 900)], "NOP-1": [("95", 700), ("185", 510), ("185", 420)]})),
 "F2-1 300/185 types swapped": dict(routes=mods({"F2-1": [("185", 610), ("300", 370)]})),
 "IC-1 95 580 read as 185": dict(routes=mods({"IC-1": [("185", 900), ("185", 580)]})),
 "repair ignored": dict(routes=[(r[0], r[1], r[2], r[3]) for r in N.ROUTES]),
 "NOP-1 open": dict(closed=state.final()["closed"] - {"NOP-1"}),
 "F2-3 opened": dict(closed=state.final()["closed"] - {"F2-3"}),
 "T1 AUTO": dict(taps={"T1": "auto", "T2": "auto"}),
 "C1 out": dict(cap=False),
 "PV 4000": dict(pv_kw=4000.0),
}
print("base", score({}))
for n, o in CASES.items():
    if o is None: continue
    try: print(f"{n:40s} {score(o):5.1f}")
    except Exception as e: print(n, "ERR", e)
