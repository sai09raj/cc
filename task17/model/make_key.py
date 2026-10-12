"""key.json for the 09:00 state."""
import json, math, pf, state, net as N
r, s = pf.solve(state.final())
rt = {x[0]: x for x in state.routes()}
z13 = pf.route_z(rt["F1-3"])
def flow(rid):
    v = r["routes"][rid]; a, b = rt[rid][1], rt[rid][2]
    return dict(I_A=round(v["I_A"], 3), P_kW=round(abs(v["P_from_kW"]), 2), dir=(f"{a}->{b}" if v["P_from_kW"] > 0 else f"{b}->{a}"))
secs = []
for rid, v in r["routes"].items():
    for k, (t, L, u) in enumerate(v["sections"]): secs.append((u, rid, k, t, L))
secs.sort(reverse=True)
V = r["kV"]
key = dict(taps=s["taps"], kV={b: round(V[b], 4) for b in V if b not in ("SRC",)},
           routes={rid: flow(rid) for rid in r["routes"]},
           T1=dict(MVA=round(r["tx"]["T1"]["MVA_lv"], 4), MW=round(r["tx"]["T1"]["P_lv_MW"], 4), Mvar=round(r["tx"]["T1"]["Q_lv_Mvar"], 4)),
           T2=dict(MVA=round(r["tx"]["T2"]["MVA_lv"], 4), MW=round(r["tx"]["T2"]["P_lv_MW"], 4), Mvar=round(r["tx"]["T2"]["Q_lv_Mvar"], 4)),
           infeed_MW=round(r["source_MW"], 4), infeed_Mvar=round(r["source_Mvar"], 4), losses_kW=round(r["losses_kW"], 2),
           C1_kvar=round(N.CAP["Q_kvar"] * (V["S6"] / 11.0) ** 2, 2), PV_kvar_absorbed=round(2500 * math.tan(math.acos(0.95)), 2),
           F1_3=dict(length_m=sum(l for _, l in rt["F1-3"][3]), R=round(z13.real, 5), X=round(z13.imag, 5)),
           max_section=dict(route=secs[0][1], section=secs[0][2] + 1, type=secs[0][3], length=secs[0][4], loading_pct=round(100 * secs[0][0], 2)),
           top3_sections=[(x[1], x[2] + 1, x[3], round(100 * x[0], 2)) for x in secs[:3]])
json.dump(key, open("key.json", "w"), indent=1); print(json.dumps(key, indent=1))
