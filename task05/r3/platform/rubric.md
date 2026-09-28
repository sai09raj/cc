# R3 rubric — frozen after hardening + full atomicity pass

Positive total **222**; one negative trap **-8**. Criteria are binary. Local
normalization is earned positive points minus triggered penalty, divided by 222,
clamped at zero; this is an explicitly labelled local diagnostic, not an assumed
official platform formula. Accept equivalent correct work throughout: equivalent
languages, source organization, output schemas, file layout, and formula notation.
No hidden filename/schema requirements.

**Why the per-design and per-design-hash buckets are unusually heavily weighted**
(11 criteria at +10, one at +7 — see the note on criterion 27 below — and 6 more
criteria at +10, all at or adjacent to the official per-criterion ceiling): the
score-topology audit (`score-topology.md`) found that with more modest weights,
several realistic wrong-but-partially-correct implementations retained 30-50% of
positive weight purely by getting most *local* rules right while missing the
*integrated* per-design result. Raising these buckets toward the legal maximum was
the fix; see `score-topology.md` for the exact counterfactual evidence that drove
this, including two rounds of retuning. Each of the 18 rows in criteria 17-28 and
38-43 tests a distinct fact (six designs' own `(makespan,bill)` pair, six matching
full-trace reconciliations, six independent trace-integrity hashes) rather than
being padding. Criterion 27 carries +7 instead of +10 because 3 of its original
weight moved to the standalone witness criterion 33, once that witness was split
out to remove a bundled-and-duplicated check (see `revision-delta.md`).

**Why criteria 1-15 look different from an earlier draft**: a rubric-guidelines
compliance pass found two things worth fixing even at the cost of renumbering
everything downstream. First, criteria 1 and 4 tested the same underlying fact
(documented, reproducible execution) as two separate rows, so they are merged
into one. Second, the oven-timer and Q-maintenance-boundary criteria each bundled
multiple independently-satisfiable/failable facts into one row (a response could
get the deadline arithmetic right while getting the tie-break wrong, or vice
versa) — a real atomicity violation per the rubric guide's Rule 3 and the
playbook's "could a response satisfy one part and fail another" test. Both are
now split. Criteria 12-14 (power admission, node-4 fault, Q-maintenance tracking)
remain single rows deliberately: each is graded as one named object (an ordered
interface, a state-transition vector, a cumulative counter's definition) under
the guidelines' own exception for a genuinely unitary answer, consistent with how
the production-witness criteria (29-33) are already structured. The net criteria
count grew from 49 to exactly 50 (the platform's ceiling) to make room for this
without cutting real coverage; see `revision-delta.md` for the full accounting.

### Package (criteria 1-3, weight 4)

1. **+2** — Executes the delivered offline simulator with a documented command
   that generates the submitted case results, and records the actual tool
   versions used, sufficient to regenerate the delivered files in a declared
   offline, stdlib-only environment; equivalent languages and source
   organization pass.
2. **+1** — Provides the six logical products as accessible files: simulator,
   independent verifier, schedules/traces, case matrix with both selections,
   certification/adversarial evidence, and memo. No particular filenames, schema, or
   physical file count is required.
3. **+1** — Identifies all six designs D0..D5, each as **one continuous four-campaign
   trace sharing one clock and one resource pool** — not four independent
   per-campaign resets and not twenty-four separate cases.

### Local semantics/rules/scaffolding (criteria 4-16, weight 16)

4. **+2** — Recovers solid undirected edges `{0-3,3-6,3-4,4-7,6-7,7-8,5-8,2-5,1-4}`,
   adding only `4-5` for open designs D3/D5; docking bays `P=3, Q=5, K=1` at
   capacity 2, all other nodes at capacity 1; and that node 1 (K) has only the edge
   `1-4` in both topologies. Equivalent labels pass with an explicit mapping.
5. **+2** — Generates 20 lots per design (campaigns s=0..3, lots j=0..4) with
   `family=(j+s)%2`, `release_local=2*floor(j/2)`, `Pbase=5+(j*j+2s)%4`,
   `Qbase=4+(3j+s)%5`, and **absolute release `35*s + release_local`** on one shared
   clock — not release times that restart at 0 for each campaign.
6. **+1** — Uses the six design input tuples `(F,G,aisle,capital)`: D0=(2,5,closed,0),
   D1=(3,5,closed,7), D2=(2,6,closed,9), D3=(2,5,open,6), D4=(3,6,closed,16),
   D5=(3,6,open,22).
7. **+1** — Machine assignment: each machine's remembered family **persists for the
   whole continuous run** (never resets at a campaign boundary); setup is 0 on a
   machine's first job or an unchanged family, else 2; a machine whose pool is empty
   or whose start is refused by the power budget claims nothing and leaves the other
   machine's pool unaffected that minute; a fixture is counted held only from an
   actually-started preparation; ties broken by lowest global index.
8. **+1** — Keeps plant-wide fixture holdings at most F at every minute across the
   entire continuous run; each lot holds one fixture from the start of its own
   preparation through cure completion.
9. **+1** — Robot dispatch applies the six-rule priority order (offline / unload /
   pickup / toward-K / toward-nearest-waiting-lot / toward-home), Robot 0 decided
   and power-finalized before Robot 1, with correct same-minute edge/node-capacity
   collision handling (including that a node vacated by one robot this same minute
   may be legally entered by the other) and ties broken by lowest target/next-hop
   node id, not highest.
10. **+1** — Matches oven batches by family: an already-arrived same-family
    partner joins the anchor immediately, tie-broken by lowest global index,
    not highest; cross-campaign same-family pairs still batch together, not
    restricted to one campaign.
11. **+1** — Sets an oven anchor's deadline to its own arrival minute (one
    minute after the delivering unload, not the minute later picked as
    anchor) plus 2; absent a partner, starts the batch alone once the current
    minute reaches or passes that deadline, not strictly after.
12. **+1** — Admits aggregate power as one ordered per-minute pass — P start, Q
    start, Robot 0, Robot 1, oven start — where each step draws only what the
    previous steps left, a refusal defers or downgrades that step's action rather
    than erroring, and the running total never exceeds the design's G.
13. **+1** — Executes the node-4 fault as one state-transition vector: triggers on
    Robot 0's first actually-admitted arrival at node 4, freezes its position and
    cargo for 6 minutes counting the arrival minute itself (the packet's explicit
    inclusive exception), and fires at most once per design's run.
14. **+2** — Tracks Q's maintenance-freeze trigger as one cumulative counter: sums
    only Q's completed processing time (never setup) continuously across the whole
    run (never reset per campaign), and triggers the first time that sum reaches 12
    at a completion boundary, firing at most once per design's run.
15. **+1** — Leaves the triggering completion minute itself unaffected by the Q
    maintenance freeze — the packet's *default* timing rule, stated with no
    inclusive exception, unlike node-4's explicit one in criterion 13.
16. **+1** — Covers the Q maintenance freeze for exactly the 13 minutes starting
    the minute **after** the trigger, through `trigger+13` inclusive. Starting
    the freeze on the trigger minute itself, copying node-4's convention, fails
    this criterion regardless of criteria 14-15.

### Integrated production execution — per-design values (criteria 17-28, weight 117)

Each pair of criteria checks one design's simulated `(makespan, bill)` pair and its
full trace reconciliation, graded as one record (lots done, fixtures released, and
cumulative bill together describe a single trace's internal consistency, not three
independent asks). Any attaining schedule passes; report however organized.

17. **+10** — Reports D0's `(makespan, bill)` as `(187, 1331)`.
18. **+10** — Reports D1's `(makespan, bill)` as `(161, 1242)`.
19. **+10** — Reports D2's `(makespan, bill)` as `(187, 1373)`.
20. **+10** — Reports D3's `(makespan, bill)` as `(185, 1408)`.
21. **+10** — Reports D4's `(makespan, bill)` as `(151, 1384)`.
22. **+10** — Reports D5's `(makespan, bill)` as `(153, 1298)`.
23. **+10** — Reconciles D0's delivered trace as one record: 20 of 20 lots done, 0
    fixtures held, and a cumulative bill of 1331, all at the final boundary.
24. **+10** — Reconciles D1's delivered trace as one record: 20 of 20 lots done, 0
    fixtures held, and a cumulative bill of 1242, all at the final boundary. (W5
    also appears here, but is graded once, via criterion 32 — not charged again.)
25. **+10** — Reconciles D2's delivered trace as one record: 20 of 20 lots done, 0
    fixtures held, and a cumulative bill of 1373, all at the final boundary.
26. **+10** — Reconciles D3's delivered trace as one record: 20 of 20 lots done, 0
    fixtures held, and a cumulative bill of 1408, all at the final boundary.
27. **+7** — Reconciles D4's delivered trace as one record: 20 of 20 lots done, 0
    fixtures held, and a cumulative bill of 1384, all at the final boundary. (W3
    also appears here, but is graded once, via criterion 33 — not charged again.)
28. **+10** — Reconciles D5's delivered trace as one record: 20 of 20 lots done, 0
    fixtures held, and a cumulative bill of 1298, all at the final boundary.

### Integrated production execution — named witnesses (criteria 29-33, weight 15)

29. **+3** — Shows W1 in the design's required continuous trace (not an isolated
    fixture): Robot 0 frozen at node 4 for exactly 6 consecutive minutes incl.
    arrival, the other robot blocked from node 4 that whole window, then legally
    entering the minute Robot 0 vacates. Firing more than once fails this.
30. **+3** — Shows production witness W2 in a delivered trace (any design): at
    least one lot from an earlier campaign still open, not yet cured, at the
    minute a later campaign's first lot releases.
31. **+3** — Shows production witness W4 in a delivered trace (D1, D4, or D5): at
    least one oven batch whose two members belong to two different campaigns.
32. **+3** — Shows W5 in the design's required continuous trace (D1-D5): Q
    eligible up to its own trigger, then absent exactly 13 minutes after, then
    eligible again. Fails if computed from an isolated single-campaign fixture,
    if it fires more than once, or if it starts on the trigger minute itself.
33. **+3** — Shows production witness W3 in D4's delivered trace: a machine job
    whose setup cost of 2 is attributable only to family memory carried over from
    an earlier campaign, not to any job within the same campaign.

### Independent verification and adversarial checks (criteria 34-37, weight 4)

34. **+1** — Delivers and executes a separately-coded verifier that
    independently re-derives the full trace (or a complete feasibility
    certificate covering fixture, power, node/edge capacity, timing), sharing
    only immutable inputs with primary; a wrapper importing primary's
    transitions/state isn't independent.
35. **+1** — Matches the independent verifier's re-derived trace to the primary's
    delivered trace exactly for all six designs. This criterion checks
    cross-implementation agreement only; correctness of the agreed-upon values is
    separately (and much more heavily) checked by criteria 17-28 and 38-43.
36. **+1** — Executes a copied-schedule mutation changing its earliest preparation
    start to -1; the verifier rejects the copy and accepts the preserved original.
37. **+1** — Executes a copied-route mutation causing an edge or interior-node
    conflict; the verifier rejects it, identifies the first invalid minute or a
    clearly mapped equivalent, and accepts the preserved original.

### Integrated production execution — per-design trace-integrity hash (criteria 38-43, weight 60)

Each design's complete minute-by-minute trace, canonically serialized as one line
per minute (`t,power,cumulative_bill`, in execution order, preceded by a
`DESIGN:<name>` marker line — see the reference command in
`platform/entry-guide.md`), hashed with SHA-256. This is sensitive to any single
divergent minute anywhere in that design's run, not just the final summary.

38. **+10** — Matches the first 16 hex characters of D0's canonical trace hash to `955957f0e6a9788d`.
39. **+10** — Matches the first 16 hex characters of D1's canonical trace hash to `0e46cf0e88a3c39d`.
40. **+10** — Matches the first 16 hex characters of D2's canonical trace hash to `3e42a4ac02477575`.
41. **+10** — Matches the first 16 hex characters of D3's canonical trace hash to `c237acbc4fab1df9`.
42. **+10** — Matches the first 16 hex characters of D4's canonical trace hash to `07824bc182e06107`.
43. **+10** — Matches the first 16 hex characters of D5's canonical trace hash to `80f5ceea7c33d2b1`.

Generated by `reference/kilnworks_sim.py` (`canonical_trace_serialization` +
SHA-256), truncated to 16 hex characters to keep manual transcription safe
while remaining overwhelmingly sensitive to any single divergent minute (64
bits of entropy makes an accidental match between two genuinely different
traces astronomically unlikely for this six-design, non-adversarial setting).
Reproduce with the command in `platform/entry-guide.md`. These were copied
from executed output, not hand-typed — cross-check against
`platform/production-witnesses.md` and `platform/frozen-packet-manifest.json`
rather than retyping.

### Decision/causal reconciliation (criteria 44-49, weight 6)

44. **+1** — Applies the lexicographic key `(makespan, bill+3*capital, capital, ID)`
    across all six designs' results and selects its minimum. Grade arithmetic on
    delivered metrics without recharging an upstream error charged in 17-22;
    correct metrics give D4, (151, 1432, 16, D4).
45. **+1** — Minimizes the same key within `capital<=9` (D0, D1, D2, D3). Grade
    population/selection on delivered metrics without recharging upstream metric
    errors; with correct metrics the result is D1, (161, 1263, 7, D1).
46. **+1** — Compares D0 (baseline) against both selected designs using the
    delivered executed objectives. Accept a comparison correct relative to
    delivered results despite an upstream error.
47. **+1** — Explains at least one actual routing, batching, or resource
    interaction using event times from a delivered trace, connected to the
    recommendation (e.g. the node-4 reroute, the Q-freeze delay, or an F=2
    fixture ceiling blocking oven pairing — any accurate example counts).
48. **+1** — Explains that distance-only travel omits shared undirected-edge and
    interior-node occupancy, so its bound alone cannot certify a feasible joint
    robot schedule or an achieved completion time.
49. **+1** — Explains that treating the four campaigns as independent per-campaign
    resets (ignoring overlapping release, persistent setup memory, shared
    fixture/robot/oven state, and the Q maintenance clock) would not reproduce the
    required continuous-run results, citing at least one concrete consequence.

### Negative trap (criterion 50)

50. **-8** — Embeds precomputed case-result values or schedule tables as substitutes
    for executing the simulator that produces reported results. Immutable input
    constants and computed search/verification caches do not trigger this
    active-behavior trap; omission alone does not trigger it.
