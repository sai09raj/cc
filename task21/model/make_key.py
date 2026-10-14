import json, dc, state, pick, net as N
st = state.final(); r = dc.solve(st); q = pick.Q(st)
k = {c: float(q[c]) for c in json.load(open("chosen.json"))}
k["dir"] = {rid: (lambda R: f"{R[1]}->{R[2]}" if v > 0 else f"{R[2]}->{R[1]}")(next(x for x in N.ROUTES if x[0] == rid)) for rid, v in r["flows"].items()}
k["Vt"] = {t: float(v) for t, v in r["Vt"].items()}; k["I_tss"] = {t: float(v) for t, v in r["I_tss"].items()}
k["all_flows"] = {t: float(v) for t, v in r["flows"].items()}; k["V"] = {t: float(v) for t, v in r["V"].items()}; k["loss_all"] = float(r["loss"]); k["blocked"] = r["blocked"]
k["low"] = sorted([t for t, v in r["Vt"].items() if v < N.V_MIN])
json.dump(k, open("key.json", "w"), indent=1); print("low:", k["low"], "blocked:", k["blocked"])
