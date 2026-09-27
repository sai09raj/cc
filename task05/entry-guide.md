# KILNWORKS Task05 - complete R2-F1 entry guide

CURRENT DISPOSITION: REJECTED FOR DIFFICULTY. Two supplied target-model trajectories solve this candidate successfully; the user reports100% scores. This guide is retained as the exact historical transcription package. Do not spend further target-model runs on unchanged R2-F1 or use it as an accepted submission. See audit/target-runs and STATUS.md. Frozen prompt, Ideal Flow, rubric and weights are not being changed retrospectively.

Status: frozen for one local blind calibration. This is a complete transcription package, not a claim of submission readiness. No target-model pilot, preferred acceptance score, platform linter execution or platform transcription verification is archived yet. The local blind run must be reviewed before deciding whether this architecture merits a target pilot.

## Exact field placement

1. Attachment: upload only `KILNWORKS-T05-R2-20260926.pdf` from the artifact folder. It is the four-page visual engineering specification. Do not attach this guide, rendering source, private reference, goldens, rubric, hashes or audits.
2. Prompt field: paste the entire Prompt block below.
3. Ideal Flow: paste Analyze, Execute & Generate and Synthesize into their respective separate fields.
4. Rubric: enter criteria1-41 below in exactly that order, each with its displayed unchanged signed weight. Each block is the complete criterion text.
5. Target model/effort: the user-requested target is Claude Opus4.8 at maximum effort. Availability has not been verified. Select the required target only when the platform makes it available; do not silently substitute this local solver.
6. First target-model execution: one pilot only, after local gates permit it. Preserve its trajectory and outputs. Do not launch remaining preferred runs until a fair technical sub50 pilot is reconstructed and verified.
7. Linter: use platform/linter-responses.md only for matching warnings; investigate real contradictions and record actual warnings/decisions.

## Prompt

```text
You are the production-optimization engineer for a small kiln plant. Use the attached KILNWORKS-T05-R2-20260926.pdf as the complete engineering specification. Recover the aisle graph from its drawing and optimize actual robot routes jointly with preparation and curing; all units, boundaries, workload formulas and investment rules are in the packet.

Implement and execute an exact offline solution for every design/campaign. Find the lexicographically optimal makespan and energy bill, then make both investment selections. Verify the results through a separately runnable implementation or an independently checked complete optimality certificate. Use tools to inspect, build, execute, diagnose and verify your work.

Deliver six logical products as files: optimizer source; independent verifier source; machine/batch schedules and minute-by-minute robot actions; the complete case matrix with both selections and their keys; certification evidence including production traces and adversarial-check results; and an engineering memo. Use descriptive filenames and give the commands that reproduce the files. Multiple source files, equivalent schemas, compressed evidence, and different optimal schedules are welcome.

The memo must include your graph interpretation, commands and tool versions, evidence of all optimum checks, comparison of the baseline with both selected designs, and a causal explanation tied to actual production events. Include the negative-start and route-collision verifier experiments from section H. Explain what a distance-only relaxation loses. Base all reported results on your delivered executed implementation; do not embed precomputed case answers as the solver.
```

## Ideal Flow: Analyze

```text
Read KILNWORKS-T05-R2-20260926.pdf and reconstruct the solid/dashed aisle graph from the drawing. Distinguish docking bays from capacity-one interior nodes and undirected edge occupancy from endpoint occupancy. Reconstruct release, setup memory, fixture lifetime, atomic minute actions, pickup/unload visibility, fixed same-family batches, aggregate power and tariff arithmetic. Treat routes, machine assignments, starts, waiting and batch membership as joint decisions. Generate all five lots for each of four campaigns and all six design IDs. Define the lexicographic makespan/bill objective and separate unrestricted versus capital<=9 selection populations. A distance matrix alone cannot establish a feasible joint route.
```

## Ideal Flow: Execute & Generate

```text
Build an offline exact optimizer and a separately runnable independent verifier, sharing only immutable input data. Execute all24 design/campaign cases. Establish each minimum makespan, then its minimum tariff-weighted bill; preserve both feasible schedules and complete independent lower-bound evidence. Justify state merging and pruning rather than treating a search digest as proof. Deliver optimizer source, verifier source, schedules with every robot-minute, full case matrix and decisions, certification evidence with production traces, and an engineering memo. Reconcile each schedule with starts/completions, robot cargo/positions, machine/oven activity, fixture conservation, aggregate power and final bill. Run the negative-start and collision mutations, preserving the originals; identify the collision mutation's first invalid minute. Record commands/tool versions and a debugging or adversarial-check iteration. Equivalent offline algorithms, source organization, output schemas and optimal schedules pass.
```

## Ideal Flow: Synthesize

```text
Use executed optimal results to recommend D5 with key (33,1116,22,D5), and choose D1 under capital<=9 with key (37,1110,7,D1). Compare D0 against both selected designs using their executed objectives. Explain at least one actual routing, batching or resource interaction using event times from delivered schedules, and connect it to the recommendation. Explain why distance-only travel is a lower bound rather than a joint collision-feasible routing certificate. Reconcile schedules, traces, metrics, proofs and selection arithmetic. Describe an executed debugging or adversarial-check iteration. Any accurate supported interaction is acceptable; no particular route, optimal schedule or additional design comparison is required.
```

## Rubric in platform order

Positive total77. One negative trap-8. Criteria are binary. Local diagnostic normalization is points/77; official platform normalization has not been assumed. A supplemental proportional diagnostic prevents incomplete multi-case profiles from manufacturing a low-difficulty claim. Neither score changes the frozen weights.

### Criterion 1 | weight +1

```text
Executes the delivered offline optimizer with a documented command to generate the submitted case results; equivalent languages and source organization pass.
```

### Criterion 2 | weight +1

```text
Provides the six logical products as accessible files: optimizer, independent verifier, schedules, case matrix/selections, certification/traces/adversarial results, and memo. No particular filenames, schema or physical file count is required.
```

### Criterion 3 | weight +1

```text
Identifies all24 distinct design/campaign cases: D0..D5 crossed with campaign0..3. Extra explanatory records pass when these cases are unambiguous.
```

### Criterion 4 | weight +2

```text
Recovers solid undirected edges {0-3,3-6,3-4,4-7,6-7,7-8,5-8,2-5,1-4}, adding only4-5 for open designs D3/D5. Node=3y+x, P=3,Q=5,K=1; equivalent labels pass with an explicit mapping.
```

### Criterion 5 | weight +2

```text
Generates lots j=0..4 for campaigns s=0..3 with family=(j+s)%2, release=2floor(j/2), Pbase=5+(j*j+2s)%4 and Qbase=4+(3j+s)%5. Equivalent formula notation passes.
```

### Criterion 6 | weight +1

```text
Uses design inputs (F,G,aisle,capital): D0=(2,5,closed,0),D1=(3,5,closed,7),D2=(2,6,closed,9),D3=(2,5,open,6),D4=(3,6,closed,16),D5=(3,6,open,22).
```

### Criterion 7 | weight +2

```text
Reports D0 four-campaign optimum makespan profile as [41, 46, 39, 47] minutes, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.
```

### Criterion 8 | weight +2

```text
Reports D1 four-campaign optimum makespan profile as [34, 37, 33, 37] minutes, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.
```

### Criterion 9 | weight +2

```text
Reports D2 four-campaign optimum makespan profile as [41, 46, 39, 46] minutes, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.
```

### Criterion 10 | weight +2

```text
Reports D3 four-campaign optimum makespan profile as [40, 44, 39, 43] minutes, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.
```

### Criterion 11 | weight +2

```text
Reports D4 four-campaign optimum makespan profile as [33, 35, 31, 35] minutes, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.
```

### Criterion 12 | weight +2

```text
Reports D5 four-campaign optimum makespan profile as [30, 33, 31, 33] minutes, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.
```

### Criterion 13 | weight +2

```text
Reports D0 four-campaign minimum bill at optimum makespan profile as [267, 307, 300, 286] benchmark cost units, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.
```

### Criterion 14 | weight +2

```text
Reports D1 four-campaign minimum bill at optimum makespan profile as [255, 289, 251, 294] benchmark cost units, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.
```

### Criterion 15 | weight +2

```text
Reports D2 four-campaign minimum bill at optimum makespan profile as [266, 289, 290, 318] benchmark cost units, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.
```

### Criterion 16 | weight +2

```text
Reports D3 four-campaign minimum bill at optimum makespan profile as [254, 301, 260, 288] benchmark cost units, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.
```

### Criterion 17 | weight +2

```text
Reports D4 four-campaign minimum bill at optimum makespan profile as [264, 284, 249, 289] benchmark cost units, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.
```

### Criterion 18 | weight +2

```text
Reports D5 four-campaign minimum bill at optimum makespan profile as [267, 274, 230, 279] benchmark cost units, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.
```

### Criterion 19 | weight +1

```text
Resets production state separately for every case and completes operations at boundary t before simultaneous starts/actions occupying [t,t+1); a duration-d operation occupies [t,t+d). Starts use resources released at t, and execution ends at the final cure boundary.
```

### Criterion 20 | weight +1

```text
Assigns each lot in executed preparation once to P or Q after release, with at most one uninterrupted setup-plus-processing operation per machine; the machine frees on completion and prepared output waits in an unlimited buffer.
```

### Criterion 21 | weight +1

```text
Initializes executed machine family memory unset, updates it at preparation start, retains it through idle, and applies setup0 initially/on unchanged family or2 on a change; processing duration is the generated duration for the selected machine.
```

### Criterion 22 | weight +1

```text
Keeps executed fixture holdings at most F; each lot holds one continuously from preparation start through waits, transport and curing, releasing only at cure completion.
```

### Criterion 23 | weight +1

```text
Starts executed robots empty at nodes3 and5 with fixed identities and executes exactly one one-minute wait, adjacent drawn-edge move, pickup or unload action per minute. Pickup/unload/wait remain at the node; empty repositioning is allowed and locations persist.
```

### Criterion 24 | weight +1

```text
Executes pickups taking one prepared untransported lot at its source using an empty robot; cargo capacity is one and duplicate pickup is forbidden. Pickup becomes cargo at t+1; unloading occurs only at K and makes the lot available for curing at t+1. Every lot is conserved through its stages.
```

### Criterion 25 | weight +1

```text
Uses each undirected edge in executed routes at most once per minute, forbidding both swaps and same-direction sharing; boundary node capacity is1 except P/Q/K capacity2. Following into a vacated node is legal.
```

### Criterion 26 | weight +1

```text
Selects at executed oven starts one or two arrived uncured same-family lots while the oven is idle; membership stays fixed for4+family minutes, then all members finish together. Waiting arrivals do not automatically start curing.
```

### Criterion 27 | weight +1

```text
Respects aggregate G in every executed minute including ongoing operations and all new starts/actions: P=2,Q=3,oven=3,robot move/pick/unload=1 each, wait=0; setup draws full machine power and other idle resources draw zero.
```

### Criterion 28 | weight +1

```text
Computes makespan as final cure boundary and bill as sum over t=0..M-1 of total minute power times 1+(floor(t/7)%3). This checks arithmetic on delivered schedules independently of whether they are optimal.
```

### Criterion 29 | weight +2

```text
Delivers and executes a separately runnable verifier that independently reconstructs constraints and checks; shared material with the optimizer is limited to immutable instance data. Equivalent complete-certificate checkers pass; a wrapper importing optimizer transitions, feasibility or pruning does not establish independence.
```

### Criterion 30 | weight +10

```text
Independently establishes the minimum makespan for all24 cases through executed complete search excluding earlier completion or a checked complete mathematical certificate, with justified state merging/pruning. Feasible schedules, labels or hashes alone do not prove optimality; equivalent complete proof methods pass.
```

### Criterion 31 | weight +10

```text
Independently establishes the minimum bill at the minimum makespan for all24 cases through executed complete cost search or a checked complete mathematical certificate. This grades complete independent evidence, not another copy of the numerical result; equivalent complete proof methods pass.
```

### Criterion 32 | weight +2

```text
Produces chronological traces from the delivered uninterrupted schedules with starts/completions, both robot positions/cargo, active preparation/oven work, fixtures, minute power and cumulative bill; final time/bill reconcile with case records. Equivalent nesting, compression and simultaneous-event ordering pass.
```

### Criterion 33 | weight +2

```text
Applies the lexicographic key (max of four makespans,sum of four bills+3capital,capital,ID) to all six designs and selects its minimum. Grade selection arithmetic/population on delivered metrics without charging an upstream metric error again; with correct metrics the result is D5,(33,1116,22,D5).
```

### Criterion 34 | weight +2

```text
Minimizes the lexicographic key (max of four makespans,sum of four bills+3capital,capital,ID) within capital<=9, including equality and hence D0,D1,D2,D3. Grade population/selection on delivered metrics without recharging upstream metric errors; with correct metrics the result is D1,(37,1110,7,D1).
```

### Criterion 35 | weight +1

```text
Compares D0 with both selected designs using the delivered executed objectives. Accept a comparison that is correct relative to delivered results despite an upstream optimization error; do not require additional design pairs.
```

### Criterion 36 | weight +2

```text
Explains at least one actual routing, batching or resource interaction using identifiable event times from delivered production schedules, connecting it to the engineering recommendation. Accept any accurate supported interaction; no particular reference route or unrequested comparison is mandatory.
```

### Criterion 37 | weight +1

```text
Explains that distance-only travel omits shared undirected-edge and interior-node occupancy interactions, so its bound alone cannot certify a feasible joint robot schedule or achieved completion time.
```

### Criterion 38 | weight +1

```text
Executes a copied-production-schedule test changing its earliest preparation start to-1; verifier rejects the copy and accepts the preserved original. Equivalent test harnesses pass.
```

### Criterion 39 | weight +1

```text
Executes a copied-production-route mutation causing an edge or interior-node conflict; verifier rejects it, identifies the first invalid action minute or clearly mapped boundary, and preserves the accepted original. Either collision type suffices.
```

### Criterion 40 | weight +1

```text
Records optimizer/verifier reproduction commands and actual tool versions, sufficient to regenerate the delivered files in the declared offline environment.
```

### Criterion 41 | weight -8

```text
Embeds precomputed case-result values or schedule tables as substitutes for executing the optimizer that produces reported results. Immutable input constants and computed search caches do not trigger this active-behavior trap; omission alone does not trigger it.
```

## Numeric transcription checklist

- [ ] Prompt: 227 whitespace-delimited words (permitted2-500).
- [ ] Analyze: 725 characters (permitted5-3000).
- [ ] Execute & Generate: 1019 characters (permitted5-3000).
- [ ] Synthesize: 729 characters (permitted5-3000).
- [ ] Exactly41 criteria; weights in order: 1,1,1,2,2,1,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,2,10,10,2,2,2,1,2,1,1,1,1,-8.
- [ ] Positive weights sum77; criterion41 alone has weight-8.
- [ ] Attachment filename includes R2 and date20260926; do not upload R1.
- [ ] Four campaigns0..3, five lots0..4, six designsD0..D5,24 cases.
- [ ] Budget capital<=9 includesD2 at equality.
- [ ] Correct unrestricted key: (33,1116,22,D5); budget key: (37,1110,7,D1).

| Design | M by campaign0,1,2,3 | Bill by campaign0,1,2,3 |
|---|---|---|
| D0 | [41, 46, 39, 47] | [267, 307, 300, 286] |
| D1 | [34, 37, 33, 37] | [255, 289, 251, 294] |
| D2 | [41, 46, 39, 46] | [266, 289, 290, 318] |
| D3 | [40, 44, 39, 43] | [254, 301, 260, 288] |
| D4 | [33, 35, 31, 35] | [264, 284, 249, 289] |
| D5 | [30, 33, 31, 33] | [267, 274, 230, 279] |

- [ ] After entry, compare an export or screenshots of every field and weight with this guide. This checkbox remains unverified until that evidence exists.

## Frozen field manifest

Freeze timestamp UTC: 2026-09-27T05:36:50.977521+00:00. Manifest file: platform/frozen-packet-manifest.json. The guide is generated from these unchanged frozen files.

| Frozen file | SHA256 |
|---|---|
| artifact/KILNWORKS-T05-R2-20260926.pdf | `85d84267f20a1444f44fef0a96694a6322397486e58fcc5e40832ce3fb287ad8` |
| platform/prompt.md | `8ec5622a14994d06510f4b97e2dd7598c5e7c60bbd470d09ad564e4873cd2738` |
| platform/ideal-flow.json | `b5a049bf8c8e28127bac24ce8985acf289ddf5e1599bc6a2fab4e0486a0ed541` |
| platform/ideal-flow.md | `b499b6aa9f01c4928be4764ba8d37b954deb61c5559fd350819f8ed9bff86c59` |
| platform/rubric.json | `ec9ef900a6a554075ac8cb5ed2f292836cc8a10023c8c84c261bbc50eb68e4d0` |
| platform/rubric.md | `7eb84e628b56ffc2602f183e84bc9a4cecdd82daa8be92cd8d50c71fd876b301` |

## Run evidence and revision discipline

Archive exact model/effort metadata, original trajectory export, every source edit, final files, execution logs, screenshots/exports and criterion-by-criterion grading. Reconstruct final code from all edits and execute it against the frozen visible inputs. Compare feasibility and optimum results, allowing different optimal schedules. Locate the first invalid transition or first unsupported/incorrect optimization claim; distinguish technical failures from resource interruption, ambiguity and presentation.

If a pilot scores50 or more, do not change this rubric to suppress it. Diagnose architecture and score survival. Any new artifact/prompt/rubric revision needs a new identifier, exact field replacements, separate weight-change list, regenerated goldens and fresh run evidence. Three preferred target runs must each independently score below50; an average does not qualify.

No platform text has been entered by this task. The empty checkboxes and missing target scores are intentional records of unperformed user-controlled work, not approvals or inferred results.
