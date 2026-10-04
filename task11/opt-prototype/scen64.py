import json, copy, instance, solve_ci, check
T = [["C1", 4, 100], ["C2", 8, 160], ["C3", 14, 245]]
base = instance.make_grid(41, 8, 8); base["dmax"] = 1300; base["types"] = T
n = len(base["turbines"])
scen = {
  "S1": dict(desc="primary platform, all cables, 6 bays", types=T, mf=6, sub=None),
  "S2": dict(desc="primary platform, all cables, 5 bays", types=T, mf=5, sub=None),
  "S3": dict(desc="primary platform, C1 unavailable, 6 bays", types=T[1:], mf=6, sub=None),
  "S4": dict(desc="alternative platform, all cables, 6 bays", types=T, mf=6, sub=[-700, 2700]),
}
out = {}
for name, s in scen.items():
    assert s["mf"] * max(c for _, c, _ in s["types"]) >= n
    inst = copy.deepcopy(base); inst["types"] = s["types"]
    if s["sub"]: inst["substation"] = s["sub"]
    r = solve_ci.solve(inst, s["mf"], time_limit=3600, workers=4)
    c = check.check(inst, s["mf"], {i: j for i, j, q in r["arcs"]}) if r["arcs"] else None
    print(name, s["desc"], r["status"], r["obj"], r["bound"], r["time"], "checker", c, flush=True)
    out[name] = dict(scenario=s, inst=inst, result=r)
    json.dump(out, open("scen64.json", "w"))
