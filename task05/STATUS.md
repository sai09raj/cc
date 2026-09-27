# Task 05 — KILNWORKS

Current active candidate: **R3b**, in `r3/` (artifact `kw-r3b.pdf`). State: LOCALLY
FROZEN, INDEPENDENTLY RECONSTRUCTED TO FULL CONVERGENCE, SCORE-TOPOLOGY AUDITED,
HARDENED AFTER PILOT 1, CONFIRMED BY A SECOND LOCAL BLIND PILOT AT 17.6%. NO
TARGET-MODEL PILOT RUN YET. Not submission-ready until Phase 10 of the playbook SOP
(one pilot, reconstructed and diagnosed) actually happens.

R3 architecture: every dispatch decision (machine assignment, robot routing, oven
batching) is pinned to one explicit deterministic policy stated in the packet —
there is no free optimization decision left for a generic solver (this is the
direct architectural response to R2's CP-SAT solve, see below). Difficulty instead
comes from correctly composing that policy across one continuous, cross-campaign,
fault-affected run per design. Two independent from-scratch reconstructions (fresh
agents, no access to the reference) converged to the reference's exact numbers after
three real specification gaps and two real reference-code bugs were found and fixed
(`r3/audit/independent-reconstruction.md`).

R3b hardening added a second, independent state-triggered disruption (S13, the
Machine-Q maintenance freeze) using the *default* boundary convention deliberately
different from S07's explicit inclusive exception, plus per-design SHA-256
trace-integrity hash criteria at the official +10 ceiling, growing the rubric from
61 to 221 positive weight. Frozen goldens (R3b): D0 187/1331, D1 161/1242,
D2 187/1373, D3 185/1408, D4 151/1384, D5 153/1298 minutes/bill; unrestricted
selection D4 (151,1432,16,D4); capital<=9 selection D1 (161,1263,7,D1).

**Local blind-pilot 1 (pre-hardening, against `kw-r3.pdf`):** scored ~85% — 4 of 6
designs matched exactly. The gap traced to one real bug in the agent's own
oven-timing code and one real packet gap (the selection-key formula was never
rendered into the PDF — fixed as Section G in R3b). See `r3/audit/blind-pilot-1.md`.

**Local blind-pilot 2 (post-hardening, against `kw-r3b.pdf`):** scored **17.6%
(39/221)** by direct rubric grading (not the agent's self-report). All six designs'
`(makespan, bill)` pairs came out wrong, despite the agent independently recovering
every local fact correctly (graph, lot-generation formulas, design tuples, tariff,
and — notably — both S07's inclusive and S13's default boundary conventions,
correctly distinguished). Root cause, confirmed by direct minute-by-minute trace
diffing against the reference: a same-minute lot-claim propagation bug (Robot 1's
turn still saw a lot Robot 0 claimed the same minute in its "move toward nearest
waiting lot" pool, because the agent only propagated Robot 0's already-decided
outcome for position collisions, not for lot claims). Two independently-written
implementations by the same agent agreed with each other and passed all adversarial
mutation checks while both being wrong — full detail, including the exact code
diff, in `r3/audit/blind-pilot-2.md`. This is a genuine task-difficulty result, not
a packet defect, and confirms the hardening worked.

Next step: run one Opus 4.8 Max pilot on the frozen R3b packet, reconstruct and
replay its delivered implementation, and find the earliest production-trace
divergence. Do not skip straight to a full run batch.

---

## R2 history (archived, rejected — preserved verbatim below)

Former frozen candidate: R2-F1. State: REJECTED FOR THE REQUESTED DIFFICULTY TARGET AFTER SUCCESSFUL TARGET-MODEL RUNS. NOT SUBMISSION-READY.

User reports100% scores on the preferred runs and supplied two Claude Opus4.8 trajectories. Both contain all24 correct optimum pairs and correct D5/D1 selections. The second trajectory records a complete CP-SAT optimization stage of169.9seconds, independent model/replay checks for24 cases, and six explicit-search crosschecks. Final sources have been reconstructed and archived under audit/target-runs. A fresh local spotcheck agrees; further local replay is in progress. These are successful technical solutions, not sub50 acceptance evidence. Do not run more target trials of unchanged R2 hoping for failure. Frozen fields/weights remain preserved for honest grading.

Architecture failure: five lots, two robots and short horizons compile directly to manageable exact constraint-programming models. Reference state-search runtime did not establish frontier difficulty. The serial-scheduler score counterfactual was too weak to predict this attack. The local blind run was interrupted by usage limits, so it never established a low score before platform use.

Completed: complete playbook/official-source intake; three-candidate screen and independent architecture attacks; rejected distance-only prototype; exact four-page R2 visual packet; fresh isolated R2 semantic reconstruction with no material ambiguity; all24 reference optimum pairs matched by a separately authored exact engine; full clean reference repeat with byte-identical schedules/matrix/decisions/search counts and24 traces;48 copied-production mutation rejections; seven realistic replay mutants;47 source-directed checks; complete bidirectional source map; nine mechanism witnesses plus early/middle/late checkpoints; independent rubric fairness repair;41 binary criteria/77positive points frozen before blind dispatch; complete entry guide and frozen hashes.

Current audit: reconstruct and locally re-execute the supplied successful target implementations. The independent global clean reproduction also completed with all24 known optimum pairs. The local blind solver and additional reviewers were interrupted by usage limits; their unfinished work is not a technical failure score.

Next architecture gate: test materially different candidate structures against a competent generic exact formulation before rendering another final packet. Any replacement requires its own prospective specification, reference, frozen generous rubric, uninterrupted blind calibration and target evidence. The old serial-scheduler ceiling of33/77 does not establish difficulty against an exact solver.

Two target-model trajectories now exist. The supplied files are execution trajectories, so their success flags are not themselves platform grading sheets; the100% scores are user-reported. Their correct numerical results and substantial independent verification support the reported success. Actual platform field/weight exports remain unavailable. Preserve R2 as a failed-difficulty candidate and its correct-run evidence; a replacement requires substantive prospective redesign and fresh certification.
