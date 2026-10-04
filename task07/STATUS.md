# Task 07 — QUORUM-7

## FAIRNESS FINDING (found during task11 calibration) — NOT submission-ready as packaged

An `opus`-alias blind pilot on the frozen `quorum7.pdf` packet (run to
calibrate the local difficulty probe; deliverables in
`audit/calibration-probe-opus/`) reported three facts the packet never
specifies. Each was then confirmed against the packet text, every figure,
and the reference code:

1. **Client command schedule is missing.** The packet says only that client
   commands "are broadcast to all 5 nodes at fixed ticks". The reference
   hard-codes five commands at t = 300, 600, 900, 1500, 2000
   (`reference/scenarios.py`, `COMMANDS`). Every `commit_index` value and
   every commit-sum criterion depends on this schedule.
2. **MESSAGE_LOSS overrides are missing.** The packet says only "targeted
   DROP/DUPLICATE/DELAY overrides". The reference applies DROP to N0→N3
   APPEND_REQ, DUPLICATE ×3 to N1→N2 VOTE_REQ, and DELAY 15 to N0→N4
   APPEND_REQ.
3. **"Message count" is undefined.** The reference increments the count only
   after the partition check, so messages blocked by a partition are never
   counted, while messages discarded by a DROP override are counted
   (`quorum_sim.py` lines 133–138). The packet defines neither. The
   calibration pilot counted every send; its PARTITION rows came out about
   +86 and its COMPETING_CANDIDATES rows about +110 above the reference,
   while CLEAN rows matched exactly.

Criteria 19–28 (100 of 197 positive points) are message sums and commit
sums, so they rest directly on items 1 and 3. The two real pilots' LONG
totals (7578, 7638 vs reference 7355) are consistent with the same
counting difference; the calibration pilot got 7550. Both real pilots also
converged on the same alternate baseline hash `d75121e3abb34538` and the
same LONG crash latency 422 (reference 419), and the calibration pilot
reproduced the 422. Identical rival results across independent runs are
the playbook's convergence alarm (mistake #6); it was recorded at the time
but not acted on.

**Consequence:** the 31%/32% real-pilot scores cannot be taken as evidence of
legitimate difficulty. A substantial part of the lost score is attributable
to hidden semantics (Playbook mistake #4, the Task 02 Revision C failure).
If this packet has already been submitted, it carries this defect. A fair
revision must state the command schedule, the override list, and the
message-count definition, then be re-piloted; given the calibration
pilot's otherwise-correct reconstruction, a fair revision would very
likely score far higher.

The rest of this file is the original record.

---

Original state line: **QUORUM-7**, in `reference/`, `design/`, `platform/`,
`artifact/quorum7.pdf`. State: SCORE-TOPOLOGY AUDITED (canonical 100%, three
mutants 25.9%/27.9%/32.0%), TWO REAL TARGET-MODEL PILOT RUNS COMPLETE, BOTH
SCORED WELL UNDER THE ACCEPTANCE BAR. SUBMISSION-READY (superseded above).

CISTERN-7 (wastewater lift-station, same simulate+sweep+verify meta-shape as
KILNWORKS/ATRIUM-9) was shelved after a shape-reuse finding — see
`design/architecture-attack.md`'s "Why CISTERN-7 is shelved" section — and
replaced with QUORUM-7 (5-node Raft-family consensus protocol under scripted
network faults), a genuinely different mechanism: concurrent/partial-failure
state-machine reasoning rather than numerical integration or request dispatch.

## Real pilot runs (claude-opus-4-8, both against the frozen `quorum7.pdf` packet)

Both scored well under the 50% threshold and comfortably under the tighter
35% target set after the fact:

- **Run A: 32%**
- **Run B: 31%**

Both runs were extremely thorough — multi-file independent verifiers (one
dict/functional style, one class-based), adversarial-mutation audits, external
`sha256sum` cross-checks, and (in Run A) a self-caught causal-attribution
error in the memo's overhead explanation, corrected before submission. Neither
run was sloppy; the task stumps careful, rigorous work, which is the design
goal.

Both runs' recovery-optimal (SHORT, 172 ticks) and overhead-optimal timeout
selection (LONG) matched the reference exactly (message-count magnitude was
the actual point of divergence — reference 7355, runs 7578/7638, both outside
tolerance). Both runs also converged on the identical baseline
(MEDIUM,PARTITION) trace-integrity hash `d75121e3abb34538`, differing from the
reference's `3243b745aaf9e7e2`. Traced this to LONG timeout's own
CRASH_RECOVER latency: both runs independently got 422 ticks: the reference
computes 419. Not a currently-graded fact (no criterion checks LONG's own
recovery latency directly) and not remediated, but recorded here as a genuine,
reproducible three-tick corner of the spec two independent implementations
agree on against the reference — worth keeping in mind if this packet is ever
revised.

No rubric or reference changes were made in response to these pilots; both
scores already landed inside the target band without any adjustment.
