# Task 15 — FIRE-15 (initial-attack crew stationing on a lightning day; Earth & Environmental Sciences)

Recipe reused from GRID-14 (playbook #80): integer-exact model, exact whole-space aggregates whose full
computation exceeds the 9000 s limit, partial-run branch scores low, timeout branch.

- Model: 128 x 128 cell landscape (16 x 16 cover blocks), stochastic spread CA (per-eligible-neighbour LCG
  draws in row-major order, so no shortest-path shortcut), lightning ignitions, 7 distinct crews that return
  to their station after each fire (station stays in the state; no configuration merging), 4 scenarios.
- Plans: 14^7 = 105,413,504. Engines: literal Python reference (proto/fire_ref.py) and bit-row C engine
  (proto/ffast.c) agree on 17 plans. C: ~4.3-4.9 ms per plan here; full sweep ~453,000 CPU-s.
  Platform estimate at C speed: 105.4M x 4.3 ms x 0.655 / 16 = ~18,500 s (about 2x the limit).
- Baseline (S1, S4, S5, S8, S9, S12, S13): A 1,992 / B 4,240 / C 3,455 / D 4,079, total 13,766 (~42% of
  plans below it). Variants: crew 7 at S6 10,956; crews 1 and 7 swapped 14,354; all at S6 18,683.
  Baseline scenario A: 40 fires, 1,020 burnt cells, so 980 spread ignitions.
- Answer key: 56 cloud workers (branches claude/fire15-gt-s{S1}q{Q}), 196 part files, launched
  2026-10-09 ~13:00 UTC; aggregator proto/aggregate.py.
- Packet artifact/fire15_v1.pdf (2 text pages, map, parameters, wind, crews), metadata-clean.
- Blind opus probe launched 13:05 UTC (2.5 h, Python/Node only, 4 cores).
