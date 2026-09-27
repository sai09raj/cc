# Case Study — Task 04 Relay, Revisions A–F

## Status and evidence boundary

Task 04 ultimately met the operational acceptance gate: the user reports that all three Revision F Opus 4.8 Max runs scored below 50%. The exact three Revision F score files and trajectories are not currently archived in this workspace, so this chapter does not invent their values or claim trajectory-level facts about those final runs.

The earlier revision evidence is stronger:

- Revision A's three 100% scores were reported by the user, and its trajectories reproduced the author results.
- Revision B's 52/61/64 scores are recorded in `task 04/revision-c/README.md`.
- Revision C's two documented scores are 91 and 100; no third score is documented.
- Revision D's 44/83/93 scores come from the user-supplied trajectory filenames in the authoring conversation; those trajectory files are not presently archived locally.
- Revision E's 37/52/59 trajectories were preserved and replayed. Its diagnosis is executable and independently checkable.
- Revision F's final outcome is user-confirmed as three sub-50 runs, while its exact scores remain an evidence-archival gap.

Treat the conclusion precisely: **Revision F passed this run gate; it does not guarantee that every future stochastic run will score below 50.**

## Task architecture

Task 04 asked the model to reconstruct and simulate a bespoke credit-controlled, two-route relay fabric from a single visual packet. Across the revisions, the model had to recover topology, visual timing constants, forward DATA and reverse control behavior, credit conservation, retry and acknowledgement rules, faults, same-cycle stages, a configuration sweep, selection rules, and causal explanations.

The final Revision F package required:

- one self-contained Python standard-library event simulator;
- 324 configurations in clean, cut, and echo scenarios, producing 972 sweep rows;
- baseline and recommended scenario records;
- five baseline/cut checkpoints;
- one complete baseline/cut execution trace;
- twelve named trace witnesses copied into `decision.json`;
- robust and clean-only selections; and
- a report reconciling implementation, outputs, failures, and one-knob neighbors.

This was a legitimate long-horizon multimodal task. The six revisions were needed because four different proofs had to succeed separately:

1. **Contract completeness:** the visible packet states every material rule.
2. **Oracle reproducibility:** independent implementations reproduce the same visible contract.
3. **Frontier difficulty:** target-model pilots fail central technical requirements.
4. **Post-pilot fairness:** the low scores remain low under generous grading and are not caused by ambiguity, packaging, or cosmetic omissions.

Passing one proof never implies the next.

## Revision chronology

| Revision | Material change | Reported scores | Disposition |
|---|---|---:|---|
| A | Five-edge acyclic relay, two forward routes, fixed credit/ACK delays, one shared serializer, 108 configurations × 3 scenarios | 100/100/100 | Correct and fair, but architecturally solved |
| B | Reverse K credit and ACK packets contend with DATA on physical serializers | 52/61/64 | Near the threshold, but per-serializer arbitration was not explicit enough |
| C | Clarified independent E/B burst arbitration at every serializer, including e4; removed revealing prompt hints; kept B's results and rubric | 91/100 documented | Clarification removed an ambiguity and showed that B's low-ish scores were not robust difficulty |
| D | Added bounded sink window `J`, out-of-order arrival versus in-order commit, commit trace events, window drops, and seven stages | 44/83/93 | Genuine new architecture, but stronger runs still used a simplifying implementation path |
| E | Replaced single arrivals with complementary U/V shards, exact `(ID,attempt)` rendezvous, expiry, and non-combinable retries | 37/52/59 | Only one run passed; integrated outputs were wrong but rubric topology still allowed two runs above 50 |
| F | Kept E's state model, goldens, and weights; clarified independent e0/e1/X/e4 E-runs and bound criteria 13–24 to twelve witnesses from one uninterrupted trace | Three user-reported scores below 50 | Passed the operational acceptance gate |

Old runs were never rescored under later revisions. Every revision used a new artifact name and a prospective contract.

## What Revision A taught

Revision A passed extensive author-side checks: source-to-code mapping, deterministic generation, independent reconstruction, mutation checks, image inspection, and a careful rubric. Those checks established correctness and fairness. They did not establish difficulty.

Once a frontier model encoded the five-edge state machine, the 108-configuration sweep was inexpensive. Three models solved the full package. More rubric rows, more output prose, or stricter grading would not have repaired the architecture.

Permanent rule:

> Local correctness evidence cannot substitute for an actual target-model difficulty pilot.

## What Revisions B and C taught

Revision B added a meaningful congestion mechanism: K and ACK controls became first-class reverse transmissions competing with DATA. Scores fell to 52/61/64, but the packet left room for a competing arbitration interpretation.

Its preflight also caught a separate activation defect: the first cut-drop window was shielded by an earlier launch block, so no baseline arrival could exercise it. The window was moved visibly to `[195,220)` and all dependent results were regenerated. This established a permanent distinction between **rule presence** and **production activation**.

Revision C made the intended rule explicit: e0, e1, X, and e4 each maintain their own E-run/BURST arbitration state; only X has the phase gate. The goldens and rubric stayed the same. The documented scores rose to 91 and 100.

This is important evidence, not a setback to hide. The clarification made the task fairer and easier to solve, proving that part of B's difficulty came from interpretation rather than the intended engineering challenge.

Permanent rules:

- Never count ambiguity-induced mistakes as legitimate difficulty.
- Removing prompt hints does little when the visible artifact still determines a short solution path.
- A clarification-only revision can increase scores; that is evidence that the clarification was necessary.
- If a complete and unambiguous architecture is solved, redesign the engineering system rather than making the prose more cryptic.

## What Revisions D and E taught

Revision D introduced a bounded moving sink window and separated physical e4 arrival from logical in-order commit. One run fell below 50, but two remained at 83 and 93. The architecture had become more stateful, yet strong runs still found a simplifying path through the system.

Revision E introduced a harder coupled state:

- every attempt creates complementary U and V shards;
- shards take complementary routes;
- only shards with the same `(ID,attempt)` may assemble;
- retries cannot combine with fragments from earlier attempts;
- incomplete assemblies expire;
- window admission and in-order commit remain separate; and
- commit alone creates the ACK.

This change created real temporal-composition difficulty. Yet Revision E still failed the acceptance gate at 37/52/59.

The reason was no longer simply the architecture. It was also **rubric score topology**.

Revision E's arithmetic mean was `49.33`, but that number had no acceptance value. The requirement applied to each run, and scores 52 and 59 individually failed it.

## Revision E trajectory forensics

The useful diagnostic was not the final metric difference. It was the first point at which the model's ordinary production execution diverged from the reference.

### Forensic procedure

1. Reconstruct the final solver implementation from trajectory `Write` and `Edit` operations.
2. Run that implementation on the frozen revision inputs.
3. Normalize its production outputs to the reference schema.
4. Compare complete traces in execution order.
5. Locate the earliest differing event.
6. Map that event to one visible semantic rule.
7. Check whether other runs share the same implementation choice.
8. Map the resulting failures to rubric points.
9. Revise prospectively; never use the new rubric to rescore completed runs.

Task 04 preserves this tooling in:

- `task 04/revision-e/reference/extract_runs.py`
- `task 04/revision-e/reference/compare_runs.py`
- `task 04/revision-e/opus-runs-37-52-59.md`

### The 52/59 common implementation

The 52 and 59 runs independently converged on the same baseline/cut behavior:

| Metric | Reference | Runs 52 and 59 |
|---|---:|---:|
| committed/acknowledged | 19/19 | 61/60 |
| p99 | 865 | 2195 |
| attempts | 146 | 185 |
| forward wire cells | 1430 | 1399 |
| K/A launches | 727/57 | 694/183 |
| window drops | 157 | 106 |
| orphan expirations | 39 | 1 |
| trace rows | 1534 | 1637 |

Their traces first diverged at zero-based event 389, which is one-based trace row 390, cycle 656, on e4:

```text
reference: (656,D,e4,16,1,U,3)
run 52/59: (656,D,e4,19,0,V,2)
```

Both implementations maintained E-run/BURST state only for the shared serializer X. On the other serializers, including e4, they used ordinary FIFO selection. The contract intended independent E-run state on e0, e1, X, and e4, with only X phase-gated.

Run 59 correctly blocked e4 DATA during the echo fault. Run 52 blocked controls but omitted the corresponding e4 DATA block. This explains part, but not necessarily all, of their seven-point score difference.

Run 37 changed the semantics more radically: it put reverse controls on a separate uncongested plane, blocked only DATA, and stopped retrying once committed rather than once acknowledged. It selected `(4,5,1,0,80,4)` and reported 12 robust and 131 clean-only configurations instead of the reference 4 and 33.

## The score-topology failure

Revision E contained 315 positive points. Criteria 2–31 carried 142 points of mostly local structure and rule compliance. The 52/59 runs also recovered the robust tuple set, robust recommendation, and clean-only recommendation, worth about 30 more points.

Thus a simulator with the wrong integrated event sequence could retain approximately:

```text
142 local/scaffolding points + 30 headline selection points
= 172 / 315
= 54.6%
```

This is the counterfactual score ceiling that should have been computed before the pilot. The task could contain genuinely difficult temporal composition and still fail the below-50 gate because broad local correctness outweighed globally wrong execution.

This does **not** mean all local-rule points are bad. It means a wrong-but-runnable implementation must not be able to coast above 50 while failing the core production behavior.

### Required score-topology audit

Before any future-task pilot, partition all positive points into:

1. package/existence/presentation;
2. local parsing and isolated rules;
3. integrated production execution;
4. final engineering decision and causal reconciliation.

Then score at least these counterfactual answers:

- empty or superficial package;
- runnable implementation with locally plausible rules but wrong temporal composition;
- correct simulator with different valid organization/wording;
- correct outputs with a weak causal report;
- strong report copied around precomputed tables or isolated fixtures.

Reject the rubric before entry if the second answer can retain 50% or more.

## What Revision F changed

Revision F did not invent a new oracle or retune the goldens. It made two targeted prospective changes:

1. The packet and Ideal Flow explicitly stated that e0, e1, X, and e4 have independent E-run counters. Every serializer applies BURST arbitration when both classes are eligible; only X is phase-gated.
2. Criteria 13–24 retained their existing weights but each local semantic was paired with a witness from the same uninterrupted baseline/cut production trace.

Those twelve rows carried 67 of 315 positive points. Both reconstructed 52/59 implementations missed all twelve trace witnesses, so the demonstrated wrong integrated engine could no longer retain those points merely by describing local rules.

### Revision F production witnesses

All ordinals below are **one-based trace data-row numbers**:

| Criterion | Row | Production record `(cycle,type,edge,id,attempt,shard,cells)` |
|---:|---:|---|
| 13 | 390 | `(656,D,e4,16,1,U,3)` |
| 14 | 400 | `(672,K,e2,19,0,V,2)` |
| 15 | 513 | `(824,K,e4,19,1,U,1)` |
| 16 | 514 | `(825,K,e1,18,2,V,3)` |
| 17 | 769 | `(1215,K,e4,20,4,V,1)` |
| 18 | 770 | `(1217,D,e3,23,3,V,3)` |
| 19 | 1025 | `(1625,D,e3,22,6,V,1)` |
| 20 | 1026 | `(1625,D,e4,20,6,U,2)` |
| 21 | 1281 | `(2020,K,e1,21,9,V,3)` |
| 22 | 1282 | `(2021,D,e0,22,8,U,1)` |
| 23 | 1501 | `(2353,K,e4,22,10,U,1)` |
| 24 | 1534 | `(2400,D,e4,24,10,U,3)` |

The witnesses span early, middle, and final execution; DATA and K events; different edges; several IDs, attempts, and shards. They are not twelve unrelated bugs. They are distributed observable consequences of correct temporal composition.

### Why these witnesses were fair

- They came from one ordinary production execution, not isolated fixtures.
- The prompt required the full trace and the twelve records in `decision.json`.
- The packet visibly specified the rules that generate them.
- The rubric declared the tuple schema and one-based indexing.
- Equivalent JSON nesting and descriptive keys remained acceptable.
- The solver still had to produce the complete trace; copying twelve literals could not manufacture the required sweep and cross-file consistency.
- Old Revision E runs were not rescored under F.

An integrated-witness criterion is defensible only when the witness is explicitly the execution manifestation of that same semantic rule. Do not join an unrelated rule and metric merely to increase its weight.

### Certification retained

Revision F preserved and revalidated:

- 972 unique sweep rows;
- four robust configurations and recommendation `(4,7,1,4,160,4)`;
- 33 clean-only configurations and recommendation `(4,5,1,0,160,4)`;
- 1534 baseline/cut trace rows with D/K/A/C counts 731/727/57/19;
- all twelve decision probes;
- two byte-identical full regenerations; and
- a PNG containing only the structural `IHDR`, `IDAT`, and `IEND` chunks.

The metadata check establishes artifact hygiene only. It is not proof of detector evasion and should never be described that way.

## What worked

1. **Prospective architectural revisioning.** Every substantive change created a new packet and invalidated old scores for selection.
2. **Packet-only independent reconstruction.** This protected fairness even when it did not predict model difficulty.
3. **First-divergence trace analysis.** One row at cycle 656 explained many downstream metrics more clearly than comparing final summaries.
4. **Counterfactual score analysis.** Replaying the 52/59 implementations exposed why globally wrong simulators still exceeded 50.
5. **Production-linked evidence.** Distributed witnesses from one uninterrupted run tested rule composition, not isolated fixture memorization.
6. **Minimal Revision F delta.** Only the artifact/prompt/Analyze/Execute fields and rubric criteria 13–24 changed; Synthesize, all other rows, all weights, and all goldens remained frozen.
7. **Changed-only handoff files.** `changed-rubrics.md` reduced retyping and protected unrelated rows.
8. **Unique short artifact names.** `t04a.png` through `t04f.png` reduced cache and transcription confusion.
9. **Honest evidence labels.** Preflight, pilot hypotheses, user-reported scores, and trajectory-verified findings remained distinct.

## What did not work

1. **Assuming correct/fair meant difficult.** Revision A disproved this with three 100% solves.
2. **Adding mechanisms without attacking the model's shortcut.** B and D increased state but still left a manageable implementation path.
3. **Treating ambiguity as difficulty.** B's arbitration ambiguity lowered scores; C's clarification raised them.
4. **Removing hints instead of changing the solution path.** Strong models recovered the complete rules from the artifact.
5. **Relying on isolated/local conformance.** A model can implement every local-looking rule yet compose them incorrectly over thousands of cycles.
6. **Letting local/scaffolding weight exceed the threshold.** E's wrong integrated engine could still retain roughly 54.6%.
7. **Launching a batch before replaying one pilot.** One replay-and-diff cycle would have revealed the shared shortcut earlier.
8. **Chasing linter wording without preserving semantic labels.** Scenario names, tuple types, row bases, and separate robust-versus-clean targets must be explicit; stochastic linter warnings are not authority over a coherent frozen contract.
9. **Manual retyping of unchanged text.** It consumed time and introduced commas, missing fields, and tuple errors. Use canonical changed-only text and exact diffs.
10. **Claiming certainty before evidence.** No local audit could honestly promise three sub-50 stochastic runs.

## Linter and transcription lessons from Task 04

The platform linter was heuristic and could surface different warnings on unchanged cards. Its feedback was useful when it found a real mismatch, but it was not authority over the frozen technical contract.

Every exact criterion should name enough dimensions to prevent false collisions:

```text
revision + tuple/configuration + scenario + time scope + stage + population + metric
```

Task 04 repeatedly exposed these distinctions:

- baseline/clean final `p99` and baseline/cut final `p99` are different objects, not contradictory values;
- the robust-feasible set/count/recommendation ranges over all three scenarios, while clean-only qualification has a different population;
- a cycle-360 stage-7 checkpoint count is not a final-horizon summary count;
- same-cycle handling can coexist with stage-snapshot deferral of controls created later in that cycle;
- requiring a live simulator and penalizing embedded precomputed tables are complementary conditions, not conflicting instructions; and
- parallel clean/cut/echo vectors should use the same metric schema unless a difference is explicitly intended.

When a warning is real, repair the artifact, prompt, Ideal Flow, oracle, and affected rubric rows as one revision. When it is false, record the exact namespaces and sibling ownership in the invalidation reason rather than rewriting correct semantics repeatedly.

For manual transcription, prioritize semantic characters:

- commas separating tuple fields;
- signs and interval brackets;
- enum values such as U/V;
- tuple arity and row ordinals;
- filenames, scenario labels, and stage numbers; and
- required final sentences.

Compound-adjective hyphens such as `cycle accurate` versus `cycle-accurate` usually do not change technical meaning. Task 04 lost time polishing harmless hyphens while malformed tuples and missing fields were the real risk.

## Revision discipline learned from F

For every prospective revision, create a delta manifest containing:

- new revision ID and unique attachment filename;
- exact old and new model-facing files;
- changed prompt passages;
- changed Ideal Flow fields;
- changed rubric IDs and whether text or weight changed;
- explicitly unchanged rubric IDs and weights;
- regenerated outputs and checksums;
- old runs invalidated for acceptance;
- new pilot required; and
- human copy instructions in UI order.

Do not generalize “never change weights.” F kept weights because the existing weights could be attached fairly to production evidence. If a future task's pre-pilot topology audit finds bad weights, fix them before any pilot and freeze them afterward.

## Mandatory gate sequence for every future task

1. Read the official sources, this playbook, Task 03's integrated-checkpoint lesson, and this case study.
2. Choose an architecture whose central difficulty is temporal or cross-component composition, not a small clean rewrite.
3. Freeze one complete visible semantic contract before writing the oracle.
4. Perform bidirectional source↔code tracing for every branch, order, boundary, counter, tie-break, and metric.
5. Obtain packet-only reconstruction and a fresh final packet audit from isolated reviewers.
6. Test plausible rival implementations and realistic mutants across the full configuration space, not only the baseline.
7. Generate a full ordinary execution trace and select representative early/middle/late production witnesses mechanically.
8. Declare trace schema and index base explicitly; never hand-copy witness values from memory.
9. Build the rubric from coverage and score topology. Verify that a locally plausible but globally wrong implementation cannot retain 50%.
10. Regenerate twice from clean directories and compare bytes, row counts, selections, checkpoints, traces, and cross-file reconciliation.
11. Enter the platform from canonical files; compare screenshots against local text and preserve a changed-only manifest.
12. Run exactly one target-model pilot first.
13. Reconstruct and replay its delivered implementation; find the earliest production divergence and calculate a generous score.
14. If the pilot is at or above 50, cosmetically wrong, environmentally blocked, or coherently ambiguous, stop. Repair before launching a batch.
15. Only after one genuine fair sub-50 pilot, run the remaining acceptance runs on the identical frozen revision.
16. Archive exact score evidence, trajectories, model/effort, frozen file hashes, grading sheets, and any convergence analysis.

## Evidence archive still required

The Task 04 Revision F package is locally certified, and the user confirms three passing scores. To close the historical record completely, archive when available:

- exact three score values;
- trajectory filenames and copies;
- model and reasoning setting screenshots;
- platform rubric export or grading sheets;
- frozen Revision F file hashes; and
- a short generous-grading confirmation for each run.

Absence of these files does not erase the user-reported outcome, but it limits later causal claims.

## Evidence paths

- `task 04/STATUS.md` — historical through Revision B; not the final status
- `task 04/CONTEXT.md` — historical through Revision B; not the final status
- `MAGNETIC-RAINSTORM-AUTHORING-PLAYBOOK/10-TASK-04-PREFLIGHT-LESSONS.md`
- `MAGNETIC-RAINSTORM-AUTHORING-PLAYBOOK/11-TASK-04-PILOT-FAILURE.md`
- `task 04/revision-b/README.md`
- `task 04/revision-c/README.md`
- `task 04/revision-d/README.md`
- `task 04/revision-e/README.md`
- `task 04/revision-e/opus-runs-37-52-59.md`
- `task 04/revision-e/reference/extract_runs.py`
- `task 04/revision-e/reference/compare_runs.py`
- `task 04/revision-f/README.md`
- `task 04/revision-f/changed-rubrics.md`
- `task 04/revision-f/reference/validate_f.py`

## Final lesson

Task 04 was not rescued by making the rubric harsher. It succeeded only after the author made the intended arbitration unambiguous, replayed the actual failed implementations, found the first integrated divergence, and made existing high-value semantic criteria require evidence from the same production execution.

For every future task, design that observability before the first expensive run.

Do not copy Revision F as a recipe for making the next model fail twelve semantic checks. Opus 4.8 Max already demonstrated that it can recover dense local protocol rules, and later frontier models may do better. Revision F repaired one task's demonstrated observability and score-topology weakness. Every new architecture must also pass the perfect-semantics ablation: even after all visible rules are understood correctly, substantial temporal composition, execution, search, verification, iteration, and engineering judgment must remain.
