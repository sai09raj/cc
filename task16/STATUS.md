# Task 16 — ISO-16 (piping isometric reading; draft stage)

Design aim (Rule Zero, QM tip 2026-10-10): difficulty must come from reading a dense 3D diagram exactly, not
from compute. Iterate as the tip says: draft -> blind probe -> read the trajectory -> close easy paths.

- proto/network.py: authored 3D cooling-water network (pump P1, header CW-101 DN150, branches CW-102..107,
  tees T1-T6, consumers C1-C6, END1), 30 elbows, 6 gate valves, 1 check valve, 1 reducer.
- proto/build.py: 3D geometry and answer key; proto/render.py: isometric (not to scale, compressed lengths,
  crossing breaks with depth from the viewer at east-south-above).
- Probe 1 (opus, 40 min, extraction only): node coordinates, length per DN, elbow count. Key in the scratch
  probe folder: lengths DN150 41,100 / DN100 17,900 / DN80 21,250 / DN50 8,950; 30 elbows.

## Probe 1 result (schematic isometric): solved
Opus read every coordinate (13/13) and every length exactly; its elbow count (29) was right and my key (30)
wrong (the main turns through tee T6). A clean schematic iso with dimension strings is not hard for it.

## v2 draft: 3D perspective views (proto3d/)
scene.py: pipe rack (columns on grid, beam levels TOS +4500/+7000), 8 equipment items with tagged nozzle
elevations, 10 lines (headers CW-201 DN200 at +7000 and CW-210 DN150 at +4500, branches). render3d.py:
shaded perspective, two views (from SE and from NW), floor survey grid every 1500 mm. Every vertex lies on the
1500 grid and every horizontal run at a TOS level or nozzle EL (stated in the conventions page).
Key: lengths DN200 30,000 / DN150 40,000 / DN100 47,200 / DN80 39,500 / DN50 11,100; 19 elbows.
Probe 2 (opus, 40 min) launched on the two views.

## Probe 2 result (3D perspective views): solved
All 10 lines' vertices, all lengths and 19 elbows exact. It fitted the floor grid to calibrate each camera,
triangulated from both views, snapped and reprojected. It also found a clash in my scene (CW-203's drop lands
on CW-210's centreline at (10500, 7500, 4500)). Playbook #84.

## Capability scan (2026-10-10): three small vision probes in parallel (scan/make_probes.py)
A: count 150 valve symbols of 4 types on a cluttered sheet (key gate 41, globe 35, check 41, ball 33).
B: trace 24 same-colour crossing wires from left to right terminals (key in scratch scan_keys.json).
C: noisy rotated scan of a 32 x 9 table of 5-digit numbers: two column sums and five cells.
Whichever fails most becomes the core of Task 16.
Scan result: A 150/150, B 24/24, C 7/7 - all exact (playbook #85). Perception is not a weakness.

## v3 draft: hidden hydraulic regime change (hyd/), user chose option 1 (2026-10-10)
Gravity cooling-water system from open head tank T-1 (level EL +25.0 m): header CW-301 DN150 at EL +14 m,
branches to O1 (EL 15), O2 (EL 17), O4 (EL 16) through exchangers (K 45/30/60), and CW-304 DN80 to the cooling
pond O3 (EL 0) over a pipe bridge with its crest at EL +31 m. Data sheet gives fluid data, Swamee-Jain friction,
K values and a generic note that the column separates at vapour pressure at the lowest-pressure point.
Key (correct): O1 8.954, O2 9.131, O3 10.658, O4 28.247, total 56.989 L/s; crest 2.339 kPa abs; T3 189.92 kPa.
Naive full-pipe: O3 24.281, total 68.224 L/s, crest -98.6 kPa abs (impossible) - every flow differs.
Probe 3 (opus, 40 min) launched.
Probe 3 result: solved exactly (all flows to 3 decimals, crest at vapour pressure, located correctly); it also
noted the siphon cannot self-prime (crest above tank level), a flaw in the draft. Playbook #86.

## v4 draft: coupled regimes + operating-log state (v4/), "toughest" per user (2026-10-10)
Three parallel pumps on check valves -> header -> consumers E-101 (FV-101), E-102 and riser to break tank TK-1
(free inlet EL 28, weir crest EL 26) -> gravity node -> E-103, E-104 (HV-204) and outfall over a crest (EL 21.5)
to a pond (EL -4). Regimes: weir overflow or not, outfall full or column-separated, controller saturated or not;
solver enumerates regimes and keeps the consistent one (unique for each state tested).
State at 09:00 from the night log: A+C running (B tripped, reset, test-run and stopped), FV-101 MANUAL 45 %,
HV-204 still closed (permit closed but valve never reopened).
Key: A 58.29, C 37.20, E-101 18.47, E-102 30.79, riser 46.24, E-103 12.89, E-104 0, outfall 33.35, weir 0 L/s;
TK-1 23.461 m (below the weir); PI-100 2.585 bar g; crest 2.339 kPa abs.
Naive (all pumps, auto, HV-204 open): overflowing, TK-1 26.007 m, E-104 12.50, outfall 34.44 L/s.
Probe 4 (opus, 40 min) launched.
Probe 4 result: everything exact (line-up, all flows, level, PI-100, crest), plus a consistency flaw found in my
log (A alone keeps PI-100 at ~2.39 bar g, so C's 23:40 auto-start needs a transient). Playbook #87.

## CW-200 (v5) - scaled-up version for platform iteration (user chose option 2, 2026-10-10)
Four pumps -> manifold -> DN200 ring main (loop solve, unknown directions) with 5 branches (E-201/FV-201,
riser to TK-1, E-202, E-203/FV-203, E-204/HV-204) -> TK-1 (free inlet EL 30, weir EL 29) -> CW-208 -> N5 ->
E-205, E-206/HV-206, outfall over crest EL 21 to pond EL -9. Geometry from 3 isometric sheets (ring to scale,
branch details). Night log: B trips (C auto-starts; A alone gives PI-100 ~2.67 < 2.8 bar g threshold), FIC-203
to MANUAL 35 %, HV-204 closed then explicitly reopened, B reset, D returned, C vibration -> B started + C stopped,
HV-206 closed (leak), FIC-201 SP 18 -> 26 (saturates), D test run then stopped. Every log state checked against
the physics (v5/timeline.py). Final regime: weir overflowing, outfall column-separated, FV-201 saturated,
ring flow Tb-Tc reversed (1.15 L/s Tc->Tb). Key: v5/key.json. Packet artifact/cw200_v1.pdf (metadata clean).
Figure checks: CW-204 length 37,500 mm; CW-211 has 4 elbows. Local fairness probe (opus, 60 min) launched.
