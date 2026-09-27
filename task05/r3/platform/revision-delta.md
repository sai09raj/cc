# R2 -> R3 -> R3b prospective revision history

## R2 -> R3

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
extraction was not the failure point. Artifact renamed
`KILNWORKS-T05-R2-20260926.pdf` / `kilnworks.pdf` -> `kw-r3.pdf`. Entirely new
prompt, Ideal Flow, rubric, and reference implementation.

## R3 -> R3b (hardening after local blind pilot 1)

Reason: a local blind-agent pilot against the frozen R3 packet (`kw-r3.pdf`,
`audit/blind-pilot-1.md`) scored ~85% against the R3 rubric. 4 of 6 designs matched
the reference exactly. The gap traced to one real bug in the agent's own oven-timing
code and one real gap in the R3 packet (the selection-key formula was never actually
rendered into the PDF). Both were confirmed by direct inspection, not assumed.

**Artifact:** `kw-r3.pdf` -> `kw-r3b.pdf` (new filename, different bytes -- do not
treat these as the same upload, per the mistake register's explicit warning against
filename reuse across revisions). Added: Section G (explicit lexicographic
selection-key formula, previously missing) and Section H (a second, independent
disruption mechanism: the Machine-Q maintenance freeze, S13). Tightened Section F's
oven-timer wording (explicit ">=" and explicit "arrival minute = one after the
delivering unload, not the minute picked up as anchor").

**Semantic contract:** added S13 (Machine-Q maintenance freeze) to
`design/semantic-contract.md`, deliberately using the *default* (non-inclusive)
boundary convention rather than copying S07's explicit inclusive exception, so a
solver must actually distinguish the two rather than pattern-match one onto the
other.

**Reference:** `reference/kilnworks_sim.py` implements S13 (`MAINT_THRESHOLD=12`,
`MAINT_WINDOW=13`, tuned empirically so the mechanism produces an observable effect
-- not merely fires silently -- in 5 of 6 designs; D0's immunity is structural, not
a shielding bug, and is disclosed as such). Added `canonical_trace_serialization`/
per-design hashing for the new trace-integrity hash criteria.
`reference/score_counterfactual.py` added: a programmatic rubric scorer used to
compute every score-topology counterfactual in this revision, replacing hand
arithmetic after it was shown to be error-prone in earlier rounds of this same
audit.

**Prompt:** unchanged in substance; filename reference updated to `kw-r3b.pdf`.

**Ideal Flow:** Analyze and Synthesize fields updated to mention the second
disruption mechanism and its deliberately-different boundary convention.

**Rubric:** substantially reweighted and extended (38 positive criteria at weight 61
-> 47 positive criteria at weight 221). New criteria 14-15 (maintenance
trigger/tracking, split from a single criterion so a boundary-only bug does not
also erase trigger-tracking credit) and 31 (maintenance-freeze production witness
W5). New criteria 36-41 (per-design SHA-256 trace-integrity hash, at the official
+10 ceiling) added specifically because lower weights let a single-mechanism
mutant retain 38-50% of positive weight -- see `score-topology.md` for the full
counterfactual evidence and the explicit disclosure that two narrow
single-boundary-bit mutants still sit at 29.9-30.8% despite two rounds of retuning.

**Goldens:** all six designs' makespan/bill changed (the new mechanism is not a
no-op): D0=187/1331 (unaffected structurally), D1=161/1242, D2=187/1373,
D3=185/1408, D4=151/1384, D5=153/1298. Unrestricted selection changed from D5 to
D4; budget selection remains D1.

**Old runs:** R2's two 100%-scoring trajectories and R3's local blind-pilot-1 run
are not acceptance evidence for R3b and are not reused in any form. A fresh local
blind pilot (`audit/blind-pilot-2.md`) and, eventually, a fresh target-model pilot
are both required before any acceptance runs.
