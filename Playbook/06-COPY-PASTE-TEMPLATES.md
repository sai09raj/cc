# Copy/Paste Templates for a New Magnetic Rainstorm Task

## 1. Agent handoff instruction

```text
You are helping author and validate a Magnetic Rainstorm frontier-model task.
First read the authoritative local PDFs (guidelines.pdf, rubric.pdf, and
common-errors.pdf), then PROJECT-TASK-HANDBOOK.md, then the entire playbook
folder. Begin with 00-START-HERE-EVERY-FUTURE-TASK.md, which routes the other
chapters but does not replace them. Treat the PDFs as authority, the handbook
as a source-cited consolidation, and the playbook as empirical procedure.

Do not optimize merely for a below-50 score. The task must be complete and
fair under the visible prompt/artifact, require genuine visual interpretation,
real tools, expert knowledge, long-horizon execution, and concrete output
files. Before model runs, perform a bidirectional source↔code audit, an
independent artifact-only semantic reconstruction, rival-interpretation tests,
mutation tests, runtime preflight, and a competent-rival rubric test.

Assume the required frontier model, including Opus 4.8 Max, reconstructs every
visible local semantic correctly. Run the perfect-semantics ablation and reject
any concept whose difficulty collapses once the rules are understood. Never
hide or blur semantics; create difficulty through integrated execution,
temporal composition, search, verification, iteration, and engineering choice.

If multiple strong model runs converge on the same non-reference answer, pause
grading and audit the specification. Never treat private oracle intent as a
visible task rule. Never tighten the rubric after seeing responses to force a
lower score. Record uncertainties and stop rather than inventing policy or
domain semantics.
```

## 2. Task architecture canvas

```text
TASK WORKING TITLE:
DOMAIN / SUBDOMAIN:
AUTHOR EXPERTISE BASIS:
REAL ENGINEERING DECISION:

FOUR PILLARS
1. Genuine visual interpretation:
   - exact visual elements:
   - measured/inferred facts:
   - why OCR alone is insufficient:
2. Iterative tool use:
   - tools/runtime:
   - inspect→build→run→diagnose→revise→rerun loop:
3. Expert knowledge:
   - domain invariants/judgments:
4. Long horizon:
   - dependent stages:
   - generated artifacts:

DIFFICULTY STACK
- distributed specification:
- stateful interaction:
- generated workload/data:
- search/design space:
- coupled targets:
- tie-break:
- cross-file consistency:
- causal synthesis:

POST-SEMANTICS DIFFICULTY
- work remaining after every local rule is granted:
- interacting persistent state domains:
- nonlocal/long-horizon consequences:
- implementation/debugging burden:
- coupled/non-monotonic search or optimization:
- independent verification and reconciliation:
- why at least three of these layers are unavoidable:

ANTI-SHORTCUTS
- why a clean rewrite does not trivialize it:
- why one worked example does not reveal all cases:
- author-owned checker/invariants:
- plausible mutants:
- legitimate alternative outputs:

HARD STOP QUESTIONS
- Can prompt+artifact determine one decision-relevant answer class? yes/no
- Does every private oracle rule have a visible source? yes/no
- If given a flawless semantic summary, is substantial integrated implementation/search/debugging/decision work still required? yes/no
- Does any expected failure depend mainly on overlooking or misreading one rule? yes/no
- Can the toolchain run in the target environment? yes/no
- Would a competent rival answer pass? yes/no
```

## 2A. Perfect-semantics ablation

```text
TASK / REVISION:
CURRENT REQUIRED FRONTIER MODEL / EFFORT:

GRANT THE HYPOTHETICAL SOLVER:
- every local rule and measured constant:
- every boundary, priority, tie-break, and reset rule:
- correct local implementation of each rule in isolation:

WORK THAT STILL REMAINS:
- integrated temporal/cross-component composition:
- workload scale and execution:
- search/optimization and coupled decision:
- debugging/iteration:
- independent verification:
- cross-file reconciliation:
- causal engineering synthesis:

Could a clean small rewrite now solve the task? yes/no
Could direct enumeration without a correct interacting model solve it? yes/no
Could copied headline literals retain >=50%? yes/no
Are at least three post-semantics difficulty layers unavoidable? yes/no
Does any planned low score depend mainly on semantic omission/misreading? yes/no

DISPOSITION: accept architecture / redesign
RATIONALE:
REVIEWER / DATE:
```

## 3. Artifact manifest

```text
ARTIFACT MANIFEST

Exact filename:
Type/dimensions/pages:
Purpose:
Normative panels/regions:
Genuine visual content:
Values that must be measured rather than OCR-read:
Revision notes and exact override targets:
Legends/axes/units:
Minimum readable zoom/resolution:
Legal/supplyability status:
Prompt filename matches exactly: yes/no
Opened after upload: yes/no
```

## 4. Visible semantic contract

| ID | Source location | Exact rule | Priority/order | Boundary/tie rule | Idle/reset/exception behavior | Reference code | Directed test |
|---|---|---|---|---|---|---|---|
| S01 |  |  |  |  |  |  |  |

Add a row for every state transition, event stage, metric, workload rule, legal-range rule, selection rule, and serialization rule.

## 5. Code-to-source reverse audit

| Code branch/operation | Material effect | Visible source | If no source, resolution |
|---|---|---|---|
| `if ...` |  |  | add to artifact / remove from oracle |

No blank visible-source cell is allowed at launch.

## 6. Rival-interpretation register

| Topic | Author interpretation | Plausible rival | Output difference | Exact visible sentence that resolves it | Status |
|---|---|---|---|---|---|
| Idle mode behavior |  |  |  |  | unresolved/resolved |
| Threshold equality |  |  |  |  |  |
| Same-cycle order |  |  |  |  |  |
| Metric endpoint |  |  |  |  |  |
| Serialization |  |  |  |  |  |

## 7. Ideal Flow templates

### Ideal Flow: Analyze

```text
Inventory [artifact] and treat [named panels/regions] as normative. Measure
[visual quantities] against [axes/geometry], resolve [revision note], and
reconstruct [state machine/topology/data model]. Derive [address/timing/order/
selection] rules from the artifact. Explicitly determine [boundary and idle
semantics] rather than assuming a conventional implementation. Verify the
generated [workload/data set] contains [counts/properties].
```

### Ideal Flow: Execute and Generate

```text
Implement [deterministic model/checker] in [tool/language]. Generate [input]
algorithmically, run [baseline/directed/mutation/randomized] checks, and execute
all [N] legal configurations. Select qualifying results using [targets and
tie-break]. Produce [exact files], with every reported value derived from
execution state. Record [runtime/version/commands] and verify [row counts,
hashes, invariants, cross-file consistency].
```

### Ideal Flow: Synthesize

```text
Explain the baseline bottleneck and the interaction among [knobs/rules]. Show
why [obvious/local/one-knob] approaches fail using observed results. Justify the
recommendation against [targets/tie-break], state at least [N] worsening metrics,
compare [alternative objectives], and identify limits or workload dependence.
Tie every claim to executed evidence rather than a precomputed literal.
```

After drafting, check each field is 5–3,000 characters and shares exact terminology with the prompt/artifact.

## 8. Prompt blueprint

```text
You are [real technical role] working from the attached [exact filename]. Treat
[specified regions] as the complete specification. Read/measure [genuine visual
elements], resolve [revision mechanism], and reconstruct [system]. Derive
[parameters/order/behavior] from the artifact.

Implement [executable artifact] and [verification/search task]. Run [complete
workload/test set/design space]. First [baseline], then [decision objective and
tie-break]. Explain [causal synthesis requirement].

Produce exactly these files:
1. [filename] — [runnability and contents].
2. [filename] — [required fields].
...

Run the files you deliver and report observed results. [Necessary positive
integrity requirements]. [Only technically necessary prohibitions, each of
which will receive a negative rubric trap].
```

Prompt checks:

- 2–500 words;
- exact attachment filename;
- output files required;
- no hidden schema;
- no unneeded prohibitions;
- no decisive golden leakage;
- every requested field defined;
- fully aligned with artifact and Ideal Flow.

## 9. Deliverable contract

| File | Required format | Required contents | Runtime behavior | Exactness required | Accepted equivalents | Rubric IDs |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## 10. Reference-run record

```text
REFERENCE RUN
Date/time:
Environment/container:
Tool versions:
Exact commands:
Clean-output directory:
Input digest:
Workload count/digest:
Search rows expected/observed:
Baseline summary:
Recommended summary:
Alternative objectives:
Checkpoints:
Serialization examples:
Hashes:
Assertions passed:
Mutation results:
Independent reconstruction result:
Unresolved differences:
```

## 11. Rubric traceability matrix

| Requirement ID | Prompt text | Artifact source | Ideal Flow | Positive criterion | Negative trap if prohibited | Reference evidence |
|---|---|---|---|---|---|---|
| R01 |  |  |  |  |  |  |

Every prompt requirement must have a positive criterion. Every explicit prohibition must have a separate negative trap.

## 12. Positive criterion templates

```text
Delivers [file] containing [required content].
Runs [file] successfully with [documented command/interface].
Reports [metric] as [value/range/unit].
Uses [visible rule] when [condition].
Applies the ordered stages [order].
Identifies [configuration/conclusion] under [target/tie-break].
Includes exactly [N] unique rows/records corresponding to [complete set].
Explains [causal relationship] using the observed changes [A→B and C→D].
```

## 13. Negative trap templates

```text
Embeds [golden metrics/hash] as literal pass conditions in [solver file].
Runs the reported result on data that deviates from [visible source] in [specific dimensions].
Presents fewer than [N] legal configurations as an exhaustive sweep.
Uses [specific stale/forbidden value or behavior].
Updates [state] when [explicitly forbidden event] occurs.
Recommends a configuration absent from its delivered sweep.
```

Avoid `fails to`, `does not`, intent phrases, and positive/negative mirrors.

## 14. Linter-response record

```text
Criterion ID:
Linter message:
Is the message substantively correct? yes/no
If yes, exact rewrite/split:
If no, precise reason with sibling criterion IDs:
Polarity check (`if true, apply weight`):
Recheck result:
```

## 15. Platform transcription verification

```text
FIELD:
Canonical local source:
Platform screenshot/export:
Length expected/observed:
Numbers compared:
Hashes 64 hex chars: yes/no
Tuples/counts compared:
Panel/file names compared:
Polarity words compared:
Reviewer/date:
Status:
```

## 16. Model-run record

| Field | Value |
|---|---|
| Model / reasoning |  |
| Run/trajectory filename |  |
| Start/end/timeout |  |
| Tool calls and environment changes |  |
| Files delivered |  |
| Reconstructed semantics |  |
| Key results/hashes |  |
| Raw platform score |  |
| Fair generous score |  |
| Core technical failures |  |
| Mere omissions |  |
| Possible ambiguity |  |
| Shared rival result with other runs |  |
| Preferred? Why? |  |

## 17. Multi-run convergence matrix

| Feature | Reference | Run 1 | Run 2 | Run 3 | Consensus conflict? | Audit result |
|---|---|---|---|---|---|---|
| Measured constants |  |  |  |  |  |  |
| Event order |  |  |  |  |  |  |
| State transitions |  |  |  |  |  |  |
| Baseline |  |  |  |  |  |  |
| Recommendation |  |  |  |  |  |  |
| Hashes |  |  |  |  |  |  |

## 18. Final handoff summary

```text
TASK STATUS: concept / preflight / pilot / rerun / submission-ready / blocked

Authoritative sources read:
Artifact and prompt version:
Reference version:
Semantic-contract audit:
Independent reconstruction:
Rival/mutation tests:
Environment preflight:
Rubric/linter status:
Run distribution:
Generous-score distribution:
Convergence audit:
Known ambiguity:
Required next action:

Submission-ready means: complete visible specification, reproducible reference,
fair rubric, runnable environment, and required below-50 preferred runs under a
generous interpretation. A low score alone is not sufficient.
```

## 19. Score-topology and plausible-wrong survival audit

```text
Revision:
Positive-weight total:
50% threshold:

| Bucket | Criterion IDs | Positive weight | Plausible wrong engine earns | Why |
| Package/existence/presentation | | | | |
| Local parsing/rules/scaffolding | | | | |
| Integrated production execution | | | | |
| Final decision/causal reconciliation | | | | |

Counterfactual answer A — empty/superficial package:
Earned / total / percent:

Counterfactual answer B1 — perfect local semantics, incomplete/wrong global execution:
Composition/search/verification failure:
Earned / total / percent:

Counterfactual answer B2 — runnable, locally plausible, globally wrong engine:
Implementation shortcut:
Earned / total / percent:

Counterfactual answer C — correct engine, equivalent organization/wording:
Earned / total / percent:

Can answer B1 or B2 retain >=50%? yes/no
If yes, prospective repair before pilot:
Reviewer/date:
```

Do not use the average of multiple model scores. Every required preferred run must individually remain below 50.

## 20. Production-witness manifest

```text
Revision:
Execution command:
Scenario/configuration:
Uninterrupted run source:
Trace/checkpoint schema:
Index base: zero/one

| Criterion | Ordinal/cycle | Exact record | Semantic rule witnessed | Component/epoch | Mutant or pilot implementation killed | Causal owner distinct? |
|---|---:|---|---|---|---|---|
| | | | | | | |

Early/middle/late coverage:
Event/component diversity:
Cross-file reconciliation:
Mechanical extraction command/script:
Checksum of source trace:
Duplicate-cascade review:
```

Each witness must come from ordinary production execution. Do not substitute isolated fixtures or attach an unrelated metric to a rule merely to increase its weight.

## 21. Pilot forensics and first-divergence record

```text
Frozen revision/hash:
Model/effort:
Trajectory path:
Exact score evidence:
Delivered files:

Reconstruction method:
Reconstructed implementation path/hash:
Replay command/environment:
Replay output matches delivered output: yes/no

Reference trace:
Pilot trace:
First divergent zero-based event:
First divergent one-based data row:
Cycle/event/component:
Reference record:
Pilot record:
Visible semantic rule:
Pilot implementation choice:
Shared by another run: unknown/yes/no

Package points earned:
Local points earned:
Integrated points earned:
Decision points earned:
Raw score / generous score:

Failure class: technical / ambiguous / environmental / cosmetic / rubric-created
Disposition: proceed / repair / redesign / rerun
```

## 22. Prospective revision-delta manifest

```text
Old revision:
New revision:
Reason for revision:
Old runs excluded from new acceptance: yes/no

New unique attachment filename:
Artifact semantic changes:
Prompt exact replacements:
Ideal Flow fields changed:
Ideal Flow fields unchanged:
Rubric text IDs changed:
Rubric weight IDs changed:
Rubric IDs/weights explicitly unchanged:
Reference-code changes:
Golden-output changes:

Clean regeneration command:
Byte/count/checksum comparison:
Independent re-audit:
Platform copy order:
Changed-only handoff file:
New pilot required: yes/no
```

Weights are not sacred before a pilot. Fix an identified topology defect prospectively, then freeze the new revision. Never alter old grading to force completed runs below 50.

## 23. Linter namespace and contradiction matrix

```text
| Criterion A | Criterion B | Revision | Tuple/config | Scenario | Time scope/stage | Population | Metric | True contradiction? | Resolution/reason |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |

Parallel scenario records use identical metric schemas: yes/no
Robust population distinguished from clean-only population: yes/no
Checkpoint scope distinguished from final summary: yes/no
Same-cycle snapshot/newborn eligibility explicit: yes/no
Live-simulation positive and precomputed-table trap ownership documented: yes/no
```

If a warning is false, preserve the frozen semantics and record the exact namespace reason. If it is true, repair every affected source together rather than patching only the rubric sentence.

## 24. Final run-evidence archive

```text
Revision and frozen file hashes:
Artifact filename/hash:
Prompt/Ideal Flow/rubric hashes:
Reference runtime and command:

| Run | Model/effort | Exact score | Generous score | Trajectory | Score screenshot/export | Grading sheet | Preferred? |
|---|---|---:|---:|---|---|---|---|
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |

Every required preferred run individually below50: yes/no
Convergence/ambiguity audit path:
Known evidence gaps:
Archive reviewer/date:
```
