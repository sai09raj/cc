# Start Here — Every Future Magnetic Rainstorm Task

## Scope of this file

This is the permanent routing page for every future task. It is not a substitute for the rest of the folder. A fresh model should receive the **entire playbook as working context**, begin here, then read the chapters routed below before proposing an architecture.

Current official project PDFs and the official handbook always override this empirical playbook.

## Central warning: semantic-only difficulty will not survive

Do **not** design a task whose below-50 outcome depends mainly on Opus 4.8 Max misunderstanding, overlooking, or inconsistently applying bespoke semantics.

Treat Opus 4.8 Max—and any later frontier model—as capable of:

- reading a dense visual packet carefully;
- reconstructing unusual state-machine and protocol rules;
- resolving distributed definitions across panels;
- writing a clean implementation from scratch;
- running broad tools and exhaustive searches;
- inspecting its own outputs;
- debugging discrepancies; and
- correcting an initial semantic mistake before submission.

Treat Opus 4.8 Max as the demonstrated capability floor from Task 04, not a permanent model ceiling. For each new task, substitute the current required frontier model and effort setting and repeat every gate in this file.

Visible semantic completeness is the **fairness floor**, not the difficulty engine. The semantics must be explicit, sufficient, and independently reconstructable. Hiding a transition, relying on ambiguity, or making wording deliberately cryptic is invalid difficulty. But merely supplying many unusual rules and hoping the model misapplies one is also not a durable architecture.

The task must remain difficult **after the model has reconstructed every semantic correctly**.

### Perfect-semantics ablation test

Before writing the oracle, imagine giving the solver a flawless one-page executable summary of every state transition, boundary, tie-break, and metric.

Ask:

1. Is substantial implementation and debugging still required?
2. Must multiple persistent state domains compose correctly over a long execution?
3. Is there broad workload generation, search, optimization, or adversarial verification that cannot be shortcut?
4. Are outputs mutually constraining across executable code, traces/checkpoints, structured results, and causal conclusions?
5. Is the final engineering decision non-obvious even after all local rules are known?

If the answer is mostly no, reject the concept. It is a semantic quiz, not a frontier-resistant engineering task.

### Difficulty that must remain after semantics are solved

A strong architecture should combine several of these independent burdens:

- **temporal composition:** interacting queues, resources, retries, failures, snapshots, and same-cycle order across a long run;
- **scale:** a workload or state space too broad for hand reasoning or a few worked examples;
- **nonlocal consequences:** early choices alter distant events, so local correctness does not guarantee global correctness;
- **search and optimization:** non-monotonic alternatives, coupled constraints, and an explicit tie-break;
- **implementation depth:** several interacting modules or algorithms rather than one small rewriteable state machine;
- **independent verification:** invariants, mutants, rival implementations, and production-trace reconciliation;
- **iteration:** inspect → build → run → diagnose → revise → rerun must be genuinely necessary;
- **cross-file consistency:** executable output, sweep, decision, trace/checkpoints, and report constrain one another; and
- **causal synthesis:** the response must explain why the observed result follows and why plausible alternatives fail.

No single obscure semantic should carry the task. A low score should still occur when the model extracts every local rule correctly but fails the genuinely difficult execution, optimization, verification, or reconciliation work.

## Required reading order

1. Current official PDFs and project handbook.
2. [README.md](README.md).
3. [01-END-TO-END-SOP.md](01-END-TO-END-SOP.md) through [04-PREFLIGHT-AND-VALIDATION.md](04-PREFLIGHT-AND-VALIDATION.md).
4. [09-CASE-STUDY-TASK-03.md](09-CASE-STUDY-TASK-03.md), especially isolated probes versus integrated checkpoints.
5. [12-CASE-STUDY-TASK-04.md](12-CASE-STUDY-TASK-04.md), especially trace forensics, score topology, and the limits of semantic-only failure.
6. [06-COPY-PASTE-TEMPLATES.md](06-COPY-PASTE-TEMPLATES.md) and [QUICK-CHECKLIST.md](QUICK-CHECKLIST.md).
7. Consult [05-CASE-STUDY-TASK-02.md](05-CASE-STUDY-TASK-02.md), [07-MISTAKE-REGISTER.md](07-MISTAKE-REGISTER.md), and [08-QMO-AND-COMMUNITY-GUIDANCE.md](08-QMO-AND-COMMUNITY-GUIDANCE.md) while designing and auditing.

## Mission for every new task

Design a task that is complete, fair, independently reproducible, substantively multimodal, tool-dependent, long-horizon, and difficult for the required frontier models under a frozen generous rubric. Transfer the playbook's method, not the surface architecture of an earlier successful task.

## Non-negotiable working rules

- Do not promise a below-50 outcome before target-model evidence.
- Do not rely on semantic misunderstanding as the principal failure mechanism.
- Do not treat local oracle agreement as difficulty evidence.
- Do not use hidden semantics, unavailable dependencies, fragile tooling, or exact-format traps.
- Do not launch a multi-run batch before replaying and diagnosing one pilot.
- Do not rescore an old run under a new prompt, artifact, Ideal Flow, or rubric.
- Do not let package/local/scaffolding points alone reach 50%.
- Do not use isolated fixtures as proof of full temporal composition.
- Do not manually retype long tuples, hashes, checkpoints, or traces from memory.
- Do not claim a fault or stress mechanism matters until it activates in an ordinary production run.
- Do not chase heuristic linter warnings without distinguishing revision, configuration, scenario, time/stage, population, and metric.

## Files to create before platform entry

Create a versioned task folder containing at least:

```text
README.md
STATUS.md
design/
  architecture-attack.md
  semantic-contract.md
  source-code-map.md
  rival-register.md
  mutation-plan.md
reference/
  executable oracle
  clean reproducibility validator
  golden outputs
audit/
  perfect-semantics-ablation.md
  packet-only reconstruction
  fresh final packet audit
platform/
  prompt.md
  ideal-flow.md
  rubric.md
  coverage-ledger.md
  score-topology.md
  production-witnesses.md
  entry-guide.md
  revision-delta.md
one uniquely named upload artifact
```

Keep private references, audits, the playbook, and goldens out of model-facing attachments.

## Architecture gate

Before implementation, write a one-page frontier attack answering:

1. If Opus reconstructs every semantic perfectly, is the remaining task still difficult?
2. Can the model replace the system with a small clean state machine?
3. Can it satisfy most points with plausible scaffolding and copied literals?
4. Can isolated tests be special-cased without composing the full system?
5. Are there multiple interacting persistent state domains, same-cycle orderings, or resource constraints?
6. Does the visual contribute a relationship that text-only OCR cannot replace?
7. Does the recommendation require broad execution and a coupled engineering tradeoff?
8. Are at least three post-semantics difficulty layers genuinely necessary?

Reject the concept if perfect semantic knowledge collapses the task, if questions 2–4 are yes, or if questions 5–8 are no.

## Oracle and specification gate

- Freeze the visible semantic contract before coding.
- Trace every material code branch back to a visible source.
- Trace every normative source rule forward to code and a test.
- Define idle/no-candidate behavior, counter persistence, exact boundaries, event order, metric endpoints, tie-breaks, and serialization.
- Reconstruct the task once from packet-only context before revealing the reference.
- Implement rival interpretations and realistic mutants.
- Test mutants across configurations and scenarios, not only one baseline.
- Record the first activation and observable effect of every fault, retry, expiry, timeout, and exceptional interval.
- Repeat the perfect-semantics ablation after the reference exists; reject the task if implementation and decision-making have become routine.

## Integrated-evidence gate

Generate ordinary production traces or checkpoints from the same uninterrupted runs that produce graded summaries. Select witnesses that:

- span early, middle, and late execution;
- cover different components and event types;
- expose plausible wrong implementations after local semantics are understood;
- are mechanically extracted;
- state whether indexing is zero- or one-based; and
- reconcile with full delivered output rather than replacing it.

Assign each witness a causal owner. If one upstream mistake corrupts many later rows, do not treat every downstream mismatch as an independent defect.

Do not blindly copy Task 04's twelve probes or 67-point allocation. Measure the new task's own failure surface.

## Score-topology gate

Record positive weight in four buckets:

| Bucket | Weight | Can a wrong integrated engine earn it? |
|---|---:|---|
| Package/presentation |  |  |
| Local semantics/rules/scaffolding |  |  |
| Integrated production execution |  |  |
| Decision/causal reconciliation |  |  |

Counterfactually grade two strong alternatives:

1. a solver with perfect local semantic reconstruction but incomplete or wrong global execution; and
2. a runnable, locally plausible, globally wrong implementation.

If either can earn 50% or more, redesign the architecture or rubric before the first pilot. Change weights now if needed; after a pilot, freeze them and make only prospective revisions.

## Pilot gate

Run one target-model pilot, then:

1. preserve its trajectory and exact score evidence;
2. reconstruct its final implementation from all file edits;
3. execute it on frozen inputs;
4. compare its full production trace against the reference;
5. identify the first divergence;
6. determine whether it actually misunderstood semantics or understood them and failed composition/execution;
7. map the divergence to the visible contract and rubric;
8. apply generous grading; and
9. classify the failure as semantic, integrated technical, ambiguous, environmental, cosmetic, or rubric-created.

A semantic error may be real evidence, but it is not enough by itself to establish durable frontier difficulty. Confirm that the task also demands substantial post-semantics work and that the rubric observes failure of that work.

Launch remaining acceptance runs only after a genuine, fair technical sub-50 pilot. If revising, issue a new artifact filename and complete a revision-delta manifest.

## Completion evidence

Do not call any future task successful until the archive contains:

- frozen prompt, artifact, Ideal Flow, rubric, and their hashes;
- architecture attack and perfect-semantics-ablation records;
- reference commands and clean-reproduction results;
- independent reconstruction and rival/mutant reports;
- score-topology and production-witness manifests;
- platform transcription verification;
- exact model/effort settings;
- every trajectory and score screenshot/export;
- one grading sheet per run;
- multi-run convergence analysis; and
- confirmation that every preferred run remains below 50 under generous grading.

Start with the templates in [06-COPY-PASTE-TEMPLATES.md](06-COPY-PASTE-TEMPLATES.md). Stop at the first failed gate rather than spending runs to discover a local defect.
