# Task 14 — GRID-14 (signal coordination on a 3 x 3 grid; Civil Engineering, transportation)

Aim (user, 2026-10-08): stump both ways - completed runs below 50, and runs that attempt the
full sweep time out.

- Engines: Python reference (`proto/grid_ref.py`), C cell-scan (`proto/cgrid.c`), C vehicle-list
  (`proto/cgrid_fast.c`), JS vehicle-list (`proto/grid_fast.js`); all agree exactly on 20 random
  configurations (Python on 6). Fast C 24.6 ms per configuration (3 scenario runs); JS as written
  60 ms, a tuned JS perhaps ~40 ms.
- Space: 6 cycles x 6 plans x 2 orders x 4^9 offsets = 18,874,368 configurations. Platform
  estimate with a tuned JS engine (~40 ms, x0.655, 17 threads): ~29,000 s, about 3.2x the 9000 s
  limit; still ~14,500 s if a run doubles that speed.
- Baseline (C 84, plan 1, lead, offsets 0): AM 1,138,089 / PM 1,097,366 / EVENT 1,817,193,
  total 4,052,648 vehicle-seconds. Variants: offsets 0/21/42 per row 3,901,019; lag 4,281,802;
  C 60 2,136,688. Some configurations gridlock (EVENT run hits the 7200 s cap).
- Packet `artifact/grid14_v1.pdf` (2 text pages, map, demand chart, turning/phases, timing table),
  metadata-clean. Draft prompt `platform/prompt.md`.
- Answer key: 36 cloud workers (one per cycle and plan, branches claude/grid14-gt-c{C}p{P}),
  launched 2026-10-08 16:34 UTC; aggregator `proto/aggregate.py`.
- Early opus-alias probe running (2.5 h budget, Python/Node only).
