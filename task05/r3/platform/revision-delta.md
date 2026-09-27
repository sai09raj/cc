# R2 -> R3 prospective revision

Reason: R2's architecture ("find the exact global optimum of a small bounded
scheduling/routing instance via complete search") is CP-SAT-shaped and was solved
by two supplied Opus 4.8 Max trajectories (100% reported, all 24 optimum pairs
matched, ~170s CP-SAT solve). R3 replaces the free-optimization ask with a fully
deterministic dispatch policy plus continuous cross-campaign chaining and a
state-triggered fault, removing any scheduling decision for a generic solver to
make. See `design/architecture-attack.md` for the full architecture attack and
perfect-semantics ablation, and `audit/independent-reconstruction.md` for the
convergence evidence this new architecture was built and checked against.

No previous task's topology, tuple format, five/six-file package, or goldens were
reused unexamined; the aisle graph and design table (F/G/aisle/capital tuples) are
the only R2 elements deliberately kept, because R2's own evidence shows visual
extraction was not the failure point.

**Artifact:** `KILNWORKS-T05-R2-20260926.pdf` / `kilnworks.pdf` -> `KILNWORKS-T05-R3.pdf`.

**Exact visual/content changes:**
- Removed: the "find the exact optimum via complete search" framing, the four
  independent per-campaign profiles per design, the 24-case sweep table.
- Added: the deterministic priority-policy sections (machine assignment, robot
  dispatch, oven pairing timer), the campaign-cadence timeline, the node-4 fault
  timeline (window length shown geometrically, not printed as a number), and the
  tariff step-function panel.
- Kept: the aisle graph (identical edge set and open/closed variant), the six
  design tuples `(F, G, aisle, capital)`.

**Prompt:** entirely rewritten (`platform/prompt.md`) — no old sentence reused
verbatim; the "exact offline solution" / "independently checked complete optimality
certificate" framing is replaced by "deterministic simulator" / "independent
verifier that re-derives the trace."

**Ideal Flow:** all three fields newly authored for R3 (`platform/ideal-flow.md`).
No R2 field carried over.

**Rubric:** entirely new 38-criterion (+1 negative) set (`platform/rubric.md`).
R2's 41-criterion set targeted per-campaign profiles and a global-optimality proof;
none of those criteria apply to a system with no free optimization decision, so
none were carried over. R2's old runs are not, and cannot be, rescored under R3.

**Reference:** new simulator (`reference/kilnworks_sim.py`) and independent verifier/
mutation harness (`reference/kilnworks_verify.py`, `reference/mutant_per_campaign_reset.py`),
validated by two independent from-scratch reconstructions to full numeric
convergence (`audit/independent-reconstruction.md`).

**Recheck performed:** visual edge inventory unchanged and reverified; fresh
packet-only-equivalent independent audits (two rounds, see above) found and closed
three real specification gaps and two real reference-code bugs before freezing;
score-topology audit run against an executed per-campaign-reset mutant and a
perfect-local-semantics hypothetical, both kept under 50% (`platform/score-topology.md`);
all field/weight limits checked (`platform/numeric-transcription-checklist.md`).

**Old runs:** R2's two 100%-scoring Opus 4.8 Max trajectories are not acceptance
evidence for R3 and are not reused in any form. A fresh target-model pilot is
required before any acceptance runs.
