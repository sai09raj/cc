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

## Answer-key verification (2026-10-10 07:35 UTC)
My independent enumeration of all 196 parts (105,413,504 plans, C engine) matches every value in the v4 rubric
(GPT's package): sum 1,517,929,184,378; below 43,983,052; all four 6,249,692; all 14 crew-7 counts; optimum
S14,S14,S8,S5,S3,S9,S7 = 6,012; crew 6 most influential (range 2,068 vs crew 7 2,006); crew 7 best S9, worst S2.
The platform package is GPT's v4 (fire15_v4.pdf, prompt, rubric, Ideal Flow); platform/rubric.md and
ideal-flow.md here are my earlier v1-based versions, kept for reference only.

## Real platform runs (2026-10-10): 4 timeouts (9000 s), 2 scored 100
The 100 runs installed C compilers (apt-get gcc / pip ziglang), used the prompt-endorsed shared-state evaluation,
and finished the full sweep in 86-100 min (6,573 s and 8,693 s total). Submitted as is by the user's decision.
Lesson: playbook mistake #83 (compute-only difficulty is a weak stump; assume the model installs any tooling).
