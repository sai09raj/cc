import json, hyd, state, pick, net as N
st = state.final(); r = hyd.solve(st); q = pick.Q(st)
k = {c: q[c] for c in json.load(open("chosen.json"))}
k.update(index=r["index"], T_ec=st["T_ec"], A3_len=sum(L for _, L in state.REPAIR["A3"]))
k["m_" + "dir"] = {rid: ([x for x in N.ROUTES if x[0] == rid][0][1] + "->" + [x for x in N.ROUTES if x[0] == rid][0][2]) if v > 0 else
                    ([x for x in N.ROUTES if x[0] == rid][0][2] + "->" + [x for x in N.ROUTES if x[0] == rid][0][1]) for rid, v in r["flows"].items() if abs(v) > 1e-6}
json.dump(k, open("key.json", "w"), indent=1); print(json.dumps(k, indent=1)[:1500])
