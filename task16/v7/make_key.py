"""Write key.json for the 09:00 state (v2)."""
import json, hyd, timeline as T
from geom import build
v = hyd.solve(T.STATES[-1][1]); assert len(v) == 1; v = v[0]
n, l = build()
L = lambda k: round(v[k] * 1000, 3)
ring = ["R1-Ta", "Ta-Tb", "Tb-Tc", "Tc-Td", "Td-Te", "Te-R1"]
key = dict(regime=dict(weir_overflowing=v["regime"][0], outfall_column_separated=v["regime"][1], FV201_saturated=v["regime"][3]["FV-201"]),
           running=["P-201A", "P-201B"], PI100_barg=round(v["PI100_barg"], 4), TK1_level_m=round(v["zt"], 4), outfall_min_kPa_abs=round(v["crest_kPa"], 3),
           Ls={"P-201A": L("Qp_P-201A"), "P-201B": L("Qp_P-201B"), "E-201": L("Q203"), "E-202": L("Q205"), "E-203": L("Q206"), "E-204": L("Q207"),
               "E-205": L("Q209"), "E-206": L("Q210"), "riser CW-204": L("Q204"), "CW-208": L("QG"), "outfall CW-211": L("Q211"), "weir": round(v.get("Qw", 0) * 1000, 3),
               **{f"ring {r}": L(f"Qr{i}") for i, r in enumerate(ring)}},
           figures={"CW-204 length m": l["CW-204"][0]["L"], "CW-204 elbows": l["CW-204"][0]["elbows"], "CW-211 elbows": l["CW-211"][0]["elbows"],
                    "Tb EL m": n["Tb"][2] / 1000, "Tc EL m": n["Tc"][2] / 1000, "TK1 inlet EL m": n["TK1IN"][2] / 1000})
json.dump(key, open("key.json", "w"), indent=1); print(json.dumps(key, indent=1))
