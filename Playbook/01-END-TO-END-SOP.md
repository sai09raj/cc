# End-to-End Magnetic Rainstorm Task SOP

## Purpose and control principle

This procedure moves from task concept to submission. Each phase has a deliverable and a gate. A failed gate sends the task backward; it must not be papered over by a stricter rubric or more runs.

The controlling sequence is:

```text
policy intake
  → domain and architecture
  → visual artifact and visible semantic contract
  → reference execution
  → independent reconstruction and rival interpretations
  → Ideal Flow
  → prompt and deliverables
  → rubric and linter
  → environment/runtime preflight
  → pilot run
  → required model runs
  → generous grading and convergence audit
  → preferred selection and submission
```

## Phase 0 — Freeze the authority and evidence set

### Actions

1. Inventory every official PDF, handbook, task input, draft, generated artifact, reference script, model trajectory, and score screenshot.
2. Declare the hierarchy:
   - official PDFs;
   - task prompt and supplied artifact;
   - source-cited handbook;
   - author notes and this empirical playbook;
   - model trajectories as evidence, not authority.
3. Record known source conflicts instead of silently resolving them.
4. Create a task manifest with exact filenames, sizes, hashes if useful, and purpose.

### Gate 0

Proceed only if all sources needed to define and verify the task are present, readable, legally supplyable, and named consistently. Broken links, missing files, or a prompt referring to the wrong panel/file are hard stops.

## Phase 1 — Choose a domain and task architecture

### Actions

1. Choose a domain in which the author can independently define correct behavior and diagnose rival answers.
2. State the real engineering decision the task simulates. Avoid a collection of disconnected facts.
3. Prove all four pillars:
   - **multimodal:** name the precise visual evidence that affects the answer;
   - **tools:** name the executable loop and why prose alone cannot solve it;
   - **expertise:** name the judgments or invariants requiring domain knowledge;
   - **long horizon:** name the dependent stages and outputs.
4. Select a difficulty architecture before drafting polished prose.
5. Assume the required frontier model recovers every visible local semantic and measured constant correctly. List the implementation, temporal-composition, search, verification, iteration, and decision work that remains.
6. Run the perfect-semantics ablation: if a flawless semantic summary collapses the task into a routine implementation or enumeration, reject the concept.

### Prefer architectures like

- reconstruct a system from a dense technical visual;
- measure one or more constants from axes or geometry;
- resolve a clearly marked revision override;
- generate a deterministic workload from compact phase rules;
- implement a stateful simulator or checker;
- exhaustively explore a legal design space;
- apply interacting constraints and a stated tie-break;
- produce multiple internally consistent output files;
- explain non-monotonic tradeoffs and alternative optima.

### Avoid architectures like

- repair one small module whose clean rewrite is obvious;
- ask the model to write its own tests for its own implementation with no independent checker;
- place all decisive values in OCR-readable text;
- request many report fields whose omission, rather than technical failure, drives the score;
- rely on one fragile exact string or hidden serialization convention;
- rely primarily on the model overlooking, misreading, forgetting, or inconsistently applying one bespoke rule;
- present a semantic quiz whose engineering work becomes routine once the rules are understood;
- create difficulty solely through volume, long literals, or arbitrary formatting.

### Gate 1

Reject the concept if a frontier model can replace the implementation wholesale, infer the intended answer from one worked trace, satisfy the core ask without interpreting the visual, or complete the remaining work routinely once granted every local semantic. Semantic completeness is required for fairness but is not itself evidence of difficulty.

## Phase 2 — Design the artifact and visible semantic contract

### Actions

1. Make the visual technically operative. At least one measured or spatial relationship must change the computation.
2. List every normative location: panels, diagram edges, waveform axes, footnotes, revision notes, legends, and serialization footer.
3. Build a **visible semantic contract** before coding. For each behavior record:
   - source location;
   - exact rule;
   - priority/order;
   - boundary convention;
   - tie-break;
   - reset/idle behavior;
   - interaction with other rules;
   - reference-code location;
   - adversarial test.
4. For state machines, enumerate the transition relation, including what happens when no outgoing condition is true.
5. For event simulators, define:
   - start/end-of-cycle convention;
   - same-cycle ordering;
   - when state becomes visible;
   - reservation and completion order;
   - inclusive/exclusive boundaries;
   - queue membership and occupancy definitions;
   - latency origin and endpoint;
   - refresh/reset behavior;
   - serialization and hashing.
6. Remove accidental contradictions. A red revision note must identify exactly what it overrides.

### Gate 2 — source-to-code completeness

For every material `if`, state transition, metric increment, sort key, or boundary in the reference code, point to a visible source statement. Conversely, every normative visual rule must map to code and at least one test.

If any material code branch has only “that is what we intended” as support, stop. Put the rule in the artifact or remove it from the oracle.

## Phase 3 — Build the reference solution and evidence chain

### Actions

1. Implement the reference from the semantic contract, not from remembered intent.
2. Keep specification constants separate from computed results.
3. Generate the workload algorithmically.
4. Execute the baseline and full legal sweep.
5. Save:
   - version/runtime information;
   - exact command lines;
   - generated outputs;
   - row counts;
   - metric summaries;
   - checkpoints;
   - serialization sample;
   - hashes;
   - assertions/invariants.
6. Perturb each decisive rule and confirm that tests detect the change.
7. Verify every golden literal by a second extraction path.
8. Prove every fault, timeout, retry, and exceptional interval actually activates in at least one certified production run and changes an observable result.
9. Run realistic mutants across the configuration/scenario space, not only the baseline. Preserve one concrete witness for every killed mutant.
10. Save complete ordinary-run traces or checkpoints that can later locate the earliest divergence of a pilot implementation.

### Goldens must be results, not pass conditions

It is acceptable for the rubric and private expected-results file to contain observed goldens. It is not acceptable for the requested solver program to embed those numbers as conditions that manufacture a pass.

### Gate 3

Proceed only if results reproduce from a clean run, every reported field is derived from execution state, and every claimed stress mechanism is demonstrably active rather than shielded by an earlier gate or empty workload region.

## Phase 4 — Independent reconstruction and ambiguity attack

This is the phase Revision C lacked.

### Actions

1. Give a reviewer only the user-visible artifact and prompt—never the reference code.
2. Ask the reviewer to write a prose semantic table before implementing anything.
3. Diff that table against the author’s contract.
4. Implement at least one **rival interpretation** for every ambiguous clause.
5. Compare outputs and identify which visible sentence resolves each divergence.
6. Create mutants for plausible mistakes: event-order swaps, strict/inclusive boundaries, fallback/no-fallback, state persistence, missing transitions, serialization ordering, queue accounting, refresh timing, tie-break ordering, stale revision values.
7. If two implementations agree, confirm they did not share code, derived notes, or hidden assumptions.

### The convergence alarm

If two or more strong model runs independently produce the same answer that differs from the reference:

1. pause grading;
2. identify their shared semantic choices;
3. compare those choices directly with the visible artifact;
4. implement their interpretation locally;
5. decide whether the artifact, oracle, or model is wrong;
6. revise and rerun if the task is ambiguous.

Do not treat correlated frontier-model disagreement as random failure.

### Gate 4

The visible task must determine one grading-equivalence class of correct answers. Multiple implementations and output layouts may be valid, but they must agree on the decision-relevant facts.

## Phase 5 — Write the three Ideal Flow fields

Each field must remain within the platform’s 5–3,000-character range.

### Analyze

Describe the evidence extraction and technical interpretation:

- which visual elements are normative;
- which quantities are measured;
- which revision notes override stale values;
- what state/order/geometry is reconstructed;
- what cannot be assumed from textbook convention.

Do not paste every golden metric. Focus on the reasoning contract and a small set of decisive expected observations.

### Execute and Generate

Describe the actual tool loop and concrete files:

- implementation language/toolchain;
- runtime commands;
- generated workload;
- exhaustive or bounded sweep;
- directed and randomized checks;
- output filenames and required contents;
- reproducibility and anti-hardcoding expectations.

### Synthesize

Describe the required causal argument:

- baseline bottleneck;
- why obvious one-knob or local fixes fail;
- why the recommendation works;
- tradeoffs and metrics that worsen;
- alternative objective optima;
- limitations and robustness.

### Gate 5

The three fields must describe the same task as the prompt and rubric. Run a terminology diff: filenames, panel names, counts, state names, thresholds, and tie-breaks must match.

## Phase 6 — Draft the prompt and deliverables

### Actions

1. Keep the prompt between 2 and 500 words.
2. State that the attached artifact is the complete specification only if it truly is.
3. Use positive instructions when possible. Instead of “do not assume conventional values,” say “derive the address map, turnaround values, event order, and scheduler behavior from the packet.”
4. Require named output files and describe the minimum contents of each.
5. State exact schema/order only when it is technically necessary and intended to be graded.
6. Require observed results from executed files.
7. State technically necessary prohibitions; remember each one creates rubric work.
8. Do not reveal so much of the expected result that the model can bypass the hard reasoning.

### Prompt completeness pass

For every noun in the deliverables—metric, figure, table, hash, checkpoint, file—answer:

- Is it defined?
- Is its source visible?
- Is its unit clear?
- Is its boundary convention clear?
- Is its accepted equivalent clear?
- Will a rubric criterion cover it?

### Gate 6

Hide all private notes and ask: “Could a competent solver construct a valid answer from only this prompt and attachment?” If not, repair the input. No rubric can cure missing specification.

## Phase 7 — Build and lint the rubric

Follow [03-RUBRIC-AND-LINTER-GUIDE.md](03-RUBRIC-AND-LINTER-GUIDE.md).

### Required passes

1. Prompt-clause coverage.
2. Deliverable/content coverage.
3. Expert-essential coverage.
4. Prohibition-to-trap coverage.
5. Overlap/duplication check.
6. Rival-answer fairness check.
7. Dependency/weight check.
8. Linter review.
9. Score-topology audit: partition weight into package, local, integrated, and decision evidence.
10. Plausible-wrong survival test: a runnable locally plausible but globally wrong implementation must remain below 50%.
11. Causal-ownership audit: integrated witnesses may expose a shared upstream defect, but unrelated or duplicate consequences must not multiply-charge it.

### Gate 7

Every criterion must be objective, binary, observable, verb-led, self-contained, and atomic except for a truly unitary answer object. It must accept valid equivalents and reject only an observable wrong action or result.

## Phase 8 — Runtime and environment preflight

### Actions

1. Identify the required runtime before platform entry.
2. Test a minimal compile/run with the exact executable.
3. Record its name/version and exact command.
4. Prefer a known-good container or official package source.
5. Avoid random Windows binaries. The earlier Icarus attempt repeatedly launched `ivl.exe` without `libgcc_s_seh-1.dll`; this consumed time and destabilized the workflow.
6. Confirm no privileged install, network download, or unavailable dependency is essential to solve the task.
7. If a container is expected, verify the engine is running and mount paths work.

### Gate 8

The task must be runnable in the model environment or explicitly provide a viable fallback. Test this before launching long runs.

## Phase 8.5 — Local blind pilot (before any platform entry)

### Purpose

Strictly cheaper than Phase 10's one official pilot: it spends no
external platform/target-model quota at all, using only a fresh
subagent inside this project's own environment. It is not a substitute
for Phase 10/11's real target-model pilots — synthetic mutants and a
local blind pilot are both pre-pilot confidence checks, not acceptance
evidence — but it catches the same class of problem (broken packaging,
genuine ambiguity, or a task that's simply too tractable for a careful
solver) before committing real pilot quota. Used for KILNWORKS/R3
(task05, two rounds) and caught a real composition bug before any
platform submission. Skipped for QUORUM-7, LEDGER-8, and TYPECHAIN-9 —
the latter two each then spent two real external pilots discovering,
expensively, a problem this step could plausibly have caught for free.

### Actions

1. Freeze the prompt and artifact exactly as they will be submitted.
2. Spawn a fresh subagent with zero memory of this conversation and zero
   access to `reference/`, `design/`, or `platform/rubric.md` — only the
   frozen `prompt.md` (renamed, e.g. `prompt.txt`) and the artifact
   file, in an isolated working directory.
3. Instruct it to solve the task exactly as a real pilot would,
   producing the same deliverables the prompt asks for.
4. Score its submission against the real rubric; reconstruct and
   re-execute its implementation on the frozen inputs; diff its trace
   against the reference's own trace to find the first point of
   divergence, if any.

### Gate 8.5

If the blind pilot solves the task cleanly (scores near 100%, or its
trace matches the reference with no meaningful divergence), treat this
exactly as Phase 10 treats a real pilot solving the task: redesign the
architecture before spending any platform-entry effort or real pilot
quota. This holds even when the same pilot also surfaces packaging
bugs; fix those, but do not count the fix as progress on difficulty
(mistake #70).

Run at least one blind pilot on the stronger `opus` model alias, and
run it as early as the engine and a draft artifact exist, before the
rubric and platform text are written. On CELLGUARD-10 the `opus`-alias
pilot and the user-run Opus 4.8 Max pilot graded identically (121/122),
while three Sonnet-tier pilots had found fewer spec gaps. Do not rationalize a clean blind-pilot solve as "the local model
is just unusually strong" without first checking whether the same
structural weakness (mistake #67: amplification without genuine
likelihood of the triggering mistake) is present.

## Phase 9 — Create a platform-entry package

### Actions

1. Freeze final text files for prompt, all three Ideal Flow fields, and rubric.
2. Generate a compact entry guide in exact UI order.
3. Keep canonical hashes/checkpoints in a verification table separate from prose.
4. Copy; do not retype, whenever the UI permits.
5. After entry, photograph or export every field and compare character-for-character.
6. Verify attachment filename/chip and open the uploaded artifact once.
7. Re-run linter after every edited criterion.

### Gate 9

No known transcription differences remain. Especially verify negative words (`deviates` versus `derives`), panel letters, digits, hexadecimal characters, braces, brackets, and tuple order.

## Phase 10 — Run one pilot

### Purpose

The pilot is not for gaming the rubric. It detects broken packaging, missing dependencies, shallow architecture, and ambiguity before six expensive runs.

### Audit the pilot

- Did it open and use the visual?
- Did tools run successfully?
- Did it produce requested files?
- Did it finish suspiciously quickly by replacing a small implementation?
- Did it find a coherent rival interpretation?
- Were failures technical or merely report omissions?
- Does generous scoring remain below 50%?
- Can its final implementation be reconstructed and replayed locally?
- What is the earliest divergence in an ordinary production trace?
- Which visible semantic rule owns that divergence?
- Does the rubric expose the integrated failure, or can local/scaffolding points still carry the response above 50%?

### Gate 10

Run exactly one target-model pilot before a batch. Preserve its trajectory and score, reconstruct its final implementation, execute it on frozen inputs, and diff its production trace against the reference. If the pilot solves the task, redesign the architecture. If it disagrees coherently, audit the specification. If it fails due to environment, packaging, or cosmetic reporting, repair those. Only a genuine, fair, generously scored technical failure below 50 supports launching the remaining acceptance runs.

## Phase 11 — Run the required models

Use the exact model/reasoning settings required by the current official UI and sources. The source set used here specifies Model A Opus 4.8 at max reasoning and Model B Muse Spark 1.1 at xhigh reasoning. Launch the same frozen prompt and artifact concurrently. Do not leak one model’s results into the other’s prompt.

Allow the expected long runtime. A two-hour timeout may be a scoreable outcome. Stay within ten runs per model.

The acceptance condition applies to every required preferred run individually. A mean below 50 does not rescue any run at or above 50.

For each run, record:

- model and effort;
- start/end and timeout state;
- trajectory filename;
- files delivered;
- tool use and environment changes;
- reconstructed semantics;
- result values;
- rubric score;
- active wrong behaviors;
- omissions;
- possible ambiguity;
- fair-score result.

## Phase 12 — Grade generously and audit convergence

### First grading pass

Score each binary criterion against the observable response and delivered files. Do not infer hidden intent.

### Fairness pass

- accept equivalent labels, schemas, ordering, units, and methods unless the prompt fixed them;
- apply documented numerical tolerances;
- do not fail a technically correct result for author-preferred wording;
- distinguish an omission from an affirmative wrong action;
- do not apply a negative trap to absence alone;
- do not double-charge one behavior through duplicate criteria.

### Convergence pass

Compare runs, not just scores:

- common measured constants;
- common state-machine interpretation;
- common alternate optimum;
- identical unexpected hashes;
- same failure mode across independent runs.

Shared detailed results are strong evidence of a coherent alternative implementation. Investigate before selecting preferred runs.

### Gate 12

Every preferred run must remain below 50% under the most generous valid interpretation, and the failures must trace to supplied technical requirements. If not, redesign and rerun.

Archive exact score evidence, trajectory files, model/effort settings, frozen revision hashes, and the generous grading record before declaring this gate complete.

## Phase 13 — Final submission gate

Ask, in this order:

1. Would a different but equally correct answer fail any criterion?
2. Could someone holding only the criterion and delivered response/output grade it?
3. Does every explicit prompt requirement have a criterion?
4. Do the required model runs still fail under generous reading?

Then additionally ask:

5. Does any private oracle branch lack a visible source?
6. Did two or more runs converge on a rival answer?
7. Did any low score depend on report attribution, spelling, file existence alone, or an unstated format?
8. Are all uploaded fields identical to the frozen local source?

Submit only when all eight questions have satisfactory answers.

## Recovery routes

| Failure | Correct response |
|---|---|
| Model scores high because it cleanly rewrites a small module | Replace the task architecture; do not add cosmetic criteria. |
| Models converge on an alternate result | Audit visible semantics and implement their interpretation. |
| Low score comes from hidden schema/name | Broaden rubric and redesign difficulty if score rises. |
| Linter flags broad/non-binary criterion | Split it or make the observable condition precise. |
| Linter flags a correct criterion based on siblings | Mark invalid only with specific coverage reasoning. |
| Runtime is missing/broken | Fix environment or provide a known runnable path before reruns. |
| Hash/checkpoint was mistyped | Correct local canonical source, re-audit all linked fields, and rerun linter. |
| Below-50 result depends on private rule | Repair artifact/oracle, regenerate all goldens, and rerun models. |
| Pilot is locally plausible but its production trace diverges | Reconstruct the delivered implementation, find the first divergence, and repair architecture or observability prospectively. |
| Wrong integrated simulator can retain 50% through local points | Rebuild score topology before the next pilot; do not retroactively rescore completed runs. |
| Fault window or stress mechanism never activates | Move or redesign it visibly, regenerate every dependent result, and repeat preflight. |
| One run passes but another required run is at or above 50 | Acceptance failed; diagnose the stronger run and create a new prospective revision if needed. |

The costliest mistake is advancing after a failed gate. The fastest workflow is the one that refuses to launch until the task is internally complete.
