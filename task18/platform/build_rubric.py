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
    KEYS.append((key, w)); v = k[key]; face = "grid 4 side" if v > 0 else "grid 1 side"
    return (w, f"Reports the grid {grid} column moment {pos} {T} as {sg(v)} kNm, tension on the {face} face (accept {acc(v)} kNm in the data sheet sign convention).")
def ux(key, lvl, w):
    KEYS.append((key, w)); return (w, f"Reports the horizontal displacement of the grid 1 joint at {lvl} {T} as {s4(k[key])} mm towards grid 4 (accept {acc(k[key], 0.02)} mm).")
LVN = {"L1": "L1", "L2": "L2", "L3": "L3", "R": "the roof"}
def posn(key):
    seg, end = key.split("_"); g = seg[1]; a, b = seg.split(":")[1].split("-")
    if end == "Mbot": return g, ("at the splice" if a == "SP" else f"just above {LVN[a]}")
    return g, ("at the splice" if b == "SP" else f"just below {LVN[b]}")
CH = json.load(open("../model/chosen.json"))
ORDER = sorted(CH, key=lambda q: (0 if q.startswith("ux") else 1 if q[0] == "V" else 2 if q.startswith("B") and not q.endswith("sag") else 3 if q.endswith("sag") else 4,
                                   q.split(":")[0] if ":" in q else q, q))
import sys; sys.path.insert(0, "../model"); import frame as FR
LV_ORDER = {"L1": 1, "L2": 2, "L3": 3, "R": 4, "SP": 0}
def colsort(q):
    g = q[1]; seg, end = q.split(":")[1].split("_"); a, b = seg.split("-")
    ysp = FR.LEVEL_Y[FR.SPLICE[g][0]] + FR.SPLICE[g][1]
    y = lambda n: ysp if n == "SP" else FR.LEVEL_Y[n]
    return (g, y(a) + 1e-3 if end == "Mbot" else y(b) - 1e-3)
COLS = sorted([q for q in CH if q.startswith("C")], key=colsort)
BEAMS = sorted([q for q in CH if q.startswith("B") and not q.endswith("sag")], key=lambda q: (LV_ORDER[q[1:3].rstrip(":")], q))
SAGS = [q for q in CH if q.endswith("sag")]
def beamrow(q):
    lvl, rest = q[1:].split(":"); bay, end = rest.split("_"); grid = bay.split("-")[0 if end == "ML" else 1]
    return beam(q, {"R": "roof"}.get(lvl, lvl), bay, grid)
C = [(1, f"States the self weight line load of the L1 beam in bay 2-3 as {k['sw_L1_23']:.4f} kN/m (accept {rng(k['sw_L1_23'] - 0.0005, k['sw_L1_23'] + 0.0005, 4)} kN/m)."),
     (1, f"States the total vertical line load on the L2 beam of bay 2-3 inside storage zone S, including self weight, as {s4(k['w_L2_23_zone'])} kN/m (accept {acc(k['w_L2_23_zone'], 0.01)} kN/m).")]
C += [ux(q, LVN[q[3:]], 4 if q == "ux_R" else 3) for q in ["ux_L1", "ux_L2", "ux_L3", "ux_R"] if q in CH]
if "V1" in CH: C.append((2, f"Reports the vertical base reaction at grid 1 {T} as {s4(k['V1'])} kN upwards (accept {acc(k['V1'], nd=1)} kN)."))
C += [beamrow(q) for q in BEAMS]
for q in SAGS:
    lvl, bay = q[1:].split(":")[0], q.split(":")[1].split("_")[0]
    C.append((3, f"Reports the maximum sagging moment in the {lvl} beam of bay {bay} {T} as {s4(k[q])} kNm (accept {acc(k[q])} kNm).")); KEYS.append((q, 3))
C += [col(q, *posn(q)) for q in COLS]
C += [
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
KEYS += [("V1", 2)] if "V1" in CH else []; json.dump(dict(KEYS), open("rubric_keys.json", "w")); open("rubric.md", "w").write("\n".join(out) + "\n"); json.dump(C, open("rubric.json", "w")); print(out[2])
for w, t in C:
    if len(t) > 301: print("TOO LONG", len(t), t)

# ---- Ideal Flow boxes (generated from the same key) ----
def f(key): return s4(k[key])
def bname(q):
    lvl, rest = q[1:].split(":"); bay, end = rest.split("_"); grid = bay.split("-")[0 if end == "ML" else 1]
    return f"{ {'R': 'roof'}.get(lvl, lvl)} {bay} at grid {grid} {f(q)}"
def cname(q):
    g, p = posn(q); return f"G{g} {p.replace('just ', '').replace('the ', '')} {sg(k[q])}"
analyze = ("Read sheet 3 member by member. Columns: grids 1 and 4 are 203x203x60 UC below their splice and 203x203x52 UC above; grids 2 and 3 are 254x254x89 UC below and 254x254x73 UC above. "
 "Each splice is dimensioned beside its own column: grids 1, 3 and 4 splice 600 mm above L2, but grid 2 splices 600 mm above L1, so grid 2 is 254x254x73 from L1 + 600 upwards. "
 "The short lengths between a floor and the splice above it are labelled with leaders and keep the lower section. Storeys 4200, 3750, 3600, 3600; bays 6000, 7500, 7200. "
 "Bases: grids 1 and 4 pinned, 2 and 3 fixed. The L3 bay 1-2 beam is simple at grid 1. Replay the site log for Day 12, 07:00: BR2 disconnected (Day 4, reinstated only Day 14), so only BR1 "
 "(168.3x6.3 CHS, grid 3 base to grid 2 at L1) braces the frame; the L2 bay 3-4 beam is simple at grid 4 (Day 5, bolts not fitted until Day 13); TP-1 removed (Day 10); "
 "storage zone S loaded (Day 8): +4.0 kN/m2 from 1500 to 4500 mm past grid 2; AHU-2 (45 kN) at temporary position T, 1800 mm from grid 3 (Day 9), not at F. "
 f"Line loads = area load x 6.0 m plus self weight (L1 bay 2-3 self weight {k['sw_L1_23']:.4f} kN/m; L2 bay 2-3 inside zone S {f('w_L2_23_zone')} kN/m). Wind 36, 34, 32, 17 kN at grid 1, L1 to roof.")
sway = ", ".join(f"{LVN[q[3:]].replace('the ', '')} {f(q)}" for q in ["ux_L1", "ux_L2", "ux_L3", "ux_R"] if q in CH)
execute = ("Write a plane frame direct stiffness program: 3 DOF per joint, axial and bending stiffness, E = 210 GPa, joints at every floor and at each splice, "
 "moment releases condensed out at simple beam ends and at both ends of BR1, consistent nodal loads for full and partial UDLs and the AHU-2 point load, column self weight along the axis; "
 f"check that the reactions balance the loads (119 kN wind). Results at Day 12, 07:00: grid 1 sway {sway} mm"
 + (f"; V at grid 1 {f('V1')} kN" if "V1" in CH else "") + ". Hogging beam end moments (kNm): " + "; ".join(bname(q) for q in BEAMS)
 + "".join(f". {q[1:3]} {q.split(':')[1].split('_')[0]} max sagging {f(q)}" for q in SAGS)
 + ". Column moments (+ = grid 4 side face in tension): " + "; ".join(cname(q) for q in COLS) + ". Deliver program, results file and memo.")
synth = ("Write the handover memo from the analysed state, listing every brace, simple connection, temporary prop, the storage zone and AHU-2 with the log entry that sets it: "
 "BR1 in service (Day 1, checked Day 11); BR2 disconnected and left out (Day 4; reinstatement planned Day 14); "
 "L2 bay 3-4 beam simple at grid 4 until its bolts are fitted (Day 5, booked Day 13), although sheet 3 shows it rigid; L3 bay 1-2 beam simple at grid 1 as drawn (Day 6); "
 "TP-1 removed (Day 10), so it carries nothing; storage zone S loaded (Day 8); AHU-2 at temporary position T, 1800 mm from grid 3 (Day 9), until it moves to F on Day 15. "
 "Flag for the site team that reinstating BR2, bolting the L2 grid 4 end plate or moving AHU-2 to F each changes the frame state and needs a fresh analysis. Base every value on the executed program.")
for n, t in (("analyze", analyze), ("execute-generate", execute), ("synthesize", synth)):
    open(f"ideal-flow-{n}.txt", "w").write(t); print(n, len(t))

# ---- prompt (generated so its lists match the rubric) ----
def pb(q):
    lvl, rest = q[1:].split(":"); bay, end = rest.split("_"); grid = bay.split("-")[0 if end == "ML" else 1]
    return f"{ {'R': 'roof'}.get(lvl, lvl)} bay {bay.replace('-', ' to ')} at grid {grid}"
bys = {}
for q in COLS: bys.setdefault(q[1], []).append(posn(q)[1])
cols_txt = ";\n".join(f"grid {g} " + ", ".join(v[:-1]) + (" and " if len(v) > 1 else "") + v[-1] for g, v in sorted(bys.items())) + "."
beams_txt = ";\n".join(pb(q) for q in BEAMS) + "."
sw = [LVN[q[3:]] for q in ["ux_L1", "ux_L2", "ux_L3", "ux_R"] if q in CH]
prompt = f"""You are the temporary works engineer for frame C of the Holloway Road extension. The attached holloway_v1.pdf (data sheet, site log, frame elevation, loading diagram) is the complete specification. Analyse frame C in the state the site log leaves it at Day 12, 07:00, under the loads on the loading diagram, by writing and running your own plane frame stiffness analysis program. Follow the data sheet's analysis model and reporting conventions, and report every value to 4 significant figures.

1. State the self weight line load of the L1 beam in bay 2 to 3, and the total vertical line load on the L2 beam in bay 2 to 3 inside storage zone S, including the beam's self weight (kN/m).

2. Report the horizontal displacement of the grid 1 joints at {", ".join(sw[:-1])} and {sw[-1]}, and the vertical base reaction at grid 1.

3. Report the beam end moments (hogging, at the column centreline) at:
{beams_txt}

4. Report the maximum sagging moment in the L2 beam in bay 1 to 2.

5. Report the column moments (positive when the column face on the grid 4 side, away from grid 1, is in tension) at:
{cols_txt}

6. Write a handover memo listing the state of every brace, every simple connection, every temporary prop, the storage zone and AHU-2 that your analysis uses, each with the site log entry that sets it.

Deliver as files: the analysis program source, a results file with every value above, and the memo. Base every number on your own executed program.
"""
open("prompt.md", "w").write(prompt); print("prompt words", len(prompt.replace("-", " ").split()))
