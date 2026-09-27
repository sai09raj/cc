# Case Study — Task 03 TempestLog

## Why the first frozen version did not meet the target

Task 03 moved to distributed systems and required reconstruction of a bespoke three-replica journal from one twelve-panel visual packet. The task was legitimate, executable, and substantially harder than the earlier small RTL designs, but the first Opus 4.8 Max runs scored 65%, 68%, and 71% rather than below 50%.

The runs did not merely make spelling or reporting errors. They built runnable simulators and broad sweeps, yet converged on wrong baseline continuations, safety counts, selected tuples, qualifier counts, p99 values, and hashes. Their selected tuples were `(12,1,4,3,48)` or `(4,1,4,3,96)` instead of `(4,1,4,3,48)`, and they reported six or nine qualifiers instead of three. This showed genuine semantic difficulty.

The score nevertheless stayed above 50 because most positive weight rewarded broad implementation scaffolding. Rows 1–35 carried 232 of 297 positive points (78.1%). A plausible but semantically wrong simulator could earn most of those points before the decisive canonical-result rows were reached. Difficulty was present, but the rubric topology did not make the decisive semantic mistakes sufficiently observable.

Do not turn this into a strategy of hoping future frontier models make semantic mistakes. Opus 4.8 Max already reconstructed most of the protocol and built runnable simulators. Semantic errors are diagnostic evidence, not a durable difficulty engine. A future architecture must remain difficult under perfect local semantic reconstruction through integrated execution, verification, search, and reconciliation.

Two Muse runs scored 0 only because they spent their trajectories on image/OCR setup and produced no required deliverables. Those scores are not evidence that the protocol itself defeated the model. A valid stump analysis distinguishes failure to engage with the task from failure after substantive execution.

## Correct rework rule

Never edit the existing rubric merely to rescore completed runs. Never append unscored prompt rules while leaving the artifact, Ideal Flow, and rubric on the old task. If repeated genuine runs remain at or above 50%, create a prospective revision:

1. preserve any still-valid workload, goldens, thresholds, hashes, IDs, and weights;
2. change the visible source and executable contract in a technically meaningful way;
3. update prompt, Ideal Flow, and only the rubric rows actually affected by that changed contract;
4. explicitly state that old runs cannot be rescored against the revision; and
5. run a fresh pilot.

Task 03 Revision B therefore added ten visible before/event/after conformance probes tied to the same production transitions as the full simulator. They target the failure modes seen in the Opus trajectories: flush capture, same-cycle flush/crash order, durable evidence, emitted-message lifetime, frozen recovery cohorts, quorum prefix, pre-truncation leader choice, blocked retry timers, deduplication, and safety-versus-completion separation.

## Revision audit lessons

The first Revision B draft mechanically passed lint but failed independent audit. Replacing Panels K/L had accidentally displaced load-bearing rules about fresh schedule state, cycles `0..5000`, exact quiescence, post-truncation allocation, dedup conflicts, and retirement token purging. A new visual can silently remove old specification content even when it adds useful tests.

The audit also caught four local issues:

- P18 omitted the third replica's evidence state, so `retired=false` was not forced.
- P22 incorrectly sounded as if replica C could never join a later fresh recovery attempt.
- P24 omitted the exact captured cohort, allowing another eligible leader candidate.
- A negative trap described generic “completion after crash,” although correct TempestLog executions do complete after crashes.

The repair restored the displaced lifecycle rules explicitly in the prompt, scoped each probe completely, aligned the authorized boundary short-circuit across prompt and rubrics, and narrowed the negative trap to the actual wrong stage ordering.

## Harness/result MECE rule

When one self-test command invokes many probes, separate the grading objects:

- one low-weight harness criterion checks use of production transition functions, invocation of every named probe, one observed result line per probe, and nonzero exit on failure;
- one criterion per probe checks its exact post-state.

The harness row must not also award correctness of every post-state, or it double-grades the same failures.

## Private certification rule

A string-presence linter is not enough. Revision B includes a private executable `probe_audit.py` that drives the frozen production reference methods and compares all ten observed results with `development_probe_results.json`. Platform lint fails if that replay diverges. This makes the certification evidence executable rather than declarative.

## Pilot gate

Revision B remains a hypothesis until a fresh Opus pilot runs. The fair claim is not “this will certainly score below 50.” The fair claim is that it targets shared substantive failures worth enough positive weight that persistence of those failures would move the observed 65–71 range below 50, while keeping every graded rule visible and executable. If the pilot still exceeds 50, analyze which high-weight semantics it solved; do not manipulate rubric weights or retrofit penalties.

## Revision B result and Revision C correction

Three fresh Revision-B Opus runs scored 59, 63, and 68. All three passed every isolated conformance probe yet produced materially wrong full-run state: selected tuples differed from `(4,1,4,3,48)`, qualifier counts were 15 or 36 instead of 3, baseline losses were 2, 44, or 42 instead of 56, and selected retry/p99 values and both hashes diverged. The probes tested local transitions but did not prove that one simulator composed them correctly over time.

Revision C keeps the same ten rubric IDs and weights but replaces each micro-probe with a checkpoint from one uninterrupted ordinary baseline execution. The checkpoints span pre-fault buildup, both crash/recovery epochs, retry pressure, durable/volatile distributions, queues, and in-flight messages. This tests temporal composition rather than the ability to implement ten special-case test fixtures. Completed Revision-B runs are not rescored.

General rule: when a solver passes isolated tests but fails integrated outputs, do not add more isolated tests. Promote existing test weight to linked checkpoints or metamorphic invariants from the same production execution, freeze every unrelated requirement, and run one new pilot before a batch.
