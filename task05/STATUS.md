# Task 05 — KILNWORKS

Current active candidate: **R3**, in `r3/`. State: LOCALLY FROZEN, INDEPENDENTLY
RECONSTRUCTED TO FULL CONVERGENCE, SCORE-TOPOLOGY AUDITED. NO TARGET-MODEL PILOT RUN
YET. Not submission-ready until Phase 10 of the playbook SOP (one pilot, reconstructed
and diagnosed) actually happens.

R3 architecture: every dispatch decision (machine assignment, robot routing, oven
batching) is pinned to one explicit deterministic policy stated in the packet —
there is no free optimization decision left for a generic solver (this is the
direct architectural response to R2's CP-SAT solve, see below). Difficulty instead
comes from correctly composing that policy across one continuous, cross-campaign,
fault-affected run per design. Two independent from-scratch reconstructions (fresh
agents, no access to the reference) converged to the reference's exact numbers after
three real specification gaps and two real reference-code bugs were found and fixed
(`r3/audit/independent-reconstruction.md`). A score-topology audit against an
executed "reverted to R2-style per-campaign resets" mutant, and a perfect-local-
semantics hypothetical, both stay under 50% of positive weight
(`r3/platform/score-topology.md`). Frozen goldens: D0 187/1331, D1 165/1294,
D2 187/1447, D3 185/1401, D4 155/1413, D5 142/1290 minutes/bill; unrestricted
selection D5 (142,1356,22,D5); capital<=9 selection D1 (165,1315,7,D1).

**Local blind-agent pilot run (not the target-model pilot):** a general-purpose
agent, given only the prompt and PDF (no rules, no rubric, no reference), scored
~85% (52/61) against the frozen rubric — 4 of 6 designs matched the reference
exactly, including correct vector-PDF graph extraction. The gap came from one real
implementation bug in the agent's own oven-timing code (arrival/deadline off-by-one)
and exposed one real gap in my own packet (the selection-key formula was defined
privately but never rendered into the PDF — now fixed). See
`r3/audit/blind-pilot-1.md` for full detail. **This is a real concern**: an 85%
blind score from an unhurried solver is well above the <50% target, and is grounds
to consider further hardening before spending a real Opus 4.8 Max platform run — not
yet decided, flagged here for the next session/human call.

Next step: either harden R3 further (increase the density/interaction of boundary
rules that a careful solver must get exactly right) or accept the risk and run one
Opus 4.8 Max pilot on the frozen R3 packet, reconstruct and replay its delivered
implementation, and find the earliest production-trace divergence. Do not skip
straight to a full run batch either way.

---

## R2 history (archived, rejected — preserved verbatim below)

Former frozen candidate: R2-F1. State: REJECTED FOR THE REQUESTED DIFFICULTY TARGET AFTER SUCCESSFUL TARGET-MODEL RUNS. NOT SUBMISSION-READY.

User reports100% scores on the preferred runs and supplied two Claude Opus4.8 trajectories. Both contain all24 correct optimum pairs and correct D5/D1 selections. The second trajectory records a complete CP-SAT optimization stage of169.9seconds, independent model/replay checks for24 cases, and six explicit-search crosschecks. Final sources have been reconstructed and archived under audit/target-runs. A fresh local spotcheck agrees; further local replay is in progress. These are successful technical solutions, not sub50 acceptance evidence. Do not run more target trials of unchanged R2 hoping for failure. Frozen fields/weights remain preserved for honest grading.

Architecture failure: five lots, two robots and short horizons compile directly to manageable exact constraint-programming models. Reference state-search runtime did not establish frontier difficulty. The serial-scheduler score counterfactual was too weak to predict this attack. The local blind run was interrupted by usage limits, so it never established a low score before platform use.

Completed: complete playbook/official-source intake; three-candidate screen and independent architecture attacks; rejected distance-only prototype; exact four-page R2 visual packet; fresh isolated R2 semantic reconstruction with no material ambiguity; all24 reference optimum pairs matched by a separately authored exact engine; full clean reference repeat with byte-identical schedules/matrix/decisions/search counts and24 traces;48 copied-production mutation rejections; seven realistic replay mutants;47 source-directed checks; complete bidirectional source map; nine mechanism witnesses plus early/middle/late checkpoints; independent rubric fairness repair;41 binary criteria/77positive points frozen before blind dispatch; complete entry guide and frozen hashes.

Current audit: reconstruct and locally re-execute the supplied successful target implementations. The independent global clean reproduction also completed with all24 known optimum pairs. The local blind solver and additional reviewers were interrupted by usage limits; their unfinished work is not a technical failure score.

Next architecture gate: test materially different candidate structures against a competent generic exact formulation before rendering another final packet. Any replacement requires its own prospective specification, reference, frozen generous rubric, uninterrupted blind calibration and target evidence. The old serial-scheduler ceiling of33/77 does not establish difficulty against an exact solver.

Two target-model trajectories now exist. The supplied files are execution trajectories, so their success flags are not themselves platform grading sheets; the100% scores are user-reported. Their correct numerical results and substantial independent verification support the reported success. Actual platform field/weight exports remain unavailable. Preserve R2 as a failed-difficulty candidate and its correct-run evidence; a replacement requires substantive prospective redesign and fresh certification.
