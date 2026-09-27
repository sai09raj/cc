# Legitimate Difficulty Engineering for Frontier Models

## Difficulty must live in the task, not the grader

The task should be hard because the solver must reconstruct, execute, and reconcile a complex but complete technical system. It should not be hard because the author withholds a transition, demands an unstated key name, relies on a broken runtime, or grades one exact prose formulation.

An honest below-50 task has three properties:

1. **Sufficiency:** prompt plus artifact determine a valid answer.
2. **Depth:** arriving at that answer requires substantial multimodal and tool-based work.
3. **Robust failure:** frontier runs fail core technical requirements even after legitimate equivalents and generous tolerances are accepted.

## Semantic reconstruction is the entrance fee, not the stump

Assume the required frontier model—including Opus 4.8 Max at maximum effort—will correctly extract the visible rules, encode each local transition, write tools, enumerate the stated space, inspect its outputs, and repair obvious mistakes. Do not make “the model probably misses one semantic” the task's difficulty plan.

This does not reduce the need for a complete semantic contract. Hidden or ambiguous rules are unfair. It means the task must stay hard after semantics are granted.

Use the **semantic-grant test**:

> Give the hypothetical solver every local rule and measured constant correctly, and assume it can implement each rule in isolation. Must it still build and execute the full interacting system, debug nonlocal behavior, search a consequential design space, verify production evidence, and reconcile the final decision? If not, reject the architecture.

Keep these layers distinct:

| Layer | Role in a valid task |
|---|---|
| Visible semantic completeness | Fairness prerequisite; every rule, boundary, and priority is supplied |
| Local semantic reconstruction | Expect a frontier model to succeed; never rely on misreading as the plan |
| Temporal/global composition | Legitimate core difficulty across interacting state, resources, and time |
| Search/optimization | Legitimate only when driven by a correct model and coupled/non-monotonic decisions, not enumeration alone |
| Verification/reconciliation | Author-owned invariants, mutants, traces, and cross-file evidence expose self-consistent bugs |
| Robust score failure | Established only by frozen target-model pilots, individually below 50 under generous grading |

A visible-rule mistake by a model can still be graded wrong. The prohibition is on **relying on such mistakes as the primary architecture**, not on scoring genuine errors.

## What actually created difficulty in Task 01

The successful cache-hierarchy task used several interacting difficulty layers:

- a dense visual packet rather than a supplied source implementation;
- a revision note changing L2 lookup latency from a stale displayed value;
- two values measured from waveform axes rather than printed as numbers;
- behavioral rules distributed across a diagram, tables, and notes;
- algorithmic expansion into a 406-access workload;
- a cycle-accurate stateful simulation;
- an exhaustive 180-configuration sweep;
- a target reached only by a joint MSHR/prefetch change;
- non-monotonic behavior, where “bigger” was not reliably better;
- a tie-break that made an otherwise equivalent set of target configurations resolve uniquely;
- causal synthesis showing that AMAT and hit rate were misleading objectives;
- five mutually consistent output files.

The hard part was not one obscure fact. It was maintaining a consistent executable interpretation across visual extraction, event simulation, optimization, and explanation.

## Why the original Task 02 and Revision B failed to stump Opus

### Original arbiter repair: roughly 80–88%

The task supplied a small buggy RTL module and asked for a repair plus verification. Once the interface and protocol were understood, a strong model could replace the internal logic with a clean state machine. More edge cases increased coverage but did not change the essential solution path.

### Revision B tagged ROB: 100% and 99%

Revision B added a dense card, generation tags, flush behavior, randomized tests, hashes, and report requirements. It still supplied a small, rewriteable state machine. Both Opus runs:

- cropped/read all panels;
- installed a simulator;
- built a Python oracle;
- validated the worked trace;
- reimplemented the ROB;
- ran directed and randomized tests;
- tested the original buggy RTL as a control;
- produced all requested artifacts.

The 99% run missed only a report attribution: it did not explicitly tie the exact cycle-38 post-edge `head/tail/occupancy = 3/4/1` state to Panel C. That is not a meaningful technical stump. Revision B was therefore not repairable by adding more report criteria, rubric weight, or prompt detail.

## Why Revision C looked successful

Revision C switched to a stronger architecture:

- visual-only controller specification;
- measured waveform constants;
- revision override;
- detailed same-cycle event order;
- generated 624-request workload;
- deterministic simulator;
- exhaustive 272-point sweep;
- coupled throughput/tail-latency targets;
- multiple alternative optima and tradeoffs;
- five delivered files.

This architecture did push Opus to 36%, 38%, and 41%. The models spent 34–56 minutes, used 80–123 tools, implemented full simulators, and generated complete result packages. That is the right scale of work.

However, all three runs converged on the same result because the artifact omitted a transition present in the private oracle. The architecture was strong; the specification contract was not complete. This distinction matters: a well-designed hard task can still be invalidated by one hidden semantic.

## The difficulty stack

Use several independent layers. No single layer should be a hidden trick.

### Layer 1 — genuine visual extraction

Good examples:

- measure waveform spans against local axes;
- infer topology from arrows and containment;
- read a state transition from edge direction and labels;
- resolve one visually marked revision override;
- distinguish row/column/bit-field geometry;
- trace a data path through multiple panels.

Weak examples:

- read a number from a screenshot of text;
- OCR a table whose layout has no technical role;
- attach an image but restate every decisive fact in the prompt.

### Layer 2 — distributed specification reconstruction

Make the solver combine facts across panels, but ensure all links are explicit enough to support one semantics. Useful distribution includes:

- timing in one panel;
- ordering in another;
- legal ranges and tie-break in another;
- workload generation elsewhere;
- serialization rules in a footer.

Do not create accidental contradictions or rely on the solver to guess which silent convention wins.

### Layer 3 — stateful execution

The system should have interactions that cannot be reduced to independent row calculations:

- resource queues;
- outstanding operations;
- same-cycle precedence;
- blocking and backpressure;
- refresh/reset/flush;
- mutable policy state;
- serialization and completion.

Every state transition, including idle transitions, must be visible.

### Layer 4 — exhaustive or broad search

A legal design space adds real work when:

- every configuration must be executed;
- constraints make some combinations illegal;
- the optimum is non-monotonic;
- a tie-break determines selection;
- different objectives select different designs.

Do not call a partial sweep exhaustive. Include a row-count check.

### Layer 5 — coupled objectives

The best tasks force tradeoffs. Examples:

- total completion time versus tail latency;
- energy versus throughput;
- area versus numerical tolerance;
- capacity versus queueing;
- accuracy versus resource ceiling.

A recommendation should require satisfying multiple thresholds, not simply minimizing one metric.

### Layer 6 — cross-file consistency

Require outputs whose contents constrain one another:

- executable implementation;
- baseline structured data;
- recommendation structured data;
- full sweep table;
- causal report;
- optional waveform or trace.

The difficulty is valid only if each file’s required content is stated and rubric-covered. File existence alone is too weak.

### Layer 7 — causal synthesis

Require the solver to explain:

- the actual bottleneck;
- why the obvious metric is misleading;
- why one-knob changes fail;
- why the chosen joint change succeeds;
- which metrics worsen;
- what alternative objectives select;
- where the conclusion is workload-specific.

This prevents a table dump from being a complete answer.

### Layer 8 — temporal-composition evidence

Task 03 and Task 04 showed that a solver can state local rules correctly, pass isolated fixtures, and still compose those rules incorrectly over a long execution. The task therefore needs observable evidence from ordinary production runs:

- linked checkpoints sampled from one uninterrupted execution;
- trace rows or short trace windows spanning early, middle, and late behavior;
- metamorphic relations across scenarios or configurations;
- conservation identities evaluated on live state; and
- cross-file reconciliation between summary, checkpoint, and full trace.

Choose witnesses mechanically from executed output and declare their schema and index base. They must be visible consequences of supplied semantics, not hidden answer literals. An integrated criterion may pair a rule with its production witness only when the witness is the named execution manifestation of that same rule; do not attach unrelated metrics merely to increase weight.

One upstream mistake can corrupt many later events. Run a causal-ownership audit so twelve downstream mismatches are not automatically treated as twelve independent bugs. Spread witnesses across distinct mechanisms, resources, epochs, and event types, and prefer checkpoint deltas or metamorphic invariants when they isolate ownership better than single rows.

## Techniques that do not create legitimate difficulty

### More criteria

A 50-item rubric does not make the task harder if 40 items are trivial or redundant. It only increases typing and error risk.

### Longer exact literals

Hashes are useful integrity evidence, but copying 64 hexadecimal characters is not frontier reasoning. A hash should verify an underlying executed sequence, not dominate score or become a transcription trap.

### Hidden conventions

Unspecified event ordering, fallback behavior, or latency endpoints create ambiguous rivals. This is a fake stump even if the author believes one convention is “obvious.”

### Self-authored tests only

A model can write an implementation and tests that share the same bug. Use author-owned invariants, reference traces, mutant cases, or a checker—without exposing golden outputs as pass literals.

### Small clean rewrite

If the model can discard the supplied implementation and reproduce a tiny state machine from the spec, localized bugs are not a long-horizon barrier.

### Cosmetic report burden

Requiring dozens of attributions, headings, or repeated values can lower score through omission but does not demonstrate technical failure.

### Environmental fragility

A missing DLL or unavailable package may cause failure, but it tests packaging luck rather than domain reasoning.

## Frontier-model attack checklist

Before finalizing a concept, assume the model will:

- crop and enlarge every panel;
- use OCR and pixel calibration;
- install or switch tools;
- write a clean implementation from scratch;
- write a separate oracle;
- run randomized tests;
- enumerate the entire search space;
- inspect output files and hashes;
- derive alternate objective optima;
- use remaining time to self-audit.

If the task becomes easy under those assumptions, redesign it now.

Also assume the model will implement a locally plausible approximation: correct filenames, schemas, many state rules, the full sweep shape, and even the headline recommendation, while composing the event system incorrectly. Counterfactually grade that answer. If package and local-rule points can carry it to 50%, the task's scoring topology is not ready even if its architecture is genuinely difficult.

## How to strengthen a weak task fairly

Fair strengthening changes the engineering work, not the scoring interpretation:

- require preservation of a large existing architecture rather than a clean rewrite;
- use multiple interacting components or files;
- introduce partial-order or simultaneous-event behavior;
- require an author-owned checker or invariant set;
- include adversarial cases not exhausted by one worked trace;
- require measured visual constants and clear revision resolution;
- use a non-monotonic design space with coupled targets;
- require a second iteration-dependent deliverable such as a debugging log, corrected artifact, or before/after evidence;
- impose a meaningful resource, tolerance, latency, or saturation constraint;
- remove an overly revealing hint while keeping the task complete.

Never strengthen by hiding semantics, tightening a rubric after seeing the answer, or refusing legitimate equivalents.

## Reusable future-task shape

The strongest reusable pattern from our experience is:

```text
dense but complete visual specification
  + measured constants and one explicit override
  + multi-component stateful model
  + author-owned invariant/mutant suite
  + algorithmic workload generation
  + exhaustive constrained search
  + coupled thresholds and explicit tie-break
  + integrated witnesses from ordinary uninterrupted execution
  + a plausible-wrong survival ceiling below 50%
  + executable + structured outputs + causal report
```

The artifact must explicitly cover every semantic used by the oracle. That final condition is more important than any extra layer of complexity.
