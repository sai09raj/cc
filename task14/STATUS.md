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

## Answer key (36 workers, 144 part files, none missing)
Sum of total TTS 123,858,216,502,180; below baseline 7,425,123; gridlock 5,485,845.
Below baseline by cycle: 60: 3,145,241 / 72: 3,126,728 / 84: 1,153,154 / 96, 108, 120: 0 (not graded:
a sample guesses 0). By plan 1-6: 1,188,148 / 1,278,030 / 1,265,778 / 1,146,190 / 1,208,142 / 1,338,835.
By order: lead 3,861,286 / lag 3,563,837. Gridlock by cycle 60..120: 514 / 17,064 / 310,502 / 872,881 /
1,410,855 / 2,874,029. Optimum: C 60, plan 6, lag, offsets 0/45/15/30/0/30/15/30/0, total TTS 1,829,597.

## Probe 1 (opus alias) - stopped by the account usage limit before finishing
Its simulator was exact (baseline 4,052,648 and all three variants match), its local search found the
true optimum (1,829,597), it simulated 324,155 configurations (1.7 %) and reported the whole-space
items as stratified-sample estimates with confidence intervals - i.e. the "partial run" branch,
which earns none of the whole-space weight. Retry launched 22:48 UTC.

## Probe 2 (opus alias, retry): 51/135 = 37.8 % - the "partial run" branch, as designed
Exact simulator, baseline, variants, optimum, checker and memo; 893,362 configurations simulated
(4.73 %); whole-space items reported as estimates (all miss). See audit/probe-2/GRADING.md.
Its JS engine ran ~25 ms per configuration (as fast as our C). Scaling as in COHERE (real engine ~1.43x
faster than the local probe's, platform x0.655, 17 threads): full sweep ~12,800 s on the platform plus
development time, versus the 9000 s limit - margin about 1.4-1.7x, thinner than COHERE v4's 2.6x.

## Real Model A runs (2026-10-09): PASSED
5 of 6 runs: "server disconnected without sending a response" (valid stump). 1 completed run, platform
score 19 (my count 34/135 = 25%): exact engine, but it ended its turn with the sweep ~4% done and the
one-shot session killed the sweep; no memo. See audit/real-runs/GRADING.md, playbook mistakes #80, #81.
