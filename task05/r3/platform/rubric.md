# R3 rubric — frozen after independent-reconstruction convergence

Positive total **61**; one negative trap **-8**. Criteria are binary. Local
normalization is earned positive points minus triggered penalty, divided by 61,
clamped at zero; this is an explicitly labelled local diagnostic, not an assumed
official platform formula. Accept equivalent correct work throughout: equivalent
languages, source organization, output schemas, file layout, and formula notation.
No hidden filename/schema requirements. Package, local, integrated and decision
weight buckets, and the plausible-wrong survival-ceiling calculation, are in
`score-topology.md`.

### Package (criteria 1-4, weight 4)

1. **+1** — Executes the delivered offline simulator with a documented command that
   generates the submitted case results; equivalent languages and source
   organization pass.
2. **+1** — Provides the six logical products as accessible files: simulator,
   independent verifier, schedules/traces, case matrix with both selections,
   certification/adversarial evidence, and memo. No particular filenames, schema, or
   physical file count is required.
3. **+1** — Identifies all six designs D0..D5, each as **one continuous four-campaign
   trace sharing one clock and one resource pool** — not four independent
   per-campaign resets and not twenty-four separate cases.
4. **+1** — Records simulator/verifier reproduction commands and actual tool
   versions sufficient to regenerate the delivered files in a declared offline,
   stdlib-only environment.

### Local semantics/rules/scaffolding (criteria 5-13, weight 11)

5. **+2** — Recovers solid undirected edges `{0-3,3-6,3-4,4-7,6-7,7-8,5-8,2-5,1-4}`,
   adding only `4-5` for open designs D3/D5; docking bays `P=3, Q=5, K=1` at
   capacity 2, all other nodes at capacity 1; and that node 1 (K) has only the edge
   `1-4` in both topologies. Equivalent labels pass with an explicit mapping.
6. **+2** — Generates 20 lots per design (campaigns s=0..3, lots j=0..4) with
   `family=(j+s)%2`, `release_local=2*floor(j/2)`, `Pbase=5+(j*j+2s)%4`,
   `Qbase=4+(3j+s)%5`, and **absolute release `35*s + release_local`** on one shared
   clock — not release times that restart at 0 for each campaign.
7. **+1** — Uses the six design input tuples `(F,G,aisle,capital)`: D0=(2,5,closed,0),
   D1=(3,5,closed,7), D2=(2,6,closed,9), D3=(2,5,open,6), D4=(3,6,closed,16),
   D5=(3,6,open,22).
8. **+1** — Machine assignment: each machine's remembered family **persists for the
   whole continuous run** (never resets at a campaign boundary); setup is 0 on a
   machine's first job or an unchanged family, else 2; a machine whose pool is empty
   or whose start is refused by the power budget claims nothing and leaves the other
   machine's pool unaffected that minute; a fixture is counted held only from an
   actually-started preparation.
9. **+1** — Keeps plant-wide fixture holdings at most F at every minute across the
   entire continuous run; each lot holds one fixture from the start of its own
   preparation through cure completion.
10. **+1** — Robot dispatch applies the six-rule priority order (offline / unload /
    pickup / toward-K / toward-nearest-waiting-lot / toward-home), Robot 0 decided
    and power-finalized before Robot 1, with correct same-minute edge/node-capacity
    collision handling, including that a node vacated by one robot this same minute
    may be legally entered by the other.
11. **+1** — Oven bounded pairing timer: an anchor's deadline is anchored to its own
    arrival minute (not the minute it is later picked up as anchor), a same-family
    partner already arrived starts the batch immediately, and batching is not
    restricted to lots from the same campaign.
12. **+1** — Aggregate power is admitted in one ordered pass per minute (P start, Q
    start, Robot 0, Robot 1, oven start), each step drawing only what the previous
    steps left; a refusal defers/downgrades the action rather than erroring, and
    never exceeds the design's G.
13. **+1** — Node-4 fault: triggers on Robot 0's first actually-admitted arrival at
    node 4, freezes it (position and cargo) for 6 minutes counting the arrival
    minute itself, and fires at most once per design's run.

### Integrated production execution — per-design values (criteria 14-25, weight 24)

Each criterion checks one design's simulated `(makespan, bill)` pair from its own
continuous run. Any attaining schedule passes; report the pair however organized.

14. **+2** — D0: makespan 187, bill 1331.
15. **+2** — D1: makespan 165, bill 1294.
16. **+2** — D2: makespan 187, bill 1447.
17. **+2** — D3: makespan 185, bill 1401.
18. **+2** — D4: makespan 155, bill 1413.
19. **+2** — D5: makespan 142, bill 1290.
20. **+2** — D0's delivered trace reconciles: 20/20 lots done, 0 fixtures held, and
    cumulative bill equal to 1331 at the final boundary.
21. **+2** — D1's delivered trace reconciles the same way, final bill 1294, and
    shows at least one oven batch pairing two lots (D1 has 4 of its 16 batches
    paired, 2 of them mixing two different campaigns).
22. **+2** — D2's delivered trace reconciles the same way, final bill 1447.
23. **+2** — D3's delivered trace reconciles the same way, final bill 1401.
24. **+2** — D4's delivered trace reconciles the same way, final bill 1413, and shows
    a machine job whose setup cost of 2 is attributable only to memory carried over
    from an earlier campaign (production witness W3: Q's campaign-1 job on lot with
    global index 6 runs 10 minutes = Qbase 8 + setup 2, not 8).
25. **+2** — D5's delivered trace reconciles the same way, final bill 1290.

### Integrated production execution — witnesses, verification, feasibility (criteria 26-32, weight 16)

26. **+3** — Within the design's required single continuous four-campaign trace (not
    an isolated fixture), Robot 0 is frozen at node 4 for exactly 6 consecutive
    minutes including its arrival minute, the other robot is unable to enter node 4
    during that window, and legally enters it the minute Robot 0 vacates (production
    witness W1). A fault that fires more than once in one design's run (e.g. because
    campaigns were wrongly simulated as independent resets) does not satisfy this
    criterion.
27. **+3** — Delivered trace (any design) shows at least one lot from an earlier
    campaign still open (not yet cured) at the minute a later campaign's first lot
    releases (production witness W2; e.g. D0 campaign-0 lots with global indices 2,
    3, 4 still open at t=35).
28. **+3** — Delivered trace (D1, D4, or D5) shows at least one oven batch whose two
    members belong to two different campaigns (production witness W4).
29. **+2** — Delivers and executes a separately-coded verifier that independently
    re-derives the full per-design trace (or an executed complete feasibility
    certificate covering fixture, power, node/edge capacity, and timing), sharing
    only immutable input constants with the primary implementation; a wrapper that
    imports the primary's transitions, feasibility checks, or state does not
    establish independence.
30. **+3** — The independent verifier's re-derived trace matches the primary's
    delivered trace exactly for all six designs (equal makespan and bill at minimum;
    equal full trace where both are produced in comparable form). This criterion
    checks cross-implementation agreement only; correctness of the agreed-upon
    values is separately checked by criteria 14-25.
31. **+1** — Executes a copied-schedule mutation changing its earliest preparation
    start to -1; the verifier rejects the copy and accepts the preserved original.
32. **+1** — Executes a copied-route mutation causing an edge or interior-node
    conflict; the verifier rejects it, identifies the first invalid minute or a
    clearly mapped equivalent, and accepts the preserved original.

### Decision/causal reconciliation (criteria 33-38, weight 6)

33. **+1** — Applies the lexicographic key `(makespan, bill+3*capital, capital, ID)`
    across all six designs' delivered results and selects its minimum. Grade
    selection arithmetic on the delivered metrics without recharging an upstream
    metric error already charged in 14-19; with correct metrics the result is
    D5, (142, 1356, 22, D5).
34. **+1** — Minimizes the same key within `capital<=9` (D0, D1, D2, D3). Grade
    population/selection on delivered metrics without recharging upstream metric
    errors; with correct metrics the result is D1, (165, 1315, 7, D1).
35. **+1** — Compares D0 (baseline) against both selected designs using the
    delivered executed objectives. Accept a comparison correct relative to
    delivered results despite an upstream error.
36. **+1** — Explains at least one actual routing, batching, or resource interaction
    using identifiable event times from a delivered production trace, connected to
    the recommendation. Any accurate supported interaction is acceptable (the
    node-4 fault forcing a reroute, and the F=2 designs' fixture ceiling preventing
    oven pairing despite the open-aisle retrofit, are two available examples, not a
    required pair).
37. **+1** — Explains that distance-only travel omits shared undirected-edge and
    interior-node occupancy, so its bound alone cannot certify a feasible joint
    robot schedule or an achieved completion time.
38. **+1** — Explains that treating the four campaigns as independent per-campaign
    resets (ignoring overlapping release, persistent setup memory, and shared
    fixture/robot/oven state) would not reproduce the required continuous-run
    results, citing at least one concrete consequence (e.g. it would miss the
    setup-2 boundary job in witness W3, or a cross-campaign oven pairing).

### Negative trap (criterion 39)

39. **-8** — Embeds precomputed case-result values or schedule tables as substitutes
    for executing the simulator that produces reported results. Immutable input
    constants and computed search/verification caches do not trigger this
    active-behavior trap; omission alone does not trigger it.
