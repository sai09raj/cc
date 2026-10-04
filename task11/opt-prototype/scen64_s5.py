import json, copy, solve_ci, check
d = json.load(open("scen64.json"))
inst = copy.deepcopy(d["S4"]["inst"])
s = dict(desc="alternative platform, all cables, 5 bays", types=inst["types"], mf=5, sub=inst["substation"])
r = solve_ci.solve(inst, 5, time_limit=7000, workers=3)
c = check.check(inst, 5, {i: j for i, j, q in r["arcs"]}) if r["arcs"] else None
print("S5", s["desc"], r["status"], r["obj"], r["bound"], r["time"], "checker", c, flush=True)
json.dump(dict(scenario=s, inst=inst, result=r), open("scen64_s5.json", "w"))
