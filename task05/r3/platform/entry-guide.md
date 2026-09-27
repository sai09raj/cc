# KILNWORKS Task05 - complete R3 entry guide

Status: frozen after two-round independent-reconstruction convergence (see audit/independent-reconstruction.md) and a pre-pilot score-topology audit (see platform/score-topology.md). No target-model pilot has been run yet. This guide is a complete transcription package, not a claim of acceptance-run success.

## Exact field placement

1. Attachment: upload only `artifact/kw-r3.pdf`. Do not attach this guide, design/, reference/, audit/, or any other private file.
2. Prompt field: paste the entire Prompt block below.
3. Ideal Flow: paste Analyze, Execute & Generate and Synthesize into their respective separate fields.
4. Rubric: enter criteria 1-39 below in exactly that order, each with its displayed unchanged signed weight.
5. Target model/effort: Claude Opus 4.8 at maximum effort. Do not silently substitute a local solver run for the target-model pilot.
6. First target-model execution: one pilot only. Preserve its trajectory and outputs; do not launch further runs until the pilot is reconstructed, replayed, and diagnosed per Playbook/04-PREFLIGHT-AND-VALIDATION.md.

## Prompt

```text
You are the production-optimization engineer for a small kiln plant. Use the attached kw-r3.pdf as the complete engineering specification. Recover the aisle graph, docking bays, and shared junction from the drawing; reconstruct the fixed dispatch policy the plant's control software already runs for machine assignment, robot routing, and oven batching (there is no free scheduling choice to search for); and reconstruct the one-time robot disruption at the shared junction from the packet.

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
printed as a number. Treat each of the six designs as one continuous run covering
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
arithmetic. Any accurate, evidence-tied causal argument is acceptable; no particular
route or additional design comparison is required.
```

## Rubric in platform order


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


## Numeric transcription checklist

- [ ] Prompt: 343 whitespace-delimited words (permitted 2-500).
- [ ] Analyze: 1064 characters (permitted 5-3000).
- [ ] Execute & Generate: 1143 characters (permitted 5-3000).
- [ ] Synthesize: 1136 characters (permitted 5-3000).
- [ ] Exactly 39 criteria (38 positive + 1 negative); weights in order:
      1,1,1,1,2,2,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,3,3,3,2,3,1,1,1,1,1,1,1,1,-8.
- [ ] Positive weights sum 61; criterion 39 alone has weight -8.
- [ ] Attachment filename: `kw-r3.pdf` (unique to this revision; do not
      upload any R1/R2 file).
- [ ] Four campaigns 0..3, five lots 0..4 per campaign, twenty lots per design, six
      designs D0..D5 — one continuous trace per design, not 24 independent cases.
- [ ] Budget population `capital<=9` includes D0, D1, D2, D3 (D2 at equality).
- [ ] Correct unrestricted key: `(142, 1356, 22, D5)`.
- [ ] Correct capital<=9 key: `(165, 1315, 7, D1)`.

| Design | Makespan | Bill |
|---|---:|---:|
| D0 | 187 | 1331 |
| D1 | 165 | 1294 |
| D2 | 187 | 1447 |
| D3 | 185 | 1401 |
| D4 | 155 | 1413 |
| D5 | 142 | 1290 |

- [ ] Node-4 fault: fires at minute 7 for D0/D2/D3/D4/D5, minute 9 for D1 (offline
      window = arrival minute + 5 more, 6 minutes total).
- [ ] Witness W3 (D4): Q's campaign-1 job on global-index-6 lot runs 10 minutes
      (Qbase 8 + setup 2).
- [ ] Witness W4 (D1): mixed-campaign batch at t=50, members {global index 3, 7}.
- [ ] After entry, compare an export or screenshots of every field and weight
      against this guide. This checkbox remains unverified until that evidence
      exists.

## Frozen field manifest

| Frozen file | SHA256 |
|---|---|

| artifact/kw-r3.pdf | `6b1b7ab16a7a3c0ee6b64988d9ce0716ee2c9125c8cc23bd37a940cb24cd0f7c` |

| prompt.md | `47ba85c4a5eaa1c8c03efdd9ad5c5a7d1ca7cf0264a2e2cc8ebf0bfb4b4353bd` |

| ideal-flow.md | `f86e621b342cb1bc43de93170c77cc1ee1e49e6599883cda561143254e90f3bb` |

| rubric.md | `9b04e3a6399ccef54bcb3c8e14dd3cd41cb038f7379fde862ae7508e4e616826` |

| score-topology.md | `a1fdd807ddeab97beec8f78f74e5859d77855066e27365831fc0ac3260dcdae4` |

| production-witnesses.md | `41c2160679d7d31ab3567aec81b544f729d0dbb1e3caaab5809fe7ab4af0f0e4` |

| coverage-ledger.md | `d31213513100dd201d698daeda247f1cd138d37818d50fc10b2907228d545baf` |
