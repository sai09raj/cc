import json
k = json.load(open("../v6/key.json")); Ls = k["Ls"]
H = "at the 09:00 handover"
def f(name, val, tol="within 0.1 %"): return f"Reports the {name} {H} as {val:#.4g} L/s, {tol}."
C = []
C += [(1, "States the elevation of ring tee Tb as EL 8.5 m (8,500 mm)."),
      (1, "States the elevation of the CW-204 riser inlet into TK-1 as EL 26.0 m (26,000 mm)."),
      (1, "States that outfall CW-211 has 4 elbows."),
      (2, f"Identifies exactly P-201A and P-201B as the pumps running {H}."),
      (5, f"Reports the P-201A flow {H} as {Ls['P-201A']:#.4g} L/s, within 0.1 %."),
      (5, f"Reports the P-201B flow {H} as {Ls['P-201B']:#.4g} L/s, within 0.1 %."),
      (5, f"Reports the PI-100 reading {H} as {k['PI100_barg']:.3f} bar g, within 0.002 bar.")]
for e in ["E-201", "E-202", "E-203", "E-204", "E-205"]:
    C.append((5, f"Reports the flow through {e} {H} as {Ls[e]:#.4g} L/s, within 0.1 %."))
C.append((1, f"Reports the flow through E-206 {H} as zero."))
C += [(5, f"Reports the flow in riser CW-204 {H} as {Ls['riser CW-204']:#.4g} L/s, within 0.1 %."),
      (5, f"Reports the flow in CW-208 {H} as {Ls['CW-208']:#.4g} L/s, within 0.1 %."),
      (5, f"Reports the flow in outfall CW-211 {H} as {Ls['outfall CW-211']:#.4g} L/s, within 0.1 %."),
      (5, f"Reports the TK-1 water level {H} as EL {k['TK1_level_m']:.3f} m, within 0.002 m."),
      (2, f"States that TK-1 is not overflowing its weir {H}.")]
names = {"R1-Ta": ("R1", "Ta"), "Ta-Tb": ("Ta", "Tb"), "Tb-Tc": ("Tb", "Tc"), "Tc-Td": ("Tc", "Td"), "Td-Te": ("Td", "Te"), "Te-R1": ("Te", "R1")}
for s, (a, b) in names.items():
    q = Ls[f"ring {s}"]; fr, to = (a, b) if q > 0 else (b, a)
    tol = "within 0.02 L/s" if abs(q) < 5 else "within 0.1 %"
    C.append((4, f"Reports the flow in ring segment {s} {H} as {abs(q):#.4g} L/s flowing from {fr} to {to}, {tol}."))
C += [(2, f"States that FIC-201 is not holding its 26.0 L/s setpoint {H}."),
      (1, f"States that FV-201 is fully open (100 %) {H}."),
      (2, f"Reports the lowest absolute pressure in outfall CW-211 {H} as 2.34 kPa abs, within 0.01 kPa."),
      (1, f"Places the lowest pressure in outfall CW-211 at the top of its 30,000 mm vertical drop (west end of the 9,000 mm run at EL 21.0 m), as a point or as the start of a vapour-filled stretch down that drop."),
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
num = sum(w for w, t in C if w >= 4)
out = ["# CW-200 rubric (v2)", "", f"{len(C)} criteria; positive weight {pos}; numeric-result weight {num} ({num/pos:.0%}); longest {L} characters.", "", "| # | Weight | Criterion |", "|---|---|---|"]
out += [f"| {i} | {'+' if w > 0 else ''}{w} | {t} |" for i, (w, t) in enumerate(C, 1)]
open("rubric.md", "w").write("\n".join(out) + "\n"); print(out[2])
json.dump(C, open("rubric.json", "w"))
