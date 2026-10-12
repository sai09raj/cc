"""key.json for HOLLOWAY-18 at Day 12 07:00 (state.final())."""
import json, numpy as np, fem, state, sens, frame as F
s = fem.solve(state.final()); q = sens.quantities(s)
chosen = json.load(open("chosen.json"))
by = {e["id"]: e for e in s["els"]}
e = by["BL2:1-2"]; xs = np.linspace(0, e["L"], 60001); Ms = np.array([fem.moment_along(e, x) for x in xs])
key = {k: float(q[k]) for k in chosen}
key["BL2:1-2_Msag_x"] = float(xs[Ms.argmax()])
key["sw_L1_23"] = F.SEC["533x210x92 UB"][2] * 9.81 / 1000
key["w_L2_23_zone"] = (F.AREA["L2"] + F.STORAGE["q"]) * F.SPACING + F.SEC["533x210x82 UB"][2] * 9.81 / 1000
key["BR1"] = float(q["BR1"]); key["ux_L1"] = float(q["ux_L1"])
json.dump(key, open("key.json", "w"), indent=1)
for k, v in key.items(): print(f"{k:18s} {v:12.5f}")
