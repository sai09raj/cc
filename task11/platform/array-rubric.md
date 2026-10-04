# ARRAY-11 rubric (v2)

Positive total **106**; four negative criteria (-10, -8, -6, -5). **41
criteria** (within the platform's 12-50 range). Every weight is capped at
10. Every criterion body is 301 characters or fewer. Criteria are binary
and each checks one fact or one requirement. Accept equivalent correct
work throughout: any language, any source organization, any layout and
table format that carries the same facts. Costs may be written with or
without thousands separators.

Every expected value is derivable from the packet as written. Platform
positions and the cable catalogue are read from the figures (the pilot
measured all eight values exactly by pixel position). Minimum costs are
certified: capacity-indexed CP-SAT with status OPTIMAL and bound equal to
cost, every cost recomputed by a separate standard-library checker
(`opt-prototype/scen64-*-certification.txt`). Optimal layouts need not be
unique, so no criterion grades a layout's structure or a feeder count
value; feeder counts and bounds are graded for presence and validity
only.

## Score topology

| Bucket | Criteria | Points | Needs an optimum? |
|---|---|---|---|
| Values read from the figures | 1-8 | 10 | no |
| Package | 9-12 | 4 | no |
| Independent checker | 13-16 | 7 | no |
| Lower bounds | 17-23 | 8 | no |
| Memo reasoning | 24-28 | 7 | no |
| Exact minimum costs | 29-33 | 50 | yes, one each |
| Cost differences | 34-37 | 20 | yes, two each |

A complete, valid submission that finds no optimum earns at most 36/106
(34%).

## Values read from the figures (1-8, weight 10)

| # | Wt | Criterion |
| --- | --- | --- |
| 1 | +2 | States the primary platform P position, read from the site plan, as (3200, 3000) metres. |
| 2 | +2 | States the alternative platform A position, read from the site plan, as (-700, 2700) metres. |
| 3 | +1 | States cable type C1's capacity, read from the catalogue chart, as 4 turbines. |
| 4 | +1 | States cable type C2's capacity, read from the catalogue chart, as 8 turbines. |
| 5 | +1 | States cable type C3's capacity, read from the catalogue chart, as 14 turbines. |
| 6 | +1 | States cable type C1's price, read from the catalogue chart, as 100 per metre. |
| 7 | +1 | States cable type C2's price, read from the catalogue chart, as 160 per metre. |
| 8 | +1 | States cable type C3's price, read from the catalogue chart, as 245 per metre. |

## Package (9-12, weight 4)

| # | Wt | Criterion |
| --- | --- | --- |
| 9 | +1 | Records the exact language and runtime version used (for example "Python 3.11.8"), not just the language name. |
| 10 | +1 | Gives concrete commands that reproduce its reported results. |
| 11 | +1 | Delivers a layout file for each of the five scenarios S1 to S5 that lists every cable with both endpoints and its cable type. |
| 12 | +1 | Reports a number of feeders used (cables ending at the platform) for each of the five scenarios S1 to S5. |

## Independent checker (13-16, weight 7)

| # | Wt | Criterion |
| --- | --- | --- |
| 13 | +1 | The checker's recorded output accepts all five of the submission's own S1 to S5 layouts. |
| 14 | +2 | The checker's recorded output rejects the broken S1 layout in which two cables cross, naming the crossing rule as the reason. |
| 15 | +2 | The checker's recorded output rejects the broken S1 layout in which a cable's type has capacity below its load, naming the capacity rule as the reason. |
| 16 | +2 | The checker's recorded output rejects the broken S1 layout with a turbine to turbine cable over 1300 metres, naming the span limit as the reason. |

## Lower bounds (17-23, weight 8)

A lower bound is valid when it does not exceed the scenario's true
minimum; the minimum is stated in each criterion so it is self-contained.

| # | Wt | Criterion |
| --- | --- | --- |
| 17 | +1 | Reports a lower bound for S1 (platform P, all cable types, 6 feeder bays) that does not exceed S1's true minimum cost of 5,878,715. |
| 18 | +1 | Reports a lower bound for S2 (platform P, all cable types, 5 feeder bays) that does not exceed S2's true minimum cost of 5,921,875. |
| 19 | +1 | Reports a lower bound for S3 (platform P, cable types C2 and C3 only, 6 feeder bays) that does not exceed S3's true minimum cost of 8,075,675. |
| 20 | +1 | Reports a lower bound for S4 (platform A, all cable types, 6 feeder bays) that does not exceed S4's true minimum cost of 7,480,955. |
| 21 | +1 | Reports a lower bound for S5 (platform A, all cable types, 5 feeder bays) that does not exceed S5's true minimum cost of 7,516,700. |
| 22 | +2 | Describes the method used to obtain its lower bounds (for example an LP relaxation, a Lagrangian relaxation, or branch and bound). |
| 23 | +1 | Reports for each scenario a gap equal to that scenario's reported cost minus its reported lower bound (a percentage of the same difference is also accepted). |

## Memo reasoning (24-28, weight 7)

| # | Wt | Criterion |
| --- | --- | --- |
| 24 | +1 | The memo attributes the cost rise from S1 to S2 (platform P, 6 to 5 feeder bays) to turbines having to be merged onto fewer, more heavily loaded feeders. |
| 25 | +1 | The memo attributes the cost rise from S4 to S5 (platform A, 6 to 5 feeder bays) to turbines having to be merged onto fewer, more heavily loaded feeders. |
| 26 | +2 | The memo attributes the cost rise from S1 to S3 (cable type C1 removed) to cables carrying 4 or fewer turbines having to use the 160 per metre type instead of the 100 per metre type. |
| 27 | +2 | The memo attributes the cost rise from S1 to S4 (platform P moved to platform A) to platform A lying at the edge of the field (or outside it), far from most turbines, so cables must run much farther to reach it. |
| 28 | +1 | The memo reports a cost for a simple greedy S1 layout that is higher than the submission's own reported S1 cost. |

## Exact minimum costs (29-33, weight 50)

| # | Wt | Criterion |
| --- | --- | --- |
| 29 | +10 | Reports the S1 cost (platform P, all cable types, 6 feeder bays) as exactly 5,878,715. |
| 30 | +10 | Reports the S2 cost (platform P, all cable types, 5 feeder bays) as exactly 5,921,875. |
| 31 | +10 | Reports the S3 cost (platform P, cable types C2 and C3 only, 6 feeder bays) as exactly 8,075,675. |
| 32 | +10 | Reports the S4 cost (platform A, all cable types, 6 feeder bays) as exactly 7,480,955. |
| 33 | +10 | Reports the S5 cost (platform A, all cable types, 5 feeder bays) as exactly 7,516,700. |

## Cost differences (34-37, weight 20)

| # | Wt | Criterion |
| --- | --- | --- |
| 34 | +5 | The memo states that losing one feeder bay at platform P (S2 against S1) costs exactly 43,160. |
| 35 | +5 | The memo states that losing one feeder bay at platform A (S5 against S4) costs exactly 35,745. |
| 36 | +5 | The memo states that removing cable type C1 (S3 against S1) costs exactly 2,196,960. |
| 37 | +5 | The memo states that moving from platform P to platform A (S4 against S1) costs exactly 1,602,240. |

## Negative criteria (38-41)

| # | Wt | Criterion |
| --- | --- | --- |
| 38 | -10 | Uses a third party package or external solver (for example OR-Tools, PuLP, SciPy, NetworkX, Gurobi, CBC, HiGHS) to compute any layout, cost or bound. |
| 39 | -8 | Calls a scenario cost optimal or proven optimal while it exceeds that scenario's true minimum: S1 5,878,715; S2 5,921,875; S3 8,075,675; S4 7,480,955; S5 7,516,700. |
| 40 | -6 | Reports a layout cost below the true minimum for any scenario (S1 5,878,715; S2 5,921,875; S3 8,075,675; S4 7,480,955; S5 7,516,700), which no valid layout can achieve. |
| 41 | -5 | The checker imports, calls or copies code from the optimizer instead of being separately coded. |

## Reverse coverage (every prompt requirement has a criterion)

| Prompt requirement | Criteria |
|---|---|
| State platform positions and cable values read from the figures | 1-8 |
| Minimum cost layout per scenario, exact integer cost | 29-33, 40 |
| Feeders used per scenario | 12 |
| Every cable with endpoints and type | 11 |
| Lower bound per scenario | 17-21 |
| How the bound was obtained | 22 |
| Gap per scenario | 23 |
| "Proven optimal" only when bound equals cost | 39 |
| Standard library only, offline | 38 |
| Runtime version, reproduction commands | 9-10 |
| Separate checker sharing no code | 41 |
| Checker accepts five layouts | 13 |
| Checker rejects three broken layouts with the rule | 14-16 |
| Results table (cost, feeders, bound, gap) | 12, 17-23, 29-33 |
| Memo: amount of each of the four changes | 34-37 |
| Memo: cause of each of the four changes | 24-27 |
| Memo: greedy comparison | 28 |

## Reviewer-feedback audit

| Past reviewer finding | Status in this rubric |
|---|---|
| Expected value a correct answer can never reach | Every value is certified or read from the figures; the pilot measured all eight figure values exactly and its five layouts recompute exactly under the author checker. |
| Prompt requirement with no criterion | Reverse coverage table above: every requirement mapped. |
| Mechanism description bundled with a value probe | None: each criterion is either one value, one explanation, or one requirement. |
| Several constants bundled in one criterion | Catalogue split into six single-value criteria; each platform position is one (x, y) point. |
| Metric the packet never defines | "Feeders used" is defined in the prompt (cables ending at the platform); "gap" is defined in the prompt and criterion 23; lower bound validity is stated against the certified minimum. No arbitrary quality threshold on bounds. |
| Prompt and rubric disagree | The prompt asks the memo to state how much each change costs; criteria 34-37 grade those amounts. |
| Correct answer phrased differently fails | Memo criteria grade the cause, not wording; criterion 27 accepts "edge" or "outside" the field; gap accepted as amount or percentage. |

Atomicity and self-containment check (done after writing): each of the 41
criteria tests exactly one value, one explanation, or one requirement;
each names its scenario by platform, cable types and bays where a
scenario is involved, and states the expected number in full, so it can
be graded without reading any other criterion.
