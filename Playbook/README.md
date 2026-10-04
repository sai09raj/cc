# Magnetic Rainstorm Frontier-Task Authoring Playbook

## Start here: policy, engineering method, and lessons through Task 04 Revision F

This folder is a handoff package for an author—or another capable agent—who must design, validate, enter, run, grade, and submit a Magnetic Rainstorm task without repeating the long trial-and-error cycle that produced it.

It combines three layers that must never be confused:

1. **Official project policy.** The authoritative sources are `guidelines.pdf`, `rubric.pdf`, and `common-errors.pdf` in `C:\Users\SAI\Downloads\MR`. They control whenever this playbook disagrees with them.
2. **Source-cited consolidation.** `C:\Users\SAI\Downloads\MR\PROJECT-TASK-HANDBOOK.md` is the detailed handbook assembled from those PDFs. It is the primary policy reference, but it is not authority over the PDFs.
3. **Empirical authoring evidence.** This playbook adds lessons from Tasks 01–04: easy clean-rewrite solves, hidden-oracle failures, isolated-probe failures, score-topology failures, trace forensics, and the final Revision F three-run outcome. These are engineering lessons, not new platform rules.

The central lesson is simple:

> A score below 50% is necessary, but it is not proof that the task is valid. The failure must come from genuine, fully specified technical difficulty—not from a hidden oracle rule, an unstated exact schema, a transcription error, an unavailable tool, or an unfair rubric interpretation.

> **Frontier-model warning — semantics alone are not the difficulty.** Assume the required frontier model, including Opus 4.8 at maximum effort, will carefully recover every visible local rule, reconstruct a clean state machine, write tools and a second oracle, enumerate the stated search space, inspect its outputs, and repair obvious local mistakes. Do not build a task around hoping it overlooks, misreads, forgets, or inconsistently applies one semantic. A complete visible semantic contract is a fairness prerequisite—the entrance fee—not a durable stump. The task must remain difficult after all local semantics are granted, through temporal and cross-component composition, broad executed work, coupled optimization, independent verification, iteration, and reconciliation of production evidence.

Never respond to this warning by hiding or blurring semantics. Apply the [perfect-semantics ablation test](00-START-HERE-EVERY-FUTURE-TASK.md#perfect-semantics-ablation-test): if flawless semantic knowledge makes the remaining task routine, reject the architecture.

Treat Opus 4.8 Max as the demonstrated capability floor from Task 04, not a permanent ceiling. For every later task, substitute the current required frontier model and effort setting, then repeat the semantic-grant, pilot-replay, and score-topology tests.

## What Magnetic Rainstorm is testing

A strong task makes a frontier model do all of the following in one coherent workflow:

- interpret a genuine technical visual artifact rather than merely OCR prose;
- reconstruct an executable or otherwise testable technical model;
- use real tools in an inspect → build → run → diagnose → revise → rerun loop;
- apply expert domain judgment;
- produce concrete output files;
- reconcile detailed observations into a causal technical conclusion; and
- remain difficult under a fair, generous grading interpretation.

The official four pillars are advanced multimodal reasoning, iterative tool use, expert-level knowledge, and long-horizon work. The prompt is 2–500 words. Each of the three Ideal Flow fields is 5–3,000 characters. The rubric contains 12–50 criteria with weights from -10 to +10. The clearest operational reading is three preferred runs per required model, every preferred run below 50%, with no more than ten runs per model. Consult the handbook for source citations, qualifications, and documented conflicts.

## The most important discovery from this attempt

The three Opus 4.8 trajectories named `36.json`, `38.json`, and `41.json` all:

- read the review packet successfully;
- measured `tBURST = 4` and `tRFC = 42`;
- applied the Rev C `W→R = 11` override;
- reconstructed the 624-request workload;
- implemented a deterministic simulator;
- swept all 272 legal configurations;
- produced all five requested files; and
- independently converged on the same results: baseline `14008`, recommendation `{Q:8,H:4,B:2,L:96}`, recommended total `8425`, and identical dispatch hashes.

Our private reference model instead expected baseline `9026` and recommendation `{Q:10,H:4,B:4,L:128}`. The reason was not weak model execution. The private reference model contained an additional transition:

```python
if write_mode and writes_waiting == 0:
    write_mode = False
    writes_in_batch = 0
```

The visible packet did not state this transition. It stated only the two drawn transitions, no fallback when the selected operation had no bank-free request, and that mode persists across idle cycles. The separate “independent” oracle copied the same hidden transition, so agreement between the two author implementations did not prove that the visible specification was complete.

This makes Revision C a valuable architecture success but a specification-fairness failure. The below-50 scores cannot, by themselves, certify that version as submission-ready. See [05-CASE-STUDY-TASK-02.md](05-CASE-STUDY-TASK-02.md).

## Non-negotiable author standard

Before launching expensive model runs, the author must be able to answer **yes** to all of these:

- Can a competent solver derive every state transition, metric definition, workload item, boundary rule, tie-break, and serialization rule from the supplied prompt and artifact?
- Does the reference implementation contain no material behavior absent from those sources?
- Has at least one reviewer or rival implementation reconstructed the semantics from the artifact without reading the reference code?
- Have plausible alternative interpretations been implemented and compared?
- Would an equally correct but differently structured output pass the rubric?
- Does every prompt requirement have rubric coverage, with no hidden requirements?
- Does every stated prohibition have a separate, affirmative, observable negative trap?
- Are the below-50 failures still failures under the most generous valid reading?

If any answer is no, stop and repair the task. Do not spend model runs to discover a defect that local preflight could catch.

### Permanent independent-audit gate

For Task 03 and every later Magnetic Rainstorm task, use a separate agent/reviewer for at least one packet-only reconstruction before freezing goldens. The reviewer must be technically isolated from the private contract, oracle code, development results, expected hashes, and prior author conclusions. Its report must name ambiguities and plausible rival interpretations, and every decision-relevant finding must be repaired or explicitly disproved before platform entry. The same reviewer context must not be reused as the final post-repair audit; use a fresh isolated audit for the frozen packet.

## Folder map

- [00-START-HERE-EVERY-FUTURE-TASK.md](00-START-HERE-EVERY-FUTURE-TASK.md) — the permanent routing page and semantic-grant architecture gate for every new task.
- [01-END-TO-END-SOP.md](01-END-TO-END-SOP.md) — the complete workflow, gates, and rework routes.
- [02-DIFFICULTY-ENGINEERING.md](02-DIFFICULTY-ENGINEERING.md) — what genuinely stumps frontier agents and what only looks difficult.
- [03-RUBRIC-AND-LINTER-GUIDE.md](03-RUBRIC-AND-LINTER-GUIDE.md) — rubric construction, negative traps, linter handling, and numeric-entry discipline.
- [04-PREFLIGHT-AND-VALIDATION.md](04-PREFLIGHT-AND-VALIDATION.md) — semantic audits, oracle independence, mutation tests, environment checks, and run gates.
- [05-CASE-STUDY-TASK-02.md](05-CASE-STUDY-TASK-02.md) — evidence from the 80–88%, 100/99%, and 36/38/41% iterations.
- [06-COPY-PASTE-TEMPLATES.md](06-COPY-PASTE-TEMPLATES.md) — reusable task, prompt, Ideal Flow, rubric, run-analysis, and handoff templates.
- [07-MISTAKE-REGISTER.md](07-MISTAKE-REGISTER.md) — the concrete mistakes, causes, prevention, and recovery actions from this attempt.
- [08-QMO-AND-COMMUNITY-GUIDANCE.md](08-QMO-AND-COMMUNITY-GUIDANCE.md) — offline, substantive-tool, genuine-visual, and deterministic-artifact guidance from Quality Managers/community evidence.
- [09-CASE-STUDY-TASK-03.md](09-CASE-STUDY-TASK-03.md) — lessons from the TempestLog 0/0 and 65/68/71 runs, prospective revisioning, conformance probes, and executable certification.
- [10-TASK-04-PREFLIGHT-LESSONS.md](10-TASK-04-PREFLIGHT-LESSONS.md) — pre-pilot source, implementation, and entry checks that established correctness but not difficulty.
- [11-TASK-04-PILOT-FAILURE.md](11-TASK-04-PILOT-FAILURE.md) — the three reported 100% solves, root cause, prospective redesign, and the required post-redesign pilot gate.
- [12-CASE-STUDY-TASK-04.md](12-CASE-STUDY-TASK-04.md) — the complete A–F history, Revision E trace forensics, score-topology failure, and Revision F's successful production-witness repair.
- [QUICK-CHECKLIST.md](QUICK-CHECKLIST.md) — the short operational checklist to keep beside the platform.

## Recommended use by another agent

1. Give the fresh model the entire playbook folder, not a copied excerpt; also provide access to the current official handbook/PDFs.
2. For every new task, begin with [00-START-HERE-EVERY-FUTURE-TASK.md](00-START-HERE-EVERY-FUTURE-TASK.md); it routes the full playbook and applies the perfect-semantics gate.
3. Read the Task 03 and Task 04 case studies before proposing an architecture. They show why isolated probes and locally weighted rubrics fail.
4. Fill the architecture, semantic-contract, score-topology, production-witness, and revision-delta templates in [06-COPY-PASTE-TEMPLATES.md](06-COPY-PASTE-TEMPLATES.md).
5. Follow [01-END-TO-END-SOP.md](01-END-TO-END-SOP.md) in order. Do not skip a gate.
6. Run every check in [04-PREFLIGHT-AND-VALIDATION.md](04-PREFLIGHT-AND-VALIDATION.md) before asking the human to enter long fields into the platform.
7. Keep [QUICK-CHECKLIST.md](QUICK-CHECKLIST.md) open during platform entry, pilot forensics, and run selection.

## The eleven principles worth memorizing

1. **Architecture beats wording.** A small rewriteable implementation remains easy even with more edge cases and a longer prompt.
2. **Visible semantics are the contract.** Private intent and reference-code behavior do not count.
3. **Independent code is not independent specification.** Both implementations can faithfully reproduce the same author assumption.
4. **Convergent disagreement is evidence.** When several frontier runs reach the same rival answer, audit the task before blaming the models.
5. **Rubrics verify; they do not create difficulty.** A harsh or overly exact rubric can only create a fake stump.
6. **Transcription is part of verification.** One omitted hexadecimal character or mistyped checkpoint can invalidate hours of work.
7. **A low score must survive generosity.** If fair equivalent handling lifts the model over 50%, redesign the task.
8. **Score topology is part of task design.** A locally plausible but globally wrong implementation must not retain 50% through scaffolding points.
9. **The first divergence beats the final summary.** Replay the pilot and find the earliest production event that departs from reference behavior.
10. **One pilot precedes the batch.** Diagnose one real target-model run before spending the remaining run budget, then archive every final score and trajectory.
11. **Semantic reconstruction is the entrance fee, not the stump.** Assume the frontier model learns every visible local rule; difficulty must survive in composition, execution, search, verification, iteration, and decision-making.

## Evidence inventory used for this playbook

Official/project sources:

- `C:\Users\SAI\Downloads\MR\guidelines.pdf`
- `C:\Users\SAI\Downloads\MR\rubric.pdf`
- `C:\Users\SAI\Downloads\MR\common-errors.pdf`
- `C:\Users\SAI\Downloads\MR\PROJECT-TASK-HANDBOOK.md`

Task evidence:

- `C:\Users\SAI\Downloads\MR\task-01\...`
- `C:\Users\SAI\Documents\ChatGPT\MR\task 02\revision-b\trajectory-analysis-100-99.md`
- `C:\Users\SAI\Documents\ChatGPT\MR\task 02\revision-c\...`
- `C:\Users\SAI\Downloads\Telegram Desktop\36.json`
- `C:\Users\SAI\Downloads\Telegram Desktop\38.json`
- `C:\Users\SAI\Downloads\Telegram Desktop\41.json`
- `C:\Users\SAI\Documents\ChatGPT\MR\task 04\revision-e\opus-runs-37-52-59.md`
- `C:\Users\SAI\Documents\ChatGPT\MR\task 04\revision-e\reference\compare_runs.py`
- `C:\Users\SAI\Documents\ChatGPT\MR\task 04\revision-f\README.md`
- `C:\Users\SAI\Documents\ChatGPT\MR\task 04\revision-f\changed-rubrics.md`

Revision F's exact final score files remain to be archived. Until then, record its outcome as “three user-reported sub-50 runs,” not as invented score values or trajectory-verified causal evidence.

This package deliberately records the Revision C ambiguity rather than concealing it. That is the strongest safeguard against repeating the same expensive mistake.

## The Task 04 discovery that changes every future task

Task 04 required six prospective revisions. Its chronology was A `100/100/100`, B `52/61/64`, C `91/100` documented, D `44/83/93`, E `37/52/59`, and finally F with three user-reported scores below 50. Exact Revision F score values are not yet archived locally, so they must not be invented.

Revision E exposed a problem not captured by the earlier playbook. Its stronger wrong implementations followed many local rules and even recovered the headline selections, but composed the event system incorrectly. The rubric still let that wrong integrated engine retain about `172/315 = 54.6%` of positive weight. Revision F kept the state model, goldens, and weights fixed, clarified independent per-serializer arbitration, and tied 67 existing points to twelve witnesses from one uninterrupted production trace. Both reconstructed 52/59 implementations missed every witness. The final revision then met the three-run gate.

The new permanent method is:

1. counterfactually score a plausible wrong-but-runnable implementation before the first pilot;
2. run one pilot before a batch;
3. reconstruct and replay its actual implementation;
4. find the earliest production-trace divergence;
5. use fair integrated evidence from ordinary execution rather than isolated fixtures; and
6. archive exact score and trajectory evidence before calling the history complete.

See [12-CASE-STUDY-TASK-04.md](12-CASE-STUDY-TASK-04.md) for the complete evidence and [00-START-HERE-EVERY-FUTURE-TASK.md](00-START-HERE-EVERY-FUTURE-TASK.md) for the permanent fresh-agent launch sequence.

## Correction (task11 calibration): Task 06 and Task 07 are not clean difficulty evidence

Code→source audits plus `opus`-alias blind pilots on the frozen packets
showed that both ATRIUM-9 (task06, 20%/21%) and QUORUM-7 (task07, 31%/32%)
graded facts their packets never specify: ATRIUM-9's busy-car assignment
cost, `avg_wait` definition, stage order, timeout semantics, tie-breaks and
run end; QUORUM-7's command schedule, loss overrides and message-count
definition. The blind pilot reproduced each task's real-pilot failure
pattern. Their low scores are substantially hidden-semantics failures
(mistakes #4, #71), and the "composition over scale" lesson drawn from
them below is unproven. Every fully specified simulation built in this
project (TYPECHAIN-9, CELLGUARD-10, TENURE-11) was solved. See
`task06/audit/code-source-audit.md` and `task07/STATUS.md`.

## The Task 06 discovery: real pilots can score below synthetic mutants

Task 06 (ATRIUM-9, an exhaustive-sweep elevator-dispatch simulation) is a
materially different task shape from Task 04's fault-injection timeline —
a 144-configuration search with three competing selection objectives
rather than a single production trace — and it confirms the same
composition-over-scale method generalizes to that shape. Three real Opus
4.8 Max pilot runs scored below 50%; two archived trajectories scored
**20%** and **21%**, both lower than every one of the three synthetic
plausible-wrong mutants used to calibrate the rubric before the pilot
(31.2% / 36.5% / 30.1%). Both real runs independently built fully
self-consistent, cross-language, independently-coded verifiers that agreed
with their own primary implementation and correctly rejected both required
adversarial mutations — and were still ~80% wrong against the actual
reference values, because the real failure surface was the compounding
interaction of many individually-correct-sounding dispatch rules over an
80-call, 144-config run, not any single rule either model got visibly
wrong.

Two lessons this adds to the permanent method:

1. Synthetic plausible-wrong mutants are a pre-pilot confidence check, not
   the acceptance gate — always run the real pilot, and treat its score as
   the evidence, even when the synthetic mutants already clear 50% with
   margin.
2. Never grade a model's own verifier's agreement with its own primary as
   a correctness signal; grade every numeric fact against the external
   reference. Both real Task 06 runs would have scored far higher under a
   rubric that rewarded verifier-primary self-agreement.

See [13-CASE-STUDY-TASK-06.md](13-CASE-STUDY-TASK-06.md) for the complete
trajectory forensics, the ten-round platform-linter chronology, and the
generalizable technique this task validates.
