# Task 05: KILNWORKS — Revision R3

R3 replaces R2's architecture after R2 was solved (two Opus 4.8 Max trajectories,
100% reported, via a straightforward CP-SAT exact-optimization model). See
`../STATUS.md` at the task05 root for R2's full rejection record — it is preserved
as-is, not overwritten.

R3 removes the free-optimization decision that CP-SAT exploited. Every dispatch
decision (machine assignment, robot routing, oven batching) is now pinned to one
explicit deterministic policy; the solver's job is to correctly **execute** that
policy across a long, continuous, cross-campaign run per design, with a state-
triggered robot fault forcing genuine engagement with the plant's shared junction.
See `design/architecture-attack.md` for the full rationale and perfect-semantics
ablation.

## Layout

- `design/` — architecture attack, perfect-semantics ablation, and the full visible
  semantic contract (S00-S12). Private authoring material.
- `reference/` — canonical simulator, independently-checked feasibility verifier,
  and mutation-test harness (including the per-campaign-reset mutant that
  represents "reverting to R2's architecture"). Private.
- `audit/` — activation-coverage evidence, mutation-kill results, and the two-round
  independent-reconstruction record that drove the reference to full numeric
  convergence with a from-scratch implementation. Private.
- `artifact/` — `make_packet.py` (deterministic matplotlib renderer, no image-
  generation model involved) and the rendered `kw-r3.pdf`. Only the PDF
  is model-facing.
- `platform/` — prompt, Ideal Flow, rubric, coverage ledger, score-topology audit,
  production witnesses, transcription checklist, entry guide, and revision delta.
  Only `prompt.md`, `ideal-flow.md`, and the rubric text are model-facing (via the
  platform UI, not as attachments); everything else here is grading material and
  must stay private.

## Status

Frozen locally after full independent-reconstruction convergence and a pre-pilot
score-topology audit. **No target-model pilot has been run.** Do not treat this as
submission-ready until Phase 10 of `../../Playbook/01-END-TO-END-SOP.md` (one pilot,
reconstructed and diagnosed) has actually happened.
