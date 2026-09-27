# Immediate platform handoff - after the successful R2 runs

The existing prompt, Ideal Flow and rubric are saved. They describe R2, which failed the requested difficulty target. No validated replacement architecture or new golden outputs exist yet. Do not spend another model run on a cosmetic rewrite of these fields.

## Changes to make now

1. Task disposition: change any Ready/Accepted status to Needs redesign, using the platform's available equivalent. R2 has successful target-model solutions and does not qualify as a technical-failure task.
2. Prompt field: no difficulty replacement is approved yet. Preserve the prompt actually used for the completed runs.
3. Ideal Flow fields: no difficulty replacement is approved yet. Preserve Analyze, Execute & Generate and Synthesize as used for those runs.
4. Rubric criteria1-41: no changes. Preserve every criterion and its exact weight. Positive total77; criterion41 is-8. The reported100% runs must not be rescored under new criteria.
5. Acceptance runs: do not launch additional unchanged R2 runs. Preserve the supplied successful trajectories.

## One existing filename mismatch

The current local prompt names KILNWORKS-T05-R2-20260926.pdf; the current local Ideal Flow Analyze field names kilnworks.pdf. The supplied trajectories refer to the uploaded artifact as kilnworks.pdf. This is a filename consistency issue, not the reason the task was solved.

Only if preparing a consistent historical copy with the actual upload named kilnworks.pdf:

- Section: prompt, first paragraph.
- Exact text to find: KILNWORKS-T05-R2-20260926.pdf
- Exact replacement: kilnworks.pdf
- Weights: unchanged.
- Everything else: unchanged, including all three Ideal Flow fields and all41 rubric criteria.
- Recheck: the actual attached file opens and contains the same four-page R2 specification. Keep the prompt used for the completed runs archived; do not overwrite that run's provenance.

Do not rerun merely because of this filename correction. A successful rewrite using CP-SAT solved the actual graph and all24 cases correctly.

## Saved files

- platform/prompt.md: existing R2 prompt.
- platform/ideal-flow.md: existing R2 Ideal Flow.
- platform/rubric.md: existing R2 rubric, singular canonical filename.
- platform/entry-guide.md: complete historical copyable fields and weights, now marked rejected for difficulty.
- audit/target-runs/architecture-failure.md: evidence-backed diagnosis and replacement gates.

The next substantive prompt/Ideal Flow/rubric must accompany a genuinely changed, executable architecture. Drafting new rules or expected answers before they exist would repeat the authoring failure. Remaining work begins with the generic-solver attack on the new architecture, then reference/goldens, then the three replacement fields and prospective frozen grading.
