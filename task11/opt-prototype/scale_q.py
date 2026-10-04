import json, copy, instance, solve_ci, check
T = [["C1", 4, 100], ["C2", 8, 160], ["C3", 14, 245]]
for rows, cols, seed, mf, tl in [(8, 8, 41, 6, 1800), (8, 9, 42, 7, 1800)]:
    inst = instance.make_grid(seed, rows, cols); inst["dmax"] = 1300; inst["types"] = T
    n = rows * cols
    assert mf * 14 >= n
    r = solve_ci.solve(inst, mf, time_limit=tl, workers=4)
    c = None
    if r["arcs"]:
        c = check.check(inst, mf, {i: j for i, j, q in r["arcs"]})
    print(dict(n=n, mf=mf, status=r["status"], obj=r["obj"], bound=r["bound"], t=r["time"], checker=c), flush=True)
    json.dump(dict(inst=inst, mf=mf, result=r), open(f"scaleq_{n}.json", "w"))
