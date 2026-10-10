# Magnetic Rainstorm Quick Checklist

## RULE ZERO: never underestimate the platform model (Opus 5.5, max effort)

Assume the model can do almost anything a strong engineer can do in 2.5 hours, and more:
- It installs whatever it needs: apt-get, pip, any compiler (gcc, clang, zig via pip), any library.
- It uses all ~17 threads, writes engine code faster than ours, profiles and re-optimises.
- It reads every page and figure of the packet in full, zoomed, before coding.
- It finds and uses exact shortcuts (shared-state execution, symmetry, pruning), above all any hinted in the prompt.
- It cross-checks its own results with independent implementations.
- It works until the time limit when the work needs it.

So: never size difficulty from our own engine, a local probe, or what a previous run happened not to do.
Compute-only difficulty fails (COHERE-12, GRID-14, FIRE-15: 2 of 6 FIRE-15 runs scored 100 after installing a
compiler). A timeout counts only if the model is stuck (iterating, debugging, not converging), and completed
runs must fail on reasoning the model gets wrong. See mistakes #77, #80, #83.


## Before designing

- [ ] Read `guidelines.pdf`, `rubric.pdf`, `common-errors.pdf`, and the handbook.
- [ ] Choose an expert domain from the platform's fixed domain picker list (`00-START-HERE-EVERY-FUTURE-TASK.md`) and a real engineering decision for the subdomain.
- [ ] Check the new task's actual mechanism/pipeline shape against the last 2-3 tasks built, not just their domain labels — a different domain label reused over the same simulate-sweep-select-verify template is not real diversity.
- [ ] Prove the four pillars: visual, tools, expertise, long horizon.
- [ ] Reject a small clean-rewrite architecture.
- [ ] Assume the target model has no internet; no required fact, package, API, or documentation may live only online.
- [ ] Prove the deliverable genuinely requires software/tool execution and is not realistically solvable by hand.
- [ ] Assume the required frontier model correctly reconstructs every visible local semantic and measured constant.
- [ ] Perfect-semantics ablation passes: after granting all local rules, substantial integrated implementation, debugging, search, verification, and decision work remains.
- [ ] No expected below-50 outcome depends mainly on overlooking, misreading, or guessing a semantic rule.
- [ ] At least three post-semantics difficulty layers are genuinely necessary.
- [ ] Broad search is downstream of a correct interacting model and coupled/non-monotonic selection, not enumeration alone.

## Before coding the oracle

- [ ] Inventory every normative panel, axis, note, legend, and footer.
- [ ] Write the semantic contract first.
- [ ] Define all state transitions, including idle/no-candidate behavior.
- [ ] Define event order, boundaries, metrics, workload, search space, tie-break, and serialization.

## Before trusting goldens

- [ ] Run source→code and code→source audits.
- [ ] Assign a separate agent/reviewer to reconstruct semantics from the artifact only, with no access to private contract, oracle, results, or expected hashes.
- [ ] Save its ambiguity report; repair every decision-relevant issue; then repeat with a fresh isolated reviewer on the frozen artifact.
- [ ] Implement plausible rival interpretations.
- [ ] Run mutation tests.
- [ ] Run realistic mutants across configurations/scenarios, not only the baseline.
- [ ] Every fault, retry, timeout, expiry, and stress interval activates in an ordinary certified run and changes observable output.
- [ ] Save mechanically extracted early/middle/late witnesses from one uninterrupted production run; declare schema and index base.
- [ ] Reproduce results from clean execution.
- [ ] Verify every hash is 64 hex characters.

## Before platform entry

- [ ] Prompt is 2–500 words.
- [ ] Each Ideal Flow is 5–3,000 characters.
- [ ] Prompt requests concrete output files.
- [ ] Artifact requires genuine visual reasoning.
- [ ] Visual-ablation test passes: OCR/typeset prose alone does not reveal every required value or relationship.
- [ ] At least one scored result depends on arrow direction, geometry, containment, plotted shape, scale, or measured interval length.
- [ ] Rendering is deterministic/editable and has been manually checked at full resolution and platform-preview scale.
- [ ] Normative-rule conservation diff confirms that no required rule disappeared when any panel/page was replaced.
- [ ] 12–50 rubric criteria, weights -10 to +10, every criterion body 301 characters or fewer.
- [ ] Criterion count is coverage-driven; no padding was added merely to reach 50.
- [ ] Coverage ledger assigns every prompt clause, deliverable field/section, visual fact, and prohibition to a criterion ID.
- [ ] Every requirement has coverage.
- [ ] Every prohibition has its own affirmative negative trap.
- [ ] Criteria are binary, atomic, self-contained, nonduplicative, and equivalent-tolerant.
- [ ] Post-drafting atomicity/self-containment recheck run over every criterion (not just ones touched by the latest edit round) — atomicity and self-containment drift with every merge, trim, or reword.
- [ ] Hide-the-prompt test passes: no row depends on `packet-defined`, `requested`, `displayed`, `specified`, `correctly`, or another unstated answer.
- [ ] Every conjunction was split or documented as one named unitary answer object.
- [ ] Pairwise MECE audit finds no duplicate positive, positive/negative mirror, or double charge.
- [ ] Integrated witnesses have distinct causal owners; one upstream defect is not charged repeatedly through a downstream cascade.
- [ ] Numeric rows state rounding/tolerance and accept equivalent formatting where exact text is unnecessary.
- [ ] Positive points are bucketed into package, local, integrated, and decision evidence.
- [ ] A runnable locally plausible but globally wrong implementation retains less than 50%.
- [ ] Exact objects are namespaced by revision, tuple, scenario, time/stage, population, and metric before contradiction lint.
- [ ] Runtime/container and minimal test work.
- [ ] Exact attachment filename verified.
- [ ] Attachment filename is unique to this task revision and run; generator, prompt, lint, guide, and uploader all use that exact name.
- [ ] Inspect the entire attachment boundary at full resolution: no internal path, draft/audit/generator footer, private note, or unintended provenance metadata remains; preserve every disclosure or attribution required by platform policy.
- [ ] Inspect container metadata (EXIF/XMP/text chunks, author/software/comment fields, embedded thumbnails, and paths); remove only nonessential metadata and never claim detector evasion or conceal required attribution.
- [ ] For any visual/graphical artifact (PDF or otherwise): metadata is a solution-leakage vector, not just a privacy concern — if Producer/Creator/Author/date/tEXt fields or vector-drawing-object coordinates survive, the model can read the answer straight out of the file and the task will not score below 50% no matter how sound the rubric is. Verify zero hits at the raw-byte level and zero vector drawing objects remain (rasterize diagrams to images), not by eye alone.
- [ ] Canonical text copied; all numbers, panel letters, tuples, and hashes compared.

## Reviewer-feedback checks (mistakes #75, #76) — run on the local rubric and again on the platform text

- [ ] Every expected value is a legal value under the packet (inside every stated option set and range) and is reproduced by the reference.
- [ ] Every graded metric is defined in the packet: what it measures, when it is sampled, its unit.
- [ ] Every prompt "explain", "why", "compare" and "state" clause has its own criterion.
- [ ] No criterion pairs a mechanism description with a trace value, or bundles two constants, or a constant with an explanation.
- [ ] No validity-only criterion where the prompt asks for the best or strongest value (a trivial answer must not pass).
- [ ] No presence-only criterion where correctness or consistency with the run's own files can be graded.
- [ ] Every conditional prompt rule ("only when", "only if") has a negative criterion for exactly that violation.
- [ ] After platform entry, every row's numbers, coordinates and scenario labels match the local file (no dropped digits, no row copied from its neighbour).

## Before full runs

- [ ] Pilot used the visual and tools.
- [ ] Pilot’s failure is technical, not packaging or reporting.
- [ ] Exactly one pilot was diagnosed before launching the remaining acceptance runs.
- [ ] Pilot's final implementation was reconstructed from all writes/edits and replayed on frozen inputs.
- [ ] Earliest production-trace divergence, visible rule, and rubric owner are recorded.
- [ ] Any coherent rival result was audited.
- [ ] Same frozen prompt/artifact will go to both models.
- [ ] Correct model and reasoning settings selected.

## While grading

- [ ] Inspect files, not just final prose.
- [ ] Score every criterion literally.
- [ ] Accept valid equivalents and tolerances.
- [ ] Penalize active wrongness, not omission, under negative traps.
- [ ] Do not double-charge one failure.
- [ ] Group earned points by package/local/integrated/decision topology.
- [ ] Track shared causal ownership of checkpoint/trace failures.
- [ ] Compare semantics/results across runs.
- [ ] Pause if runs converge on the same non-reference answer.

## Submission gate

- [ ] A different equally correct answer would pass.
- [ ] Each criterion is gradeable from itself plus delivered outputs.
- [ ] Every prompt requirement is covered.
- [ ] Preferred runs remain below 50% under generous reading.
- [ ] Every required preferred run individually passes; no average is used as a substitute.
- [ ] No private oracle branch lacks a visible source.
- [ ] Low scores do not depend on spelling, attribution, hidden schema, or broken tools.
- [ ] Current platform text matches frozen local files.
- [ ] If this is a revision, old runs are excluded and prompt, artifact, Ideal Flow, and affected rubric rows share one revision ID.
- [ ] Positive-weight topology does not let a broadly plausible but semantically wrong solution retain 50% or more.
- [ ] Exact score evidence, trajectories, model/effort settings, frozen hashes, and grading sheets are archived.

## Immediate stop signs

- a model gives a coherent alternate result shared by another run;
- a reference behavior exists only in private code;
- a linter warning reveals reversed criterion polarity;
- a required runtime cannot execute;
- the human is retyping long hashes or tuple lists from memory;
- the score falls mainly because of cosmetic report omissions;
- a fault/stress interval is printed but never activates in production;
- a plausible wrong integrated engine can earn 50% from local/scaffolding points;
- more than one pilot is being launched before the first is replayed and diffed;
- the task is already solved by cleanly replacing a small implementation.
- perfect semantic knowledge makes the remaining task routine.

Stop, repair, regenerate, and only then rerun.
