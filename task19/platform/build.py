"""Generate rubric.md/json, prompt.md and the three Ideal Flow boxes for DH-19 from model/key.json."""
import json, math
k = json.load(open("../model/key.json")); CH = json.load(open("../model/chosen.json")); T = "at the 09:00 handover"
def rng(lo, hi, nd): f = 10 ** nd; return f"{math.floor(lo * f) / f:.{nd}f} to {math.ceil(hi * f) / f:.{nd}f}"
def s4(v): return f"{v:#.4g}".rstrip(".")
FLOWS = [c for c in CH if c.startswith("m_")]; TEMPS = [c for c in CH if c.startswith("T_")]
order = lambda c: (c[2], int(c[3:])) if c[2].isalpha() and c[3:].isdigit() else (c, 0)
FLOWS.sort(key=lambda c: (c[2], c[3:])); TEMPS.sort(key=lambda c: int(c[3:]))
C = [(1, f"States that route A3 is in service at 09:00 with a series length of {k['A3_len']} m (450 m of DN125 plus the new 290 m of DN125)."),
     (1, f"States that the EC supply setpoint in force at 09:00 is {k['T_ec']:.1f} C."),
     (2, f"Identifies {k['index']} as the index substation (least available differential pressure) {T}.")]
KEYS = []
for c in FLOWS:
    rid = c[2:]; v = abs(k[c]); d = max(0.001 * v, 0.002); a, b = k["m_dir"][rid].split("->")
    C.append((4, f"Reports the supply mass flow in route {rid} {T} as {s4(v)} kg/s (accept {rng(v - d, v + d, 3)} kg/s) flowing from {a} to {b}.")); KEYS.append((c, 4))
for c in TEMPS:
    v = k[c]; C.append((3, f"Reports the supply temperature at substation {c[2:]} {T} as {v:.2f} C (accept {rng(v - 0.005, v + 0.005, 3)} C).")); KEYS.append((c, 3))
if "dp" in CH:
    v = k["dp"]; C.append((5, f"Reports the EC pump differential pressure {T} as {s4(v)} kPa (accept {rng(v * 0.999, v * 1.001, 2)} kPa).")); KEYS.append(("dp", 5))
if "loss" in CH:
    v = k["loss"]; C.append((4, f"Reports the network (supply-pipe) heat loss {T} as {s4(v)} kW (accept {rng(v * 0.999, v * 1.001, 1)} kW).")); KEYS.append(("loss", 4))
C += [(1, "The handover memo lists crossover X3 as open (valve XV3 open), citing the 23:30 log entry or the 06:40 log entry."),
      (1, "In the handover memo, the entry for route A3 cites the 06:40 log entry (the A3 repair) as the entry that sets its 09:00 state."),
      (1, "The handover memo lists substation H7 as isolated (taking no flow), citing the 02:10 log entry or the 07:30 log entry."),
      (1, "The handover memo lists loop route L2 as open (valves open), citing the 08:15 log entry."),
      (1, "The handover memo lists loop route L1 as open, citing the 22:00 handover log entry."),
      (1, "In the handover memo, the entry for the EC supply setpoint cites the 06:00 log entry as the entry that sets the setpoint in force at 09:00."),
      (1, "Delivers the source code of the network solver as a file."),
      (1, "Delivers a results file that lists the reported flows, temperatures, pump differential pressure and heat loss."),
      (1, "Delivers the handover memo as a file."),
      (-5, "Reports a flow, temperature, pressure or heat value that the response's own delivered program does not compute (a value typed in or estimated by hand rather than produced by executed code).")]
pos = sum(w for w, _ in C if w > 0); L = max(len(t) for _, t in C)
out = ["# DH-19 rubric (v1)", "", f"{len(C)} criteria; positive weight {pos}; longest {L} characters.", "", "| # | Weight | Criterion |", "|---|---|---|"]
out += [f"| {i} | {'+' if w > 0 else ''}{w} | {t} |" for i, (w, t) in enumerate(C, 1)]
open("rubric.md", "w").write("\n".join(out) + "\n"); json.dump(C, open("rubric.json", "w")); json.dump(dict(KEYS), open("rubric_keys.json", "w"))
print(out[2]); assert L <= 301
fl = ", ".join(c[2:] for c in FLOWS); tl = ", ".join(c[2:] for c in TEMPS)
extra = " and ".join(x for x, c in (("the EC pump differential pressure", "dp"), ("the network heat loss", "loss")) if c in CH)
prompt = f"""You are the duty engineer taking over the Ashgrove district heating network at 09:00. The attached dh19_v3.pdf (data sheet, control room log, pipe route plan) is the complete specification. Determine the network state the log leaves at 09:00 and compute its steady-state hydraulic and thermal operation by writing and running your own network solver, following the data sheet's formulas and conventions. Report every value to 4 significant figures.

1. State the series length of route A3 as it is at 09:00 and the EC supply setpoint in force.

2. Report the supply mass flow and its direction (from which node to which node) in routes {fl}.

3. Report the supply temperature at substations {tl}.

4. Identify the index substation and report {extra}.

5. Write a handover memo listing the state of crossover X3, routes A3, L1 and L2, substation H7 and the EC supply setpoint that your solution uses, each with the log entry that sets it.

Deliver as files: the solver source, a results file with every value above, and the memo. Base every number on your own executed program.
"""
open("prompt.md", "w").write(prompt); print("prompt words", len(prompt.replace("-", " ").split()))
fv = "; ".join(f"{c[2:]} {s4(abs(k[c]))} {k['m_dir'][c[2:]].replace('->', ' to ')}" for c in FLOWS)
tv = "; ".join(f"{c[2:]} {k[c]:.2f}" for c in TEMPS)
analyze = ("Read the route plan route by route, taking each section's type and length from the label whose leader touches that section, and keep the sections of neighbouring routes apart where they meet at a node "
           "(at H1 A1 ends DN150 330 m and A2 starts DN150 420 m; at H8 C1 ends DN125 520 m and C2 starts DN125 400 m; at H4 A4 ends DN80 390 m and L1 starts DN80 640 m; at H12 D2 ends DN80 250 m and L2 ends DN80 340 m; at H6 B2 ends DN125 470 m and X3 ends DN100 470 m). "
           "Replay the log for 09:00: A3 repaired at 06:40, the 260 m DN100 section replaced by 290 m of DN125, so A3 is 450 + 290 = 740 m of DN125; XV3 left open, so X3 carries flow; "
           "H7 isolated since 02:10 (its node still joins B3 and L2); L2 isolation deferred at 08:15, so L2 stays open; L1 open; EC setpoint 92.0 C (06:00, after the 04:00 setback). "
           "The whole network is therefore meshed through X3, L1 and L2. Use the stated water properties, Swamee-Jain friction, exponential supply heat loss with flow-weighted mixing, consumer flow Q/(cp (Ts - 45)), and identical return pipes.")
execute = ("Write a network solver: Newton (or Hardy Cross) on node pressures with Darcy-Weisbach/Swamee-Jain section losses, wrapped in an outer iteration on consumer flows, because each substation's flow depends on the supply temperature reaching it, "
           "which depends on the flows. Size the pump from the index substation: dp = 2 x supply-path loss + 60 kPa. Check mass and energy balance (EC output = demand + heat loss). "
           f"Results {T}: flows (kg/s) {fv}. Supply temperatures (C) {tv}. Index substation {k['index']}"
           + (f"; pump dp {s4(k['dp'])} kPa" if "dp" in CH else "") + (f"; network heat loss {s4(k['loss'])} kW" if "loss" in CH else "") + ". Deliver solver, results file and memo.")
synth = ("Write the handover memo from the solved state: X3 open with XV3 left open after the 06:40 repair (23:30 opening), so the B branch still feeds the A branch and X3 flows from H6 to H2; "
         "A3 back in service with the new 290 m DN125 section (06:40); H7 isolated (02:10, parts not delivered 07:30) although its node still passes flow from B3 into L2; "
         "L2 open because the meter isolation was deferred (08:15); L1 open (22:00); EC setpoint 92.0 C (06:00). Base every value on the executed solver.")
for n, t in (("analyze", analyze), ("execute-generate", execute), ("synthesize", synth)):
    open(f"ideal-flow-{n}.txt", "w").write(t); print(n, len(t))
