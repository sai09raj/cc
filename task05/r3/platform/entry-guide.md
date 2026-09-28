# KILNWORKS Task05 - complete R3c entry guide (post target-model-pilot hardening: recurring Q-maintenance)

Status: hardened after a local blind-agent pilot scored ~85% against the pre-hardening rubric (audit/blind-pilot-1.md); a second local blind pilot against the hardened R3b packet scored 17.6% (audit/blind-pilot-2.md, later 18.0% under the current rubric weights). Two rubric-guidelines compliance passes then split several bundled criteria, merged two redundant ones, and shortened every criterion beyond 301 characters, growing the rubric from 48 to 50 criteria (revision-delta.md). Three real target-model (Opus 4.8 Max) pilots then scored 72%, 73%, and 99% against the R3b rubric -- forensic reconstruction proved the two lower-scoring runs' delivered simulators were bit-exact correct, a genuine task-difficulty gap, not a scoring artifact. R3c hardens Section H's Q-maintenance freeze from a one-time event to a recurring interval (threshold 12->10) in response, and also fixes three pre-existing over-301-character criteria (4, 7, 9) found during this pass. No pilot has yet been run against R3c.

## Exact field placement

1. Attachment: upload only `artifact/kw-r3c.pdf`. Do not attach this guide, design/, reference/, audit/, or any other private file.
2. Prompt field: paste the entire Prompt block below.
3. Ideal Flow: paste Analyze, Execute & Generate and Synthesize into their respective separate fields.
4. Rubric: enter criteria 1-50 below in exactly that order, each with its displayed unchanged signed weight. Every criterion body (text after the weight) is under 301 characters (verified programmatically). Criteria 38-43 take only the 16-character hash prefix shown -- do not type the full 64-character hash.
5. Target model/effort: Claude Opus 4.8 at maximum effort. Do not silently substitute a local solver run for the target-model pilot.
6. First target-model execution against R3c: one pilot only. Preserve its trajectory and outputs; do not launch further runs until the pilot is reconstructed, replayed, and diagnosed per Playbook/04-PREFLIGHT-AND-VALIDATION.md.

## Prompt

```text
You are the production-optimization engineer for a small kiln plant. Use the attached kw-r3c.pdf as the complete engineering specification. Recover the aisle graph, docking bays, and shared junction from the drawing; reconstruct the fixed dispatch policy the plant's control software already runs for machine assignment, robot routing, and oven batching (there is no free scheduling choice to search for); and reconstruct the one-time robot disruption at the shared junction from the packet.

Implement and execute an offline, deterministic, event-by-event simulator for all six retrofit designs (D0-D5). Each design is ONE continuous run covering all four campaigns back-to-back on a shared clock and a shared resource pool -- not four independent per-campaign resets. Report each design's resulting makespan and tariff-weighted bill, then make both investment selections (unrestricted, and restricted to capital<=9) using the lexicographic key in the packet. Verify your results with a separately-coded implementation that independently re-derives the full trace, or an executed complete feasibility certificate, sharing only immutable input constants with your primary implementation.

Deliver six logical products as files: simulator source; independent verifier source; full per-design schedules with every robot-minute and machine/oven activity; the complete six-design case matrix with both selections and their keys; certification evidence including full production traces and adversarial-check results; and an engineering memo. Use descriptive filenames and give the commands that reproduce the files. Multiple source files, equivalent schemas, and compressed evidence are welcome; only one physically valid schedule per design is possible since every dispatch decision is fully determined.

The memo must include your graph interpretation, commands and tool versions, evidence that your verifier's trace matches your primary's trace for all six designs, comparison of the baseline (D0) with both selected designs, and a causal explanation tied to actual production events from your delivered trace(s). Include the negative-start and route-collision verifier experiments from the packet, and explain why treating the four campaigns as independent resets would not reproduce a correct continuous run. Explain what a distance-only relaxation loses. Base all reported results on your delivered executed implementation; do not embed precomputed case answers as the solver.
```

## Ideal Flow: Analyze

```text
Read the packet and reconstruct the solid/dashed aisle graph, docking bays P/Q/K,
and the shared junction node 4 that every delivery to K must cross in both aisle
configurations. Recover the fully deterministic dispatch policy already in force:
machine assignment priority and persistent per-machine family memory, the six-rule
robot priority order with same-minute collision resolution, and the oven's bounded
pairing timer anchored to each lot's own arrival minute. There is no free scheduling
choice to search for. Recover the one-time node-4 disruption: on Robot 0's first
arrival there, it freezes for a fixed window read from the packet's timeline, not
printed as a number. Recover the independent machine-Q maintenance freeze triggered
by cumulative processing time, and notice it uses the packet's default t-to-t+1
timing convention rather than the node-4 rule's explicitly stated inclusive
exception -- the two disruptions are deliberately timed differently. Treat each of
the six designs as one continuous run covering
all four campaigns on a shared clock, shared fixture pool, and shared machine memory
-- overlapping campaign release windows mean lots from two campaigns are routinely
in the plant at once. A distance-only relaxation cannot certify a feasible joint
robot schedule because it ignores shared-edge and interior-node occupancy.
```

Character count: 1352

## Ideal Flow: Execute & Generate

```text
Implement a deterministic, offline, minute-by-minute event simulator executing the
packet's policy exactly -- for each of the six designs, one continuous trace across
all 20 lots (four campaigns). Build a separately-coded verifier that independently
re-derives each design's full trace from the same visible rules, sharing only
immutable input constants with the primary implementation, and confirm the two agree
exactly. Run the required negative-start and route-collision adversarial mutations
against preserved originals, and identify the collision mutation's first invalid
minute. Deliver simulator source, verifier source, full per-design schedules with
every robot-minute and machine/oven activity, the six-design case matrix with both
selections and keys, certification evidence (traces plus adversarial results), and a
memo. Reconcile each trace's starts/completions, robot cargo/position, fixture
holdings, minute power, and cumulative bill against the reported case values.
Equivalent languages, source organization, output schemas, and physically-valid
tie-broken routes all pass; only one policy-conformant trace per design exists.
```

Character count: 1143

## Ideal Flow: Synthesize

```text
Using the six executed results, apply the lexicographic key (makespan, bill plus
three times capital, capital, design ID) to select the unrestricted recommendation
and, separately, the best design with capital at most nine. Compare the baseline
design against both selections using their executed objectives. Explain at least one
actual routing, batching, or resource interaction using event times from a delivered
trace -- for example how the node-4 disruption forces a reroute, or how a design's
fixture ceiling determines whether the oven ever pairs two lots -- and connect it to
the recommendation. Explain why a distance-only travel bound cannot certify the
achieved schedule, and why treating the four campaigns as independent resets would
not reproduce the required continuous-run results (cite a concrete consequence, such
as a machine losing its cross-campaign setup memory or a cross-campaign oven pairing
becoming impossible). Reconcile schedules, traces, verifier agreement, and selection
arithmetic against both disruption mechanisms as well as the ordinary machine/robot/
oven rules. Any accurate, evidence-tied causal argument is acceptable; no particular
route or additional design comparison is required.
```

Character count: 1221

## Rubric in platform order

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
   capacity 2, other nodes at capacity 1; node 1 (K) has only edge `1-4` in both
   topologies. Equivalent labels pass with an explicit mapping.
5. **+2** — Generates 20 lots per design (campaigns s=0..3, lots j=0..4) with
   `family=(j+s)%2`, `release_local=2*floor(j/2)`, `Pbase=5+(j*j+2s)%4`,
   `Qbase=4+(3j+s)%5`, and **absolute release `35*s + release_local`** on one shared
   clock — not release times that restart at 0 for each campaign.
6. **+1** — Uses the six design input tuples `(F,G,aisle,capital)`: D0=(2,5,closed,0),
   D1=(3,5,closed,7), D2=(2,6,closed,9), D3=(2,5,open,6), D4=(3,6,closed,16),
   D5=(3,6,open,22).
7. **+1** — Machine assignment: family memory persists for the whole run (never
   resets per campaign); setup 0 on a first job or unchanged family, else 2; an
   empty/power-refused machine claims nothing, leaving the other's pool
   unaffected; fixture held only from actual prep start; ties by lowest index.
8. **+1** — Keeps plant-wide fixture holdings at most F at every minute across the
   entire continuous run; each lot holds one fixture from the start of its own
   preparation through cure completion.
9. **+1** — Robot dispatch: six-rule priority order (offline/unload/pickup/
   toward-K/toward-nearest-lot/toward-home), Robot 0 decided and power-finalized
   before Robot 1, correct same-minute collision handling (a node vacated this
   minute may be entered by the other robot), ties by lowest target/next-hop id.
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
14. **+2** — Tracks Q's maintenance trigger as one cumulative counter: sums only
    Q's completed processing (never setup) since its last freeze ended, triggers
    at a completion boundary once the sum reaches 10, and resets to 0 on each
    trigger — recurring, uncapped, not a one-time event.
15. **+1** — Leaves the triggering completion minute itself unaffected by the Q
    maintenance freeze on every trigger, not only the first — the packet's
    *default* timing rule, stated with no inclusive exception, unlike node-4's
    explicit one in criterion 13.
16. **+1** — Covers each Q freeze for 13 minutes starting the minute **after**
    its trigger, through `trigger+13`, resuming tracking from 0 at
    `trigger+14`. Copying node-4's inclusive convention, or capping this at
    one occurrence, fails this criterion regardless of 14-15.

### Integrated production execution — per-design values (criteria 17-28, weight 117)

Each pair of criteria checks one design's simulated `(makespan, bill)` pair and its
full trace reconciliation, graded as one record (lots done, fixtures released, and
cumulative bill together describe a single trace's internal consistency, not three
independent asks). Any attaining schedule passes; report however organized.

17. **+10** — Reports D0's `(makespan, bill)` as `(187, 1331)`.
18. **+10** — Reports D1's `(makespan, bill)` as `(159, 1239)`.
19. **+10** — Reports D2's `(makespan, bill)` as `(188, 1435)`.
20. **+10** — Reports D3's `(makespan, bill)` as `(185, 1378)`.
21. **+10** — Reports D4's `(makespan, bill)` as `(152, 1344)`.
22. **+10** — Reports D5's `(makespan, bill)` as `(151, 1258)`.
23. **+10** — Reconciles D0's delivered trace as one record: 20 of 20 lots done, 0
    fixtures held, and a cumulative bill of 1331, all at the final boundary.
24. **+10** — Reconciles D1's delivered trace as one record: 20 of 20 lots done, 0
    fixtures held, and a cumulative bill of 1239, all at the final boundary. (W5
    also appears here, but is graded once, via criterion 32 — not charged again.)
25. **+10** — Reconciles D2's delivered trace as one record: 20 of 20 lots done, 0
    fixtures held, and a cumulative bill of 1435, all at the final boundary.
26. **+10** — Reconciles D3's delivered trace as one record: 20 of 20 lots done, 0
    fixtures held, and a cumulative bill of 1378, all at the final boundary.
27. **+7** — Reconciles D4's delivered trace as one record: 20 of 20 lots done, 0
    fixtures held, and a cumulative bill of 1344, all at the final boundary. (W3
    also appears here, but is graded once, via criterion 33 — not charged again.)
28. **+10** — Reconciles D5's delivered trace as one record: 20 of 20 lots done, 0
    fixtures held, and a cumulative bill of 1258, all at the final boundary.

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
32. **+3** — Shows W5 in the design's trace (D1-D5): for every Q trigger, Q
    eligible up to it, absent 13 minutes after, eligible again with tracking
    reset. Fails on an isolated single-campaign fixture, a missing later
    trigger (single-shot, not recurring), or a freeze on its trigger minute.
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
39. **+10** — Matches the first 16 hex characters of D1's canonical trace hash to `9eafc0820bda70a9`.
40. **+10** — Matches the first 16 hex characters of D2's canonical trace hash to `7d104044363f36b2`.
41. **+10** — Matches the first 16 hex characters of D3's canonical trace hash to `b1086cb4f38396f4`.
42. **+10** — Matches the first 16 hex characters of D4's canonical trace hash to `c9e705daef1ddcf7`.
43. **+10** — Matches the first 16 hex characters of D5's canonical trace hash to `6a1d99ca7302e560`.

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
    correct metrics give D5, (151, 1324, 22, D5).
45. **+1** — Minimizes the same key within `capital<=9` (D0, D1, D2, D3). Grade
    population/selection on delivered metrics without recharging upstream metric
    errors; with correct metrics the result is D1, (159, 1260, 7, D1).
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

## Numeric transcription checklist


- [ ] Prompt: 343 whitespace-delimited words (permitted 2-500).
- [ ] Analyze: 1352 characters (permitted 5-3000).
- [ ] Execute & Generate: 1143 characters (permitted 5-3000).
- [ ] Synthesize: 1221 characters (permitted 5-3000).
- [ ] Exactly 50 criteria (49 positive + 1 negative); weights in order:
      2,1,1, 2,2,1,1,1,1,1,1,1,1,2,1,1, 10,10,10,10,10,10,10,10,10,10,7,10, 3,3,3,3,3,
      1,1,1,1, 10,10,10,10,10,10, 1,1,1,1,1,1, -8.
      (Criterion 27 is +7, not +10 — 3 of its original weight moved to the standalone
      witness criterion 33, once W3 was split out to stop double-counting/inconsistent
      bundling. Criteria 1-3 are 3 rows, not 4 — the old commands/tool-versions
      criterion merged into criterion 1. Criteria 10/11 and 14/15/16 are each split
      from one previously-bundled criterion, per a rubric-guidelines atomicity fix;
      see `revision-delta.md` for the full accounting.)
- [ ] Positive weights sum 222; criterion 50 alone has weight -8.
- [ ] Attachment filename: `kw-r3c.pdf` (unique to this revision; do not upload any
      R1/R2/R3b file, and do not upload the earlier `kw-r3b.pdf` that blind-pilot-2
      saw — this hardened version changes Section H's maintenance mechanism to
      recurring and has different bytes; verify against the hash in
      `frozen-packet-manifest.json`).
- [ ] Four campaigns 0..3, five lots 0..4 per campaign, twenty lots per design, six
      designs D0..D5 — one continuous trace per design, not 24 independent cases.
- [ ] Budget population `capital<=9` includes D0, D1, D2, D3 (D2 at equality).
- [ ] Correct unrestricted key: `(151, 1324, 22, D5)`.
- [ ] Correct capital<=9 key: `(159, 1260, 7, D1)`.

| Design | Makespan | Bill |
|---|---:|---:|
| D0 | 187 | 1331 |
| D1 | 159 | 1239 |
| D2 | 188 | 1435 |
| D3 | 185 | 1378 |
| D4 | 152 | 1344 |
| D5 | 151 | 1258 |

- [ ] Node-4 fault (S07): freezes 6 minutes including arrival, fires once per design.
- [ ] Machine-Q maintenance freeze (S13, hardened R3c): triggers at cumulative
      processing (since the last freeze ended) >= 10; freezes 13 minutes starting
      the minute AFTER the trigger (not inclusive, unlike S07); **recurring** —
      cumulative tracking resets to 0 on every trigger, no per-design cap. D0
      triggers it exactly once (its 2-job Q workload sums to exactly 12, crossing
      on its last job) but that trigger has zero effect — no remaining Q work is
      left to delay. D1/D2/D3/D4/D5 each trigger it 2-3 times with real effect.
- [ ] Witness W3 (D4): Q's campaign-1 job on global-index-6 lot runs 10 minutes
      (Qbase 8 + setup 2). Unaffected by the R3c threshold change.
- [ ] Witness W4 (D1): mixed-campaign batch at t=50, members {global index 3, 7}.
      Unaffected by the R3c threshold change.
- [ ] Witness W5 (D1): two maintenance triggers — t=44 (freeze [45,57]) and t=118
      (freeze [119,131]) — the second changes which lot fills Q's last slot
      (global index 18 instead of 16, see `production-witnesses.md`).
- [ ] All six per-design trace-integrity values are each exactly 16 lowercase hex
      characters — the first 16 characters of the full SHA-256, truncated for safe
      manual transcription (verify programmatically, not by eye) and copied from
      `production-witnesses.md` / `frozen-packet-manifest.json`, never retyped by
      hand:
      D0=`955957f0e6a9788d`, D1=`9eafc0820bda70a9`, D2=`7d104044363f36b2`,
      D3=`b1086cb4f38396f4`, D4=`c9e705daef1ddcf7`, D5=`6a1d99ca7302e560`.
      (Only D0's value is unchanged from R3b — see above.)
- [ ] After entry, compare an export or screenshots of every field and weight
      against this guide. This checkbox remains unverified until that evidence
      exists.

## Canonical trace-hash reproduction command

```text
python3 -c "
import hashlib, kilnworks_sim as k
for name in k.DESIGNS:
    r = k.simulate(name)
    h = hashlib.sha256(k.canonical_trace_serialization(r).encode()).hexdigest()
    print(name, h, '-> rubric value:', h[:16])
"
```

## Frozen field manifest

| Frozen file | SHA256 |
|---|---|

| artifact/kw-r3c.pdf | `ecd0308c675fababd72bef5a35fcfb48d29b67d35024a795b2eea1598234b01b` |

| prompt.md | `4cee8d930d1a74e0aa2a8a949bca620c56c729568f4afe2d173a810e729e8d89` |

| ideal-flow.md | `4f055175e0d585b3b0eb8e458c3cf7a0e31a75182e5ad7ea29043f5e4e3266f0` |

| rubric.md | `e6334c58061837c47610fa88398cf9d4375797d895496e700f673f9eb26ad90f` |

| score-topology.md | `755457cfce9eb0876a5b62a530adae022c5bccef88ad17db343795babdeb09da` |

| production-witnesses.md | `114f2d9dc1b2db321a7c044883dbfe4c11b520a3474b5d0d6249eef55422d521` |

| coverage-ledger.md | `85a2c6f19670d3ccb751f583fd8c5dad6d217408643d4b5b501186627ab0f1d8` |

| numeric-transcription-checklist.md | `faa36e59ffdc096a4aee79e9707d9dc75ad86e85dc0867f0033268b1780e1ae4` |
