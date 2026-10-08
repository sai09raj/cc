# COHERE-12 rubric (v3, packet cohere12_v4.pdf)

Positive total **138**; six negative criteria (-10, -8, -8, -6, -5, -5). **50
criteria**. Every weight is within -10..+10; every criterion body is 301
characters or fewer; criteria are binary and each checks one value, one
claim or one requirement. Accept any language, source organization,
results-file format and trace format. Numbers may be written with or
without thousands separators.

Answer key: exhaustive simulation of all 29,360,128 configurations
(2,400 operations per core) with the optimized C engine
(`proto/cohere_fast.c`), split over 28 parallel workers, one per directory
placement, 448 chunk files in all, aggregated by `proto/aggregate_v4.py`.
Its results match the JavaScript engine (`proto/cohere.js`) and the real
pilot model's own engine on 41 sampled entries plus the baseline, the
three variants and the optimum. The unoptimized C reference
(`proto/cohere.c`) recomputed one full chunk (D0 on N2, D1 on N6, Q = 4,
B = 1) with the same makespan sum and histogram. Every
graded metric is defined in packet Section 8; the optimum's tie-break is
in Section 9.

## Score topology

| Bucket | Criteria | Points | Needs the whole space simulated? |
|---|---|---|---|
| Values read from the figures | 1-12 | 12 | no |
| Package | 13-14, 50 | 3 | no |
| Baseline and variants | 15-21 | 19 | no |
| Optimal configuration | 22-23 | 7 | no (findable by search) |
| Whole-space characterization | 24-34 | 86 | yes |
| Checker | 35-39 | 5 | no |
| Memo reasoning | 40-43 | 6 | no |

A correct simulator with a correct optimum but an incomplete sweep earns
at most 52/138 (37.7%). Each per-Q count needs one quarter of the space
(7,340,032 runs) and each per-B count another quarter; the three totals
need all of it.

## Values read from the figures (1-12, weight 12)

| # | Wt | Criterion |
| --- | --- | --- |
| 1 | +1 | States the node layout read from Figure 1: N0, N1, N2, N3 form row 0 and N4, N5, N6, N7 form row 1, each row ordered column 0 to column 3. |
| 2 | +1 | States the latency of the link between N0 and N1 as 1 cycle. |
| 3 | +1 | States the latency of the link between N1 and N2 as 2 cycles. |
| 4 | +1 | States the latency of the link between N2 and N3 as 1 cycle. |
| 5 | +1 | States the latency of the link between N4 and N5 as 2 cycles. |
| 6 | +1 | States the latency of the link between N5 and N6 as 1 cycle. |
| 7 | +1 | States the latency of the link between N6 and N7 as 3 cycles. |
| 8 | +1 | States the latency of the link between N0 and N4 as 1 cycle. |
| 9 | +1 | States the latency of the link between N1 and N5 as 3 cycles. |
| 10 | +1 | States the latency of the link between N2 and N6 as 1 cycle. |
| 11 | +1 | States the latency of the link between N3 and N7 as 2 cycles. |
| 12 | +1 | States the baseline line map number read from Figure 5 as 19245 (lines 0, 2, 3, 5, 8, 9, 11 and 14 homed at D1, all others at D0). |

## Package (13-14, weight 2)

| # | Wt | Criterion |
| --- | --- | --- |
| 13 | +1 | Records the exact language and runtime version used (for example "Node.js v20.11.1"), not just the language name. |
| 14 | +1 | Gives concrete commands that rerun its simulator and its checker to reproduce the reported results. |

## Baseline and variants (15-21, weight 19)

| # | Wt | Criterion |
| --- | --- | --- |
| 15 | +4 | Reports the baseline's (D0 on N0, D1 on N7, Q = 2, B = 2, line map 19245) makespan as exactly 39,980 cycles. |
| 16 | +2 | Reports the baseline's (D0 on N0, D1 on N7, Q = 2, B = 2, line map 19245) p95 load miss latency as exactly 38 cycles. |
| 17 | +2 | Reports the baseline's (D0 on N0, D1 on N7, Q = 2, B = 2, line map 19245) total messages created as exactly 58,447. |
| 18 | +2 | Reports the baseline's (D0 on N0, D1 on N7, Q = 2, B = 2, line map 19245) Nack count as exactly 2,181. |
| 19 | +3 | Reports the makespan of the variant that replaces the baseline line map with 43690 (D0 on N0, D1 on N7, Q = 2, B = 2) as exactly 39,767 cycles. |
| 20 | +3 | Reports the makespan of D0 on N1, D1 on N6, Q = 2, B = 2 with line map 19245 as exactly 36,306 cycles. |
| 21 | +3 | Reports the makespan of D0 on N1, D1 on N6, Q = 4, B = 1 with line map 19245 as exactly 35,693 cycles. |

## Optimal configuration (22-23, weight 7)

| # | Wt | Criterion |
| --- | --- | --- |
| 22 | +4 | Identifies the optimal configuration (smallest makespan; ties by messages, D0 node, D1 node, Q, B, line map) as D0 on N2, D1 on N6, Q = 4, B = 1, line map 63905. |
| 23 | +3 | Reports the optimal configuration's (D0 on N2, D1 on N6, Q = 4, B = 1, line map 63905) makespan as exactly 33,626 cycles. |

## Whole-space characterization (24-34, weight 86)

All counts and sums are over the 29,360,128 configurations of packet
Section 1; "below the baseline" means makespan less than 39,980 cycles.

| # | Wt | Criterion |
| --- | --- | --- |
| 24 | +10 | Reports the sum of makespan over all 29,360,128 configurations as exactly 1,234,126,567,296. |
| 25 | +10 | Reports the number of configurations, out of 29,360,128, whose makespan is below the baseline's 39,980 cycles as exactly 9,711,036. |
| 26 | +10 | Reports the number of configurations, out of 29,360,128, with makespan at most 36,000 cycles as exactly 1,239,802. |
| 27 | +8 | Reports the number of configurations with Q = 1 whose makespan is below 39,980 cycles as exactly 1,416,317. |
| 28 | +8 | Reports the number of configurations with Q = 2 whose makespan is below 39,980 cycles as exactly 2,396,296. |
| 29 | +8 | Reports the number of configurations with Q = 3 whose makespan is below 39,980 cycles as exactly 2,825,944. |
| 30 | +8 | Reports the number of configurations with Q = 4 whose makespan is below 39,980 cycles as exactly 3,072,479. |
| 31 | +6 | Reports the number of configurations with B = 1 whose makespan is below 39,980 cycles as exactly 2,614,670. |
| 32 | +6 | Reports the number of configurations with B = 2 whose makespan is below 39,980 cycles as exactly 2,547,107. |
| 33 | +6 | Reports the number of configurations with B = 4 whose makespan is below 39,980 cycles as exactly 2,395,093. |
| 34 | +6 | Reports the number of configurations with B = 8 whose makespan is below 39,980 cycles as exactly 2,154,166. |

## Checker (35-39, weight 5)

| # | Wt | Criterion |
| --- | --- | --- |
| 35 | +1 | The checker's recorded output reports that in the baseline trace no cycle has two caches holding the same line in state M. |
| 36 | +1 | The checker's recorded output reports that in the baseline trace every load returned the value of the most recent store to its line. |
| 37 | +1 | The checker's recorded output reports checking exactly 9,609 loads in the baseline trace (the baseline run's total LD operations). |
| 38 | +1 | The checker's recorded output rejects the altered baseline trace in which one load returns a different value, naming the load value invariant as violated. |
| 39 | +1 | The checker's recorded output rejects the altered baseline trace in which a second cache holds a line in state M, naming the single M holder invariant as violated. |

## Memo reasoning (40-43, weight 6)

| # | Wt | Criterion |
| --- | --- | --- |
| 40 | +2 | The memo identifies the directory placement as the knob with the largest effect on makespan, larger than the line map, Q or B. |
| 41 | +2 | The memo attributes the best placement's (D0 on N2, D1 on N6) advantage to its directories being the fewest link cycles from the cores. |
| 42 | +1 | The memo states that a larger Q lowers the average makespan across the configuration space. |
| 43 | +1 | The memo states that a larger B raises the average makespan across the configuration space. |

## Negative criteria (44-49)

| # | Wt | Criterion |
| --- | --- | --- |
| 44 | -10 | Uses a third party package or external tool (for example NumPy, SimPy, NetworkX, gem5) to compute any simulation result. |
| 45 | -8 | Reports a whole-space sum or count over the 29,360,128 configurations while stating it simulated fewer configurations than that (an estimate or extrapolation presented as the value). |
| 46 | -6 | Calls its reported configuration optimal (rather than the best found) while stating it simulated fewer than all 29,360,128 configurations. |
| 47 | -5 | The checker imports, calls or copies code from the simulator instead of being separately coded. |
| 48 | -8 | Hard codes any reported simulation result (a makespan, p95, message count, Nack count, or whole-space count or sum) as a literal in its delivered source code instead of computing it by running its simulator. |
| 49 | -5 | Accesses the internet or any external source (for example downloading packages, code, documentation or results) while building or running its simulator or checker. |

## Package completeness (50, weight 1)

Contents of each file are graded elsewhere (simulator and results 15-34, checker 35-39, memo 40-43); this row checks delivery only.

| # | Wt | Criterion |
| --- | --- | --- |
| 50 | +1 | Delivers as files a simulator source, a separately coded checker source, a baseline trace, a results file and an engineering memo. |

## Reverse coverage

| Prompt requirement | Criteria |
|---|---|
| State node layout, link latencies, baseline line map number | 1-12 |
| Simulator, standard library only, offline | 15-34, 44, 49 |
| Runtime version, reproduction commands | 13-14 |
| Baseline makespan, p95, messages, Nacks | 15-18 |
| Three variant makespans | 19-21 |
| Sum of makespan; count below baseline; count at most 36,000 | 24-26 |
| Count below baseline per Q and per B | 27-34 |
| Optimal configuration and its makespan | 22-23 |
| Call it optimal only after simulating all configurations | 46 |
| Number of configurations actually simulated | 45, 46 |
| Base every number on your own executed programs | 48 |
| Deliver the five files | 50 |
| Separate checker, two invariants reported | 35-36, 47 |
| Number of loads the checker checked | 37 |
| Checker rejects the two altered traces, naming the invariant | 38-39 |
| Memo: knob with largest effect, why best placement wins | 40-41 |
| Memo: effect of larger Q and larger B on average makespan | 42-43 |

## Reviewer-feedback audit

| Past reviewer finding | Status here |
|---|---|
| Expected value a correct answer can never reach / unstated rule | Values come from exhaustive simulation by a reference whose rules the v1 blind probe reproduced exactly from the packet; C, Python and JavaScript engines agree. |
| Prompt explanation with no criterion | Every memo requirement mapped (40-43); coverage table above. |
| Mechanism description bundled with a trace value | None. |
| Several constants in one criterion | Each link latency is its own criterion; the line map is one 16-bit number, stated with its decoding. |
| Metric the packet never defines | Makespan, p95, messages, Nacks: packet Section 8; configuration space and tie-break: Sections 1 and 9; "below the baseline" defined above each count and inside each criterion. |

| Validity-only or presence-only criterion (ARRAY-11 review) | None graded on presence alone: the checker must report the exact load count and reject both altered traces; every value criterion states its exact expected answer. |
| Prompt rule with no matching trap (ARRAY-11 review) | "Call it optimal only if you simulated all configurations" has its own negative (46); estimates presented as values have 45. |

Atomicity and self-containment check (after writing): every criterion
tests one value, one claim or one requirement, names its configuration or
population in full, and states its expected answer.
