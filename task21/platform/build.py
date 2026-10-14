"""Generate rubric.md/json, prompt.md and the three Ideal Flow boxes for TR-21 from model/key.json."""
import json, math
k = json.load(open("../model/key.json")); CH = json.load(open("../model/chosen.json")); T = "at the 07:30 peak"; PDF = "tr21_v1.pdf"
def rng(lo, hi, nd): f = 10 ** nd; return f"{math.floor(lo * f) / f:.{nd}f} to {math.ceil(hi * f) / f:.{nd}f}"
def s4(v): return f"{v:#.4g}".rstrip(".")
FLOWS = sorted([c for c in CH if c.startswith("q_")], key=lambda c: c[2:]); VOLT = sorted([c for c in CH if c.startswith("v_")]); TSSI = sorted([c for c in CH if c.startswith("i_")])
TR = {"T104": "N1", "T117": "N3", "T122": "N4", "T109": "N5", "T131": "N7", "T126": "N8", "T113": "N9", "T140": "B"}
assert k["low"] == ["T126"] and k["blocked"] == []
C = [(1, f"States that substation TSS-B is out of service {T}."),
     (1, f"States that the TSS-D no-load voltage in force {T} is 850 V (tap +1)."),
     (1, f"States that the TSS-C no-load voltage in force {T} is 835 V (tap 0)."),
     (1, f"States that route X1 (N9 to N1) is in service {T}.")]
KEYS = []
for c in TSSI:
    v = k[c]; d = max(0.001 * v, 0.5)
    C.append((4, f"Reports the output current of substation {c[2:]} {T} as {s4(v)} A (accept {rng(v - d, v + d, 1)} A).")); KEYS.append((c, 4))
for c in FLOWS:
    rid = c[2:]; v = abs(k[c]); d = max(0.001 * v, 0.5); a, b = k["dir"][rid].split("->")
    C.append((4, f"Reports the current in route {rid} {T} as {s4(v)} A (accept {rng(v - d, v + d, 1)} A) flowing from {a} to {b}.")); KEYS.append((c, 4))
for c in VOLT:
    v = k[c]; C.append((4, f"Reports the pantograph voltage of tram {c[2:]} at {TR[c[2:]]} {T} as {s4(v)} V (accept {rng(v - 0.1, v + 0.1, 2)} V).")); KEYS.append((c, 4))
v = k["loss"]; C.append((4, f"Reports the total conductor loss {T} as {s4(v)} kW (accept {rng(v * 0.999, v * 1.001, 1)} kW).")); KEYS.append(("loss", 4))
C += [(3, f"Identifies tram T126 at N8 as the only tram below the 600 V minimum pantograph voltage {T}."),
      (1, f"States that no in-service substation rectifier is blocked {T}."),
      (1, "In the handover memo, the entry for substation TSS-B cites the 05:40 log entry or the 07:10 log entry as the entry that sets its state at 07:30."),
      (1, "In the handover memo, the entry for the TSS-D tap cites the 06:15 log entry as the entry that sets it at 07:30."),
      (1, "In the handover memo, the entry for the TSS-C tap cites the 06:55 log entry as the entry that sets it at 07:30."),
      (1, "In the handover memo, the entry for route X1 cites the 05:20 log entry as the entry that sets its state at 07:30."),
      (1, "Delivers the source code of the load-flow solver as a file."),
      (1, "Delivers a results file that lists the reported substation currents, route currents, tram voltages and conductor loss."),
      (1, "Delivers the handover memo as a file."),
      (-5, "Reports in its results a current, voltage or loss value that its own delivered solver does not output when run (a value typed in or estimated by hand).")]
pos = sum(w for w, _ in C if w > 0); L = max(len(t) for _, t in C)
out = ["# TR-21 rubric (v1)", "", f"{len(C)} criteria; positive weight {pos}; longest {L} characters.", "", "| # | Weight | Criterion |", "|---|---|---|"]
out += [f"| {i} | {'+' if w > 0 else ''}{w} | {t} |" for i, (w, t) in enumerate(C, 1)]
open("rubric.md", "w").write("\n".join(out) + "\n"); json.dump(C, open("rubric.json", "w")); json.dump(dict(KEYS), open("rubric_keys.json", "w"))
print(out[2]); assert L <= 301
fl = ", ".join(c[2:] for c in FLOWS); tl = ", ".join(c[2:] for c in VOLT); sl = ", ".join(c[2:] for c in TSSI)
prompt = f"""You are the traction control engineer on the Hartsdown Tramway at the 07:30 morning peak. The attached {PDF} (data sheet, control log, and a drawn route plan; the network topology and every section's conductor type and length are given only on the drawing) is the complete specification. Determine the supply state the log leaves at 07:30 and compute the steady state DC load flow for the 07:30 snapshot by writing and running your own network solver, following the data sheet's model and conventions. Report every value to 4 significant figures.

1. State which substations are in service at 07:30, the no load voltages of TSS-C and TSS-D in force, and whether route X1 is in service.

2. Report the output current of substations {sl}, and the current and its direction (from which node to which node) in routes {fl}.

3. Report the pantograph voltage of trams {tl}, and the total conductor loss.

4. Identify every tram below the minimum pantograph voltage, and state whether any in-service substation rectifier is blocked.

5. Write a handover memo listing the state of TSS-B, the TSS-C and TSS-D taps and route X1 that your solution uses, each with the log entry that sets it.

Deliver as files: the solver source, a results file with every value above, and the memo. Base every number on your own executed program.
"""
open("prompt.md", "w").write(prompt); print("prompt words", len(prompt.replace("-", " ").split()))
fv = "; ".join(f"{c[2:]} {s4(abs(k[c]))} {k['dir'][c[2:]].replace('->', ' to ')}" for c in FLOWS)
vv = "; ".join(f"{c[2:]} {s4(k[c])}" for c in VOLT); iv = "; ".join(f"{c[2:]} {s4(k[c])}" for c in TSSI)
analyze = ("Read the route plan route by route, taking each section's conductor type and length from the label whose leader touches that section, and keep the sections of neighbouring routes apart where they meet at a node "
           "(at N4 M1 ends K3 360 m and M2 starts K3 470 m; at N9 X1 starts K4 520 m and N9R ends K4 410 m; at N6 S3 ends K3 470 m and S4 starts K3 580 m; at N7 S6 ends K2 440 m and S5 starts K2 330 m; at N3 L4 starts K1 450 m and S6 starts K2 450 m). "
           "Replay the log for 07:30: TSS-B tripped at 05:40 and is still out (07:10); TSS-D raised to tap +1 at 06:15, so its no-load voltage is 850 V; the TSS-C tap raise was refused at 06:55, so TSS-C stays at 835 V; X1 was isolated at 02:00 and re-energised at 05:20, so it is in service; "
           "T150 is stabled with its pantograph down and draws nothing. Place the eight trams at their stops as constant-power loads.")
execute = ("Write a DC load-flow solver: section loop resistances r x L, nodal equations with substations as E - R_i I sources and trams as I = P/V loads, solved by Newton iteration; check every rectifier for reverse current and block any that would take current back. "
           "Check current balance at every node and that total substation output equals tram power plus conductor loss plus internal loss. "
           f"Results {T}: substation currents (A) {iv}. Route currents (A) {fv}. Pantograph voltages (V) {vv}. Total conductor loss {s4(k['loss'])} kW. "
           "No rectifier is blocked. T126 at N8 is the only tram below 600 V. Deliver solver, results file and memo.")
synth = ("Write the handover memo from the solved state: TSS-B out of service (tripped 05:40, still out at 07:10); TSS-D at tap +1, 850 V (06:15); TSS-C at tap 0, 835 V, because the raise was refused (06:55); "
         "X1 back in service after its repair (05:20). Flag that T126 at N8 is below the 600 V minimum at the peak. Base every value on the executed solver.")
for n, t in (("analyze", analyze), ("execute-generate", execute), ("synthesize", synth)):
    open(f"ideal-flow-{n}.txt", "w").write(t); print(n, len(t))
