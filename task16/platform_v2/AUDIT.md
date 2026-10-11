# CW-200 v2 pre-entry audit (2026-10-11)

## Standing checks
- Tool use + output files: prompt says "Using tools"; 3 files required (solver source, results file, memo). PASS
- PDF metadata: no Info/ID/XMP/Producer/Creator/dates; answer values absent from PDF text (make_packet.py asserts). PASS
- Criterion length <= 301: longest 201. PASS
- Atomic: one value / state / file per criterion; signed ring flows are one quantity. PASS
- Self-contained: each criterion names item, time (09:00), value, tolerance. PASS

## Against reviewer feedback
- Expected values derivable: blind solve of the final PDF (no key access) reproduced every value to 6 s.f. (pumps 75.2076 / 71.8556, PI-100 3.2018, E-201 25.8250, level 34.1888, ring 72.1202 ... ). PASS
- Unstated rules: junction energy continuity now explicit (note 6); riser exit against TK-1 level stated; low alarm and auto-start at 3.0 bar g stated; log now records the standing low alarm 23:20-01:40, consistent with the physics (A+C 2.97 bar g, cleared at 01:40 at 3.27 bar g).
- Missing criteria: every prompt item, both parts of items 1/5/7/8, each memo line-up item, all 3 files mapped. PASS
- Tolerances: 0.1 % on flows, 0.002 bar, 0.002 m; prompt asks 4 s.f. / 3 decimals; data sheet fixes every formula, so an exact solve agrees to ~1e-6. Tb-Tc (0.899 L/s) uses an absolute 0.02 L/s.
- Ideal Flow values = key values (same formatter). PASS

## Difficulty design (from v1 real runs 96/78/59/59)
- Riser now submerged: tank level couples the gravity side to pumps, PI-100, ring and every exchanger.
- Ring pipe-rack rise/drop (Tb, Tc at EL 8.5) adds chained elevation reading.
- 09:00 regime: TK-1 not spilling (it was spilling 04:30-06:00).
- Simulated single misreads (rest correct): 18/19 swap 32, detail E 30, detail F 37, ring rise missed 23, riser extra elbow 66, detail A 2000->1500 79.
