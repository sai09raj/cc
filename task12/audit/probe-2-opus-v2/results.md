# COHERE-12 results

All numbers below come from the programs in this directory, executed offline: simulator `sim.js` (Node.js v22.22.2), checker `checker.py` and analysis scripts (Python 3.11.15).

## Values read from the figures

* Figure 1 (floorplan): node Nn is at row n div 4, column n mod 4 (N0..N3 = row 0, columns 0..3; N4..N7 = row 1, columns 0..3); core Cn sits on node Nn.
* Figure 2 (link latency, cycles, both directions): N0-N1 = 1, N1-N2 = 2, N2-N3 = 1, N4-N5 = 2, N5-N6 = 1, N6-N7 = 3, N0-N4 = 1, N1-N5 = 3, N2-N6 = 1, N3-N7 = 2. (Measured from the embedded image: bars end exactly on the 1st/2nd/3rd major gridline; pixel ends 802/1291/1779 vs gridlines at 803/1292/1780, axis origin 317.)
* Figure 5 (baseline line map): L0 D1, L1 D0, L2 D1, L3 D1, L4 D0, L5 D1, L6 D0, L7 D0, L8 D1, L9 D1, L10 D0, L11 D1, L12 D0, L13 D0, L14 D1, L15 D0 -> bits 0,2,3,5,8,9,11,14 set -> **line map number 19245** (0x4B2D).

## Baseline and variants (each a single executed run)

| run | D0 | D1 | line map | Q | B | makespan | p95 load-miss latency | messages | Nacks |
|---|---|---|---|---|---|---|---|---|---|
| Baseline | N0 | N7 | 19245 | 2 | 2 | **6725** | 39 | 9762 | 401 |
| Variant 1: line map 43690 | N0 | N7 | 43690 | 2 | 2 | **6931** | 38 | 9891 | 377 |
| Variant 2: D0 N1, D1 N6 | N1 | N6 | 19245 | 2 | 2 | **6198** | 30 | 9913 | 403 |
| Variant 3: D0 N1, D1 N6, Q=4, B=1 | N1 | N6 | 19245 | 4 | 1 | **6141** | 27 | 9199 | 74 |

Baseline: makespan **6725** cycles, p95 load-miss latency **39** cycles (over 1224 loads that sent GetS; issue cycle = cycle the GetS was first sent; if the issue cycle is instead taken as the first cycle the core attempted the load, including eviction retries, p95 = 43), messages **9762**, Nacks **401**. Run end cycle 6725.

## Whole configuration space (29,360,128 configurations)

**Not every configuration was simulated.** At ~5 ms per simulation per CPU core (4 cores), the full space needs ~41 core-hours (~10 h wall-clock), far beyond the 2.5 h budget. Method actually used:

* **Census (exact)**: every one of the 65,536 line maps was simulated for 24 of the 448 (placement, Q, B) cells: D0=N2/D1=N6 with all 16 (Q,B); D0=N2/D1=N5 with Q=4 (all B); D0=N1/D1=N6 with Q=4 (all B). That is 1,572,864 configurations.
* **Stratified sample**: in each of the other 424 cells, 7,717 line maps drawn without replacement (keyed pseudo-random permutation, identical sample size in every cell): 3,272,008 configurations.
* **Distinct configurations simulated and used: 4,844,872** (16.50% of the space). (Sweep samples that fell in census cells, 185,208 runs, duplicate census runs and are not counted; plus the handful of baseline/variant/validation runs.)
* Whole-space figures = exact census totals + (65,536 x sample mean) for every sampled cell. Intervals are 95% (1.96 SE, stratified, finite-population corrected) and cover sampling error only. **These are estimates, not exact counts.**

| quantity | value |
|---|---|
| Sum of makespan over all configurations | ≈ 209,213,635,173 ± 11,912,385 (95% CI; SE 6,077,748; exact census part 9,660,041,472) |
| Mean makespan | ≈ 7125.8 cycles |
| Configurations with makespan < baseline (6725) | ≈ 9,227,923 ± 10,152 (95% CI; SE 5,179; exact census part 1,492,391) |
| Configurations with makespan ≤ 6,000 | ≈ 655,456 ± 1,468 (95% CI; SE 749; exact census part 573,258) |
| Q = 1: makespan < baseline | ≈ 1,281,237 ± 4,171 (95% CI; SE 2,128; exact census part 239,370) |
| Q = 2: makespan < baseline | ≈ 2,290,343 ± 5,213 (95% CI; SE 2,660; exact census part 260,952) |
| Q = 3: makespan < baseline | ≈ 2,704,399 ± 5,441 (95% CI; SE 2,776; exact census part 261,979) |
| Q = 4: makespan < baseline | ≈ 2,951,945 ± 5,374 (95% CI; SE 2,742; exact census part 730,090) |
| B = 1: makespan < baseline | ≈ 2,506,440 ± 5,245 (95% CI; SE 2,676; exact census part 378,894) |
| B = 2: makespan < baseline | ≈ 2,430,837 ± 5,189 (95% CI; SE 2,647; exact census part 377,548) |
| B = 4: makespan < baseline | ≈ 2,274,362 ± 5,063 (95% CI; SE 2,583; exact census part 372,994) |
| B = 8: makespan < baseline | ≈ 2,016,285 ± 4,795 (95% CI; SE 2,446; exact census part 362,955) |

## Optimal configuration

**Best configuration found: D0 on N2, D1 on N6, line map 55860, Q = 4, B = 1, makespan 5470 cycles** (9121 messages, 79 Nacks).

Status: this is the exact optimum of the D0=N2/D1=N6 placement (all 1,048,576 of its configurations were simulated) and it beats every one of the other 3,796,296 simulated configurations (best of the exhaustively simulated N2-N5 and N1-N6 Q=4 cells: 5604 and 5627). It is **not certified** as the global optimum: 83.5% of the space was not simulated. The evidence that it is global: N2-N6 has the lowest mean makespan of all 28 placements, 290 cycles below the next placement, and the best simulated configuration of any other placement is 134 cycles slower.

Top configurations found (spec order: makespan, messages, D0, D1, Q, B, map):

| rank | D0 | D1 | map | Q | B | makespan | messages |
|---|---|---|---|---|---|---|---|
| 1 | N2 | N6 | 55860 | 4 | 1 | 5470 | 9121 |
| 2 | N2 | N6 | 21748 | 4 | 2 | 5476 | 9097 |
| 3 | N2 | N6 | 39820 | 3 | 1 | 5479 | 9230 |
| 4 | N2 | N6 | 53700 | 3 | 1 | 5479 | 9233 |
| 5 | N2 | N6 | 9126 | 4 | 1 | 5484 | 9095 |
| 6 | N2 | N6 | 5553 | 4 | 1 | 5491 | 8964 |
| 7 | N2 | N6 | 53269 | 4 | 2 | 5495 | 8969 |
| 8 | N2 | N6 | 56404 | 3 | 2 | 5495 | 9171 |
| 9 | N2 | N6 | 29748 | 4 | 2 | 5498 | 9129 |
| 10 | N2 | N6 | 47665 | 4 | 4 | 5499 | 9006 |

Best found per placement:

| placement | estimated mean makespan | best found | config of best (Q, B, map) |
|---|---|---|---|
| N0-N1 | 7955 | 7121 | Q=4, B=1, map=54211 |
| N0-N2 | 7180 | 6156 | Q=3, B=2, map=50175 |
| N0-N3 | 7254 | 6428 | Q=4, B=4, map=36483 |
| N0-N4 | 8175 | 7399 | Q=4, B=2, map=32132 |
| N0-N5 | 7435 | 6623 | Q=4, B=2, map=45675 |
| N0-N6 | 6938 | 5882 | Q=2, B=2, map=62443 |
| N0-N7 | 7188 | 6173 | Q=4, B=1, map=64353 |
| N1-N2 | 6718 | 5893 | Q=3, B=8, map=31483 |
| N1-N3 | 6950 | 6080 | Q=3, B=1, map=23882 |
| N1-N4 | 7745 | 6928 | Q=4, B=4, map=26497 |
| N1-N5 | 6934 | 6201 | Q=4, B=2, map=4206 |
| N1-N6 | 6488 | 5627 | Q=4, B=4, map=60259 |
| N1-N7 | 6938 | 6010 | Q=4, B=8, map=20276 |
| N2-N3 | 6964 | 5966 | Q=4, B=1, map=38168 |
| N2-N4 | 7007 | 6017 | Q=2, B=2, map=28676 |
| N2-N5 | 6362 | 5604 | Q=4, B=2, map=50884 |
| N2-N6 | 6072 | 5470 | Q=4, B=1, map=55860 |
| N2-N7 | 7020 | 5970 | Q=4, B=1, map=4388 |
| N3-N4 | 7113 | 6142 | Q=4, B=1, map=4028 |
| N3-N5 | 6786 | 5912 | Q=4, B=1, map=48934 |
| N3-N6 | 6810 | 6009 | Q=4, B=4, map=4199 |
| N3-N7 | 7837 | 7083 | Q=2, B=2, map=13908 |
| N4-N5 | 7894 | 7086 | Q=3, B=1, map=59267 |
| N4-N6 | 7099 | 6002 | Q=4, B=4, map=62843 |
| N4-N7 | 7478 | 6584 | Q=4, B=2, map=22001 |
| N5-N6 | 6662 | 5866 | Q=2, B=1, map=23371 |
| N5-N7 | 7213 | 6247 | Q=4, B=8, map=14513 |
| N6-N7 | 7308 | 6314 | Q=4, B=4, map=5368 |

Mean makespan by Q (over the whole space, estimated): Q=1: 7351, Q=2: 7134, Q=3: 7038, Q=4: 6980

Mean makespan by B (estimated): B=1: 7081, B=2: 7098, B=4: 7131, B=8: 7193

Mean makespan by (Q,B) (estimated): Q1B1: 7252, Q1B2: 7290, Q1B4: 7364, Q1B8: 7499, Q2B1: 7089, Q2B2: 7106, Q2B4: 7139, Q2B8: 7200, Q3B1: 7014, Q3B2: 7023, Q3B4: 7041, Q3B8: 7074, Q4B1: 6970, Q4B2: 6972, Q4B4: 6982, Q4B8: 6998

Average within-cell standard deviation of makespan across line maps: 400 cycles.

Share of makespan variance over the space (uniform stratified sample): placement 54.1%, Q 4.7%, B 0.4%, all (placement,Q,B) cells together 59.7%, line map within a cell 40.3%.

## Checker (baseline trace)

```
trace: baseline_trace.txt
records: 7996 state transitions, 1648 loads, 940 stores, last cycle 6725
Invariant 1 (at most one M holder per line at every cycle): PASS (0 violations; max simultaneous M holders of a line = 1)
Invariant 2 (every load returns the most recent store): PASS (0 violations over 1648 loads)
Trace consistency checks: PASS (0 problems)
```

Mutation tests (to show the checker can fail): changing one load value in the trace -> Invariant 2 FAIL; injecting a second cache entering M on a line -> Invariant 1 FAIL. The checker also passed on traces of 6 other configurations (incl. the best one and Q=1 high-Nack runs).

## Reproduction

```
cd outputs
node sim.js baseline baseline_trace.txt      # baseline metrics + trace (prints JSON metrics)
node sim.js run 0 7 43690 2 2                # variant 1
node sim.js run 1 6 19245 2 2                # variant 2
node sim.js run 1 6 19245 4 1                # variant 3
node sim.js run 2 6 55860 4 1                # best configuration found
python3 checker.py baseline_trace.txt
# census of a placement (worker w of 4):  node census.js 2 6 4:1,4:2,...,1:8 w 4 c26_w$w.csv
# stratified sweep (worker w of 4):       node sweep.js w 4 sweep_w$w.csv <stop-epoch-seconds>
# combine:  python3 analyze.py 6725 analysis.json --census c*.csv --sweep sweep_w*.csv
# render:   python3 report.py analysis.json runs.json checker_output.txt > results.md
```

Raw per-configuration CSVs (census and sample) are in `outputs/data/` (gzipped).

## Runtime and effort

* Simulator speed: about 5.0 to 5.3 ms per configuration per CPU core once the JIT is warm (Node v22.22.2). That is about 800 configurations per second on the 4 available cores. A cold single CLI run takes 40 to 100 ms.
* Wall-clock: about 10 min reading the packet and figures; about 10 min building the simulator, checker and validation (reference-versus-optimized regression on 150 configurations, mutation tests); about 105 min of computation (N2-N6 census 22 min, N2-N5/N1-N6 Q=4 census 11 min, stratified sweep about 75 min in total); about 15 min of analysis and writing.
* Across all ~5.0M simulations the simulator's protocol assertions never fired. Any message arriving in a Figure 3/4 cell marked '-' throws. No run deadlocked.

## Interpretation choices (where the packet is ambiguous)

1. Figure 2 has no numeric tick labels. I took the caption's "major gridline = 1 cycle" with the bars starting at 0. The bars start at the axis spine, and the spine-to-first-gridline spacing equals the gridline spacing.
2. Load-miss latency "issue cycle" is taken as the cycle the GetS was first sent. The alternative, the first cycle the core attempted the load including eviction retries, gives a baseline p95 of 43 instead of 39.
3. FWD "blocked" lines are reset every cycle: blocking applies within one scan.
4. After an eviction the operation is retried next cycle. If the set is still full, with the evicted way now in SI_A or MI_A, and the other way is in S or M, that way is evicted too. This is a literal reading of Section 5.
5. "Data from home" means Data whose sender is a directory bank. "Data from a cache" means Data whose sender is a cache.
6. The refusal count k is kept per (cache, line). Each line has at most one outstanding request.
7. A REQ arriving at a directory from the co-located core is subject to the Q check like any other.
8. Messages are counted up to run end, so they include PutAcks and similar traffic after the last core finished.
