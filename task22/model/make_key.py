import json, eps, state, pick, net as N
st = state.base(); r = eps.simulate(st); q = pick.Q(st)
k = {c: float(q[c]) for c in json.load(open("chosen.json"))}
k["events"] = [[f"{t // 60:02d}:{t % 60:02d}", p, e] for t, p, e in r["events"]]
k["pmin_node"], t = r["pmin"][1], r["pmin"][2]; k["pmin_time"] = f"{t // 60:02d}:{t % 60:02d}"
low = sorted({(x["t"], n) for x in r["rows"] for n, (z, d) in N.NODE.items() if d > 0 and x["H"][n] - z < N.P_MIN})
k["below"] = [[f"{t // 60:02d}:{t % 60:02d}", n] for t, n in low]
lv = [(x["t"], x["level"]) for x in r["rows"]] + [(1440, r["final"])]; tm = min(lv, key=lambda v: v[1])[0]; k["minlev_time"] = f"{tm // 60:02d}:{tm % 60:02d}"
k["prv_modes"] = sorted({x["prv"] for x in r["rows"]}); k["minJ6"] = min(x["H"]["J6"] for x in r["rows"])
k["levels"] = {f"{t // 60:02d}:{t % 60:02d}": v for t, v in lv}
k["decision"] = {f"{sp:.2f}": dict(cost=q[f"dc_{sp:.2f}"], minlev=q[f"dm_{sp:.2f}"]) for sp in N.SETPOINTS}
ok = [sp for sp, v in k["decision"].items() if v["minlev"] >= N.RESERVE]; k["recommend"] = min(ok, key=lambda s: k["decision"][s]["cost"])
k["all"] = {kk: float(v) for kk, v in q.items() if not kk.startswith("_")}
json.dump(k, open("key.json", "w"), indent=1)
print({x: k[x] for x in ("events", "pmin_node", "pmin_time", "below", "minlev_time", "prv_modes", "minJ6", "recommend")})
print({s: (round(v["cost"], 3), round(v["minlev"], 4)) for s, v in k["decision"].items()})
