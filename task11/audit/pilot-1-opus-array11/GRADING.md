# ARRAY-11 pilot 1 (`opus` alias, frozen packet array11_v1.pdf + array-prompt.md)

Wall time about 38 minutes (2266 s), CPython 3.11.15, standard library only.
All five layouts recomputed by the author checker (`opt-prototype/check.py`):
S1 5,878,715; S2 5,921,875; S3 8,075,675; S4 7,535,670; S5 7,535,670. All valid.

| # | Wt | Result | Note |
|---|---|---|---|
| 1-4 | 7 | 7 | P (3200,3000), A (-700,2700), 4/8/14, 100/160/245 by pixel measurement |
| 5-6 | 2 | 2 | CPython 3.11.15; commands given |
| 7-10 | 7 | 7 | accepts five; rejects crossing, capacity, length with the right rule |
| 11 | 2 | 0 | S1 bound 5,611,567 < 5,643,567 (95.5%) |
| 12 | 2 | 0 | S4 bound 6,898,889 < 7,181,717 (92.2%) |
| 13 | 2 | 2 | relabelling 43,944 m of C1 as C2; reoptimised shorter strings |
| 14 | 2 | 2 | A off the west edge, average turbine distance 4,035 m vs 2,467 m |
| 15 | 1 | 1 | feeders at load 8 merged to 12-13 on C3 |
| 16 | 1 | 1 | Esau Williams greedy 6,177,435 |
| 17 | 10 | 10 | S1 5,878,715 exact |
| 18 | 10 | 10 | S2 5,921,875 exact |
| 19 | 10 | 10 | S3 8,075,675 exact |
| 20 | 10 | 0 | S4 7,535,670 (+54,715, +0.73%) |
| 21 | 10 | 0 | S5 7,535,670 (+18,970, +0.25%) |
| 22 | 5 | 5 | 43,160 |
| 23 | 5 | 5 | 2,196,960 |
| 24 | 5 | 0 | reported 1,656,955 |
| 25 | 5 | 0 | reported 0 (its S4 layout uses 5 bays) |
| 26-29 | neg | 0 | stdlib only; no optimality claim; no cost below minimum; checker separate |

**Total 62/96 = 64.6%. Gate 8.5: FAIL.**

Diagnosis: simulated annealing over non-crossing trees (cut a branch,
re-root, re-attach; exact crossing bitmasks) finds the optimum of every
central-platform scenario in minutes (S1 hit independently in three
runs). It misses both edge-platform scenarios, which also defeated
probe 3 hardest (+4.83%). Its Lagrangian bound is weak (2.5-8.5% gap),
and it made no optimality claim. Difficulty in this family lives in the
edge-platform landscape, not in the central one.
