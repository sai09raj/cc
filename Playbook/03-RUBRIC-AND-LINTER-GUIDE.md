# Rubric, Linter, and Platform-Entry Guide

## What the rubric is for

The rubric converts observable task requirements into fair binary checks. It does not define missing task semantics and must not be used to manufacture difficulty.

The project source set used here requires 12–50 criteria, each weighted from -10 to +10. This is a range, not a quota: use only the rows needed for complete, nonduplicative coverage. Never pad a rubric to 50. The handbook contains the page-level citations and documented policy conflicts.

## Criterion construction formula

A reliable positive criterion has this shape:

```text
<observable verb> <specific delivered object/result> <expected condition> <tolerance/equivalence if needed>.
```

Examples:

- `Reports the measured refresh occupancy as 42 cycles.`
- `Delivers sweep.csv with exactly 272 data rows, one for each legal configuration.`
- `Identifies {Q:8,H:4,B:2,L:96} as the sole target-qualified configuration under the visible packet semantics.`

A reliable negative trap has this shape:

```text
<affirmative observable wrong behavior>, when that behavior is explicitly prohibited or observed and materially wrong.
```

Examples:

- `Embeds reported metric values as literal pass conditions in controller_sim.py.`
- `Presents fewer than 272 legal configurations as an exhaustive sweep.`
- `Runs a workload whose request operation, address, phase count, or phase order deviates from the supplied workload specification.`

## Eight tests for every criterion

1. **Objective:** two careful graders should reach the same pass/fail result.
2. **Binary:** the condition has a clear boundary.
3. **Observable:** the response or delivered files contain the evidence.
4. **Verb-led:** it begins with an action such as Reports, Delivers, Uses, Identifies, Demonstrates, or Embeds.
5. **Atomic:** it tests one behavior or one indivisible answer object.
6. **Self-contained:** the expected answer is in the criterion; the grader need not reopen the input or recalculate it.
7. **Nonduplicative:** no sibling charges the same behavior again.
8. **Equivalent-tolerant:** valid alternative wording, organization, method, units, and schema pass unless the prompt made exactness essential.

## Embedded canonical rules from the official rubric guide

This section is the local operational substitute for repeatedly extracting `rubric.pdf`. Recheck the source PDF only when the platform publishes a newer revision or a linter message reveals a policy change.

1. A rubric is a weighted set of binary checks on the delivered response and files.
2. Every criterion must begin with an observable verb and name a yes/no condition.
3. Grade delivered artifacts, not hidden reasoning, effort, or intent.
4. Split a row whenever two clauses can be independently right or wrong.
5. Keep a genuinely unitary object together: one tuple, one ordered interface, one state-transition vector, one serialized record, or one named output vector.
6. Put the expected answer inside the criterion. A heading, prompt reference, sibling row, or phrase such as `packet-defined` cannot supply a missing expected value.
7. Make the set mutually exclusive and collectively exhaustive: no duplicate, mirror, uncovered prompt clause, uncovered deliverable field, or unscored essential expert check.
8. State tolerances, rounding, units, equivalent formats, and semantic equivalents wherever exact textual form is not essential.
9. Phrase a negative trap as an affirmative description of active bad behavior. If the statement is true, its negative weight must subtract points.
10. Penalize an active fabrication, forbidden shortcut, false conclusion, or material corruption - not a simple omission already handled by a positive row.
11. Do not mirror a positive row with the corresponding wrong answer as a negative row.
12. Prefer observed failure modes from a pilot. An explicit prompt prohibition may justify a trap before the pilot, but it must still be active, atomic, self-contained, and nonduplicative.

### Self-containment substitution test

Temporarily hide the prompt and attachment, then hand a grader only the criterion and the submitted files. If the grader must ask what `exact`, `requested`, `packet-defined`, `correct`, or `specified` means, the criterion fails.

Common forbidden shorthand:

- `the exact requested columns` - list the columns;
- `the packet release ranges` - list the ranges and formulas;
- `the displayed order` - state the order;
- `the specified cleanup` - state the before/after state;
- `the same command` - repeat the command;
- `correctly explains` - state the expected causal conclusion;
- `focused tests` - state an observable test count or named boundary.

The text above a rubric table is documentation only. It cannot rescue a criterion that lacks its own expected answer.

### Atomicity decision procedure

For every conjunction, semicolon, slash, comma-separated list, or range:

1. Ask whether a response could satisfy one part and fail another.
2. If yes, split the row.
3. If no because the parts form one answer object, name that object explicitly, such as `latency vector`, `crash transition`, `ordered schedule set`, or `CSV header`.
4. Keep presentation or existence checks low weight; put high weight on technical state transitions and decisions.
5. Never call a table atomic merely because the row limit is inconvenient.

An answer vector is permissible only when all components belong to the same named record and are graded together as that record. Do not combine a metric vector with a separate safety conclusion, file-existence check, or causal explanation.

## Mandatory rubric construction workflow

### Step 1 - Freeze sources

Freeze the prompt, upload artifact, semantic contract, executable oracle, and canonical result files before authoring criteria. Any later semantic change invalidates the rubric audit.

### Step 2 - Build a coverage ledger

Create one row for every:

- prompt action;
- output file;
- required field or section;
- visual measurement;
- state-transition family;
- exact count, tuple, ordering rule, threshold, and hash;
- explanation or engineering decision;
- explicit prohibition.

Give each ledger item an owner criterion ID. A prompt clause may have multiple owners only when they score distinct behaviors.

### Step 3 - Prepare canonical answer objects

Generate named objects from executable output rather than typing literals manually:

- ordered filename set;
- configuration-space product;
- schedule set;
- stage-order list;
- metric vectors;
- safety-classification records;
- qualifier summary;
- hash-serialization contract;
- affirmative anti-pattern list.

### Step 4 - Budget rows before prose

Reserve rows in this order:

1. explicit prohibitions and observed catastrophic anti-patterns;
2. visual measurements and central state transitions;
3. runnability, workload, schedule, and search-space checks;
4. decisive output records and selection;
5. lower-weight packaging and report-section inventory.

If the 50-row limit is exceeded, remove low-value duplication or combine fields only into a defensible named answer object. Never hide independent behavior behind `and` merely to fit. If coverage is complete at 37, 44, or 49 rows, stop there.

### Step 5 - Run four audits

1. **Criterion audit:** verb-led, binary, observable, atomic, self-contained, tolerant.
2. **Pairwise audit:** compare every row against every sibling for duplicate or mirror scoring.
3. **Coverage audit:** map every prompt clause and deliverable requirement to at least one row.
4. **Adversarial audit:** test a technically correct alternate format and a superficial literal-copy solution.

### Step 6 - Freeze and enter

Run mechanical lint, save the final local rubric, then enter exactly that version. After manual entry, compare screenshots or exported text against the canonical file row by row. Do not repair individual UI tokens from memory.

## Task 03 corrective case study

The first Task 03 draft had 50 rows and valid weights, yet it was not ready. Its title claimed `50 Atomic Criteria`, but many rows used shorthand such as `packet-defined`, bundled unrelated metrics, or double-counted safety and sweep completeness.

The repair established these reusable patterns:

- one exact five-file package row, with separate runnability and content siblings;
- complete workload, schedule, stage-order, and schema objects embedded directly in their rows;
- separate network, disk, admission, flush, recovery, retry, deduplication, and retirement transitions;
- named baseline/selected latency, queue, protocol, and safety records rather than one giant metric paragraph;
- explicit rounding acceptance for three-decimal means and equivalent JSON formatting;
- a sweep-completeness positive row plus a distinct negative trap for fabricated/unevaluated rows, avoiding a direct mirror;
- five affirmative traps covering external dependencies, golden-oracle use, precomputed configuration answers, partial execution disguised as complete, and weakened safety evaluation;
- automated lint for verb starts, vague shorthand, exact knob sets, schedules, measured constants, CSV schema, canonical vectors, qualifier summary, hash integrity, and negative polarity.

The lesson is structural: passing a count/weight linter is not rubric certification. Manual atomicity, self-containment, MECE, coverage, and tolerance audits remain mandatory.

The corrected Task 03 rubric deliberately uses 49 rows. One selected metric was removed and the causal/tradeoff paragraph was split because independently gradable claims matter more than filling the fiftieth slot.

## Atomicity without absurd fragmentation

Separate independent requirements:

- reset state;
- reset outputs;
- accepted-tail base update;
- unlocked single-beat behavior.

Do not split a unitary answer object solely because it contains fields. A configuration tuple, ordered interface, or one serialized record can be one criterion if it is judged as one object.

The earlier ROB rubric triggered atomicity concerns by combining reset base, buffer, and lock state and by combining accepted-tail behavior with the single-beat special case. Those should be separate unless the platform limit makes a clearly justified unitary object necessary.

## Existence is not content

`Delivers five files` checks package completeness only. It does not prove the files contain anything useful. Add sibling criteria for the required content and behavior of each file.

An existence-only first criterion was once flagged by the linter as broad/non-binary because “five empty files” could pass it. That criticism is valid if no siblings cover contents. It is not necessarily valid when the criterion intentionally checks package completeness and later criteria exhaustively check content. If marking such feedback invalid, state exactly which sibling criteria cover the contents.

## Negative criteria and prohibitions

### Every prompt prohibition creates a trap obligation

If the prompt says “do not,” “must not,” “cannot,” or “not acceptable,” create a separate negative criterion for each observable forbidden behavior. A compound sentence with four prohibitions may require four traps.

This caused a platform warning for the phrase:

> Do not assume a conventional address map, turnaround value, event order, or scheduler behavior.

The cleaner repair was to rewrite it positively:

> Derive the address map, turnaround values, event order, and scheduler behavior from the packet.

Positive requirements are still rubric-covered, but they do not force a forest of negative traps.

### Negative traps penalize active wrongness, not omission

Good:

- `Uses a stale W→R guard of 8 cycles.`
- `Changes scheduler mode because an aged request dispatches.`
- `Closes an open row after every request.`

Bad:

- `Fails to mention the guard.`
- `Does not explain scheduler mode.`
- a negative mirror of a positive metric criterion.

### Make the direction unmistakable

One attempted trap used “derives from Panel E” when it needed “deviates from Panel E.” That one word reversed the meaning: a correct packet-derived workload would have triggered the penalty. Always read negative criteria as executable logic:

```text
IF criterion is true, subtract points.
```

If the statement describes correct behavior, the trap is backwards.

### Avoid intent qualifiers

The linter correctly rejected “to improve the result” because intent is unobservable. Replace it with an external condition:

```text
Runs a workload that deviates from Panel E in any request operation,
request address, phase count, or phase order.
```

### A prohibition can hide inside a positive criterion, not just the prompt

“Every prompt prohibition creates a trap obligation” above covers a
standalone prompt sentence such as “do not assume X.” The same obligation
also applies when a *rubric-authored* positive criterion bundles its own
“must never,” “not automatic,” or “always X, not Y” clause into an AND
alongside an unrelated positive fact. Task 06 shipped six instances of
exactly this pattern across six separate linter rounds — verifier
independence, reassignment non-reuse, per-tick search, equal-cost
bouncing, shortened runs, and DWELL-to-CLOSING gating each started as a
clause bundled inside a positive criterion, and each had to be split into
its own dedicated negative one round at a time.

Fix pattern, in order:

1. Trim the bundled clause out of the positive criterion, keeping only its
   core fact.
2. Add a dedicated negative criterion stating the forbidden behavior
   directly (`IF criterion is true, subtract weight`, per the polarity
   check above).
3. Check whether the trimmed positive's remaining wording (often a
   leftover parenthetical) still restates the same fact the new negative
   now owns — if so, trim that too, or the contradiction linter will flag
   the fact as graded twice (see the next section).
4. Pay for the new negative's row by merging a same-mechanism pair
   elsewhere, never by exceeding the criteria cap.

Run this as a systematic pass over every positive criterion during initial
authoring — scanning for “must,” “never,” “always … not,” and “not
automatic” inside AND-joined clauses — rather than waiting for the linter
to surface each instance separately.

## Coverage passes

### Pass 1 — prompt clauses

Underline every requested action, file, metric, explanation, constraint, exact format, and prohibition. Map each to at least one criterion.

### Pass 2 — deliverables

For each file, cover:

- existence if package completeness matters;
- runnability or parseability;
- essential fields/sections;
- decisive computed values;
- cross-file consistency;
- row/count/completeness requirements.

### Pass 3 — expert essentials

Cover the technically central facts a superficially complete answer could still get wrong:

- measured constants;
- revision priority;
- state/event ordering;
- boundary convention;
- legal search space;
- selection/tie-break;
- causal conclusion.

### Pass 4 — anti-patterns

Cover each explicit prohibition and only material observed wrong behaviors that are not mere omissions or duplicate mirrors.

## Weighting

Highest positive weights should go to the core decision and foundational behavior. Lower weights should go to supporting metrics and report presentation.

Check dependency direction. A downstream hash or final recommendation should not completely outweigh the correct simulator semantics from which it derives. Conversely, a file-existence point should not rival the core technical result.

For negative weights, reserve -8 to -10 for catastrophic cheating or a central prohibited behavior, not minor formatting.

After assigning weights:

1. sort by absolute weight;
2. inspect the top five;
3. ask whether they represent the real task;
4. find duplicate routes to the same loss;
5. simulate a technically strong but differently formatted answer;
6. simulate a superficial package with exact literals;
7. confirm the former passes and the latter fails.

### Score topology and the plausible-wrong survival ceiling

Weight totals can hide a weak grading structure. Before platform entry, partition every positive point into four buckets:

1. package, existence, schema, and presentation;
2. local parsing, constants, and isolated rules;
3. integrated production execution;
4. final decision and causal reconciliation.

Then counterfactually grade both (a) an answer granted perfect local semantics but with incomplete or wrong global execution and (b) a runnable answer that gets most local rules right but composes the system incorrectly. Include any headline results a plausible shortcut could still recover. Reject the rubric if either answer can retain 50% or more.

The rubric must not depend on the frontier model making a semantic-reading mistake. Local semantic rows may verify correctness, but integrated execution, verification, and decision evidence must still make a globally wrong answer fail after every local rule is granted.

Task 04 Revision E had 315 positive points. Mostly local criteria 2–31 carried 142, and a wrong integrated simulator still recovered about 30 points of headline selections. Its survival ceiling was therefore approximately `172/315 = 54.6%`. Two real runs scored 52 and 59 despite producing the wrong production trace. This was a rubric-topology failure, not evidence that local criteria were individually invalid.

For a new task, change weights or criterion ownership before the first pilot if needed. After a run exists, do not retrofit grading to lower its score; create a prospective revision.

Treat hand-picked synthetic mutant scores as a pre-pilot confidence check,
not the acceptance evidence itself. Task 06's three synthetic mutants
(timeout reassignment disabled, cost-compare disabled, power admission
disabled) scored 31.2% / 36.5% / 30.1% against the frozen rubric; two real
Opus 4.8 Max pilot runs against the same rubric scored 20% and 21% —
*lower* than every synthetic mutant. That is the safe direction of
surprise: the synthetic mutants under-estimated real difficulty rather
than over-estimating it. Always run the real pilot even after synthetic
mutants clear the bar with margin, and treat the real scores as the actual
gate.

### Integrated conformance witnesses

When temporal composition is central, a local rule may be checked through a named record from the same ordinary execution that produces the graded summaries. Such a row is defensible only when:

- the prompt requires the underlying full trace/checkpoint output;
- the artifact visibly specifies the rule;
- the criterion states schema, index base, and expected record;
- the witness is mechanically extracted from one uninterrupted run;
- equivalent organization remains acceptable where exact layout is unnecessary; and
- the record is the execution manifestation of that rule, not an unrelated second claim.

Do not count a cascade of downstream rows as independent defects without a dependency audit. A single missing persistent counter may alter hundreds of events. Select witnesses across different rules, components, and epochs, or use checkpoint deltas/metamorphic invariants with clearer causal ownership.

## Tolerances and equivalent forms

Use exact values when the system is deterministic and exactness is meaningful. Use justified bands when rounding, stochasticity, measurement, or tool variation exists.

For each numerical criterion record:

- canonical value;
- unit;
- accepted range;
- rounding rule;
- whether an equivalent fraction/percentage/unit passes;
- decision boundary that must not be crossed.

Do not enforce 16 significant figures because the private reference printed them. Do not accept a range that crosses the engineering decision boundary.

## Hash criteria

Hashes are high-risk for human transcription and should verify a clearly specified serialization.

Before entering a hash:

1. copy from the executed output, not from memory;
2. verify it is exactly 64 lowercase hexadecimal characters;
3. split it into eight groups of eight for manual comparison;
4. compare first eight, last eight, and full length;
5. check that the prompt/artifact fully specifies record fields, order, separators, encoding, and ordering;
6. ensure the solver computes it from state rather than using it as a pass literal.

Past entry errors included missing the letter `b` in a SHA. A syntactically valid 63-character or altered hash can silently poison a criterion.

## Numeric and tuple entry discipline

Past manual errors included:

- baseline checkpoint `400:4374` entered instead of `400:4355`;
- an extra recommended checkpoint `497:7299`;
- omitted hexadecimal characters;
- panel-letter mistakes;
- tuple terminology changing from “retirements” to “requirements.”

Use this procedure:

1. Maintain one canonical machine-readable results file.
2. Generate human entry text from it where possible.
3. Use a two-column comparison: canonical versus platform screenshot/transcription.
4. Validate counts: tuple arity, tuple count, checkpoint count, sweep row count.
5. Compare ordered sequences element by element.
6. After any edit, recheck all later text; manual cursor edits often shift or duplicate nearby content.

## Common linter messages and correct responses

### “Slightly broad / non-binary”

Ask whether the condition truly has more than one independent behavior. Split if yes. If the criterion is a unitary package/completeness check with content covered elsewhere, mark invalid only with precise sibling references.

### “Unobservable intent qualifier”

Replace purpose words such as “to improve,” “in order to,” or “tries to” with the observable state or output deviation.

### “Criterion reverses intended meaning”

Read the criterion under `if true, apply this weight`. Fix polarity words such as `derives/deviates`, `includes/omits`, `matches/differs`.

### “Prohibition criteria missing”

Either:

- rewrite the prompt positively if prohibition is unnecessary; or
- add one affirmative negative trap per forbidden behavior.

Do not mark valid prohibition feedback invalid merely to advance.

### Linter is wrong because of sibling coverage

Mark invalid with a concrete explanation, for example:

```text
This item intentionally checks only delivery of the five-file package.
Criteria 2, 8–14, and 20–32 separately check runnability and required
contents, so empty or stub files cannot satisfy the rubric as a whole.
```

### Apparent contradictions caused by missing namespaces

Heuristic linter output can change between rechecks. Do not alter a coherent criterion merely because an unchanged card receives a new warning. First namespace every exact object by the dimensions that distinguish it:

```text
revision + tuple + scenario + time scope + stage + population + metric
```

Common non-contradictions include:

- baseline/clean final p99 versus baseline/cut final p99;
- robust-feasible set/count/recommendation over all scenarios versus clean-only population;
- cycle-360 stage-7 checkpoint counts versus final-horizon summary counts;
- same-cycle visibility versus newborn-control deferral under an explicit stage snapshot;
- a positive live-simulation requirement versus a negative trap for embedded precomputed tables; and
- two different multi-dimension sweep/config selections that legitimately share every dimension but one (Task 06's energy-optimal and budget-constrained rows both targeted `active_cars=2, wait_timeout=50, power_budget=6` and differed only in `zoning`; that partial overlap is the correct answer for two distinct objectives, not a contradiction).

Use identical metric schemas across parallel scenario vectors unless a difference is intentional and explained. If the warning identifies a real mismatch, repair prompt, artifact, Ideal Flow, and rubric together. If it is false, record the exact namespaces and sibling ownership in the invalidation reason. Maintain a deterministic local contradiction matrix instead of repeatedly changing text to satisfy stochastic warnings.

### Platform row numbers can drift from your source document

On a platform where criteria can be added, deleted, and reordered through
its own UI, the displayed row number for a given piece of criterion text
can drift from this repo's sequential numbering — observed at least twice
on Task 06 as mismatched row numbers over identical underlying content.
Never give or follow a fix instruction keyed only to "row N." Always
identify the criterion by exact quoted text to find and exact text to
replace it with, and verify the edit landed by re-reading the changed
content back, not by trusting the row index.

## Final rubric audit

- [ ] 12–50 criteria.
- [ ] The chosen count follows coverage needs; no row exists merely to reach 50.
- [ ] Every weight is between -10 and +10.
- [ ] Every criterion begins with an observable verb.
- [ ] Every criterion is binary and self-contained.
- [ ] Hiding the prompt and attachment leaves every criterion independently gradeable from its own expected answer and the delivered files.
- [ ] Independent behaviors are split.
- [ ] Unitary answer objects remain intact.
- [ ] Every retained multi-field row explicitly names its unitary object and has no unrelated conclusion attached.
- [ ] No duplicate or positive/negative mirror.
- [ ] Every row has been compared with every sibling for duplicate loss.
- [ ] Every explicit prompt requirement is covered.
- [ ] Every deliverable has content criteria, not existence alone.
- [ ] Every prompt prohibition has its own affirmative trap.
- [ ] Negative traps describe active wrongness.
- [ ] Exact schemas/names are enforced only when stated in the prompt.
- [ ] Tolerances accept legitimate equivalents.
- [ ] Highest weights match the core task.
- [ ] Package/local/scaffolding points cannot carry a wrong integrated engine to 50%.
- [ ] A plausible-wrong survival-ceiling calculation is saved.
- [ ] Every integrated witness has one declared execution source, schema, index base, and causal owner.
- [ ] Downstream witness cascades do not duplicate-charge one upstream defect.
- [ ] All hashes, tuples, counts, and checkpoints match canonical output.
- [ ] A competent rival answer passes.
- [ ] A superficial literal-copy answer fails.
- [ ] The rubric title and status do not claim atomicity or certification before these checks pass.

Only after this audit should the human spend time entering the rubric into the platform.
