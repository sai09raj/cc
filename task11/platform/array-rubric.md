# ARRAY-11 rubric (v1)

Positive total **96**; four negative criteria (-10, -8, -6, -5). **29
criteria** (within the platform's 12-50 range). Every weight is capped at
10. Every criterion body is 301 characters or fewer. Criteria are binary.
Accept equivalent correct work throughout: any language, any source
organization, any layout and table format that carries the same facts.
Costs may be written with or without thousands separators.

Optimal layouts need not be unique, so no criterion grades a layout's
structure; the graded facts are the certified minimum costs and the
differences between them. Certification: capacity-indexed CP-SAT
(status OPTIMAL, bound equal to cost) with every cost recomputed by a
separate standard-library checker, plus a second, zero-gap SCIP run
(`opt-prototype/scen64-*-certification.txt`).

## Score topology

| Bucket | Criteria | Points | Needs an optimum? |
|---|---|---|---|
| Measurement and package | 1-6 | 9 | no |
| Independent checker | 7-10 | 7 | no |
| Lower bounds | 11-12 | 4 | no |
| Memo reasoning | 13-16 | 6 | no |
| Exact minimum costs | 17-21 | 50 | yes, one each |
| Cost differences | 22-25 | 20 | yes, two each |

Everything a strong run can earn without finding an optimum is 26/96
(27%). The `opus` probe on the 64-turbine set (`audit/probe-3-opus-cable64/`)
found valid layouts within 0.37% to 4.83% of every optimum, valid bounds,
and no optimum: it sits in that 27% band. A run that finds two optima
with no shared difference (for example S2 and S3) reaches 46/96 (47.9%).
A run must find at least two optima that form a difference pair, or
three optima, to pass 50%. That is the intended line: finding the
minimum is the task.

## Measurement and package (1-6, weight 9)

| # | Wt | Criterion |
| --- | --- | --- |
| 1 | +2 | States the primary platform P position, read from the site plan, as (3200, 3000) metres. |
| 2 | +2 | States the alternative platform A position, read from the site plan, as (-700, 2700) metres. |
| 3 | +1 | States the cable capacities read from the catalogue chart as 4 turbines for C1, 8 for C2 and 14 for C3. |
| 4 | +2 | States the cable prices per metre read from the catalogue chart as 100 for C1, 160 for C2 and 245 for C3. |
| 5 | +1 | Records the exact language and runtime version used (for example "Python 3.11.8"), not just the language name. |
| 6 | +1 | Gives concrete commands that rerun its optimizer and its checker to reproduce the reported results. |

## Independent checker (7-10, weight 7)

| # | Wt | Criterion |
| --- | --- | --- |
| 7 | +1 | The checker's recorded output accepts all five of the submission's own S1 to S5 layouts. |
| 8 | +2 | The checker's recorded output rejects the broken S1 layout in which two cables cross, citing the crossing rule. |
| 9 | +2 | The checker's recorded output rejects the broken S1 layout in which a cable's type has capacity below its load, citing the capacity rule. |
| 10 | +2 | The checker's recorded output rejects the broken S1 layout with a turbine to turbine cable over 1300 metres, citing the span limit. |

## Lower bounds (11-12, weight 4)

| # | Wt | Criterion |
| --- | --- | --- |
| 11 | +2 | Reports a lower bound for S1 (platform P, all cable types, 6 bays) that is at least 5,643,567 and at most 5,878,715. |
| 12 | +2 | Reports a lower bound for S4 (platform A, all cable types, 6 bays) that is at least 7,181,717 and at most 7,480,955. |

## Memo reasoning (13-16, weight 6)

| # | Wt | Criterion |
| --- | --- | --- |
| 13 | +2 | The memo attributes the S3 cost rise over S1 to cables carrying 4 or fewer turbines, which make up most of the cable length, having to use the 160 per metre type instead of the 100 per metre type. |
| 14 | +2 | The memo attributes the S4 cost rise over S1 to platform A lying at the western edge of the field rather than near its centre, so feeders and heavily loaded cables must run much farther. |
| 15 | +1 | The memo attributes the S2 cost rise over S1 to the turbines having to be merged onto fewer, more heavily loaded feeders when one bay is lost. |
| 16 | +1 | The memo reports a cost for a simple greedy S1 layout that is higher than the submission's own reported S1 cost. |

## Exact minimum costs (17-21, weight 50)

| # | Wt | Criterion |
| --- | --- | --- |
| 17 | +10 | Reports the S1 cost (platform P, all cable types, 6 feeder bays) as exactly 5,878,715. |
| 18 | +10 | Reports the S2 cost (platform P, all cable types, 5 feeder bays) as exactly 5,921,875. |
| 19 | +10 | Reports the S3 cost (platform P, cable types C2 and C3 only, 6 feeder bays) as exactly 8,075,675. |
| 20 | +10 | Reports the S4 cost (platform A, all cable types, 6 feeder bays) as exactly 7,480,955. |
| 21 | +10 | Reports the S5 cost (platform A, all cable types, 5 feeder bays) as exactly S5_COST. |

## Cost differences (22-25, weight 20)

| # | Wt | Criterion |
| --- | --- | --- |
| 22 | +5 | States that losing one feeder bay at platform P (S2 against S1) costs exactly 43,160. |
| 23 | +5 | States that removing cable type C1 (S3 against S1) costs exactly 2,196,960. |
| 24 | +5 | States that moving to platform A (S4 against S1) costs exactly 1,602,240. |
| 25 | +5 | States that losing one feeder bay at platform A (S5 against S4) costs exactly S5_DIFF. |

## Negative criteria (26-29)

| # | Wt | Criterion |
| --- | --- | --- |
| 26 | -10 | Uses a third party package or external solver (for example OR-Tools, PuLP, SciPy, NetworkX, Gurobi, CBC, HiGHS) to compute any layout, cost or bound. |
| 27 | -8 | Calls a scenario cost optimal or proven optimal while it exceeds that scenario's minimum: S1 5,878,715; S2 5,921,875; S3 8,075,675; S4 7,480,955; S5 S5_COST. |
| 28 | -6 | Reports a cost below the true minimum for any scenario (S1 5,878,715; S2 5,921,875; S3 8,075,675; S4 7,480,955; S5 S5_COST), which no valid layout can achieve. |
| 29 | -5 | The checker imports, calls or copies code from the optimizer instead of being separately coded. |

## Reverse coverage

| Prompt requirement | Criteria |
|---|---|
| Read and state platform positions and catalogue | 1-4 |
| Minimum cost layout per scenario, exact integer cost | 17-21, 28 |
| Feeders used, every cable listed | not graded separately (optima not unique); layout files feed 7 and 28 |
| Lower bound, method, gap; "proven optimal" only when bound equals cost | 11-12, 27 |
| Standard library only, offline | 26 |
| Runtime version, reproduction commands | 5-6 |
| Separate checker, five accepts, three rejects | 7-10, 29 |
| Memo: bay loss at each platform | 15, 22, 25 |
| Memo: removing smallest type | 13, 23 |
| Memo: alternative platform | 14, 24 |
| Memo: greedy comparison | 16 |
