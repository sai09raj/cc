# KILNWORKS Task05 - complete R3(b) entry guide (post-hardening)

Status: hardened after a local blind-agent pilot scored ~85% against the pre-hardening rubric (audit/blind-pilot-1.md). Added the Machine-Q maintenance freeze (S13), fixed a real packet gap (the selection-key formula), reweighted the rubric per score-topology.md, and renamed the attachment to kw-r3b.pdf so it cannot be confused with the bytes blind-pilot-1 actually saw. A second local blind pilot is documented in audit/blind-pilot-2.md. No target-model platform pilot has been run yet.

## Exact field placement

1. Attachment: upload only `artifact/kw-r3b.pdf`. Do not attach this guide, design/, reference/, audit/, or any other private file.
2. Prompt field: paste the entire Prompt block below.
3. Ideal Flow: paste Analyze, Execute & Generate and Synthesize into their respective separate fields.
4. Rubric: enter criteria 1-48 below in exactly that order, each with its displayed unchanged signed weight.
5. Target model/effort: Claude Opus 4.8 at maximum effort. Do not silently substitute a local solver run for the target-model pilot.
6. First target-model execution: one pilot only. Preserve its trajectory and outputs; do not launch further runs until the pilot is reconstructed, replayed, and diagnosed per Playbook/04-PREFLIGHT-AND-VALIDATION.md.

## Prompt

```text
You are the production-optimization engineer for a small kiln plant. Use the attached kw-r3b.pdf as the complete engineering specification. Recover the aisle graph, docking bays, and shared junction from the drawing; reconstruct the fixed dispatch policy the plant's control software already runs for machine assignment, robot routing, and oven batching (there is no free scheduling choice to search for); and reconstruct the one-time robot disruption at the shared junction from the packet.

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

## Rubric in platform order


Positive total **221**; one negative trap **-8**. Criteria are binary. Local
normalization is earned positive points minus triggered penalty, divided by 221,
clamped at zero; this is an explicitly labelled local diagnostic, not an assumed
official platform formula. Accept equivalent correct work throughout: equivalent
languages, source organization, output schemas, file layout, and formula notation.
No hidden filename/schema requirements.

**Why the per-design and per-design-hash buckets are unusually heavily weighted**
(12 criteria at +10 and 6 criteria at +10 — both at the official per-criterion
ceiling): the score-topology audit (`score-topology.md`) found that with more
modest weights, several realistic wrong-but-partially-correct implementations
retained 30-50% of positive weight purely by getting most *local* rules right while
missing the *integrated* per-design result. Raising these two buckets to the legal
maximum was the fix; see `score-topology.md` for the exact counterfactual evidence
that drove this, including two rounds of retuning. Each of the 18 rows tests a
distinct fact (six designs' own `(makespan,bill)` pair, six matching full-trace
reconciliations, six independent trace-integrity hashes) rather than being padding.

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

### Local semantics/rules/scaffolding (criteria 5-15, weight 15)

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
   actually-started preparation; ties broken by lowest global index.
9. **+1** — Keeps plant-wide fixture holdings at most F at every minute across the
   entire continuous run; each lot holds one fixture from the start of its own
   preparation through cure completion.
10. **+1** — Robot dispatch applies the six-rule priority order (offline / unload /
    pickup / toward-K / toward-nearest-waiting-lot / toward-home), Robot 0 decided
    and power-finalized before Robot 1, with correct same-minute edge/node-capacity
    collision handling (including that a node vacated by one robot this same minute
    may be legally entered by the other) and ties broken by lowest target/next-hop
    node id, not highest.
11. **+1** — Oven bounded pairing timer: an anchor's deadline is anchored to its own
    arrival minute (the minute one after the delivering unload action, not the
    minute it is later picked up as anchor), a same-family partner already arrived
    starts the batch immediately (tie-break lowest global index, not highest), the
    batch starts as soon as the current minute reaches or passes the deadline (not
    strictly after), and batching is not restricted to lots from the same campaign.
12. **+1** — Aggregate power is admitted in one ordered pass per minute (P start, Q
    start, Robot 0, Robot 1, oven start), each step drawing only what the previous
    steps left; a refusal defers/downgrades the action rather than erroring, and
    never exceeds the design's G.
13. **+1** — Node-4 fault: triggers on Robot 0's first actually-admitted arrival at
    node 4, freezes it (position and cargo) for 6 minutes counting the arrival
    minute itself (the packet's explicit inclusive exception), and fires at most
    once per design's run.
14. **+2** — Machine-Q maintenance freeze correctly tracks and triggers: sums only
    Q's completed **processing** time (never setup), continuously across the whole
    run (never reset), and triggers the first time that sum reaches 12 at a
    completion boundary, firing at most once per design's run.
15. **+2** — Machine-Q maintenance freeze uses the correct boundary convention: the
    triggering completion minute itself is unaffected, and the freeze covers the 13
    minutes starting the minute **after** the trigger — the packet's *default*
    timing rule, deliberately stated with no inclusive exception, unlike node-4's
    explicit one in criterion 13. A freeze that starts on the trigger minute itself
    (copying node-4's convention) does not satisfy this criterion even if criterion
    14's trigger detection is otherwise correct.

### Integrated production execution — per-design values (criteria 16-27, weight 120)

Each pair of criteria checks one design's simulated `(makespan, bill)` pair and its
full trace reconciliation. Any attaining schedule passes; report however organized.

16. **+10** — D0: makespan 187, bill 1331.
17. **+10** — D1: makespan 161, bill 1242.
18. **+10** — D2: makespan 187, bill 1373.
19. **+10** — D3: makespan 185, bill 1408.
20. **+10** — D4: makespan 151, bill 1384.
21. **+10** — D5: makespan 153, bill 1298.
22. **+10** — D0's delivered trace reconciles: 20/20 lots done, 0 fixtures held, and
    cumulative bill equal to 1331 at the final boundary.
23. **+10** — D1's delivered trace reconciles the same way, final bill 1242, and
    shows the machine-Q maintenance freeze actually delaying a lot that would
    otherwise have started on Q during the freeze window (production witness W5).
24. **+10** — D2's delivered trace reconciles the same way, final bill 1373.
25. **+10** — D3's delivered trace reconciles the same way, final bill 1408.
26. **+10** — D4's delivered trace reconciles the same way, final bill 1384, and shows
    a machine job whose setup cost of 2 is attributable only to memory carried over
    from an earlier campaign (production witness W3).
27. **+10** — D5's delivered trace reconciles the same way, final bill 1298.

### Integrated production execution — named witnesses, verification, feasibility (criteria 28-35, weight 12)

28. **+3** — Within the design's required single continuous four-campaign trace (not
    an isolated fixture), Robot 0 is frozen at node 4 for exactly 6 consecutive
    minutes including its arrival minute, the other robot is unable to enter node 4
    during that window, and legally enters it the minute Robot 0 vacates (production
    witness W1). A fault that fires more than once in one design's run does not
    satisfy this criterion.
29. **+3** — Delivered trace (any design) shows at least one lot from an earlier
    campaign still open (not yet cured) at the minute a later campaign's first lot
    releases (production witness W2).
30. **+3** — Delivered trace (D1, D4, or D5) shows at least one oven batch whose two
    members belong to two different campaigns (production witness W4).
31. **+3** — Within the design's required single continuous four-campaign trace (D1,
    D2, D3, D4, or D5), Q is assignment-eligible for every minute up to its own
    maintenance-freeze trigger, then absent from every Q assignment for exactly the
    13 minutes after the trigger, then eligible again (production witness W5). A
    freeze computed from an isolated single-campaign fixture, one that fires more
    than once, or one that starts on the trigger minute itself, does not satisfy
    this criterion.

### Independent verification and adversarial checks (criteria 32-35, weight 4)

32. **+1** — Delivers and executes a separately-coded verifier that independently
    re-derives the full per-design trace (or an executed complete feasibility
    certificate covering fixture, power, node/edge capacity, and timing), sharing
    only immutable input constants with the primary implementation; a wrapper that
    imports the primary's transitions, feasibility checks, or state does not
    establish independence.
33. **+1** — The independent verifier's re-derived trace matches the primary's
    delivered trace exactly for all six designs. This criterion checks
    cross-implementation agreement only; correctness of the agreed-upon values is
    separately (and much more heavily) checked by criteria 16-27 and 36-41.
34. **+1** — Executes a copied-schedule mutation changing its earliest preparation
    start to -1; the verifier rejects the copy and accepts the preserved original.
35. **+1** — Executes a copied-route mutation causing an edge or interior-node
    conflict; the verifier rejects it, identifies the first invalid minute or a
    clearly mapped equivalent, and accepts the preserved original.

### Integrated production execution — per-design trace-integrity hash (criteria 36-41, weight 60)

Each design's complete minute-by-minute trace, canonically serialized as one line
per minute (`t,power,cumulative_bill`, in execution order, preceded by a
`DESIGN:<name>` marker line — see the reference command in
`platform/entry-guide.md`), hashed with SHA-256. This is sensitive to any single
divergent minute anywhere in that design's run, not just the final summary.

36. **+10** — D0's canonical trace hash matches `955957f0e6a9788d034f615b29341368fae4d42a5fa575a788379d3a6f1e3212`.
37. **+10** — D1's canonical trace hash matches `0e46cf0e88a3c39dd2e997d1184d70361a8d7a124b03e5715c05c5bb27deef46`.
38. **+10** — D2's canonical trace hash matches `3e42a4ac02477575336794f1283c0ac5193f439ef691ea2cb039cbb0a2c91bcd`.
39. **+10** — D3's canonical trace hash matches `c237acbc4fab1df9e28de4c573de705ba9f08d0c671392466c80ef41ec7a5c97`.
40. **+10** — D4's canonical trace hash matches `07824bc182e06107852a8196806f0a90c9f12cf33d01b3d7583380c0cd064374`.
41. **+10** — D5's canonical trace hash matches `80f5ceea7c33d2b145fc87f1a087c8dd1b1e6142c8767401ee2208d240cf940b`.

Generated by `reference/kilnworks_sim.py` (`canonical_trace_serialization` +
SHA-256); reproduce with the command in `platform/entry-guide.md`. These were
copied from executed output, not hand-typed — cross-check against
`platform/production-witnesses.md` and `platform/frozen-packet-manifest.json`
rather than retyping.

### Decision/causal reconciliation (criteria 42-47, weight 6)

42. **+1** — Applies the lexicographic key `(makespan, bill+3*capital, capital, ID)`
    across all six designs' delivered results and selects its minimum. Grade
    selection arithmetic on the delivered metrics without recharging an upstream
    metric error already charged in 16-21; with correct metrics the result is
    D4, (151, 1432, 16, D4).
43. **+1** — Minimizes the same key within `capital<=9` (D0, D1, D2, D3). Grade
    population/selection on delivered metrics without recharging upstream metric
    errors; with correct metrics the result is D1, (161, 1263, 7, D1).
44. **+1** — Compares D0 (baseline) against both selected designs using the
    delivered executed objectives. Accept a comparison correct relative to
    delivered results despite an upstream error.
45. **+1** — Explains at least one actual routing, batching, or resource interaction
    using identifiable event times from a delivered production trace, connected to
    the recommendation. Any accurate supported interaction is acceptable (the
    node-4 fault forcing a reroute, the machine-Q maintenance freeze delaying a
    lot to P, and the F=2 designs' fixture ceiling preventing oven pairing despite
    the open-aisle retrofit, are three available examples, not a required set).
46. **+1** — Explains that distance-only travel omits shared undirected-edge and
    interior-node occupancy, so its bound alone cannot certify a feasible joint
    robot schedule or an achieved completion time.
47. **+1** — Explains that treating the four campaigns as independent per-campaign
    resets (ignoring overlapping release, persistent setup memory, shared
    fixture/robot/oven state, and the Q maintenance clock) would not reproduce the
    required continuous-run results, citing at least one concrete consequence.

### Negative trap (criterion 48)

48. **-8** — Embeds precomputed case-result values or schedule tables as substitutes
    for executing the simulator that produces reported results. Immutable input
    constants and computed search/verification caches do not trigger this
    active-behavior trap; omission alone does not trigger it.


## Numeric transcription checklist

- [ ] Prompt: 343 whitespace-delimited words (permitted 2-500).
- [ ] Analyze: 1352 characters (permitted 5-3000).
- [ ] Execute & Generate: 1143 characters (permitted 5-3000).
- [ ] Synthesize: 1221 characters (permitted 5-3000).
- [ ] Exactly 48 criteria (47 positive + 1 negative); weights in order:
      1,1,1,1,2,2,1,1,1,1,1,1,1,2,2,10,10,10,10,10,10,10,10,10,10,10,10,3,3,3,3,1,1,1,1,
      10,10,10,10,10,10,1,1,1,1,1,1,-8.
- [ ] Positive weights sum 221; criterion 48 alone has weight -8.
- [ ] Attachment filename: `kw-r3b.pdf` (unique to this revision; do not upload any
      R1/R2 file, and do not upload the earlier `kw-r3.pdf` that blind-pilot-1 saw —
      this hardened version adds Section G and Section H and has different bytes;
      verify against the hash in `frozen-packet-manifest.json`).
- [ ] Four campaigns 0..3, five lots 0..4 per campaign, twenty lots per design, six
      designs D0..D5 — one continuous trace per design, not 24 independent cases.
- [ ] Budget population `capital<=9` includes D0, D1, D2, D3 (D2 at equality).
- [ ] Correct unrestricted key: `(151, 1432, 16, D4)`.
- [ ] Correct capital<=9 key: `(161, 1263, 7, D1)`.

| Design | Makespan | Bill |
|---|---:|---:|
| D0 | 187 | 1331 |
| D1 | 161 | 1242 |
| D2 | 187 | 1373 |
| D3 | 185 | 1408 |
| D4 | 151 | 1384 |
| D5 | 153 | 1298 |

- [ ] Node-4 fault (S07): freezes 6 minutes including arrival, fires once per design.
- [ ] Machine-Q maintenance freeze (S13): triggers at cumulative processing >= 12;
      freezes 13 minutes starting the minute AFTER the trigger (not inclusive,
      unlike S07); fires once per design. D0 never triggers it (structural, not a
      bug — Q's total workload in D0 stays under 12).
- [ ] Witness W3 (D4): Q's campaign-1 job on global-index-6 lot runs 10 minutes
      (Qbase 8 + setup 2).
- [ ] Witness W4 (D1): mixed-campaign batch at t=50, members {global index 3, 7}.
- [ ] Witness W5 (D1): maintenance trigger at t=44, freeze [45,57]; Q's next job
      (global index 8) delayed to t=62 (vs t=55 if the mechanism were absent).
- [ ] All six per-design trace-integrity SHA-256 hashes are each exactly 64
      lowercase hex characters (verify programmatically, not by eye) and were
      copied from `production-witnesses.md` / `frozen-packet-manifest.json`, never
      retyped by hand.
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
    print(name, h)
"
```

## Frozen field manifest

| Frozen file | SHA256 |
|---|---|

| artifact/kw-r3b.pdf | `0fdfe24a70020217047f911ea1ddd03de408e009c4fcd5a92b02ac13fbe831ca` |

| prompt.md | `b5bbf7e7efbb351376c2305f014be0397dbe545f036fec8421f454e49ac17403` |

| ideal-flow.md | `4f055175e0d585b3b0eb8e458c3cf7a0e31a75182e5ad7ea29043f5e4e3266f0` |

| rubric.md | `cbd7dd968ab88c8eaa462c3da1b497fe99cf4b4cb80972c66d80cccce18ece37` |

| score-topology.md | `226d9d69420dea24207f6de3d6a73f7c1b5991daa4b3b895c1ac27b467e87bb2` |

| production-witnesses.md | `58bce4595349f7938c68d7f331593f469d5f63e959edbe076781a52d5fa6f254` |

| coverage-ledger.md | `6776110dba37c2dc4d9b25d889cdabc9660ca9d1003a34cd96615fba60015bd5` |

| numeric-transcription-checklist.md | `85f39307a11534b05cbbf745ecdca3a2533a8b7689d8cf051e55ee0cda627ac7` |
