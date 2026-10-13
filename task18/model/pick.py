"""Greedy choice of graded quantities: minimise the worst simulated score over the likely drawing misreads."""
import copy, fem, state, sens, frame as F
SIB = {"457x191x67 UB": "457x191x74 UB", "457x191x74 UB": "457x191x67 UB", "533x210x82 UB": "533x210x92 UB",
       "533x210x92 UB": "533x210x82 UB", "406x178x54 UB": "406x178x60 UB", "406x178x60 UB": "406x178x54 UB"}
def likely():
    t = {}
    fb = state.final()["BEAM"]
    for w, name in ((6.0, "load strip 6.0 (B-C only)"), (6.6, "load strip 6.6 (C-D only)"), (12.6, "load strip 12.6 (B to D)")):
        t[name] = state.final(SPACING=w)
    for g in "1234":
        for line in "BD":
            lo, sl, sh, up, base = F.COLSCHED[f"{line}/{g}"]
            t[f"C/{g} read from {line}/{g} row"] = state.final(COL={**F.COL, g: (lo, up)}, SPLICE={**F.SPLICE, g: (sl, sh)}, BASE={**F.BASE, g: base})
    for line, src in (("B", F.BEAM_B), ("D", F.BEAM_D)):
        for lvl in ("L1", "L2", "L3", "R"):
            b = copy.deepcopy(fb)
            for bay in ("1-2", "2-3", "3-4"):
                sec, l_, r_ = b[(lvl, bay)]; b[(lvl, bay)] = (src[(lvl, bay)], l_, r_)
            t[f"{lvl} beams read from line {line}"] = state.final(BEAM=b)
    y = dict(F.LEVEL_Y); y["L2"] = 7.80; t["storeys 3.75/3.60 swapped"] = state.final(LEVEL_Y=y)
    x = dict(F.GRID_X); x["3"] = 13.2; t["bays 7.5/7.2 swapped"] = state.final(GRID_X=x)
    b = copy.deepcopy(fb); b[("L2", "3-4")] = ("457x191x74 UB", "S", "M"); t["L2 3-4 pin at grid 3 end"] = state.final(BEAM=b)
    b = copy.deepcopy(fb); b[("L3", "1-2")] = ("457x191x74 UB", "M", "M"); t["L3 1-2 simple end missed"] = state.final(BEAM=b)
    st = dict(F.STORAGE); st["a"], st["b"] = 3.0, 6.0; t["storage measured from grid 3"] = state.final(STORAGE=st)
    p = dict(F.PLANT); p["a"] = 7.2 - F.PLANT_TEMP_A; t["AHU-2 measured from grid 4"] = state.final(PLANT=p)
    return t
def secondary():
    t = {}; fb = state.final()["BEAM"]
    for k, (sec, a, b) in fb.items():
        bb = copy.deepcopy(fb); bb[k] = (SIB[sec], a, b); t[f"beam {k} misread"] = state.final(BEAM=bb)
    return t
def ok(k, a, b):
    return abs(a - b) <= max(0.001 * abs(b), 0.02 if k.startswith("ux") else 0.05)
if __name__ == "__main__":
    base = sens.quantities(fem.solve(state.final()))
    cand = [k for k, v in base.items() if (abs(v) > 20 or k.startswith("ux")) and not k.startswith(("M2", "M3", "H1", "H2")) and not k.endswith("L2-SP_Mtop")]
    L = {n: sens.quantities(fem.solve(c)) for n, c in likely().items()}
    S2 = {n: sens.quantities(fem.solve(c)) for n, c in secondary().items()}
    fail = {n: {k for k in cand if not ok(k, q.get(k, 0), base[k])} for n, q in {**L, **S2}.items()}
    NUMROWS, W, NONNUM = 30, 4, 24
    chosen = []
    def scores(ch):
        pos = W * len(ch) + NONNUM
        return {n: 100 * (pos - W * len(fail[n] & set(ch))) / pos for n in fail}
    while len(chosen) < NUMROWS:
        best = min((k for k in cand if k not in chosen and all(abs(abs(base[k]) - abs(base[j])) > 1e-6 for j in chosen)),
                   key=lambda k: (max(v for n, v in scores(chosen + [k]).items() if n in L),
                                  sum(v for n, v in scores(chosen + [k]).items() if n in S2)))
        chosen.append(best)
    sc = scores(chosen)
    print("chosen:", chosen)
    import json; json.dump(chosen, open("chosen.json", "w"))
    for k in chosen: print(f"    {k:18s} {base[k]:10.4f}")
    for n in L: print(f"  L {n:32s} {sc[n]:5.1f}")
    for n in S2: print(f"  S {n:32s} {sc[n]:5.1f}")
