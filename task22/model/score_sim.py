"""Strict re-grade: each scenario's reported values graded against the PRINTED accept ranges in platform/rubric.json."""
import json, re, itertools, eps, state, pick, net as N
R = json.load(open("../platform/rubric.json"))
def resp(st):
    r = eps.simulate(st); o = {"events": [(f"{t // 60:02d}:{t % 60:02d}", p, e) for t, p, e in r["events"]]}
    lv = [(x["t"], x["level"]) for x in r["rows"]] + [(1440, r["final"])]
    o["lev"] = {f"{t // 60:02d}:00": round(v, 3) for t, v in lv if t % 60 == 0}
    o["minlev"] = round(min(v for _, v in lv), 3); tm = min(lv, key=lambda v: v[1])[0]; o["minlev_t"] = f"{tm // 60:02d}:{tm % 60:02d}"
    o["energy"] = float(f"{r['energy']:.4g}"); o["cost"] = round(r["cost"], 2); o["pmin"] = round(float(r["pmin"][0]), 2)
    o["pnode"] = r["pmin"][1]; o["ptime"] = f"{r['pmin'][2] // 60:02d}:{r['pmin'][2] % 60:02d}"
    o["below"] = sorted({(f"{x['t'] // 60:02d}:{x['t'] % 60:02d}", n) for x in r["rows"] for n, (z, d) in N.NODE.items() if d > 0 and x["H"][n] - z < N.P_MIN})
    o["dec"] = {}
    for sp in N.SETPOINTS:
        r2 = eps.simulate(dict(st, ctrl={"P-1": (sp, N.CTRL["P-1"][1]), "P-2": N.CTRL["P-2"]}))
        o["dec"][f"{sp:.2f}"] = (round(r2["cost"], 2), round(r2["minlevel"], 3))
    ok = [s for s, (c, m) in o["dec"].items() if m >= N.RESERVE]; o["rec"] = min(ok, key=lambda s: o["dec"][s][0]) if ok else None
    return o
def inr(v, t):
    m = re.search(r"accept (?:GBP )?([\d.]+) to ([\d.]+)", t); return float(m.group(1)) <= v <= float(m.group(2))
def grade(o):
    got = 0; pos = 0; J8 = [(t, "J8") for t in ("08:30", "08:45", "09:00", "09:15", "09:30", "09:45", "10:00", "10:15", "10:30")]
    for w, t in R:
        if w < 0: continue
        pos += w; ok = False
        if m := re.match(r"States that pump (P-\d) (stops|starts) at (\d\d:\d\d)", t): ok = (m.group(3), m.group(1), m.group(2)[:-1].replace("stop", "stop")) in [(a, b, c) for a, b, c in o["events"]]
        elif t.startswith("States that no pump starts or stops"): ok = [e[0] for e in o["events"]] == ["03:15", "05:30", "07:15", "23:15"]
        elif m := re.match(r"Reports the tank level at (\d\d:00)", t): ok = inr(o["lev"][m.group(1)], t)
        elif t.startswith("Reports the minimum tank level of the day"): ok = inr(o["minlev"], t)
        elif t.startswith("States that the minimum tank level of the day occurs"): ok = o["minlev_t"] == "10:00"
        elif t.startswith("Reports the total pump energy"): ok = inr(o["energy"], t)
        elif t.startswith("Reports the total energy cost"): ok = inr(o["cost"], t)
        elif t.startswith("Reports the lowest junction pressure"): ok = inr(o["pmin"], t)
        elif t.startswith("Identifies J8"): ok = o["pnode"] == "J8"
        elif t.startswith("States that the lowest pressure head"): ok = o["ptime"] == "09:45"
        elif t.startswith("States that J8 is below"): ok = [b for b in o["below"] if b[1] == "J8"] == J8
        elif t.startswith("States that no junction other than J8"): ok = all(b[1] == "J8" for b in o["below"])
        elif m := re.match(r"Reports the daily energy cost with a P-1 start level of ([\d.]+)", t): ok = inr(o["dec"][m.group(1)][0], t)
        elif m := re.match(r"Reports the minimum tank level with a P-1 start level of ([\d.]+)", t): ok = inr(o["dec"][m.group(1)][1], t)
        elif "2.40 m lets the tank" in t: ok = o["dec"]["2.40"][1] < N.RESERVE
        elif "2.60 m lets the tank" in t: ok = o["dec"]["2.60"][1] < N.RESERVE
        elif t.startswith("Recommends"): ok = o["rec"] == "2.80"
        elif t.startswith("Delivers"): ok = True
        else: raise ValueError(t)
        got += w * ok
    return 100 * got / pos
if __name__ == "__main__":
    sw = pick.swaps(); CORN = {"J3 A2/C1": "J3: A2[-1] DI200 360 <-> C1", "J5 B2/B3": "J5: B2[0]", "J6 B2/C3": "J6: B2[-1]", "J7 C1/C3": "J7: C1[-1]"}
    keyof = {c: next(n for n in sw if n.startswith(p)) for c, p in CORN.items()}
    def multi(names):
        s = pick.secs()
        for n in names:
            m = re.match(r"(J\d+): (\w+)\[(-?\d)\] \S+ \d+ <-> (\w+)\[(-?\d)\]", keyof[n] if n in keyof else n)
            a, i, b, j = m.group(2), int(m.group(3)), m.group(4), int(m.group(5)); s[a][i], s[b][j] = s[b][j], s[a][i]
        return state.base(pipes=s)
    sc = {"CORRECT": state.base()}
    for c in CORN: sc["corner " + c] = multi([c])
    sc["crowded J3 A2/A3"] = multi(["J3: A2[-1] DI200 360 <-> A3[0] DI200 400"]); sc["crowded J3 A3/C1"] = multi(["J3: A3[0] DI200 400 <-> C1[0] DI200 460"])
    for a, b in itertools.combinations(CORN, 2): sc[f"corners {a} + {b}"] = multi([a, b])
    sc["all four corners"] = multi(list(CORN))
    for h in (0, 3, 7, 8, 12, 18, 22):
        for d in (-0.05, 0.05):
            pat = list(N.PATTERN); pat[h] = round(pat[h] + d, 2); sc[f"chart {h:02d}:00 {d:+.2f}"] = state.base(pattern=pat)
    res = {n: grade(resp(st)) for n, st in sc.items()}
    eps.EXP = 1 / 0.54; res["FAIRNESS: correct reading, textbook 0.54 exponent"] = grade(resp(state.base())); eps.EXP = 1.852
    for n, v in res.items(): print(f"{v:6.1f}  {n}")
    json.dump(res, open("score_sim.json", "w"), indent=1)
