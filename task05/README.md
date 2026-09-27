# Task 05: KILNWORKS

This folder is separate from the read-only authoring playbook. Start with STATUS.md.

**Active candidate: R3, in `r3/`.** R2 (the flat files at this folder's root:
`prompt.md`, `ideal-flow.md`, `rubric.md`, `entry-guide.md`, etc.) is **archived,
rejected-for-difficulty evidence** — two supplied Opus 4.8 Max trajectories solved
it at 100% via a straightforward CP-SAT exact-optimization model. Those files are
kept as-is for provenance; do not edit them and do not attach them to the platform.

R3 replaces R2's "find the exact global optimum via search" architecture with a
fully deterministic dispatch-and-simulate architecture (no free optimization
decision left for a generic solver), plus continuous cross-campaign chaining and a
state-triggered robot fault at the plant's shared junction. See
`r3/design/architecture-attack.md` for the rationale and `r3/README.md` for the
folder layout. Only `r3/artifact/KILNWORKS-T05-R3.pdf` plus `r3/platform/prompt.md`
and the Ideal Flow/rubric text are model-facing; everything else under `r3/design/`,
`r3/reference/`, `r3/audit/`, and the rest of `r3/platform/` is private grading
material.

The original R1/R2 provenance note is preserved below for history: R1 was a local
development packet; R2 deleted two lower aisles so production transport had to use
the shared junction. No previous task's topology, tuple format, file package, or
goldens were reused across R1/R2/R3 without fresh derivation and re-audit.
