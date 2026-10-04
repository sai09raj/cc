import json, copy, instance, solve_ci
base = instance.make_grid(31, 6, 8); base["dmax"] = 1300
T = [["C1", 3, 100], ["C2", 5, 145], ["C3", 8, 210]]
n = len(base["turbines"])
scen = {
  "S1": dict(desc="base: all cables, 7 bays", types=T, mf=7, sub=None),
  "S2": dict(desc="6 bays (tight: 6 x 8 = 48)", types=T, mf=6, sub=None),
  "S3": dict(desc="C3 unavailable, 11 bays", types=T[:2], mf=11, sub=None),
  "S4": dict(desc="alternative platform, 7 bays", types=T, mf=7, sub=[-700, 1900]),
}
out = {}
for name, s in scen.items():
    assert s["mf"] * max(c for _, c, _ in s["types"]) >= n, name
    inst = copy.deepcopy(base); inst["types"] = s["types"]
    if s["sub"]: inst["substation"] = s["sub"]
    r = solve_ci.solve(inst, s["mf"], time_limit=900, workers=4)
    print(name, s["desc"], r["status"], r["obj"], r["bound"], r["time"], flush=True)
    out[name] = dict(scenario=s, inst=inst, result=r)
json.dump(out, open("scen48.json", "w"))
