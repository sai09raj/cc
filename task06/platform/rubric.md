# ATRIUM-9 rubric

Positive total **280**; one negative trap **-8**. Criteria are binary, and
**every criterion is capped at weight 10** (the platform's per-criterion
maximum). Accept equivalent correct work throughout: equivalent languages,
source organization, output schemas, file layout, and formula notation. No
hidden filename/schema requirements.

Because no single criterion can carry outsized weight, this rubric's
discriminating power comes from a LARGER NUMBER of small, independent,
whole-sweep aggregate facts (criteria 31-41: three grand totals plus eight
partial sums, each restricted to one or two sweep dimensions) rather than
from one or two heavy witnesses. Each of these eleven aggregate criteria is
wrong under every plausible-wrong mutant tested, so together they form the
rubric's main discriminating bloc; see `score-topology.md` for the
counterfactual evidence.

### Package (criteria 1-3, weight 3)

1. **+1** — Executes the delivered offline simulator with a documented
   command that generates the submitted sweep/decision results, and records
   the actual tool versions used, in a declared offline, stdlib-only
   environment; equivalent languages and source organization pass.
2. **+1** — Delivers all six named products as accessible files: simulator
   source, verifier source, the 144-row sweep table, a decision file with
   all three selections, certification evidence (baseline trace + hash +
   adversarial-mutation results), and an engineering memo.
3. **+1** — The delivered sweep table contains exactly 144 rows, one per
   legal `(active_cars, zoning, wait_timeout, power_budget)` combination,
   with no duplicate and no missing combination.

### Local semantics/rules/scaffolding (criteria 4-18, weight 27)

4. **+2** — Generates the 80-call workload from the packet's formulas:
   `origin=(3*group+2*s) mod 8` with `group=k//3`, direction UP at floor 0,
   DOWN at floor 7, else by `(group+s)` parity; `arrival=200*s+8*k`;
   destination via the stated span formula, revealed only at boarding.
5. **+1** — Uses the zoning home-floor table: SPLIT=(0,2,5,7),
   GROUND=(0,0,0,0), TOP=(7,7,7,7) for cars A,B,C,D respectively.
6. **+1** — Puts only the lowest-ID `ACTIVE_CARS` cars into service; an
   inactive car never moves and is never eligible for assignment.
7. **+2** — Hall-call eligibility: idle car eligible for any call at
   distance-based cost; a scanning car eligible only for a call in its OWN
   current direction that still lies ahead of its position, never behind
   (no mid-scan backtracking).
8. **+1** — Ties in the assignment-cost comparison broken by lowest car ID,
   not highest.
9. **+2** — Tracks each car's commitments SEPARATELY per direction (a floor
   needed while scanning up is a distinct commitment from the same floor
   needed while scanning down); boarding only serves calls matching the
   SPECIFIC direction currently being scanned.
10. **+1** — A car re-derives its next action fresh each decision: continues
    its current scan direction only while a commitment remains ahead in
    that direction, otherwise switches to the nearer remaining commitment.
11. **+1** — Uses the stated timing constants for one full door cycle:
    `T_DOOR_OPEN=2`, `T_DWELL=3`, `T_DOOR_CLOSE=2`, and `T_FLOOR=4` per
    floor traversed.
12. **+1** — Boards, atomically at the first DWELL tick, every waiting call
    matching the car's current direction at that floor, in ascending
    call-index order, up to capacity 6; boards deferred by capacity retry
    only at that car's next visit to that same stop.
13. **+1** — Alights, in the same atomic DWELL-start step, every boarded
    call whose destination is the current floor under the current
    direction, freeing capacity immediately.
14. **+5** — Admits power in one ordered pass per tick, car priority A, B,
    C, D: mandatory ongoing draws (mid-hop=2, mid-open-or-close=1) are
    honored first, then new events draw from what remains; a refusal
    defers that car's event to a later tick rather than erroring.
15. **+5** — Treats the DWELL-to-CLOSING transition as its own power-gated
    event, not automatic: a car whose dwell has elapsed stays in DWELL,
    drawing no power, until its door-close is itself admitted.
16. **+1** — Energy per moving tick is `3 + load` for UP and `3 - load` for
    DOWN (net regenerative credit for a loaded descent).
17. **+1** — Triggers timeout re-evaluation for any still-`assigned` call
    whose current assignment age reaches `WAIT_TIMEOUT` ticks.
18. **+2** — Reassigns only when a strictly cheaper alternative car exists
    at that tick (never bounces a call between equally-good cars); a call
    once reassigned away from a car is never later served by that car.

### Integrated production execution — exhaustive sweep (criteria 19-30, weight 28)

19. **+2** — Reports the wait-optimal selection as `(active_cars=4,
    zoning=SPLIT, wait_timeout=50, power_budget=6)` with `avg_wait=8.1375`
    (±0.01) and `net_energy=4116`.
20. **+2** — Reports the energy-optimal selection as `(active_cars=2,
    zoning=TOP, wait_timeout=50, power_budget=6)` with `avg_wait=34.2875`
    (±0.01) and `net_energy=2676`.
21. **+2** — Reports the budget-constrained selection (minimize `avg_wait`
    among configurations with `net_energy<=3800`) as `(active_cars=2,
    zoning=SPLIT, wait_timeout=50, power_budget=6)` with `avg_wait=21.70`
    (±0.01) and `net_energy=2796`.
22. **+2** — The delivered sweep table has exactly 144 unique legal
    `(active_cars, zoning, wait_timeout, power_budget)` tuples spanning the
    full Cartesian product `{2,3,4} x {SPLIT,GROUND,TOP} x {50,75,100,125}
    x {6,8,10,12}`.
23. **+1** — Confirms the three selections in criteria 19-21 need not agree
    (report explicitly whether each pair agrees or diverges) rather than
    silently reporting only one config as if it served all three.
24. **+4** — Reports `(active_cars=2, zoning=TOP, wait_timeout=50,
    power_budget=6)`'s own row as `avg_wait=34.2875, net_energy=2676`.
25. **+4** — Reports `(active_cars=4, zoning=GROUND, wait_timeout=75,
    power_budget=8)`'s row as `avg_wait=11.9625, net_energy=4428`.
26. **+4** — Reports `(active_cars=4, zoning=GROUND, wait_timeout=75,
    power_budget=6)`'s row as `avg_wait=12.4000, net_energy=4380`.
27. **+4** — Reports `(active_cars=2, zoning=GROUND, wait_timeout=125,
    power_budget=8)`'s row as `avg_wait=27.1625, net_energy=2772`.
28. **+1** — Reconciles the wait-optimal design's own row (criterion 19)
    against its position in the full sweep: no other legal configuration
    has a strictly lower `avg_wait`.
29. **+1** — Reconciles the energy-optimal design's own row (criterion 20)
    against its position in the full sweep: no other legal configuration
    has a strictly lower `net_energy`.
30. **+1** — Reconciles the budget-constrained design's own row (criterion
    21): every configuration with strictly lower `avg_wait` has
    `net_energy > 3800`.

### Whole-sweep aggregate totals (criteria 31-41, weight 110)

Each of these eleven totals is computed by summing one or two metrics
across a stated subset of the 144-row sweep table (the whole table for
31-33, a stated filter for 34-41). Report each to the stated tolerance.

31. **+10** — Reports the total number of genuine reassignments (S09)
    summed across all 144 sweep configurations as `43`.
32. **+10** — Reports the sum of `net_energy` across all 144 sweep
    configurations as `547080`.
33. **+10** — Reports the sum of `avg_wait` across all 144 sweep
    configurations as `2739.8125` (±0.05).
34. **+10** — Reports, summed over only the `active_cars=4` configurations
    (48 rows), `avg_wait` totaling `595.6625` (±0.05) and `net_energy`
    totaling `222024`.
35. **+10** — Reports, summed over only the `zoning=GROUND` configurations
    (48 rows), `avg_wait` totaling `884.4875` (±0.05) and `net_energy`
    totaling `180000`.
36. **+10** — Reports, summed over only the `zoning=TOP` configurations (48
    rows), `avg_wait` totaling `1071.15` (±0.05) and `net_energy` totaling
    `183072`.
37. **+10** — Reports, summed over only the `wait_timeout=50`
    configurations (36 rows), `avg_wait` totaling `693.65` (±0.05) and
    `net_energy` totaling `136440`.
38. **+10** — Reports, summed over only the `wait_timeout=75`
    configurations (36 rows), `avg_wait` totaling `682.25` (±0.05) and
    `net_energy` totaling `136464`.
39. **+10** — Reports, summed over only the `power_budget=6` configurations
    (36 rows), `avg_wait` totaling `687.8875` (±0.05) and `net_energy`
    totaling `134664`.
40. **+10** — Reports, summed over only `active_cars=4 AND zoning=GROUND`
    configurations (12 rows), `avg_wait` totaling `191.7875` (±0.05) and
    `net_energy` totaling `73248`.
41. **+10** — Reports, summed over only `active_cars=4 AND zoning=TOP`
    configurations (12 rows), `avg_wait` totaling `229.05` (±0.05) and
    `net_energy` totaling `75648`.

### Production witnesses from the baseline trace (criteria 42-51, weight 97)

Baseline configuration for criteria 42-46 and the hash:
`(active_cars=3, zoning=TOP, wait_timeout=50, power_budget=8, capacity=6)`.

42. **+9** — Shows, in the baseline's continuous trace, two cars scanning
    genuinely different directions at the same tick early in the run (by
    `t=28`: car A scanning UP with doors OPENING at floor 0, car B
    scanning DOWN in DWELL at floor 3) — independent per-car state, not a
    single shared direction.
43. **+9** — Shows call `gidx=15` (origin floor 7, direction DOWN, arrival
    `t=120`, boarded `t=169`) alighting at exactly `t=200`, the same tick
    campaign 1's first call releases — cross-campaign overlap in one
    continuous run, not four independent resets.
44. **+10** — Shows call `gidx=5` (origin floor 3, direction DOWN, arrival
    `t=40`) reassigned exactly once (attempt=2) to car C at `t=91`,
    boarding at `t=94`.
45. **+10** — Shows call `gidx=19` (floor 2, UP, arrival `t=152`) assigned
    ONCE, at `t=243` to car A, boarding `t=248` (attempt stays 1); car A
    stays best through its own timeout window. Switching whenever the
    clock merely expires would delay this same call to `t=265` instead.
46. **+10** — Shows, in `(active_cars=4, zoning=GROUND, wait_timeout=50,
    power_budget=6, capacity=6)`: some tick in `t=24`-`t=59` draws exactly
    6 power, and drawn power never exceeds 6 anywhere in the run
    (genuinely binding, not silently exceeded).
47. **+10** — Shows call `gidx=26` (origin floor 0, UP, arrival `t=248`)
    boards at exactly `t=278`, assigned to car B (attempt stays 1).
48. **+10** — Shows call `gidx=27` (origin floor 0, UP, arrival `t=256`)
    boards at exactly `t=302`, assigned to car C (attempt stays 1).
49. **+10** — Shows, in `(active_cars=4, zoning=SPLIT, wait_timeout=50,
    power_budget=6, capacity=6)`: drawn power never exceeds 6 anywhere in
    the run.
50. **+10** — Shows, in `(active_cars=4, zoning=TOP, wait_timeout=50,
    power_budget=6, capacity=6)`: drawn power never exceeds 6 anywhere in
    the run.
51. **+10** — Matches the first 16 hex characters of the baseline's
    canonical trace-integrity hash (algorithm in the packet) to
    `f544b2d2a1d0fb30`.

### Independent verification and adversarial checks (criteria 52-55, weight 4)

52. **+1** — Delivers and executes a separately-coded verifier re-deriving
    the call table from the packet's formulas, checking a feasibility
    certificate (power within budget, capacity never exceeded, board no
    earlier than arrival, alight after board); a wrapper importing the
    primary's state isn't independent.
53. **+1** — The verifier accepts the delivered baseline trace as feasible.
54. **+1** — Executes a mutation setting one call's boarding tick before its
    own arrival tick; the verifier rejects it and the original is
    preserved and still accepted.
55. **+1** — Executes a mutation inflating one tick's power above that
    configuration's budget; the verifier rejects it, identifies the
    offending tick, and the original is preserved and still accepted.

### Decision/causal reconciliation (criteria 56-60, weight 10)

56. **+2** — Explains, citing the baseline trace's own car counts and
    metrics, why the wait-optimal and energy-optimal selections diverge
    (more active cars lowers wait but raises simultaneous power/energy
    draw) rather than asserting they must coincide.
57. **+2** — Explains what the budget-constrained selection trades away
    relative to the unconstrained wait-optimal selection, citing both
    selections' own `avg_wait` values.
58. **+2** — Explains, citing a concrete tick and car pair from a delivered
    trace, one instance where the shared power budget delayed one car's
    door-open or floor-hop because another car's admission consumed the
    remaining budget that tick.
59. **+2** — Explains why a call reassigned away from a car must never
    later be served by that original car even if it is still nearby,
    tying the explanation to what would go wrong (a passenger served
    twice, or a phantom stop) if this were not enforced.
60. **+2** — Explains why treating the DWELL-to-CLOSING transition as
    automatic rather than power-gated would understate real contention: an
    ungated close draws power outside the admission pass, so a tick that
    should show the budget binding would not.

### Negative trap (criterion 61)

61. **-8** — Embeds precomputed sweep rows, selection values, or the
    trace-integrity hash as literals substituting for executing the
    delivered simulator that produces them. Immutable input constants
    (the call-generation formulas, timing/power constants) do not trigger
    this; omission alone does not trigger it.
