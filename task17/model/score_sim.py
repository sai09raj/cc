"""Rubric score under single misreads (everything else assumed right)."""
import copy, pf, state, net as N
def vals(over):
    r, s = pf.solve(state.final(**over)); rt = {x[0]: x for x in over.get("routes", state.routes())}
    v = {f"V{b}": r["kV"][b] for b in ("A", "B", "S2", "S4", "S7", "S10", "S12")}
    for rid in ("F1-1", "F2-1", "F3-1", "F4-1", "F1-3", "IC-1", "IC-2", "NOP-1", "NOP-2"):
        x = r["routes"].get(rid); v[f"I{rid}"] = (x["I_A"], x["P_from_kW"] > 0) if x else (0.0, True)
    v.update(T1MVA=r["tx"]["T1"]["MVA_lv"], T1Q=r["tx"]["T1"]["Q_lv_Mvar"], T2MVA=r["tx"]["T2"]["MVA_lv"], tap=s["taps"]["T2"],
             MW=r["source_MW"], Mvar=r["source_Mvar"], loss=r["losses_kW"], C1=1200 * (r["kV"]["S6"] / 11) ** 2 if over.get("cap", True) else 0)
    secs = sorted(((u, rid, k) for rid, x in r["routes"].items() for k, (t, L, u) in enumerate(x["sections"])), reverse=True)
    v["maxsec"] = (secs[0][1], secs[0][2]); v["maxpct"] = 100 * secs[0][0]
    return v
W = dict(VA=5, VB=5, VS2=4, VS4=4, VS7=4, VS10=4, VS12=4, T1MVA=5, T1Q=4, T2MVA=5, tap=3, MW=4, Mvar=4, loss=5, C1=2, maxsec=2, maxpct=2)
W.update({f"I{r}": 4 for r in ("F1-1", "F2-1", "F3-1", "F4-1", "F1-3", "IC-1", "IC-2", "NOP-1", "NOP-2")})
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
CASES = {
 "repair ignored (95 380)": dict(routes=state.routes(False)),
 "repair length 380": dict(routes=mod("F1-3", [("185", 640), ("185", 380)])),
 "repair added in series (95 380 kept)": dict(routes=mod("F1-3", [("185", 640), ("95", 380), ("185", 410)])),
 "F2-2 1240 -> 1420": dict(routes=mod("F2-2", [("185", 1420)])),
 "F4-2 95 -> 185": dict(routes=mod("F4-2", [("185", 1060)])),
 "IC-1 1480 -> 1840": dict(routes=mod("IC-1", [("185", 1840)])),
 "F2-3 70 -> 95": dict(routes=mod("F2-3", [("95", 770), ("95", 450)])),
 "NOP-1 open": dict(closed=state.final()["closed"] - {"NOP-1"}),
 "F2-3 opened (transfer assumed done)": dict(closed=state.final()["closed"] - {"F2-3"}),
 "BS closed": dict(bs=True),
 "T1 AUTO": dict(taps={"T1": "auto", "T2": "auto"}),
 "C1 out": dict(cap=False),
 "PV 4000": dict(pv_kw=4000.0),
 "tap direction reversed (sign)": None,
}
print("base", score({}))
for n, o in CASES.items():
    if o is None: continue
    try: print(f"{n:40s} {score(o):5.1f}")
    except Exception as e: print(n, "ERR", e)
