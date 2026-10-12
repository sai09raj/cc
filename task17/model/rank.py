import pf, state, net as N, score_sim as S
def allv(over):
    r, s = pf.solve(state.final(**over)); v = {}
    for b in ["A", "B"] + [f"S{i}" for i in range(1, 13)]: v["V" + b] = r["kV"][b]
    for rid, x in r["routes"].items(): v["I" + rid] = x["I_A"]
    for t in ("T1", "T2"):
        for q in ("MVA_lv", "P_lv_MW", "Q_lv_Mvar"): v[t + q] = r["tx"][t][q]
    v.update(MW=r["source_MW"], Mvar=r["source_Mvar"], loss=r["losses_kW"]); return v
base = allv({}); cnt = {k: 0 for k in base}
for name, o in S.CASES.items():
    if not o.get("routes"): continue                 # drawing misreads only
    v = allv(o)
    for k in base:
        if k not in v: continue
        tol = 0.002 if k.startswith("V") else (0.4 if k == "loss" else 0.001 * abs(base[k]))
        cnt[k] += abs(v[k] - base[k]) > tol
n = sum(1 for o in S.CASES.values() if o.get("routes"))
print("drawing-misread cases:", n)
for k, c in sorted(cnt.items(), key=lambda x: -x[1]): print(f"{k:16s} {c}/{n}")
