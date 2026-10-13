"""Which quantities does each plausible misread move? (relative change > tol counts as 'moved')."""
import copy, numpy as np, fem, frame as F

def quantities(s):
    c, idx, U, R = s["c"], s["idx"], s["U"], s["R"]
    q = {}
    for l in ("L1", "L2", "L3", "R"):
        q[f"ux_{l}"] = U[3 * idx[("1", l)]] * 1000
    for g in "1234":
        i = idx[(g, "G")]
        q[f"H{g}"] = R[3 * i]; q[f"V{g}"] = R[3 * i + 1]
        if c["BASE"][g] == "fixed": q[f"M{g}"] = R[3 * i + 2]
    for e in s["els"]:
        if e["kind"] == "beam":
            if not e["rel"][0]: q[f"{e['id']}_ML"] = e["f"][2]
            if not e["rel"][1]: q[f"{e['id']}_MR"] = -e["f"][5]
            xs = np.linspace(0, e["L"], 2001); Ms = [fem.moment_along(e, x) for x in xs]
            q[f"{e['id']}_Msag"] = max(Ms)
        elif e["kind"] == "col":
            q[f"{e['id']}_Mbot"] = fem.moment_along(e, 0.0); q[f"{e['id']}_Mtop"] = fem.moment_along(e, e["L"])   # + = tension on grid-4 face
        elif e["kind"] == "brace":
            q[e["id"]] = -e["f"][0]
    return q

def mods(base=None):
    import state
    m = {}; fb = state.final()["BEAM"]
    def cfg(**kw): return state.final(**kw)
    def beam(**ch):
        b = copy.deepcopy(fb)
        for k, v in ch.items(): b[tuple(k.split("_"))] = v
        return b
    m["col G2 lower read 73"] = cfg(col_override={("2", 0): "254x254x73 UC", ("2", 1): "254x254x73 UC", ("2", 2, "L2"): "254x254x73 UC"})
    m["col G2 splice labels swapped"] = cfg(COL={**F.COL, "2": ("254x254x73 UC", "254x254x89 UC")})
    m["col G3 splice labels swapped"] = cfg(COL={**F.COL, "3": ("254x254x73 UC", "254x254x89 UC")})
    m["col G1 splice labels swapped"] = cfg(COL={**F.COL, "1": ("203x203x52 UC", "203x203x60 UC")})
    m["splice at L2"] = cfg(SPLICE=1e-6)
    m["beam L2 67/74 swap"] = cfg(BEAM=beam(**{"L2_1-2": ("457x191x74 UB", "M", "M"), "L2_3-4": ("457x191x67 UB", "M", "S")}))
    m["beam L1 2-3 read 82"] = cfg(BEAM=beam(**{"L1_2-3": ("533x210x82 UB", "M", "M")}))
    y = dict(F.LEVEL_Y); y["L2"] = 4.20 + 3.60; m["storeys 3.75/3.60 swap"] = cfg(LEVEL_Y=y)
    x = dict(F.GRID_X); x["3"] = 6.0 + 7.2; m["bays 7.5/7.2 swap"] = cfg(GRID_X=x)
    m["L2 3-4 pin at grid 3 end"] = cfg(BEAM=beam(**{"L2_3-4": ("457x191x74 UB", "S", "M")}))
    st = dict(F.STORAGE); st["a"], st["b"] = 7.5 - 4.5, 7.5 - 1.5; m["storage from grid 3"] = cfg(STORAGE=st)
    p = dict(F.PLANT); p["a"] = 7.2 - F.PLANT_TEMP_A; m["plant temp from grid 4"] = cfg(PLANT=p)
    m["LOG plant at final pos"] = cfg(PLANT=dict(F.PLANT))
    m["LOG BR2 in"] = cfg(BRACE=F.BRACE)
    m["LOG L2 3-4 moment"] = cfg(BEAM=beam(**{"L2_3-4": ("457x191x74 UB", "M", "M")}))
    m["no self-weight"] = cfg(self_weight=False)
    bs = dict(F.BASE); bs["1"] = "fixed"; m["base 1 fixed"] = cfg(BASE=bs)
    return m

if __name__ == "__main__":
    import state
    base = quantities(fem.solve(state.final()))
    tol = 0.002
    print(len(base), "quantities")
    moved = {k: 0 for k in base}
    for name, c in mods(base).items():
        q = quantities(fem.solve(c))
        ch = {k: abs(q.get(k, 0) - v) / max(abs(v), 1e-9) for k, v in base.items()}
        n = sum(1 for k in base if ch[k] > tol)
        for k in base:
            if ch[k] > tol: moved[k] += 1
        print(f"{name:28s} moves {n:2d}/{len(base)}")
    print("\nper quantity: number of misreads that move it >0.2%")
    for k, v in sorted(moved.items(), key=lambda t: -t[1]): print(f"  {k:18s} {v:2d}  base={base[k]:.4f}")
