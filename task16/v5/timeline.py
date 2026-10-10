"""Check every log state against the physics (unique solution, auto-start consistency, tank within range)."""
from hyd import solve, show
base = dict(fv={"FV-201": "auto", "FV-203": "auto"}, sp={"FV-201": 0.018, "FV-203": 0.016}, hv={"HV-204": True, "HV-206": True})
def st(pumps, **kw):
    s = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}; s["pumps"] = pumps
    for k, v in kw.items(): s[k].update(v)
    return s
STATES = [
    ("22:00 A+B, all auto/open", st(["P-201A", "P-201B"])),
    ("23:20 B trips -> A only (before auto-start)", st(["P-201A"])),
    ("23:20 C auto-started -> A+C", st(["P-201A", "P-201C"])),
    ("01:10 FIC-203 MANUAL 35%", st(["P-201A", "P-201C"], fv={"FV-203": 35})),
    ("01:40 HV-204 closed", st(["P-201A", "P-201C"], fv={"FV-203": 35}, hv={"HV-204": False})),
    ("04:30 B started, C stopped -> A+B", st(["P-201A", "P-201B"], fv={"FV-203": 35}, hv={"HV-204": False})),
    ("05:20 HV-206 closed", st(["P-201A", "P-201B"], fv={"FV-203": 35}, hv={"HV-204": False, "HV-206": False})),
    ("06:00 HV-204 reopened", st(["P-201A", "P-201B"], fv={"FV-203": 35}, hv={"HV-206": False})),
    ("07:10 FIC-201 SP 26 L/s (FINAL 09:00)", st(["P-201A", "P-201B"], fv={"FV-203": 35}, sp={"FV-201": 0.026}, hv={"HV-206": False})),
]
if __name__ == "__main__":
    for lab, s in STATES:
        sols = solve(s)
        print(lab, "| solutions:", len(sols))
        for v in sols:
            reg, o = show(v)
            print("   regime", reg, "PI100", o["PI100_barg"], "zt", o["zt"], "tank_ok", v["tank_ok"], "E201", o["Q203"], "E203", o["Q206"],
                  "outfall", o["Q211"], "weir", o.get("Qw", 0), "pumps", {k: o[k] for k in o if k.startswith("Qp")})
