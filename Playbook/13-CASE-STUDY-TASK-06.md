# Case Study — Task 06 ATRIUM-9

> **Correction (later audit):** the packet never states the busy-car
> assignment cost, the `avg_wait` definition, the per-tick stage order,
> the timeout threshold and reset rule, the direction and selection
> tie-breaks, or when the run ends, all of which the reference uses, and
> the reference does not implement the packet's reassignment ban. An
> `opus`-alias blind pilot reproduced the real pilots' failure pattern
> from those gaps. The 20%/21% below are therefore not clean evidence of
> difficulty, and the "what worked" conclusions should be read with that
> in mind. See `task06/audit/code-source-audit.md` and mistake #71.

## Status and evidence boundary

ATRIUM-9 (task06, Building Systems / Vertical Transportation Engineering)
replaced a shelved prior candidate, KILNWORKS (task05), which had no genuine
search or optimization space and could be passed by a small clean rewrite.
ATRIUM-9 is a deterministic tick-by-tick discrete-event simulation of a
4-car elevator bank with a 144-configuration exhaustive sweep and three
competing selection objectives.

Three real Opus 4.8 Max pilot runs are user-confirmed complete, all scoring
below the 50% target. Two full trajectories are archived locally (see
Evidence paths) with confirmed scores of **20%** and **21%**; the third run's
exact score is user-reported as "below 50" but its trajectory was not
uploaded and must not be invented beyond that. This case study's forensic
claims about model behavior are drawn only from the two archived
trajectories; do not extend the specific numeric claims below to the third,
unarchived run.

## Task architecture

- 4 independent cars (A–D) as separate state machines, 8 floors (L0–L7).
- Direction-separated commitment tracking: `committed[UP]` and
  `committed[DOWN]` are different sets even for the same floor, because a
  call's required direction is fixed at assignment and must not be confused
  with whichever way the car physically faces when it later reaches that
  floor.
- Hall-call eligibility: an idle car (no commitments in either direction) is
  eligible for any call at distance-based cost; a scanning car is eligible
  only for a call in its own current direction still ahead of it (no
  mid-scan backtracking).
- A shared, cross-car power budget admitted in one fixed-priority
  (A,B,C,D) pass per tick; a new floor-hop, a new door-open, and the
  DWELL-to-CLOSING transition are each their own power-gated event — a car
  whose dwell has elapsed does not leave DWELL until its door-close is
  itself admitted.
- Non-combinable, cost-compared timeout reassignment: a call switches cars
  only when a strictly cheaper alternative exists, never merely because a
  clock expired, and a call once reassigned away from a car is permanently
  banned from that car.
- The genuine decision space: a 144-configuration exhaustive sweep
  (`active_cars` in {2,3,4} x `zoning` in {SPLIT,GROUND,TOP} x
  `wait_timeout` in {50,75,100,125} x `power_budget` in {6,8,10,12}), with
  three non-monotonic, competing lexicographic selections (wait-optimal,
  energy-optimal, budget-constrained under `net_energy<=3800`) that do not
  agree in the reference solution.

The prompt (`platform/prompt.md`) requires an offline deterministic
simulator, a separately-coded verifier sharing only immutable constants,
execution of the full 144-row sweep as one continuous 80-call run per
configuration (explicitly forbidding a shortened/sampled run), the two
required adversarial mutations, and a memo with causal explanations tied
to actual trace events. The artifact (`atrium9.pdf`) carries the shaft
layout, door-timing waveform, and power-tariff constraint as raster
diagrams with figures the model must measure, not read off as printed
numbers.

## Rubric evolution: 61 -> 50 -> 10 linter rounds

The first weight-capped redesign was built checking only the platform's
`<=10` per-criterion weight cap and missed the separate `<=50` total
criteria cap, shipping 61 criteria. This was caught and fixed by
consolidating same-mechanism pairs (see Mistake #38 in the register: never
pad to 50, but also never blow past it).

After that, ten rounds of platform-linter "Critical" findings were
diagnosed and fixed, each verified against the actual source files
(`prompt.md`, `semantic-contract.md`, `atrium_sim.py`) before any edit, and
each re-verified with `score_counterfactual.py` afterward so the fix never
silently broke the score topology. Genuine findings, in order:

1. Verifier-independence prohibition stated only inside a positive
   criterion -> dedicated `-4` negative added.
2. Reassigned-away-call non-reuse prohibition, same pattern -> `-4`
   negative added.
3. Per-tick search / free scheduling choice prohibition uncovered ->
   `-4` negative added.
4. Equal-cost bouncing between cars prohibition uncovered -> `-3`
   negative added.
5. Shortened/sampled sweep run prohibition uncovered -> `-5` negative
   added.
6. DWELL-to-CLOSING gating stated only inside the power-admission-order
   positive criterion -> `-5` negative added (round 10; see below).
7. A dropped reconciliation criterion left criterion 19's sample row
   (lower `avg_wait` than the budget-constrained pick) unexplained ->
   explanatory parenthetical added citing the `net_energy<=3800` ceiling
   by number.
8. "Budget" used for both `power_budget` (a sweep dimension) and
   "budget-constrained" (a selection name) collided on one config row ->
   reworded to remove the overloaded word entirely.
9. "Inactive" (outside the active roster) vs. "idle" (active but
   uncommitted) used without disambiguation -> explicit "active roster" /
   "OUTSIDE the active roster" language added to both criteria.
10. A positive criterion's parenthetical restated a fact a newly-added
    dedicated negative now independently tested (double-charging) ->
    parenthetical trimmed, weight moved to the new negative.

Two findings were diagnosed as false positives and marked invalid on the
platform, not edited:

- A "same target, zoning TOP vs SPLIT on the same 2-car/50/6 config"
  contradiction flag on the energy-optimal (criterion 14) and
  budget-constrained (criterion 15) rows. These are two different,
  deliberately distinct selections that legitimately share
  `active_cars=2, wait_timeout=50, power_budget=6` and differ only in
  `zoning` — that is the correct answer, not a contradiction. See the new
  "Partial-tuple overlap is not a contradiction" entry in
  `03-RUBRIC-AND-LINTER-GUIDE.md`.
- Two false positives from the same underlying cause were also traced and
  fixed rather than invalidated (`power_budget` vs. `budget-constrained`,
  `inactive` vs. `idle`) — see #8 and #9 above; these were genuine wording
  collisions, not spurious pattern-matches, so they were fixed, not
  invalidated.

Net result across all ten rounds: positive total moved 281 -> 266,
negative total moved -28 (six negatives) -> -33 (seven negatives), and the
criteria count stayed pinned at exactly 50 throughout — every negative
added was paid for by trimming or merging a positive, never by exceeding
the cap.

One process lesson surfaced repeatedly: the platform's displayed criterion
row numbers drifted from this repo's sequential numbering at least twice
(observed as "C44 vs C45," "C33 vs C47" mismatches against the same
underlying content). Every fix was therefore given to the user as exact
quoted text to find and replace, never as "row N," and that discipline
should be treated as mandatory for any future task with a similar
platform-side editing loop.

## Score-topology validation: synthetic mutants vs. real runs

`reference/score_counterfactual.py` scores the canonical reference and
three plausible-wrong mutants (timeout reassignment disabled, reassignment
that never compares cost, power admission disabled) against the live
rubric weights. Final verified state:

| Run | Score |
|---|---|
| Canonical (sanity) | 100.0% |
| `mutant_no_timeout` | 31.2% |
| `mutant_no_cost_compare` | 36.5% |
| `mutant_power_disabled` | 30.1% |

All three plausible-wrong mutants land comfortably under 50%, and the
`mutant_power_disabled` case was confirmed (by reading `atrium_sim.py`
directly, not assumed) to also violate the new DWELL-to-CLOSING negative
criterion, since that mutant sets `remaining = 10**9`, which bypasses the
same `remaining < POWER["door"]` gate the DWELL-to-CLOSING transition
checks — not a separate failure mode, the same power-budget-disabled bug
the mutant already fails criterion 10 for.

The two archived real pilot runs scored **20%** and **21%** — both *below*
every synthetic mutant's score, not just below 50%. This is the single
most important empirical result of this task: the rubric's synthetic
plausible-wrong mutants, calibrated by hand before any real pilot ran,
turned out to be *more generous* to a wrong implementation than what an
actual frontier-model attempt produces. That is the direction of error you
want — a rubric whose synthetic mutants score lower than real failures
would be dangerously over-fit to hand-picked bugs and might pass a real
wrong answer; here the reverse happened, giving genuine safety margin.

## Real trajectory forensics

Both archived trajectories (Opus 4.8 Max, full effort, ~88 and ~unknown
turn counts, session durations on the order of 45+ minutes of API time)
independently:

- Correctly recovered every global constant from `atrium9.pdf` by
  pixel-measuring the raster diagrams (capacity 6, door-timing waveform
  4/2/3/2 ticks, power-tariff units) — the artifact's metadata-stripping
  and rasterization did not stop correct semantic recovery, confirming the
  security measure did not accidentally make the task unfair.
- Built a from-scratch primary simulator plus a genuinely independent,
  different-language verifier (Python primary + Node.js verifier in both
  cases), matching the prompt's independence requirement.
- Ran the full 144-config sweep as one continuous 80-call run per config
  (no shortened/sampled run — the negative trap for that did not trigger).
- Self-certified: baseline trace hashed and cross-checked across Python
  `hashlib`, Node `crypto`, and `sha256sum`; both required adversarial
  mutations correctly rejected by each model's own verifier.
- Produced polished, professional, highly confident memos ("All six checks
  PASS," "every reported number is produced at runtime," "independently
  verified").

And yet both were substantively wrong against the reference:

| Selection | Reference | Traj (score 21) | Traj (score 20) |
|---|---|---|---|
| Wait-optimal config | `(4,SPLIT,50,6)` | `(4,SPLIT,50,6)` — right config, wrong numbers | `(4,SPLIT,50,8)` — wrong `power_budget` |
| Wait-optimal `avg_wait` | 8.1375 | 15.888 (~1.95x) | 15.25 (~1.87x) |
| Energy-optimal config | `(2,TOP,50,6)` | `(2,GROUND,50,6)` — wrong zoning | `(2,SPLIT,50,6)` — wrong zoning |
| Budget-constrained config | `(2,SPLIT,50,6)` | `(2,GROUND,50,6)` — wrong zoning, wrongly coincides with energy-optimal | `(2,GROUND,50,6)` — wrong zoning |
| Baseline trace hash (first 16 hex) | `f544b2d2a1d0fb30` | `cff62dd19005b579` | `6a7bfe50783935f1` |

Three findings from this table matter beyond this one task:

1. **Both models converged on the same qualitative dispatch architecture as
   the reference** (per-direction commitments, LOOK-style scanning,
   idle-car home-parking, cost-compared timeout reassignment, power-gated
   admission in fixed priority) — confirmed by reading the actual
   simulator source both models wrote. The task is not being failed by
   models missing the high-level design; it is being failed by small,
   independent deviations in the exact eligibility/cost/tie-break rules
   that compound across an 80-call, 144-config run into a ~2x wait-time
   error and a wrong zoning pick. This is the compounding-fragility
   mechanism documented for Task 03/04 (register entries #45, #51, #58),
   now confirmed on a genuinely different task shape (exhaustive
   multi-objective sweep, not a fault-injection timeline) — evidence the
   principle generalizes rather than being an artifact of one task's
   mechanism.
2. **The two models did not converge on the same wrong answer.** Traj 21
   picked GROUND for both energy-optimal and budget-constrained; traj 20
   picked SPLIT for energy-optimal and GROUND for budget-constrained.
   Different specific implementation choices produced different specific
   wrong numbers, which is a healthy sign: there is no single "attractor"
   wrong answer a model can get lucky into, consistent with the design
   note in `semantic-contract.md` that only one policy-conformant trace
   per configuration exists.
3. **A fully self-consistent, cross-language, independently-verified
   result was still wrong.** Both models' own verifiers reported 100%
   agreement with their own primary implementation and correctly rejected
   both adversarial mutations — and both were still ~80% wrong on the
   graded facts. Self-consistency between a primary and its own verifier
   proves internal consistency of one (possibly wrong) interpretation; it
   is not evidence of correctness against the packet. This rubric never
   grades "does the verifier agree with the primary" as a proxy for
   correctness — every numeric criterion is checked against the actual
   reference sweep/baseline values, independent of what either model's
   internal verification concluded — and that design choice is what let a
   fully-self-certified wrong answer still score 20-21%. A rubric that
   rewarded verifier-primary agreement as a correctness signal would have
   scored these runs far higher than they deserved.

Both models also correctly implemented the harder, easy-to-miss rules the
prompt calls out explicitly — power-gated (not automatic) door-closing,
and permanent reassignment bans — matching what the negative criteria for
those specific anti-patterns were designed to catch. Neither negative
triggered for either run, meaning essentially all of the ~79-80% points
lost came from the **positive** discriminating criteria, chiefly the
whole-sweep aggregate bloc (criteria 20-32, 130 of 266 positive points)
and the baseline-trace witnesses (criteria 33-40, tied to a hash that
diverged in both runs) — exactly the buckets this rubric weights heaviest,
by design, because they are wrong under every plausible-wrong mutant
tested and, now confirmed, under every real attempt observed.

## What worked

- **Exhaustive-sweep-plus-aggregates as the primary difficulty
  mechanism.** A 144-row sweep with grand totals and filtered partial
  sums over the sweep dimensions is wrong under all three synthetic
  mutants and both real runs simultaneously, because any local dispatch
  deviation perturbs nearly every row, not a handful of calls. This
  "universal-fail" property is what let ten criteria (130 points) do most
  of the discriminating work, matching the register's existing guidance
  (#51, #58) but now validated on an aggregation-based task shape.
- **Grading against the external reference, never against internal
  verifier agreement.** Confirmed necessary by the real trajectories: both
  models' verifiers passed their own primary with 100% agreement while
  being substantively wrong against the reference.
- **Counterfactual mutant testing before the pilot, then treating real
  pilot scores as the actual gate, not the synthetic scores.** The
  synthetic mutants (30.1-36.5%) gave confidence to submit; the real pilot
  runs (20%, 21%) confirmed the margin was real and, if anything,
  under-estimated how hard the task would be for a real attempt.
- **Metadata-stripped, rasterized PDF artifact.** Verified zero hits for
  Producer/Creator/Author/dates/tEXt chunks and zero vector drawing
  objects in the raw PDF bytes, so the diagrams cannot leak
  authoring-tool coordinate data as a shortcut to the numeric answers —
  and the real trajectories confirm this did not prevent correct
  legitimate recovery of the layout/timing/power constants, so the
  fairness measure did not accidentally make the task impossible.
- **Fixing platform-linter findings by verifying against source first,
  every time**, rather than trusting the linter's framing. Nine of eleven
  findings across this task were genuine and required real rubric
  changes; two were false positives from partial-tuple overlap and were
  correctly marked invalid rather than "fixed" into something worse.

## What did not work / cost time

- **Missing the separate 50-criteria cap on the first pass** (61
  criteria shipped, checking only the per-criterion `<=10` weight cap).
  Caught before platform entry, not after — a preflight checklist item to
  keep first on any future task with a hard-capped platform.
- **A naive "just clamp the five over-10 weights down to 10" repair was
  tested and rejected before implementation** — hand-computed, it would
  have pushed all three mutants to 52-68%, the opposite of the
  requirement. Worth stating as a general warning: clamping weights
  without redesigning which facts carry them can silently invert a
  rubric's score topology; always re-run the counterfactual scorer after
  any weight change, never assume a clamp is safe by inspection.
- **Chasing a `<15%` target past the mathematically achievable floor.**
  The floor any mutant earns even failing every discriminating criterion
  was computed at ~15.3%; going lower would have required either gutting
  genuine coverage or grading against non-plausible mutants, neither
  permitted by the playbook's difficulty-engineering rules. The task
  settled at real scores of 20-21%, which is a better outcome than a
  forced sub-15% design would have produced, since it left genuine
  coverage intact.
- **A "positive-only prohibition" pattern kept recurring across rounds**
  (verifier independence, reassignment reuse, per-tick search, equal-cost
  bouncing, shortened runs, DWELL-to-CLOSING gating) — six separate
  instances of the same authoring mistake, each caught by the platform
  linter one round at a time rather than all at once during initial
  authoring. A systematic pass — for every "must," "never," or "not
  automatic" clause anywhere in the rubric, positive or bundled inside
  another positive, confirm a dedicated negative exists — should be run
  once during initial authoring, not discovered six times by the linter
  after submission.

## Generalizable technique: how to fail a frontier model on a future task

Distilled from what actually discriminated real Opus 4.8 Max attempts on
this task, for reuse on a materially different future task shape:

1. **Put the genuine difficulty in composition over scale, not in any
   single hard rule.** Both real trajectories implemented every
   individually-named hard rule correctly (power-gating, non-reuse,
   direction-separated commitments) yet still failed, because the actual
   failure surface was the compounding interaction of many correctly-named
   but subtly-misimplemented small rules (eligibility boundary, cost
   tie-breaking, exact scan-continuation order) across a long run. A model
   can special-case any one rule you name explicitly; it cannot as easily
   special-case the emergent behavior of dozens of rules composed over an
   80-call, 144-config execution.
2. **Grade grand totals and filtered partial sums over the full
   search/sweep space, not just the headline selections.** A wrong
   selection can still land close to a plausible config by chance; a wrong
   aggregate over 144 rows almost never does, because it is wrong by the
   same small compounding error on nearly every row.
3. **Never grade a model's own verifier's agreement with its own primary
   as a correctness signal.** Grade every numeric fact against the actual
   external reference value. A verifier only proves a model is
   consistent with itself.
4. **Run real pilot(s) even after synthetic mutants clear the bar with
   margin**, and treat the real scores, not the synthetic ones, as the
   actual acceptance evidence. Here the real scores were lower (harder)
   than the synthetic mutants predicted, which is the safe direction of
   surprise — but that could only be confirmed by actually running the
   pilot.
5. **Audit every positive criterion for a bundled "must never" or "not
   automatic" clause during initial authoring**, not only in response to
   linter findings. Six separate instances of exactly this pattern were
   caught one at a time by the platform linter on this task; a single
   systematic pass at authoring time would have caught all six before the
   first submission attempt.
6. **When a linter flags two criteria as contradictory, check for
   legitimate partial overlap before rewriting anything.** Two distinct,
   correct answers in a multi-dimension sweep can legitimately share every
   dimension but one; that is not a contradiction, and the fix is to mark
   the finding invalid with the specific shared/differing dimensions
   named, not to reword either criterion.

## Evidence paths

- `task06/reference/atrium_sim.py` — canonical reference simulator.
- `task06/reference/score_counterfactual.py` — synthetic mutant scorer
  (canonical 100%, mutants 31.2% / 36.5% / 30.1%).
- `task06/platform/rubric.md` — final 50-criterion rubric (positive 266,
  negative -33 across seven negative criteria).
- `task06/platform/prompt.md`, `task06/platform/ideal-flow.md`,
  `task06/design/semantic-contract.md` — frozen source-of-truth documents
  every linter finding was verified against before any fix.
- `task06/artifact/atrium9.pdf`, `task06/artifact/make_packet.py` —
  metadata-stripped, rasterized artifact and its generator.
- Real pilot trajectories: two full Opus 4.8 Max session transcripts,
  user-scored 20% and 21%, uploaded and analyzed for this case study. A
  third real run is user-confirmed below 50% with no further detail
  archived locally; do not cite a specific score for it.

## Final lesson

A task can be architecturally sound, pass every synthetic mutant test with
margin, and still under-predict how hard it actually is for a frontier
model — in the safe direction. The two real trajectories analyzed here
show a capable model doing essentially everything asked competently and
confidently (correct artifact recovery, independent cross-language
verification, polished causal memos) while still landing at 20% and 21%
because the task's genuine difficulty lives in the composed interaction of
many small, individually-reasonable dispatch rules over a long
deterministic run — not in any single rule a model could special-case, and
not recoverable by a self-consistent but ungrounded verifier. That
composition-over-scale mechanism, not any one clever trap criterion, is
what should be reused on the next task.
