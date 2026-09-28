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
  semantic contract (S00-S13, including the hardening-round S13 Machine-Q
  maintenance freeze). Private authoring material.
- `reference/` — canonical simulator, independently-checked feasibility verifier,
  mutation-test harness (per-campaign-reset, fault/oven/maintenance disable,
  tiebreak-reversal, maintenance-boundary mutants), and `score_counterfactual.py`
  (the programmatic rubric scorer used for every score-topology number). Private.
- `audit/` — activation-coverage evidence, mutation-kill results, the two-round
  independent-reconstruction record, and two local blind-pilot runs
  (`blind-pilot-1.md` against the pre-hardening packet, `blind-pilot-2.md` against
  this hardened one). Private.
- `artifact/` — `make_packet.py` (deterministic matplotlib renderer, no image-
  generation model involved) and the rendered `kw-r3c.pdf` (current; `kw-r3b.pdf`
  kept for record only, do not upload it). Only the PDF is model-facing.
- `platform/` — prompt, Ideal Flow, rubric, coverage ledger, score-topology audit,
  production witnesses, transcription checklist, entry guide, and revision delta.
  Only `prompt.md`, `ideal-flow.md`, and the rubric text are model-facing (via the
  platform UI, not as attachments); everything else here is grading material and
  must stay private.

## Status

R3b's frozen packet was actually piloted: three real Opus 4.8 Max transcripts came
back scoring 72%, 73%, and 99% — far above the <50% target. Forensic reconstruction
(see `platform/revision-delta.md`'s R3b->R3c section) proved the two lower-scoring
runs' delivered simulators were bit-exact correct against `reference/kilnworks_sim.py`,
a genuine task-difficulty gap, not a scoring artifact. **R3c** hardens Section H's
Q-maintenance freeze from a one-time event to a recurring interval in response
(`kw-r3c.pdf`, new goldens, new rubric wording for criteria 14-16 — no weight or
criterion-count change). **No pilot has yet been run against R3c.** Do not treat
R3c as submission-ready until a fresh target-model pilot against it has been run,
reconstructed, and diagnosed per `../../Playbook/01-END-TO-END-SOP.md` Phase 10.
