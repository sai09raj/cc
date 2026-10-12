"""Generate rubric.md / rubric.json and the three Ideal Flow boxes for HOLLOWAY-18 from model/key.json."""
import json, math
k = json.load(open("../model/key.json")); T = "at Day 12, 07:00"
def rng(lo, hi, nd=2):
    f = 10 ** nd; return f"{math.floor(lo * f) / f:.{nd}f} to {math.ceil(hi * f) / f:.{nd}f}"
def acc(v, floor=0.05, nd=2):
    d = max(0.001 * abs(v), floor); return rng(v - d, v + d, nd)
def s4(v): return f"{v:#.4g}".rstrip(".")
def sg(v): return ("+" if v > 0 else "-") + s4(abs(v))
KEYS = []
def beam(key, lvl, bay, grid, w=4):
    KEYS.append((key, w)); return (w, f"Reports the hogging moment in the {lvl} beam of bay {bay} at its grid {grid} end {T} as {s4(k[key])} kNm (accept {acc(k[key])} kNm).")
def col(key, grid, pos, w=4):
    KEYS.append((key, w)); v = k[key]; face = "grid 4" if v > 0 else "grid 1"
    return (w, f"Reports the grid {grid} column moment {pos} {T} as {sg(v)} kNm, tension on the face towards {face} (accept {acc(v)} kNm in the data sheet sign convention).")
def ux(key, lvl, w):
    KEYS.append((key, w)); return (w, f"Reports the horizontal displacement of the grid 1 joint at {lvl} {T} as {s4(k[key])} mm towards grid 4 (accept {acc(k[key], 0.02)} mm).")
C = [(1, f"States the self weight line load of the L1 beam in bay 2-3 as {k['sw_L1_23']:.4f} kN/m (accept {rng(k['sw_L1_23'] - 0.0005, k['sw_L1_23'] + 0.0005, 4)} kN/m)."),
     (1, f"States the total vertical line load on the L2 beam of bay 2-3 inside storage zone S, including self weight, as {s4(k['w_L2_23_zone'])} kN/m (accept {acc(k['w_L2_23_zone'], 0.01)} kN/m)."),
     ux("ux_L2", "L2", 3), ux("ux_L3", "L3", 3), ux("ux_R", "the roof", 4),
     (2, f"Reports the vertical base reaction at grid 1 {T} as {s4(k['V1'])} kN upwards (accept {acc(k['V1'], nd=1)} kN)."),
     beam("BL1:1-2_MR", "L1", "1-2", 2), beam("BL1:2-3_ML", "L1", "2-3", 2), beam("BL1:2-3_MR", "L1", "2-3", 3), beam("BL1:3-4_MR", "L1", "3-4", 4),
     beam("BL2:2-3_ML", "L2", "2-3", 2), beam("BL2:2-3_MR", "L2", "2-3", 3),
     beam("BL3:1-2_MR", "L3", "1-2", 2), beam("BL3:2-3_ML", "L3", "2-3", 2), beam("BL3:2-3_MR", "L3", "2-3", 3), beam("BL3:3-4_MR", "L3", "3-4", 4),
     beam("BR:2-3_ML", "roof", "2-3", 2),
     (3, f"Reports the maximum sagging moment in the L2 beam of bay 1-2 {T} as {s4(k['BL2:1-2_Msag'])} kNm (accept {acc(k['BL2:1-2_Msag'])} kNm)."),
     col("C1:L3-R_Mtop", 1, "just below the roof"),
     col("C2:L1-L2_Mbot", 2, "just above L1"), col("C2:L1-L2_Mtop", 2, "just below L2"), col("C2:SP-L3_Mtop", 2, "just below L3"),
     col("C3:L1-L2_Mbot", 3, "just above L1"), col("C3:L1-L2_Mtop", 3, "just below L2"), col("C3:L2-SP_Mbot", 3, "just above L2"),
     col("C3:SP-L3_Mbot", 3, "at the splice"), col("C3:SP-L3_Mtop", 3, "just below L3"), col("C3:L3-R_Mtop", 3, "just below the roof"),
     col("C4:L1-L2_Mbot", 4, "just above L1"), col("C4:SP-L3_Mtop", 4, "just below L3"), col("C4:L3-R_Mbot", 4, "just above L3"), col("C4:L3-R_Mtop", 4, "just below the roof"),
     (1, "The handover memo lists brace BR1 as in service, citing the Day 1 07:30 or Day 11 17:30 log entry."),
     (1, "The handover memo lists brace BR2 as disconnected and left out of the analysis, citing the Day 4 08:20 log entry."),
     (1, "The handover memo lists the grid 4 end of the L2 beam in bay 3-4 as a simple connection, citing the Day 5 11:45 log entry."),
     (1, "The handover memo lists the grid 1 end of the L3 beam in bay 1-2 as a simple connection, citing the Day 6 10:30 log entry or sheet 3."),
     (1, "The handover memo lists temporary prop TP-1 as removed and left out of the analysis, citing the Day 10 08:00 log entry."),
     (1, "The handover memo lists storage zone S on L2 bay 2-3 as loaded, citing the Day 8 09:00 log entry."),
     (1, "The handover memo lists AHU-2 at temporary position T, 1800 mm from grid 3, citing the Day 9 13:40 log entry."),
     (1, "Delivers the source of the frame analysis program as a file."),
     (1, "Delivers a results file containing the reported values."),
     (1, "Delivers the handover memo as a file."),
     (-5, "Reports a displacement, reaction or moment that the response's own delivered program does not compute (a value typed in or estimated by hand rather than produced by executed code).")]
pos = sum(w for w, _ in C if w > 0); L = max(len(t) for _, t in C); num = sum(w for w, t in C if w > 1 and t.startswith("Reports"))
out = ["# HOLLOWAY-18 rubric (v1)", "", f"{len(C)} criteria; positive weight {pos}; numeric weight {num} ({num/pos:.0%}); longest {L} characters.", "", "| # | Weight | Criterion |", "|---|---|---|"]
out += [f"| {i} | {'+' if w > 0 else ''}{w} | {t} |" for i, (w, t) in enumerate(C, 1)]
KEYS += [("V1", 2), ("BL2:1-2_Msag", 3)]; json.dump(dict(KEYS), open("rubric_keys.json", "w")); open("rubric.md", "w").write("\n".join(out) + "\n"); json.dump(C, open("rubric.json", "w")); print(out[2])
for w, t in C:
    if len(t) > 301: print("TOO LONG", len(t), t)

# ---- Ideal Flow boxes (generated from the same key) ----
def f(key, nd=None): return s4(k[key]) if nd is None else f"{k[key]:.{nd}f}"
analyze = ("Read sheet 3 member by member. Columns: grids 1 and 4 are 203x203x60 UC from the base to the splice and 203x203x52 UC above it; grids 2 and 3 are 254x254x89 UC "
 "to the splice and 254x254x73 UC above. The splice is 600 mm above L2, so the short length L2 to splice (labelled with a leader) is still the lower section. Storeys 4200, 3750, 3600, 3600; "
 "bays 6000, 7500, 7200. Bases: grids 1 and 4 pinned, grids 2 and 3 fixed. Beam sections as labelled; the L3 bay 1-2 beam is simple at grid 1. "
 "Replay the site log for Day 12, 07:00: BR2 disconnected (Day 4, reinstated only Day 14), so only BR1 braces bay 2-3 from the grid 3 base to grid 2 at L1; "
 "the L2 bay 3-4 beam is simple at grid 4 (Day 5, bolts not fitted until Day 13); TP-1 removed (Day 10); storage zone S loaded (Day 8): +4.0 kN/m2 from 1500 to 4500 mm past grid 2; "
 "AHU-2 (45 kN) at temporary position T, 1800 mm from grid 3 (Day 9), not at F. "
 f"Line loads = area load x 6.0 m plus self weight (L1 bay 2-3 self weight {k['sw_L1_23']:.4f} kN/m; L2 bay 2-3 inside zone S {f('w_L2_23_zone')} kN/m). Wind 36, 34, 32, 17 kN at grid 1, L1 to roof.")
execute = ("Write a plane frame direct stiffness program: 3 DOF per joint, axial and bending stiffness, E = 210 GPa, joints at every floor and at each splice, "
 "moment releases condensed out at simple beam ends and at both ends of BR1, consistent nodal loads for full and partial UDLs and the AHU-2 point load, column self weight along the axis; "
 f"check that the reactions balance the loads (119 kN wind). Results at Day 12, 07:00: grid 1 sway L2 {f('ux_L2')}, L3 {f('ux_L3')}, roof {f('ux_R')} mm; V at grid 1 {f('V1')} kN. "
 f"Hogging beam end moments (kNm): L1 1-2 at grid 2 {f('BL1:1-2_MR')}; L1 2-3 {f('BL1:2-3_ML')} / {f('BL1:2-3_MR')}; L1 3-4 at grid 4 {f('BL1:3-4_MR')}; L2 2-3 {f('BL2:2-3_ML')} / {f('BL2:2-3_MR')}; "
 f"L3 1-2 at grid 2 {f('BL3:1-2_MR')}; L3 2-3 {f('BL3:2-3_ML')} / {f('BL3:2-3_MR')}; L3 3-4 at grid 4 {f('BL3:3-4_MR')}; roof 2-3 at grid 2 {f('BR:2-3_ML')}. L2 1-2 max sagging {f('BL2:1-2_Msag')}. "
 f"Column moments (+ = grid 4 face in tension): G1 below roof {sg(k['C1:L3-R_Mtop'])}; G2 above L1 {sg(k['C2:L1-L2_Mbot'])}, below L2 {sg(k['C2:L1-L2_Mtop'])}, below L3 {sg(k['C2:SP-L3_Mtop'])}; "
 f"G3 above L1 {sg(k['C3:L1-L2_Mbot'])}, below L2 {sg(k['C3:L1-L2_Mtop'])}, above L2 {sg(k['C3:L2-SP_Mbot'])}, splice {sg(k['C3:SP-L3_Mbot'])}, below L3 {sg(k['C3:SP-L3_Mtop'])}, below roof {sg(k['C3:L3-R_Mtop'])}; "
 f"G4 above L1 {sg(k['C4:L1-L2_Mbot'])}, below L3 {sg(k['C4:SP-L3_Mtop'])}, above L3 {sg(k['C4:L3-R_Mbot'])}, below roof {sg(k['C4:L3-R_Mtop'])}. Deliver program, results file and memo.")
synth = ("Write the handover memo from the analysed state, listing every brace, simple connection, temporary prop, the storage zone and AHU-2 with the log entry that sets it: "
 "BR1 in service (Day 1, checked Day 11); BR2 disconnected and left out (Day 4; reinstatement planned Day 14), so storeys L1 to L2 and above rely on frame action; "
 "L2 bay 3-4 beam simple at grid 4 until its bolts are fitted (Day 5, booked Day 13), although sheet 3 shows it rigid; L3 bay 1-2 beam simple at grid 1 as drawn (Day 6); "
 "TP-1 removed (Day 10), so it carries nothing; storage zone S loaded (Day 8); AHU-2 at temporary position T, 1800 mm from grid 3 (Day 9), until it moves to F on Day 15. "
 "Flag for the site team that reinstating BR2, bolting the L2 grid 4 end plate or moving AHU-2 to F each changes the frame state and needs a fresh analysis. Base every value on the executed program.")
for n, t in (("analyze", analyze), ("execute-generate", execute), ("synthesize", synth)):
    open(f"ideal-flow-{n}.txt", "w").write(t); print(n, len(t))
