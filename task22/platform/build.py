"""Generate rubric.md/json, prompt.md and the three Ideal Flow boxes for WD-22 from model/key.json."""
import json, math
k = json.load(open("../model/key.json")); A = k["all"]; PDF = "wd22_v1.pdf"
def rng(lo, hi, nd): f = 10 ** nd; return f"{math.floor(lo * f) / f:.{nd}f} to {math.ceil(hi * f) / f:.{nd}f}"
def s4(v): return f"{v:#.4g}".rstrip(".")
def lv(v): return f"{v:.3f}"
assert k["events"] == [["03:15", "P-1", "stop"], ["05:30", "P-1", "start"], ["07:15", "P-2", "start"], ["23:15", "P-2", "stop"]]
assert k["pmin_node"] == "J8" and k["pmin_time"] == "09:45" and k["minlev_time"] == "10:00" and k["recommend"] == "2.80" and k["prv_modes"] == ["active"]
assert [b for b in k["below"]] == [[f"{t}", "J8"] for t in ("08:30", "08:45", "09:00", "09:15", "09:30", "09:45", "10:00", "10:15", "10:30")]
D = k["decision"]; assert D["2.40"]["minlev"] < 1.0 and D["2.60"]["minlev"] < 1.0 and min(D["2.00"]["minlev"], D["2.20"]["minlev"], D["2.80"]["minlev"]) >= 1.0
C = [(2, "States that pump P-1 stops at 03:15."), (2, "States that pump P-1 starts at 05:30."), (2, "States that pump P-2 starts at 07:15."), (2, "States that pump P-2 stops at 23:15."),
     (1, "States that no pump starts or stops at any time other than 03:15, 05:30, 07:15 and 23:15.")]
for h in range(11, 25):
    v = A[f"lev_{h:02d}"]; C.append((4, f"Reports the tank level at {h:02d}:00 as {lv(v)} m (accept {rng(v - 0.005, v + 0.005, 3)} m)."))
v = A["minlev"]; C.append((4, f"Reports the minimum tank level of the day as {lv(v)} m (accept {rng(v - 0.005, v + 0.005, 3)} m)."))
C.append((1, "States that the minimum tank level of the day occurs at 10:00."))
v = A["energy"]; C.append((4, f"Reports the total pump energy for the day as {s4(v)} kWh (accept {rng(v * 0.999, v * 1.001, 1)} kWh)."))
v = A["cost"]; C.append((4, f"Reports the total energy cost for the day as GBP {v:.2f} (accept GBP {rng(v * 0.999, v * 1.001, 2)})."))
v = A["pmin"]; C.append((4, f"Reports the lowest junction pressure head of the day as {v:.2f} m (accept {rng(v - 0.05, v + 0.05, 2)} m)."))
C += [(1, "Identifies J8 as the junction with the lowest pressure head of the day."),
      (1, "States that the lowest pressure head of the day occurs in the step starting at 09:45."),
      (1, "States that J8 is below the 20.0 m minimum pressure head in exactly the steps starting from 08:30 to 10:30."),
      (1, "States that no junction other than J8 falls below the 20.0 m minimum pressure head during the day.")]
for sp in ("2.00", "2.80"):
    v = D[sp]["cost"]; C.append((4, f"Reports the daily energy cost with a P-1 start level of {sp} m as GBP {v:.2f} (accept GBP {rng(v * 0.999, v * 1.001, 2)})."))
    v = D[sp]["minlev"]; C.append((4, f"Reports the minimum tank level with a P-1 start level of {sp} m as {lv(v)} m (accept {rng(v - 0.005, v + 0.005, 3)} m)."))
C += [(1, "States that the present P-1 start level of 2.40 m lets the tank level fall below the 1.00 m reserve."),
      (1, "States that a P-1 start level of 2.60 m lets the tank level fall below the 1.00 m reserve."),
      (3, "Recommends a P-1 start level of 2.80 m."),
      (1, "Delivers the source code of the extended-period simulation as a file."),
      (1, "Delivers a results file that lists the pump events, hourly tank levels, energy, cost, pressure results and candidate results."),
      (1, "Delivers the operations note as a file."),
      (-5, "Reports in its results a level, energy, cost or pressure value that its own delivered simulation does not output when run (a value typed in or estimated by hand).")]
pos = sum(w for w, _ in C if w > 0); L = max(len(t) for _, t in C)
out = ["# WD-22 rubric (v1)", "", f"{len(C)} criteria; positive weight {pos}; longest {L} characters.", "", "| # | Weight | Criterion |", "|---|---|---|"]
out += [f"| {i} | {'+' if w > 0 else ''}{w} | {t} |" for i, (w, t) in enumerate(C, 1)]
open("rubric.md", "w").write("\n".join(out) + "\n"); json.dump(C, open("rubric.json", "w")); print(out[2]); assert L <= 301
prompt = f"""You are the network operations engineer for the Fenwick Hill water supply zone. The attached {PDF} is the complete specification: a data sheet, a drawn pipe plan (the network topology and every pipe section's type and length are given only on this drawing), and a demand pattern bar chart (the hourly demand multipliers are given only on this chart). Write and run your own extended-period simulation of the 24 h day, following the data sheet's hydraulic model, time stepping and control rules exactly.

1. List every pump start and stop event of the day with its time.

2. Report the tank level at every full hour from 01:00 to 24:00, and the minimum tank level of the day with the time it occurs.

3. Report the total pump energy and the total energy cost for the day.

4. Report the lowest junction pressure head of the day with its junction and step start time, and list every junction and step below the minimum pressure head.

5. For each candidate P-1 start level in the operations review, report the daily energy cost and the minimum tank level, state which candidates let the tank fall below the reserve, and recommend a start level using the data sheet's rule.

6. Write an operations note for the operations manager giving your recommendation and the low pressure finding.

Report tank levels in m to 3 decimal places, pressure heads to 0.01 m, energy to 4 significant figures and costs to 0.01 GBP. Deliver as files: the simulation source, a results file with every value above, and the operations note. Base every number on your own executed program.
"""
open("prompt.md", "w").write(prompt); print("prompt words", len(prompt.split()))
levs = "; ".join(f"{h:02d}:00 {lv(A[f'lev_{h:02d}'])}" for h in range(11, 25))
analyze = ("Read the pipe plan pipe by pipe, taking each section's pipe type and length from the label whose leader line touches that section, and keep neighbouring pipes' sections apart where they meet at a junction "
           "(at J3 A2 ends DI200 360 m and C1 starts DI200 460 m; at J5 B3 ends DI200 490 m and B2 starts DI200 380 m; at J6 B2 ends CI200 460 m and C3 starts CI200 350 m; at J7 C1 ends DI200 390 m and C3 ends DI200 520 m). "
           "Read the 24 hourly multipliers from the bar chart against its grid lines. Note the rules that fix the answer: controls are evaluated at the start of each 15 min step with the level at that time, P-1 before P-2, with hysteresis between start and stop levels; "
           "the tank is a fixed head within a step and is updated explicitly afterwards; PRV-1 holds 72.0 m at J10 while the J6 head is at or above 72.0 m; pressure is checked only at junctions with demand.")
execute = ("Write the simulation: per step, solve the looped network (Hazen-Williams with the exact 1.852 exponent, parallel pumps on the stated curve with a non-return valve, PRV-1, tank head), then update the tank level and accumulate energy and cost. "
           "Check continuity at every junction and that PRV-1 stays active all day. Results: P-1 stops 03:15 and starts 05:30; P-2 starts 07:15 and stops 23:15; no other events. "
           f"Tank levels (m): {levs}. Minimum level {lv(A['minlev'])} m at 10:00. Energy {s4(A['energy'])} kWh, cost GBP {A['cost']:.2f}. "
           f"Lowest pressure head {A['pmin']:.2f} m at J8 in the 09:45 step; J8 is below 20.0 m in the steps from 08:30 to 10:30 and no other junction is. "
           f"Candidates: 2.00 m costs GBP {D['2.00']['cost']:.2f} with minimum {lv(D['2.00']['minlev'])} m; 2.80 m costs GBP {D['2.80']['cost']:.2f} with minimum {lv(D['2.80']['minlev'])} m; 2.40 m and 2.60 m fall below the 1.00 m reserve. Recommend 2.80 m.")
synth = ("Write the operations note from the executed simulation: the present 2.40 m P-1 start level lets the tank fall below the 1.00 m reserve in the late morning, and so does 2.60 m; "
         "recommend 2.80 m, the cheapest candidate that keeps the reserve all day. Report that J8 is below the 20.0 m minimum pressure head from 08:30 to 10:30 with the present setting and needs attention. Base every value on the executed program.")
for n, t in (("analyze", analyze), ("execute-generate", execute), ("synthesize", synth)):
    open(f"ideal-flow-{n}.txt", "w").write(t); print(n, len(t))
