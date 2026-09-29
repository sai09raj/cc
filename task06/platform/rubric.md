# ATRIUM-9 rubric

Positive total **281**; six negative criteria totaling **-28** (**-8**,
**-5**, **-4**, **-4**, **-4**, **-3** — see the two negative sections
below). Exactly **50 criteria** (the platform maximum; not padded — see
`07-MISTAKE-REGISTER.md` #38). Every weight is capped at 10 (the
platform's per-criterion maximum). Criteria are binary. Accept equivalent
correct work throughout: equivalent languages, source organization,
output schemas, file layout, and formula notation.

This revision responds to two rounds of platform-linter feedback.
Round 1: criterion 16 (agree/diverge disclosure) was reworded to remove
ambiguous "must be compared as equal" framing; two "must never"
prohibitions (verifier independence; reassigned-away non-reuse) that were
previously positive-only got dedicated negative criteria. Round 2: three
more prompt-stated prohibitions were found uncovered (no free per-tick
search/optimization in place of the fixed policy; no bouncing between
equally-good cars; no shortened/sampled sweep runs) and given dedicated
negatives too. To stay at exactly 50 criteria across both rounds, several
same-mechanism local-semantics pairs were merged further and the
reconciliation criterion (which had become largely tautological once
criteria 13-15 already grade the selection value against a known-correct
reference) was dropped.

Score-topology floor: even a mutant that failed every single discriminating
criterion in this rubric would still earn a low-double-digit percentage
from package, core local semantics, selections, W1, and verifier-delivery
checks — things any competent submission gets right regardless of which
one mechanism it breaks. See `score-topology.md` for the counterfactual
evidence this weighting is built from.

### Package (1-2, weight 3)

| # | Wt | Criterion |
| --- | --- | --- |
| 1 | +2 | Executes the delivered offline simulator with a documented, reproducible command in a declared offline, stdlib-only environment, and delivers all six named products as accessible files (simulator, verifier, sweep table, decision file, certification evidence, memo). |
| 2 | +1 | The delivered sweep table contains exactly 144 unique legal `(active_cars, zoning, wait_timeout, power_budget)` rows, no duplicate, no missing combination. |

### Local semantics/rules/scaffolding (3-12, weight 26)

| # | Wt | Criterion |
| --- | --- | --- |
| 3 | +2 | Generates the 80-call workload from the packet's formulas: `origin=(3*group+2*s) mod 8` with `group=k//3`; direction UP at floor 0, DOWN at floor 7, else by `(group+s)` parity; `arrival=200*s+8*k`; destination via the stated span formula, revealed only at boarding. |
| 4 | +2 | Uses the zoning home-floor table (SPLIT=(0,2,5,7), GROUND=(0,0,0,0), TOP=(7,7,7,7) for cars A,B,C,D) AND puts only the lowest-ID `ACTIVE_CARS` cars into service; an inactive car never moves and is never eligible. |
| 5 | +3 | Hall-call eligibility: idle car eligible for any call at distance-based cost; a scanning car eligible only for a call in its OWN current direction still ahead of its position (no mid-scan backtracking); ties broken by lowest car ID. |
| 6 | +2 | Tracks each car's commitments SEPARATELY per direction; boarding only serves calls matching the SPECIFIC direction currently being scanned. |
| 7 | +1 | A car re-derives its next action fresh each decision: continues its scan direction only while a commitment remains ahead, else switches to the nearer remaining commitment. |
| 8 | +1 | Uses the stated timing constants: `T_DOOR_OPEN=2`, `T_DWELL=3`, `T_DOOR_CLOSE=2`, `T_FLOOR=4` per floor. |
| 9 | +2 | Boards, atomically at the first DWELL tick, every waiting call matching direction at that floor (ascending call-index, up to capacity 6), then alights every boarded call whose destination is the current floor, freeing capacity immediately. |
| 10 | +10 | Admits power in one ordered pass per tick, car priority A,B,C,D (mandatory draws first, new events from what remains, a refusal defers rather than errors) AND treats DWELL-to-CLOSING as its own power-gated event, not automatic. |
| 11 | +1 | Energy per moving tick is `3+load` UP, `3-load` DOWN (regenerative credit for a loaded descent). |
| 12 | +3 | Triggers timeout re-evaluation at `WAIT_TIMEOUT` age AND reassigns only when a strictly cheaper alternative exists (never bounces between equally-good cars; a reassigned-away call is never later served by that car). |

### Integrated production execution — exhaustive sweep (13-19, weight 20)

| # | Wt | Criterion |
| --- | --- | --- |
| 13 | +2 | Reports wait-optimal as `(active_cars=4, zoning=SPLIT, wait_timeout=50, power_budget=6)`, `avg_wait=8.1375` (±0.01), `net_energy=4116`. |
| 14 | +2 | Reports energy-optimal as `(active_cars=2, zoning=TOP, wait_timeout=50, power_budget=6)`, `avg_wait=34.2875` (±0.01), `net_energy=2676`. |
| 15 | +2 | Reports budget-constrained (min `avg_wait` s.t. `net_energy<=3800`) as `(active_cars=2, zoning=SPLIT, wait_timeout=50, power_budget=6)`, `avg_wait=21.70` (±0.01), `net_energy=2796`. |
| 16 | +1 | Reports explicitly, for each pair among the three selections in criteria 13-15, whether it agrees (identical configuration) or diverges (different configuration); this packet's reference has all three diverge — the criterion tests the disclosure, not agreement itself. |
| 17 | +4 | Reports `(2,TOP,50,6)`'s own row as `avg_wait=34.2875, net_energy=2676`. |
| 18 | +4 | Reports `(4,GROUND,75,8)`'s row as `avg_wait=11.9625, net_energy=4428`. |
| 19 | +4 | Reports `(4,GROUND,75,6)`'s row as `avg_wait=12.4000, net_energy=4380`. |

### Whole-sweep aggregate totals (20-32, weight 130)

Each total sums one or two metrics across a stated subset of the 144-row
sweep (the whole table for 20-22, a stated filter for 23-32). Report to
the stated tolerance. Each of these 13 facts is wrong under every
plausible-wrong mutant tested — the rubric's main discriminating bloc.

| # | Wt | Criterion |
| --- | --- | --- |
| 20 | +10 | Reports the total number of genuine reassignments summed across all 144 configs as `43`. |
| 21 | +10 | Reports the sum of `net_energy` across all 144 configs as `547080`. |
| 22 | +10 | Reports the sum of `avg_wait` across all 144 configs as `2739.8125` (±0.05). |
| 23 | +10 | Summed over only `active_cars=4` (48 rows): `avg_wait` totals `595.6625` (±0.05), `net_energy` totals `222024`. |
| 24 | +10 | Summed over only `zoning=GROUND` (48 rows): `avg_wait` totals `884.4875` (±0.05), `net_energy` totals `180000`. |
| 25 | +10 | Summed over only `zoning=TOP` (48 rows): `avg_wait` totals `1071.15` (±0.05), `net_energy` totals `183072`. |
| 26 | +10 | Summed over only `wait_timeout=50` (36 rows): `avg_wait` totals `693.65` (±0.05), `net_energy` totals `136440`. |
| 27 | +10 | Summed over only `wait_timeout=75` (36 rows): `avg_wait` totals `682.25` (±0.05), `net_energy` totals `136464`. |
| 28 | +10 | Summed over only `power_budget=6` (36 rows): `avg_wait` totals `687.8875` (±0.05), `net_energy` totals `134664`. |
| 29 | +10 | Summed over only `active_cars=4 AND zoning=GROUND` (12 rows): `avg_wait` totals `191.7875` (±0.05), `net_energy` totals `73248`. |
| 30 | +10 | Summed over only `active_cars=4 AND zoning=TOP` (12 rows): `avg_wait` totals `229.05` (±0.05), `net_energy` totals `75648`. |
| 31 | +10 | Summed over only `zoning=TOP AND power_budget=6` (12 rows): `avg_wait` totals `272.2875` (±0.05), `net_energy` totals `45552`. |
| 32 | +10 | Summed over only `zoning=TOP AND wait_timeout=50` (12 rows): `avg_wait` totals `286.9375` (±0.05), `net_energy` totals `45672`. |

### Production witnesses from the baseline trace (33-41, weight 89)

Baseline configuration for 33-35 and the hash: `(active_cars=3, zoning=TOP,
wait_timeout=50, power_budget=8, capacity=6)`.

| # | Wt | Criterion |
| --- | --- | --- |
| 33 | +9 | Shows two cars scanning genuinely different directions at the same tick early in the run (by `t=28`: car A UP/OPENING at floor 0, car B DOWN/DWELL at floor 3). |
| 34 | +10 | Shows call `gidx=15` alighting at exactly `t=200` (cross-campaign overlap) AND call `gidx=5` reassigned exactly once, to car C at `t=91`, boarding `t=94`. |
| 35 | +10 | Shows call `gidx=19` (floor 2, UP, arrival `t=152`) assigned ONCE, at `t=243` to car A, boarding `t=248` (attempt stays 1) — switching on timeout expiry alone would delay it to `t=265`. |
| 36 | +10 | Shows, in `(4,GROUND,50,6)`: some tick in `t=24`-`t=59` draws exactly 6 power, and power never exceeds 6 anywhere in the run. |
| 37 | +10 | Shows call `gidx=26` (floor 0, UP, arrival `t=248`) boards at exactly `t=278`, assigned to car B (attempt stays 1). |
| 38 | +10 | Shows call `gidx=27` (floor 0, UP, arrival `t=256`) boards at exactly `t=302`, assigned to car C (attempt stays 1). |
| 39 | +10 | Shows, in `(4,SPLIT,50,6)`: drawn power never exceeds 6 anywhere in the run. |
| 40 | +10 | Shows, in `(4,TOP,50,6)`: drawn power never exceeds 6 anywhere in the run. |
| 41 | +10 | Matches the first 16 hex chars of the baseline's trace-integrity hash to `f544b2d2a1d0fb30`. |

### Independent verification and decision/causal reconciliation (42-44, weight 13)

| # | Wt | Criterion |
| --- | --- | --- |
| 42 | +3 | Delivers a separately-coded verifier, sharing only immutable input constants with the primary, that re-derives the call table, checks a feasibility certificate or re-simulates the baseline trace, and rejects both adversarial mutations, with the original preserved and accepted. |
| 43 | +8 | Explains, citing the baseline trace's own numbers, why wait-optimal and energy-optimal diverge and what budget-constrained trades away, AND explains, citing a concrete tick/car pair, a power-budget delay and why treating DWELL-to-CLOSING as automatic would understate it. |
| 44 | +2 | Explains why a reassigned-away call must never later be served by that car, tied to the concrete failure (double-served passenger, phantom stop). |

### Negative criteria — verifier and reassignment prohibitions (45-46)

| # | Wt | Criterion |
| --- | --- | --- |
| 45 | −4 | Delivers a verifier that shares anything beyond immutable input constants with the primary implementation (importing or wrapping its internal state, classes, or in-memory objects) rather than independently re-deriving the call table and trace or certificate. |
| 46 | −4 | Simulator logic allows a call reassigned away from a car to later be boarded or served again by that same car, rather than permanently excluding it from that car's future assignments. |

### Negative criteria — architecture and execution prohibitions (47-49)

| # | Wt | Criterion |
| --- | --- | --- |
| 47 | −4 | Implements hall-call assignment, commitment scanning, or reassignment as a per-tick search or optimization computed fresh each tick, rather than the packet's fixed, deterministic policy (there is no free scheduling choice at the per-tick level). |
| 48 | −3 | Reassigns a call to an alternative car whose cost is equal to (not strictly less than) the incumbent's, or reassigns the same call back and forth between two equally-good cars over time. |
| 49 | −5 | Runs any of the 144 legal configurations as a shortened, truncated, or sampled subset of its 80 calls rather than one continuous run to completion. |

### Negative trap (50)

| # | Wt | Criterion |
| --- | --- | --- |
| 50 | −8 | Embeds precomputed sweep rows, selection values, or the trace-integrity hash as literals substituting for executing the delivered simulator. Immutable input constants don't trigger this; omission alone doesn't either. |
