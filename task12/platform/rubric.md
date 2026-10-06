# COHERE-12 rubric (v1)

Positive total **101**; three negative criteria (-10, -5, -5). **41
criteria**. Every weight is within -10..+10; every criterion body is 301
characters or fewer; criteria are binary and each checks one value, one
claim or one requirement. Accept any language, source organization, CSV
column order and trace format. Numbers may be written with or without
thousands separators.

Every expected value comes from the packet as written: the reference
simulator (`proto/cohere.py`) implements only rules stated in
`artifact/cohere12_v1.pdf`, checked clause by clause, and its runs end with
zero invariant violations. Metrics used here (makespan, p95 load miss
latency, messages, Nacks) are defined in packet Section 8.

## Score topology

| Bucket | Criteria | Points | Needs a correct simulation? |
|---|---|---|---|
| Values read from the figures | 1-15 | 15 | no |
| Package | 16-17 | 2 | no |
| Baseline run | 18-21 | 18 | yes |
| Whole sweep | 22-25 | 25 | yes (25: no) |
| Selections | 26-29 | 24 | yes |
| Gain decomposition | 30-31 | 8 | yes |
| Checker | 32-33 | 2 | no |
| Memo reasoning | 34-38 | 7 | partly |

A complete submission whose simulator diverges anywhere earns roughly 27
points (figures, package, CSV shape, checker, qualitative memo claims),
plus 8 if it lands on the Fastest configuration by chance: about 35/101.

## Values read from the figures (1-15, weight 15)

| # | Wt | Criterion |
| --- | --- | --- |
| 1 | +1 | States the node layout read from Figure 1: N0, N1, N2, N3 form row 0 and N4, N5, N6, N7 form row 1, each row ordered column 0 to column 3. |
| 2 | +1 | States that directory placement option P1 puts directory bank D0 at node N0 and D1 at node N7. |
| 3 | +1 | States that directory placement option P2 puts directory bank D0 at node N1 and D1 at node N6. |
| 4 | +1 | States that directory placement option P3 puts directory bank D0 at node N3 and D1 at node N4. |
| 5 | +1 | States that directory placement option P4 puts directory bank D0 at node N2 and D1 at node N5. |
| 6 | +1 | States the latency of the link between N0 and N1 as 1 cycle. |
| 7 | +1 | States the latency of the link between N1 and N2 as 2 cycles. |
| 8 | +1 | States the latency of the link between N2 and N3 as 1 cycle. |
| 9 | +1 | States the latency of the link between N4 and N5 as 2 cycles. |
| 10 | +1 | States the latency of the link between N5 and N6 as 1 cycle. |
| 11 | +1 | States the latency of the link between N6 and N7 as 3 cycles. |
| 12 | +1 | States the latency of the link between N0 and N4 as 1 cycle. |
| 13 | +1 | States the latency of the link between N1 and N5 as 3 cycles. |
| 14 | +1 | States the latency of the link between N2 and N6 as 1 cycle. |
| 15 | +1 | States the latency of the link between N3 and N7 as 2 cycles. |

## Package (16-17, weight 2)

| # | Wt | Criterion |
| --- | --- | --- |
| 16 | +1 | Records the exact language and runtime version used (for example "Python 3.11.8"), not just the language name. |
| 17 | +1 | Gives concrete commands that rerun its simulator and its checker to reproduce the reported results. |

## Baseline run: placement P1, Q = 2, B = 2 (18-21, weight 18)

| # | Wt | Criterion |
| --- | --- | --- |
| 18 | +6 | Reports the baseline configuration's (placement P1, Q = 2, B = 2) makespan as exactly 685 cycles. |
| 19 | +4 | Reports the baseline configuration's (placement P1, Q = 2, B = 2) p95 load miss latency as exactly 44 cycles. |
| 20 | +4 | Reports the baseline configuration's (placement P1, Q = 2, B = 2) total messages created as exactly 886. |
| 21 | +4 | Reports the baseline configuration's (placement P1, Q = 2, B = 2) Nack count as exactly 38. |

## Whole sweep (22-25, weight 25)

| # | Wt | Criterion |
| --- | --- | --- |
| 22 | +8 | Reports the sum of makespan over all 64 configurations (P1 to P4, Q 1 to 4, B 1, 2, 4, 8) as exactly 43,328. |
| 23 | +8 | Reports the sum of messages created over all 64 configurations (P1 to P4, Q 1 to 4, B 1, 2, 4, 8) as exactly 56,774. |
| 24 | +8 | Reports the sum of Nacks over all 64 configurations (P1 to P4, Q 1 to 4, B 1, 2, 4, 8) as exactly 2,669. |
| 25 | +1 | Delivers a sweep CSV with exactly 64 data rows, one for each combination of placement P1 to P4, Q 1 to 4 and B 1, 2, 4, 8. |

## Selections (26-29, weight 24)

| # | Wt | Criterion |
| --- | --- | --- |
| 26 | +8 | Identifies the Fastest configuration (smallest makespan; ties by p95, messages, placement, Q, B) as placement P2, Q = 4, B = 1. |
| 27 | +4 | Reports the Fastest configuration's (placement P2, Q = 4, B = 1) makespan as exactly 586 cycles. |
| 28 | +8 | Identifies the Leanest configuration (fewest messages among makespan at most 640; ties by makespan, placement, Q, B) as placement P2, Q = 4, B = 4. |
| 29 | +4 | Reports the Leanest configuration's (placement P2, Q = 4, B = 4) message count as exactly 795. |

## Gain decomposition (30-31, weight 8)

| # | Wt | Criterion |
| --- | --- | --- |
| 30 | +4 | Reports the makespan of placement P2 with Q = 2, B = 2 (placement changed alone from the baseline) as exactly 635 cycles. |
| 31 | +4 | Reports the makespan of placement P1 with Q = 4, B = 1 (Q and B changed alone from the baseline) as exactly 690 cycles. |

## Checker (32-33, weight 2)

| # | Wt | Criterion |
| --- | --- | --- |
| 32 | +1 | The checker's recorded output reports that in the baseline trace no cycle has two caches holding the same line in state M. |
| 33 | +1 | The checker's recorded output reports that in the baseline trace every load returned the value of the most recent store to its line. |

## Memo reasoning (34-38, weight 7)

| # | Wt | Criterion |
| --- | --- | --- |
| 34 | +2 | The memo attributes the placement gain to P2's directory nodes N1 and N6 being fewer link cycles from the cores than P1's corner nodes N0 and N7. |
| 35 | +2 | The memo states that changing only Q and B to the Fastest's values (Q = 4, B = 1) while keeping placement P1 does not beat the baseline's makespan. |
| 36 | +1 | The memo states that the sweep's total Nacks fall as Q rises from 1 to 4. |
| 37 | +1 | The memo states that the sweep's total Nacks fall as B rises from 1 to 8. |
| 38 | +1 | The memo states that a larger B does not always shorten the makespan. |

## Negative criteria (39-41)

| # | Wt | Criterion |
| --- | --- | --- |
| 39 | -10 | Uses a third party package or external tool (for example NumPy, SimPy, NetworkX, gem5) to compute any simulation result. |
| 40 | -5 | The checker imports, calls or copies code from the simulator instead of being separately coded. |
| 41 | -5 | Presents a sweep with fewer than 64 configurations (P1 to P4, Q 1 to 4, B 1, 2, 4, 8) as the complete sweep. |

## Reverse coverage

| Prompt requirement | Criteria |
|---|---|
| State node layout, placement options, link latencies read from figures | 1-15 |
| Simulator, standard library only, offline | 18-31, 39 |
| Runtime version, reproduction commands | 16-17 |
| Baseline makespan, p95, messages, Nacks | 18-21 |
| 64-row CSV | 25, 41 |
| Sums of makespan, messages, Nacks | 22-24 |
| Fastest and Leanest with makespan / message count | 26-29 |
| Separate checker, two invariants reported | 32-33, 40 |
| Memo: P2/2/2 and P1/4/1 makespans | 30-31 |
| Memo: explain what each shows, why placement matters | 34-35 |
| Memo: Nacks vs Q, Nacks vs B | 36-37 |
| Memo: whether larger B always shortens makespan | 38 |

## Reviewer-feedback audit

| Past reviewer finding | Status here |
|---|---|
| Expected value a correct answer can never reach / unstated rule | Reference implements only packet rules (clause-by-clause check); expected values are its outputs. An isolated blind probe on the packet is the final check before any real pilot. |
| Prompt explanation with no criterion | Every memo requirement mapped above (34-38). |
| Mechanism description bundled with a trace value | None: no criterion pairs a rule with a value. |
| Several constants in one criterion | Each placement option and each link latency is its own criterion. |
| Metric the packet never defines | All graded metrics are defined in packet Section 8; trace format is free and not graded. |

Atomicity and self-containment check (after writing): every criterion
tests one value, one claim or one requirement, names its configuration in
full, and states its expected answer.
