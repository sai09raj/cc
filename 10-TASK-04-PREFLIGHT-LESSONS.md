# Task 04 preflight — evidence before platform results

> Historical snapshot: this chapter records the pre-pilot state only. Task 04 continued through Revision F and ultimately achieved three user-reported sub-50 runs. Use [12-CASE-STUDY-TASK-04.md](12-CASE-STUDY-TASK-04.md) for the complete A–F history and current lessons.

Status: author-side preflight only; no target-model scores available. Do not cite this as a successful below50 case study.

Task04 is a credit-controlled two-route fabric. Two independent implementations agree on all324 scenario rows and15 checkpoint records; a fresh PNG-only auditor reconstructs the visual constants. The entry set was reviewed before user transcription and finalized at41 criteria, not padded to50.

Carry these specific lessons forward:

1. **Baseline mutation coverage is not sweep coverage.** Retry-before-ACK and idle-fairness-reset mistakes escaped Task04's baseline/cut checks but changed an ordinary different sweep configuration. Test plausible mutants across configurations and retain a concrete witness; do not claim an undetected mutant is harmless.
2. **Audit the auditor's extraction.** The fresh visual reviewer initially conflated displayed tuple order(W,C,BURST,P,R) with selection key(C,W,BURST,P,R). The packet explicitly distinguished them. The reviewer corrected the audit after source-only reinspection. Audit approval is evidence, not authority over the source.
3. **A source table is not a coverage ledger.** Explicitly own checkpoint field inventory, common trace/checkpoint provenance, the full simulation horizon, fresh-state isolation and cross-file agreement. Numeric samples alone do not cover these requirements.
4. **Separate result facts from explanations.** A correct neighbor metric can coexist with a wrong causal explanation. Give each its own criterion; avoid repeatedly scoring the baseline value inside every comparison.
5. **Avoid selection-error cascades.** Grade a named candidate's metric from correct sweep evidence even if the response recommends another candidate. Reserve selection correctness for the selection criterion.
6. **Make unnecessary presentation order optional in the prompt itself.** Do not request an ordered feasible set then mark order irrelevant only in the rubric. In Task04 the list's membership matters; only the minimum-selection operation needs an exact ordering key.
7. **Replay the actual delivery command.** Two isolated directories containing exactly the requested five files produced byte-identical outputs. This checks packaging and CLI behavior as well as internal reference functions.

The next gate remains actual target-model pilot execution and generous scoring. Independent agreement, mutation sensitivity, image clarity and sound rubrics cannot by themselves establish difficulty for a particular frontier model.
