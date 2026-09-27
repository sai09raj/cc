# Task 04 pilot failure: genuine 100% solves

> Historical snapshot: this chapter covers Revision A and the then-prospective Revision B only. Task 04 continued through Revision F and ultimately achieved three user-reported sub-50 runs. Use [12-CASE-STUDY-TASK-04.md](12-CASE-STUDY-TASK-04.md) for the complete chronology and [00-START-HERE-EVERY-FUTURE-TASK.md](00-START-HERE-EVERY-FUTURE-TASK.md) for permanent future-task rules.

The three attached Task 04 Revision A trajectories (`trajectory-12acfff9334642879220fd8151818845.json`, `trajectory-e1c1b3a756a0448db520a30135c691d3.json`, and `trajectory-9ebaec268c3e44848be013f1c59f4e42.json`) were successful Opus 4.8 max runs. The user reports that the platform scored all three 100%. The raw trajectories do not carry the platform score, but their generated results match the author reference: 324 sweep rows, nine robust tuples, robust choice `(8,5,1,4,160)`, 24 clean-only tuples, and clean-only choice `(8,5,1,0,80)`. The models worked for roughly 24–36 minutes and produced the five requested artifacts. Treat this as an actual difficulty failure, not a linter or grading problem.

## Why the author-side checks were insufficient

Independent implementations, source-to-code mapping, screenshot audits, mutation checks, and a careful rubric established *fairness and correctness*, not frontier difficulty. The original packet exposed a five-edge acyclic network with two routes, fixed credit-return and ACK delays, one shared serializer, and a seven-stage recipe. Once the model implemented those transitions, 108 configurations and three scenarios were inexpensive to sweep. More rubric rows or report obligations would not change the core solution path.

## Prospective architectural repair

Task 04 Revision B makes reverse K credit returns and ACKs first-class transmissions that contend with DATA on the same physical serializers. Credits become available only after K traverses its reverse edge, and an ID retires only after its three-hop ACK reaches S. These mechanisms create coupled congestion, credit starvation, admission delays, retries, and duplicates. The packet explicitly states control priority, reverse routes, timing, conservation, fault behavior, stage order, and drain. An independent implementation built without the author reference agrees on all 324 runs and four checkpoints.

This repair is a **hypothesis about increased difficulty**, not evidence of a below-50 score. Pilot the frozen Revision B prompt, packet, and rubric. If frontier runs solve it again, redesign the architecture rather than editing rubric weights or withholding semantics. If runs fail, inspect their trajectories to ensure the errors are substantive and the packet remains sufficient.

## Permanent gate

Before any future task is declared ready, distinguish three proofs:

1. Contract completeness: a source-only reader can reconstruct every material transition.
2. Oracle reproducibility: an independent implementation matches the reference and the supplied packet.
3. Frontier difficulty: target-model pilot runs fail core requirements under a fair, frozen rubric.

The first two never imply the third. Do not tell the user a task will score below 50% until target-model evidence exists.
