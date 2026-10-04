import tenure_engine as E
base = E.sweep()
feas = {c: r for c, r in base.items() if not r["oom"]}
s1 = min(feas, key=lambda c: (feas[c]["pause_total"], feas[c]["pause_max"], c))
print("cost-optimal", s1, feas[s1]["pause_total"], feas[s1]["pause_max"])
for budget in [200000, 220000, 240000, 260000]:
    ok = [c for c in feas if feas[c]["pause_total"] <= budget]
    s2 = min(ok, key=lambda c: (feas[c]["pause_max"], feas[c]["pause_total"], c))
    print(" budget", budget, "n", len(ok), "->", s2, feas[s2]["pause_max"], feas[s2]["pause_total"])
for ceil in [2100, 2200, 2300, 2400, 2500]:
    ok = [c for c in feas if feas[c]["pause_max"] <= ceil]
    if not ok: continue
    s3 = min(ok, key=lambda c: (c[0] + 2 * c[1], feas[c]["pause_total"], c))
    print(" ceiling", ceil, "n", len(ok), "->", s3, feas[s3]["pause_max"], feas[s3]["pause_total"])
print("global min pmax", min(feas, key=lambda c:(feas[c]["pause_max"],c)), min(r["pause_max"] for r in feas.values()))
