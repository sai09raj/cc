# Preflight and Validation Protocol

## Why this protocol exists

The expensive failure in Revision C was not caught by two local implementations because both encoded the same unstated author assumption. This protocol tests the visible specification itself, not merely code consistency.

## Validation layers

### Layer A — policy qualification

Confirm:

- genuine visual technical interpretation;
- real tool use;
- expert domain work;
- long-horizon execution;
- required output files;
- prompt and field limits;
- rubric count/weights;
- required model/run configuration.
- offline self-containment: no required browsing, remote API, download, or unstated external source;
- substantive tool necessity: the concrete deliverable cannot credibly be produced by hand.

### Layer B — artifact completeness

Confirm every decisive behavior is visible and readable at full resolution. Treat OCR text as support, not the only multimodal mechanism.

Run a visual-ablation test: extract the prose and table text while discarding arrows, geometry, containment, axes, plotted intervals, and spatial association. The task passes only if at least one required value or rule is then missing and must be recovered from the genuine visual. Do not neutralize the visual requirement by repeating all measured values in captions.

### Layer C — source-derived semantic contract

Write the full semantic contract without looking at reference code. This is the task’s executable constitution.

After writing it, run the perfect-semantics ablation: grant the hypothetical solver this entire contract and correct isolated implementations of its local rules. The architecture remains viable only if substantial temporal composition, implementation, search, verification, iteration, and engineering-decision work still remains. Semantic completeness proves fairness, not frontier difficulty.

### Layer D — reference implementation

Implement the semantic contract and reproduce results from a clean run.

### Layer E — independent reconstruction

Another reviewer reconstructs the contract from only the supplied prompt/artifact and compares it to Layer C before seeing the reference.

### Layer F — rival interpretations and mutants

Implement plausible alternatives and prove the visible source distinguishes them.

### Layer G — response/rubric fairness

Test competent alternative outputs against the rubric.

### Layer H — environment and packaging

Test the actual runtime, attachment, commands, and output workflow.

Also inspect how the artifact was produced. Prefer deterministic editable rendering code, verify it at full resolution and platform-preview scale, and confirm that no unintended footer, private path, draft note, malformed glyph, or opaque generation artifact remains.

**Metadata is a solution-leakage vector, not only a privacy concern.** A
visual or graphical artifact — a PDF, image, or any other rendered file —
can carry the actual answer inside data the model can read even when the
rendered picture looks clean: Producer/Creator/Author/XMP/tEXt fields,
embedded authoring paths, generation timestamps, and, for a PDF
specifically, vector drawing objects whose exact coordinates encode the
measurements the model is supposed to have to *measure* off the image. If
any of this survives, the model does not need to solve the task at all —
it reads the answer out of the file's metadata or vector layer — and the
task will not score below 50%, full stop, regardless of how sound the
rubric is. Strip all metadata (`set_metadata({})`, `del_xml_metadata()`,
blank any embedded generator-tool header comment) and rasterize every
diagram (flatten to an image XObject; zero vector drawing objects) before
shipping any artifact with a visual or graphical component, in PDF form or
any other form. Then verify at the raw-byte level, not by eye — grep the
file for Producer/Creator/Author/dates/tEXt/iTXt and confirm zero hits,
and confirm zero vector drawing objects remain — before it ever reaches
the platform.

## The source-to-code audit

Build a table like this for every material behavior:

| ID | Visible source | Exact rule | Reference code | Test | Rival interpretation | Source resolves rival? |
|---|---|---|---|---|---|---|
| S01 | Panel C mode edge | READ→WRITE when writes ≥ H or no reads | `select()` lines … | `test_enter_write` | Transition before/after age | yes/no |
| S02 | Panel C text | Mode persists across idle cycles | `select()` lines … | `test_idle_persistence` | Exit if no writes wait | **must be explicit** |

Then perform both directions:

### Source → code

Every normative visual statement maps to code and a test.

### Code → source

Every material branch, comparator, ordering key, metric increment, boundary, and serialization operation maps to a visible statement.

The second direction would have exposed Revision C’s hidden no-writes transition.

## State-machine completeness audit

For every state, enumerate:

- all explicit outgoing transitions;
- priority when multiple guards are true;
- action when no guard is true;
- whether state persists during idle;
- whether exceptional operations alter state;
- counter reset/increment conditions;
- reset/refresh/flush effects;
- same-cycle observation point.

Use a truth table over the guards. If the reference transitions on a guard combination absent from the artifact, the artifact is incomplete.

## Event-order completeness audit

For a cycle-accurate task, test at least:

- completion and admission on the same cycle;
- full queue and same-cycle dispatch;
- refresh becoming due during in-flight work;
- age threshold exactly equal to the limit;
- simultaneous aged candidates;
- selected operation with no bank-free candidate;
- row hit and older non-hit competition;
- bus turnaround at exact prior burst end;
- completion/refresh collision;
- final event and total-cycle definition.

Each test must state pre-edge state, ordered events, and post-edge state.

## Metric-definition audit

For every reported metric, define:

- population;
- unit;
- start/end events;
- inclusive/exclusive convention;
- aggregation;
- percentile method;
- rounding;
- tie handling;
- whether reset/idle/refresh cycles count.

Never assume that names such as “total cycles,” “latency,” “queue full,” or “idle” have universal meanings.

## Workload audit

Confirm:

- each phase’s operation, base, count, stride/pattern, and order;
- total request count;
- read/write counts;
- IDs and indexing origin;
- boundary between phases;
- deterministic generation;
- no altered request is used in the reported run.

Generate a compact digest and a few checkpoints from the actual workload.

## Search-space audit

Confirm:

- knob values;
- legality constraints;
- expected Cartesian size before constraints;
- exact legal row count;
- every legal configuration appears exactly once;
- no illegal configuration appears;
- target predicates;
- tie-break ordering;
- alternative objective definitions.

For Revision C, the claim was 272 legal configurations. The delivered sweep row count and uniqueness should be asserted programmatically.

## Serialization and hash audit

Specify and test:

- record fields and their exact order;
- numeric representation;
- boolean representation;
- record ordering;
- field separator;
- record separator;
- whitespace;
- encoding;
- trailing separator/newline rule;
- hash algorithm and case.

Publish one or two example records in the artifact if the hash is graded. A hash without complete serialization rules is not a fair criterion.

## Oracle independence: the three-proof rule

Use three different forms of evidence:

1. **Semantic proof:** a prose/table contract derived from visible sources.
2. **Executable proof:** a reference implementation.
3. **Adversarial proof:** a rival or mutant implementation that disagrees under one plausible interpretation.

Two implementations written by the same author from the same unstated assumption count as one proof, not two.

## Required rival interpretations

At minimum, deliberately vary:

- event order;
- `>` versus `>=` thresholds;
- state persistence versus implicit fallback;
- selected-operation fallback versus no fallback;
- latency endpoint;
- bus reservation ordering;
- queue occupancy including/excluding dispatched work;
- refresh boundary;
- percentile convention;
- serialization order;
- tie-break order.

For each variant, record whether the artifact unambiguously rejects it. If not, revise the artifact.

## Mutation suite

Create intentional wrong implementations that reflect realistic model mistakes. Tests should kill them.

Example mutation families:

- use stale revision value;
- swap two same-cycle stages;
- update policy state on an override path;
- allow fallback to the other operation;
- count an in-flight request as queued;
- close a row after every request;
- reorder bus reservations by service-ready time;
- omit a reset/flush effect;
- hard-code a golden result;
- sweep only a selected subset.

Mutation testing validates checks. Rival-interpretation testing validates specification. Both are required.

## Activation-coverage audit

A rule can be visible, implemented, and tested locally yet never affect the certified production workload. For every fault window, timeout, retry path, expiry, admission guard, and exceptional stage:

1. identify at least one ordinary configuration/scenario where it activates;
2. record the first activation cycle and affected object;
3. prove that disabling or shifting it changes a delivered metric, checkpoint, trace, or selection;
4. check that no earlier launch block, empty queue, or unrelated guard shields it; and
5. retain a concrete witness in the validation record.

Task 04's first Revision B cut-drop window was shielded by an earlier launch block. Independent audit moved it to `[195,220)` before the pilot. A printed fault interval is not coverage evidence.

## Golden-result verification

1. Delete generated outputs.
2. Run from a clean environment.
3. Recreate workload, baseline, sweep, recommendation, report, and hash.
4. Confirm deterministic byte-for-byte reproduction where promised.
5. Recalculate key results with a second method.
6. Check every value copied into Ideal Flow, rubric, and entry guide.
7. Verify list counts and SHA lengths.
8. Record command, runtime version, and timestamp.

## Environment preflight

### Minimal test first

Before building the task around a compiler/simulator:

1. run `--version`;
2. compile/run a minimal example;
3. verify all runtime DLLs/libraries;
4. execute a tiny test through the same wrapper the model will use;
5. confirm output paths and permissions.

The previous `ivl.exe`/`libgcc_s_seh-1.dll` error is the canonical warning. Reinstalling arbitrary binaries after task entry is not a robust plan. Prefer a verified container, bundled runtime, or official package source.

### Reproducibility record

Store:

- operating system/container image;
- tool versions;
- installation source;
- exact commands;
- expected minimal output;
- fallback tool if permitted.

## Platform transcription audit

### Canonical-source rule

There must be one canonical local file for each platform field. The UI is a copy target, not an editing workspace.

### Compare these character classes explicitly

- digits that differ by one (`4355`/`4374`);
- panel letters (`E`/`R`/`F`);
- negative polarity words (`deviates`/`derives`);
- hexadecimal `b`, `d`, `0`, and `8`;
- braces/brackets/parentheses;
- commas and tuple order;
- Unicode arrows versus ASCII;
- filenames and extensions.

### Checks

- prompt word count;
- each Ideal Flow character count;
- criterion count;
- every weight in range;
- exact attachment name;
- every hash length 64;
- every list/tuple/checkpoint count;
- no truncated first criterion;
- no stale draft text after edits.

## Pilot-run audit

Do not look only at score. Extract:

- semantic choices;
- implementation approach;
- tool path;
- values and hashes;
- what was technically wrong;
- what was omitted;
- whether the response found ambiguity;
- whether a strong rival answer would be accepted.

### Pilot disposition

| Observation | Action |
|---|---|
| Solves core task | Redesign architecture. |
| Fails only formatting/reporting | Simplify reporting and increase real technical depth. |
| Cannot run tool | Fix environment. |
| Produces coherent rival values | Audit specification before grading. |
| Fails core semantics despite complete spec | Proceed to additional runs. |

The last row is necessary but not sufficient. A semantic failure can be scored, but do not infer durable difficulty from it alone. Confirm through the semantic-grant test that the task would remain demanding even if a stronger run recovered those semantics correctly.

### Pilot implementation replay and first-divergence workflow

Do not diagnose a pilot from its final prose alone:

1. preserve the raw trajectory before any rerun;
2. reconstruct the final delivered implementation by replaying all file writes and edits in order;
3. run it with the frozen task command in an isolated directory;
4. normalize generated files without changing semantics;
5. compare its ordinary production trace with the reference;
6. locate the earliest differing event, including zero-based and one-based ordinal where relevant;
7. map the difference to a visible rule, state variable, and rubric owner;
8. compare the same location across other runs only after the first pilot is diagnosed; and
9. save the reconstructed source, command, diff, and causal conclusion.

The earliest divergence is usually more actionable than a dozen downstream summary differences. In Task 04 Revision E, both stronger runs first diverged at one-based trace row 390, cycle 656, because they maintained E-run arbitration only on X rather than independently on e0/e1/X/e4.

### Counterfactual rubric replay

Score the reconstructed pilot under the frozen rubric and group earned points into package, local, integrated, and decision buckets. Also score one deliberately plausible wrong mutant before the pilot. If either wrong integrated implementation can retain 50%, repair the prospective rubric topology rather than adding cosmetic penalties after the fact.

One upstream defect may cause many later mismatches. Record both criterion failures and shared causal ownership so the rubric does not accidentally charge the same behavior repeatedly.

## Multi-run convergence audit

Create a comparison table with one row per semantic/result feature and one column per run. Flag identical non-reference values.

Three independent Opus runs produced the same alternate baseline, recommendation, and hashes in Revision C. The probability that this was random implementation noise was negligible. Their convergence should have immediately triggered a specification audit.

## Final pre-launch gate

- [ ] Official-policy qualification passes.
- [ ] Artifact is genuinely visual and readable.
- [ ] Prompt/artifact are sufficient.
- [ ] Semantic contract is complete.
- [ ] Perfect-semantics ablation passes; the task does not collapse after all local rules are granted.
- [ ] Every reference branch maps to visible source.
- [ ] Independent reviewer reconstructed the same contract.
- [ ] Rival interpretations are visibly resolved.
- [ ] Mutation suite catches intended defects.
- [ ] Every fault/stress mechanism activates in a certified ordinary run and has a retained witness.
- [ ] Golden results reproduce cleanly.
- [ ] Runtime works in the expected environment.
- [ ] Every artifact with a visual/graphical component (PDF or otherwise) has had all metadata stripped and every diagram rasterized, verified at the raw-byte level (zero Producer/Creator/Author/date/tEXt hits, zero vector drawing objects) — not verified by eye alone.
- [ ] Every rubric criterion body is 301 characters or fewer, and the post-drafting atomicity/self-containment recheck was run over every criterion.
- [ ] Prompt, Ideal Flow, rubric, and artifact terminology match.
- [ ] Platform text matches canonical files.
- [ ] Pilot failure is genuine and fair.
- [ ] Pilot implementation was reconstructed, replayed, and first-divergence analyzed.
- [ ] Plausible-wrong survival ceiling is below 50%.
- [ ] Exact score/trajectory/model evidence has an archive location.

If one item fails, do not launch the full run set.
