"""Generate rubric.md/json, prompt.md and the three Ideal Flow boxes for MV-20 from model/key.json."""
import json, math
k = json.load(open("../model/key.json")); CH = json.load(open("../model/chosen.json")); T = "at the 08:00 handover"; PDF = "mv20_v1.pdf"
def rng(lo, hi, nd): f = 10 ** nd; return f"{math.floor(lo * f) / f:.{nd}f} to {math.ceil(hi * f) / f:.{nd}f}"
def s4(v): return f"{v:#.4g}".rstrip(".")
def nd(v): return max(0, 3 - int(math.floor(math.log10(abs(v)))) + 1)
num = lambda c: int(c.split("J")[-1]) if "J" in c else 0
FLOWS = sorted([c for c in CH if c.startswith("q_")], key=lambda c: (c[2], c[3:]))
PRES = sorted([c for c in CH if c.startswith("p_")], key=lambda c: (c != "p_PB", c != "p_UB", num(c)))
REGS = sorted([c for c in CH if c.startswith("dp_")])
C = [(1, f"States that the standby fan (not the main fan) is the fan in service {T}."),
     (1, f"States that the opening of regulator REG-E in force {T} is 3.6 m2."),
     (1, f"States that the opening of regulator REG-T in force {T} is 1.0 m2.")]
KEYS = []
for c in FLOWS:
    rid = c[2:]; v = abs(k[c]); d = max(0.001 * v, 0.02); a, b = k["dir"][rid].split("->")
    C.append((4, f"Reports the airflow in airway {rid} {T} as {s4(v)} m3/s (accept {rng(v - d, v + d, 2)} m3/s) flowing from {a} to {b}.")); KEYS.append((c, 4))
if "Q" in CH:
    v = k["Q"]; d = 0.001 * v; C.append((4, f"Reports the total fan airflow {T} as {s4(v)} m3/s (accept {rng(v - d, v + d, 2)} m3/s).")); KEYS.append(("Q", 4))
for c in PRES:
    v = k[c]; d = 0.001 * abs(v); n = 2 if abs(v) < 100 else 1
    C.append((4, f"Reports the static pressure at node {c[2:]} {T} as {s4(v)} Pa relative to surface atmospheric pressure (accept {rng(v - d, v + d, n)} Pa).")); KEYS.append((c, 4))
for c in REGS:
    v = k[c]; d = 0.001 * v
    C.append((4, f"Reports the pressure drop across regulator {c[3:]} {T} as {s4(v)} Pa (accept {rng(v - d, v + d, 1)} Pa).")); KEYS.append((c, 4))
fail = [x for x, v in k["face"].items() if v < 30.0]; okf = [x for x, v in k["face"].items() if v >= 30.0]
assert fail == ["C"] and okf == ["W", "E"]
C += [(2, f"Identifies the C panel face (airway C2) as below the 30.0 m3/s statutory minimum airflow {T}."),
      (1, f"States that the W panel face (airway W2) meets the 30.0 m3/s statutory minimum airflow {T}."),
      (1, f"States that the E panel face (airway E2) meets the 30.0 m3/s statutory minimum airflow {T}."),
      (1, "In the handover memo, the entry for the fan in service cites the 04:10 log entry or the 06:30 log entry as the entry that sets it."),
      (1, "In the handover memo, the entry for regulator REG-E cites the 07:55 log entry or the 02:00 log entry as the entry that sets its 08:00 opening."),
      (1, "In the handover memo, the entry for regulator REG-T cites the 00:30 log entry as the entry that sets its 08:00 opening."),
      (1, "The handover memo lists door D1 as open, citing the 03:20 log entry or the 07:15 log entry."),
      (1, "The handover memo lists stopping ST-7 as replaced by a temporary brattice, citing the 05:10 log entry or the 06:20 log entry."),
      (1, "Delivers the source code of the network solver as a file."),
      (1, "Delivers a results file that lists the reported airflows, node pressures, regulator pressure drops and fan airflow."),
      (1, "Delivers the handover memo as a file."),
      (-5, "Reports in its results an airflow, pressure or pressure-drop value that its own delivered solver does not output when run (a value typed in or estimated by hand).")]
pos = sum(w for w, _ in C if w > 0); L = max(len(t) for _, t in C)
out = ["# MV-20 rubric (v1)", "", f"{len(C)} criteria; positive weight {pos}; longest {L} characters.", "", "| # | Weight | Criterion |", "|---|---|---|"]
out += [f"| {i} | {'+' if w > 0 else ''}{w} | {t} |" for i, (w, t) in enumerate(C, 1)]
open("rubric.md", "w").write("\n".join(out) + "\n"); json.dump(C, open("rubric.json", "w")); json.dump(dict(KEYS), open("rubric_keys.json", "w"))
print(out[2]); assert L <= 301
fl = ", ".join(c[2:] for c in FLOWS); pl = ", ".join(c[2:] for c in PRES); rl = ", ".join(c[3:] for c in REGS)
prompt = f"""You are the ventilation officer taking over the 400 m level of Bramhall Colliery at the 08:00 handover. The attached {PDF} (data sheet, control room log, ventilation plan) is the complete specification. Determine the ventilation state the log leaves at 08:00 and compute its steady-state airflow distribution by writing and running your own network solver, following the data sheet's formulas and conventions. Report every value to 4 significant figures.

1. State which fan is in service at 08:00 and the openings of regulators REG-E and REG-T in force.

2. Report the airflow and its direction (from which node to which node) in airways {fl}, and the total fan airflow.

3. Report the static pressure relative to surface atmospheric pressure at nodes {pl}, and the pressure drop across regulators {rl}.

4. State, for each working face (W, C and E panels), whether it meets the statutory minimum airflow.

5. Write a handover memo listing the state of the fan in service, door D1, stopping ST-7 and regulators REG-E and REG-T that your solution uses, each with the log entry that sets it.

Deliver as files: the solver source, a results file with every value above, and the memo. Base every number on your own executed program.
"""
open("prompt.md", "w").write(prompt); print("prompt words", len(prompt.replace("-", " ").split()))
fv = "; ".join(f"{c[2:]} {s4(abs(k[c]))} {k['dir'][c[2:]].replace('->', ' to ')}" for c in FLOWS)
pv = "; ".join(f"{c[2:]} {s4(k[c])}" for c in PRES); rv = "; ".join(f"{c[3:]} {s4(k[c])}" for c in REGS)
analyze = ("Read the ventilation plan airway by airway, taking each section's profile and length from the label whose leader touches that section, and keep the sections of neighbouring airways apart where they meet at a junction "
           "(at J2 C1 starts P2 360 m and I3 starts P2 450 m; at J5 C2 ends P5 350 m and R2 starts P5 440 m; at J7 W1 ends P3 380 m and X1 starts P3 470 m; at J9 E1 ends P4 280 m and X2 ends P4 360 m). "
           "Replay the log for 08:00: main fan tripped 04:10 and held on standby at 06:30, so the standby fan curve applies (the +5 deg blade change was never made); REG-E opened to 3.6 m2 at 02:00 and its reset deferred at 07:55; "
           "REG-T closed to 1.0 m2 at 00:30; door D1 propped open at 03:20 and still open at 07:15, so X1 carries air; stopping ST-7 damaged at 05:10 and replaced by brattice at 06:20, so X2 carries air through an added 3.5 N s2/m8. "
           "The level is therefore meshed through X1 and X2.")
execute = ("Write a network solver: Atkinson resistances R = k L per / A^3 per section, regulators rho/(2 (0.65 A)^2) in series, p = R Q|Q|, and Newton (or Hardy Cross) on node pressures closed by the standby fan curve and the shaft resistances. "
           "Check that airflow balances at every junction and that the fan pressure equals the total drop around the circuit. "
           f"Results {T}: airflows (m3/s) {fv}; fan airflow {s4(k['Q'])} m3/s. Static pressures (Pa, relative to surface) {pv}. Regulator drops (Pa) {rv}. "
           f"Face airflows W {s4(k['face']['W'])}, C {s4(k['face']['C'])}, E {s4(k['face']['E'])} m3/s, so the C face is below the 30.0 m3/s minimum. Deliver solver, results file and memo.")
synth = ("Write the handover memo from the solved state: standby fan in service (main fan tripped 04:10, held on standby 06:30); door D1 open (03:20, still open 07:15), so X1 carries air from J7 to J8; "
         "stopping ST-7 replaced by temporary brattice (05:10 damage, 06:20 brattice), so X2 carries air from J8 to J9; REG-E at 3.6 m2 (02:00, reset deferred 07:55); REG-T at 1.0 m2 (00:30). "
         "Flag that the C panel face is below the statutory minimum. Base every value on the executed solver.")
for n, t in (("analyze", analyze), ("execute-generate", execute), ("synthesize", synth)):
    open(f"ideal-flow-{n}.txt", "w").write(t); print(n, len(t))
