import json, vent, state, pick, net as N
st = state.final(); r = vent.solve(st); q = pick.Q(st)
k = {c: q[c] for c in json.load(open("chosen.json"))}
k["dir"] = {rid: (lambda R: f"{R[1]}->{R[2]}" if v > 0 else f"{R[2]}->{R[1]}")(next(x for x in N.ROUTES if x[0] == rid)) for rid, v in r["flows"].items()}
k["face"] = r["face"]; k["Q"] = r["Q"]; k["pfan"] = r["p_fan"]; k["power"] = r["power"]
k["all_flows"] = r["flows"]; k["all_p"] = r["p"]; k["reg_dp"] = r["reg_dp"]
json.dump(k, open("key.json", "w"), indent=1)
print({kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in k.items() if kk not in ("all_flows", "all_p")})
