import json, math
k = json.load(open("../v7/key.json")); Ls = k["Ls"]; H = "at the 09:00 handover"
def rng(v, rel=0.001, absd=None, nd=2):
    d = absd if absd is not None else abs(v) * rel; f = 10 ** nd
    return f"{math.floor((abs(v) - d) * f) / f:.{nd}f} to {math.ceil((abs(v) + d) * f) / f:.{nd}f}"
def flow(name, key, w=5):
    v = Ls[key]; return (w, f"Reports the {name} {H} as {v:#.4g} L/s (accept {rng(v)} L/s).")
C = [(1, "States the elevation of ring tee Tb as EL 8.5 m (8,500 mm)."),
     (1, "States the elevation of the CW-204 riser inlet into TK-1 as EL 26.0 m (26,000 mm)."),
     (1, "States that outfall CW-211 has 4 elbows."),
     (2, f"Identifies exactly P-201A and P-201B as the pumps running {H}."),
     flow("P-201A flow", "P-201A"), flow("P-201B flow", "P-201B"),
     (5, f"Reports the PI-100 reading {H} as {k['PI100_barg']:.3f} bar g (accept {rng(k['PI100_barg'], absd=0.002, nd=3)} bar g).")]
for e in ["E-201", "E-202", "E-203", "E-204", "E-205"]: C.append(flow(f"flow through {e}", e))
C.append((1, f"Reports the flow through E-206 {H} as zero."))
C += [flow("flow in riser CW-204", "riser CW-204"), flow("flow in CW-208", "CW-208"), flow("flow in outfall CW-211", "outfall CW-211"),
      (5, f"Reports the TK-1 water level {H} as EL {k['TK1_level_m']:.3f} m (accept EL {rng(k['TK1_level_m'], absd=0.002, nd=3)} m)."),
      (2, f"States that TK-1 is not overflowing its weir {H}.")]
names = {"R1-Ta": ("R1", "Ta"), "Ta-Tb": ("Ta", "Tb"), "Tb-Tc": ("Tb", "Tc"), "Tc-Td": ("Tc", "Td"), "Td-Te": ("Td", "Te"), "Te-R1": ("Te", "R1")}
for s, (a, b) in names.items():
    q = Ls[f"ring {s}"]; fr, to = (a, b) if q > 0 else (b, a)
    r = rng(q, absd=0.02, nd=3) if abs(q) < 5 else rng(q)
    C.append((4, f"Reports the flow in ring segment {s} {H} as {abs(q):#.4g} L/s flowing from {fr} to {to} (accept {r} L/s, that direction)."))
C += [(2, f"States that FIC-201 is not holding its 26.0 L/s setpoint {H}."),
      (1, f"States that FV-201 is fully open (100 %) {H}."),
      (2, f"Reports the lowest absolute pressure in outfall CW-211 {H} as 2.34 kPa abs (accept 2.33 to 2.35 kPa abs)."),
      (1, "Places the lowest pressure in outfall CW-211 at the top of its 30,000 mm vertical drop (west end of the 9,000 mm run at EL 21.0 m), as a point or as the start of a vapour-filled stretch down that drop."),
      (1, "The handover memo lists P-201A as running, citing the 22:00 handover log entry."),
      (1, "The handover memo lists P-201B as running, citing the 04:30 log entry."),
      (1, "The handover memo lists P-201C as stopped, citing the 04:30 log entry."),
      (1, "The handover memo lists P-201D as stopped in AUTO-standby, citing the 07:40 log entry."),
      (1, "The handover memo lists FIC-203 in MANUAL holding FV-203 at 35 %, citing the 01:10 log entry or the 06:45 log entry."),
      (1, "The handover memo lists HV-204 as open, citing the 06:00 log entry."),
      (1, "The handover memo lists HV-206 as closed, citing the 05:20 log entry."),
      (1, "The handover memo lists FIC-201 in AUTO with a 26.0 L/s setpoint, citing the 07:10 log entry."),
      (1, "Delivers the source of the program used to solve the system as a file."),
      (1, "Delivers a results file containing the reported values."),
      (1, "Delivers the handover memo as a file."),
      (-5, "Reports a flow, level or pressure that the response's own delivered program does not compute (a value typed in or estimated by hand rather than produced by executed code).")]
pos = sum(w for w, _ in C if w > 0); L = max(len(t) for _, t in C)
out = ["# CW-200 rubric (v3)", "", f"{len(C)} criteria; positive weight {pos}; longest {L} characters.", "", "| # | Weight | Criterion |", "|---|---|---|"]
out += [f"| {i} | {'+' if w > 0 else ''}{w} | {t} |" for i, (w, t) in enumerate(C, 1)]
open("rubric.md", "w").write("\n".join(out) + "\n"); json.dump(C, open("rubric.json", "w")); print(out[2])
