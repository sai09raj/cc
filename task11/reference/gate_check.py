import tenure_engine as E
base = E.sweep()
feas = {c: r for c, r in base.items() if not r["oom"]}
pt = sorted(r["pause_total"] for r in feas.values()); pm = sorted(r["pause_max"] for r in feas.values())
print("feasible", len(feas), "ptot range", pt[0], pt[-1], "pmax range", pm[0], pm[-1])
print("ptot quartiles", pt[len(pt)//4], pt[len(pt)//2], pt[3*len(pt)//4])
print("pmax quartiles", pm[len(pm)//4], pm[len(pm)//2], pm[3*len(pm)//4])
# tenuring non-monotonic groups (feasible only)
g = {}
for (e, s, t, p), r in base.items(): g.setdefault((e, s, p), {})[t] = r
nm = 0
for d in g.values():
    seq = [d[t]["pause_total"] for t in sorted(d) if not d[t]["oom"]]
    df = [b - a for a, b in zip(seq, seq[1:])]
    nm += any(x > 0 for x in df) and any(x < 0 for x in df)
print("tenuring non-monotonic groups", nm, "/", len(g))
for m in ["dfs", "remset_insertion", "tenure_gt", "no_coalesce", "guard_largest"]:
    E.MUTANT.clear(); E.MUTANT[m] = True
    r = E.sweep()
    print(f"{m:18s} rows changed {sum(1 for c in base if base[c] != r[c]):3d}/96  oom {sum(x['oom'] for x in r.values())}")
E.MUTANT.clear()
