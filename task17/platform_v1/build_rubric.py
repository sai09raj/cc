import json, math
k = json.load(open("../model/key.json")); H = "at the 09:00 handover"; R = k["routes"]
def rng(v, d, nd):
    f = 10 ** nd; return f"{math.floor((abs(v) - d) * f) / f:.{nd}f} to {math.ceil((abs(v) + d) * f) / f:.{nd}f}"
def rel(v, nd=2): return rng(v, abs(v) * 0.001, nd)
def cur(rid, w=4, direction=True):
    v = R[rid]; a, b = v["dir"].split("->")
    if not direction: return (w, f"Reports the current in route {rid} {H} as {v['I_A']:#.4g} A (accept {rel(v['I_A'])} A).")
    return (w, f"Reports the current in route {rid} {H} as {v['I_A']:#.4g} A (accept {rel(v['I_A'])} A) with active power flowing from {a} to {b}.")
def kv(b, w=4): return (w, f"Reports the voltage of {('11 kV section ' + b) if b in ('A', 'B') else 'substation ' + b} {H} as {k['kV'][b]:.3f} kV (accept {rng(k['kV'][b], 0.002, 3)} kV).")
C = [(1, "States the length of route F1-3 as in service at 09:00 as 1,050 m."),
     (1, f"States the F1-3 series impedance as {k['F1_3']['R']:.5f} + j{k['F1_3']['X']:.5f} ohm per phase (accept each part within 0.0005 ohm)."),
     (1, "States that T1 is on tap 9 at the 09:00 handover."),
     (3, f"States that T2 is on tap {k['taps']['T2']} at the 09:00 handover."),
     (5, f"Reports the T1 loading at its 11 kV terminals {H} as {k['T1']['MVA']:#.4g} MVA (accept {rel(k['T1']['MVA'], 3)} MVA)."),
     (4, f"Reports T1 reactive power at its 11 kV terminals {H} as {k['T1']['Mvar']:#.4g} Mvar (accept {'-' + rel(k['T1']['Mvar'], 3).split(' to ')[1] + ' to -' + rel(k['T1']['Mvar'], 3).split(' to ')[0]} Mvar, or that magnitude stated as flowing from the 11 kV busbar into T1)."),
     (5, f"Reports the T2 loading at its 11 kV terminals {H} as {k['T2']['MVA']:#.4g} MVA (accept {rel(k['T2']['MVA'], 3)} MVA)."),
     kv("A", 5), kv("B", 5), kv("S2"), kv("S4"), kv("S7"), kv("S10"), kv("S12"),
     cur("F1-1", direction=False), cur("F2-1", direction=False), cur("F3-1", direction=False), cur("F4-1", direction=False), cur("F1-3"), cur("IC-1"), cur("IC-2"), cur("NOP-1"), cur("NOP-2"),
     (4, f"Reports the active power drawn from the 33 kV infeed {H} as {k['infeed_MW']:#.4g} MW (accept {rel(k['infeed_MW'], 3)} MW)."),
     (4, f"Reports the reactive power drawn from the 33 kV infeed {H} as {k['infeed_Mvar']:#.4g} Mvar (accept {rel(k['infeed_Mvar'], 3)} Mvar)."),
     (5, f"Reports the network losses {H} as {k['losses_kW']:#.4g} kW (accept {rng(k['losses_kW'], 0.4, 1)} kW)."),
     (2, f"Reports the C1 output {H} as {k['C1_kvar']:.0f} kvar (accept {rng(k['C1_kvar'], 1.0, 1)} kvar)."),
     (1, f"Reports the PV-1 export {H} as 2500 kW."),
     (1, f"Reports the PV-1 reactive absorption {H} as {k['PV_kvar_absorbed']:#.4g} kvar (accept {rng(k['PV_kvar_absorbed'], 0.5, 1)} kvar)."),
     (2, f"Identifies the 590 m type 185 section of route F4-1 (the section after joint J4) as the cable section loaded highest relative to its rating {H}."),
     (2, f"Reports that section's loading {H} as {k['max_section']['loading_pct']:#.4g} % of rating (accept {rng(k['max_section']['loading_pct'], 0.1, 2)} %)."),
     (1, "The handover memo lists T1 on tap 9 with AVC in MANUAL, citing the 03:40 log entry."),
     (1, "The handover memo lists T2 in service with AVC in AUTO, citing the 06:30 log entry."),
     (1, "The handover memo lists the bus-section breaker BS as open, citing the 06:30 log entry."),
     (1, "The handover memo lists route F1-3 in service with its 410 m 185 replacement section, citing the 07:20 log entry."),
     (1, "The handover memo lists IC-1 as closed, citing the 22:00 handover log entry."),
     (1, "The handover memo lists IC-2 as closed, citing the 22:00 handover log entry."),
     (1, "The handover memo lists NOP-1 as closed, citing the 01:20 log entry or the 07:20 log entry."),
     (1, "The handover memo lists NOP-2 as closed, citing the 07:50 log entry."),
     (1, "The handover memo lists route F2-3 as still closed, citing the 07:50 log entry."),
     (1, "The handover memo lists C1 as switched in, citing the 05:10 log entry."),
     (1, "The handover memo lists PV-1 export limited to 2500 kW, citing the 08:15 log entry."),
     (1, "Delivers the source of the program used to solve the network as a file."),
     (1, "Delivers a results file containing the reported values."),
     (1, "Delivers the handover memo as a file."),
     (-5, "Reports a voltage, current or power that the response's own delivered program does not compute (a value typed in or estimated by hand rather than produced by executed code).")]
pos = sum(w for w, _ in C if w > 0); L = max(len(t) for _, t in C); num = sum(w for w, _ in C if w >= 4)
out = ["# KINGSMEAD-11 rubric (v1, audited)", "", f"{len(C)} criteria; positive weight {pos}; numeric weight {num} ({num/pos:.0%}); longest {L} characters.", "", "| # | Weight | Criterion |", "|---|---|---|"]
out += [f"| {i} | {'+' if w > 0 else ''}{w} | {t} |" for i, (w, t) in enumerate(C, 1)]
open("rubric.md", "w").write("\n".join(out) + "\n"); json.dump(C, open("rubric.json", "w")); print(out[2])
for w, t in C:
    if len(t) > 301: print("TOO LONG", len(t), t)
