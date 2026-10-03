# Task 09 — TYPECHAIN-9

Current active candidate: **TYPECHAIN-9**, in `reference/`, `design/`,
`platform/`, `artifact/`. State: SCORE-TOPOLOGY GATE PASSED (S08),
ENGINE AND INDEPENDENT CHECKER VERIFIED END TO END, FULL PLATFORM
PACKAGE COMPLETE (rubric, prompt, ideal-flow, metadata-stripped PDF
artifact). NOT YET pilot-tested.

## Why this task exists

LEDGER-8 was shelved after two real pilots scored 98%/100% against the
(spec-bug-fixed) packet: its facts were largely independent, so a
careful model could get every fact right in isolation with nothing to
trip over. TYPECHAIN-9 was built around the one property that fixes
this: Hindley-Milner type inference threads **one global substitution**
through the whole program, so a wrong generalization decision at one
binding corrupts the substitution used for everything built on top of
it — the same "early mistake corrupts most of the rest" property that
made QUORUM-7 real, in a genuinely new domain (programming languages/
type systems, not accounting or distributed systems).

User-set targets going in: real pilots under 50%, every tested
single-bug mutant under 33%.

## The program had to be redesigned once to actually cascade

The first draft (23 bindings, closure_pair_x/closure_pair_n as the only
two bindings exercising the generalization-exclusion rule) diverged on
only 2/23 bindings (8.7%) under the primary mutant — the exact same
failure LEDGER-8 had, caught before it went any further this time by
testing it empirically up front (S08's gate), not after a real pilot.

Rebuilt around a 10-stage chained "capturing factory" pattern
(`mk1`/`r1` through `mk10`/`r10`), where each stage's own result feeds
the next stage's input. Verified via the real mutant audit: dropping
S02's generalization-exclusion rule now diverges on **23 of 27
bindings (85%)**.

## Score-topology audit (S08 gate, run before the rubric was written)

`reference/score_counterfactual.py`, scored against the actual executed
engine, not estimated:

| Mutant | Score |
|---|---|
| canonical (sanity) | 100.0% |
| drops S02's generalization-exclusion rule (primary) | **17.2%** |
| drops only the alias-eligibility clause (secondary) | 76.2% |

The primary mutant clears the <33% target with real margin. The
secondary mutant was tested honestly and excluded from the scored
rubric design rationale as a non-discriminating scenario for this
program's specific structure — every binding it could affect (only
`alias_id`) happens to resolve to a value that doesn't change whether
or not it's generalized correctly. Two other candidate mutants (ignoring
S02 entirely and using standard ML's value restriction instead;
omitting the occurs-check) were also tested and confirmed to have **zero
effect on this program's certificate** — the former because every
literal/pair/list binding in the program happens to already resolve
concrete regardless of generalization eligibility, the latter because
the program is fully well-typed and never exercises the occurs-check
naturally. Both are still tested as the two REQUIRED ADVERSARIAL
MUTATIONS against the independent checker (S05/S10), via standalone
crafted scenarios, not via the main program — this is the same
distinction QUORUM-7 and LEDGER-8 both used (two different verification
mechanisms: score-topology mutants against the main trace/program, and
required adversarial mutations against the independent verifier/checker
on crafted bad inputs).

## Independent checker verified end to end

`reference/checker.py` — a structurally different bidirectional type
checker (not a second inferencer), with its own over-generalization
detector: double-instantiates a claimed scheme and checks whether two
claimed-independent quantified variables are forced to coincide during
checking.

- **Accepts the true 27-binding certificate in full** (all 27 bindings
  accept, confirmed by execution).
- **Rejects a certificate produced by the primary mutant**, right at
  the first corrupted binding (`mk1`, via the over-generalization
  check), cascading the rejection forward through every later binding
  that depends on it (`unbound variable mk1`, `unbound variable r1`,
  ...) — exactly mirroring how the corruption itself cascades on the
  engine side.
- **Rejects the self-application adversarial case** (`(fun x (x x))`,
  requiring an infinite type) when the occurs-check is correctly
  implemented; confirmed the engine without the occurs-check hits
  unbounded recursion trying to resolve the resulting cyclic
  substitution rather than producing a clean wrong answer — also a
  valid, detectable failure mode.

## A real bug found and fixed while building the certificate renderer

The first draft's `forall` quantifier list was ordered by each type
variable's internal name, not by first-occurrence position in the
printed type — e.g. `compose` printed `forall t2 t0 t1 . ...` instead
of the S06-required `forall t0 t1 t2 . ...`. Caught by actually running
the engine and reading the output, not by inspection, fixed before any
rubric text referenced it.

## Deliverables so far

- `reference/typecheck_engine.py` — primary Algorithm-W-style inference
  engine, S01-S03/S06, with mutant hooks for the score-topology audit.
- `reference/program.ty` — the fixed 27-binding program, a genuine
  dependency chain (most bindings consume 2-4 earlier ones).
- `reference/checker.py` — independent bidirectional checker (S05),
  verified to accept the true certificate and reject both required
  adversarial mutations.
- `reference/score_counterfactual.py` — score-topology audit, verified
  primary mutant at 17.2%, well under the 33% target.
- `design/architecture-attack.md`, `design/semantic-contract.md`.
- `platform/rubric.md` — 37 criteria, positive total 122, negative
  total -12 (one independence-prohibition negative learned proactively
  from the LEDGER-8 postmortem instead of waiting for a platform
  linter, one trap), re-verified (301-char cap, ≤10 weight cap,
  atomicity, positive total matches score_counterfactual.py exactly).
  Re-audited against the full `03-RUBRIC-AND-LINTER-GUIDE.md` after a
  real external task scored "2" (Fail, 20%+ moderate rubric errors) for
  bundling independently-reachable facts into one row plus an unstated
  term. Found one real instance of exactly that pattern here: the
  original package criterion bundled reproducible-execution,
  tool-version/environment recording, and six-file delivery into one
  AND-joined row, and "six named products" wasn't self-contained (the
  six weren't named in the criterion itself). Split into three atomic
  +1 rows (criteria 1-3); package weight unchanged at 3, criteria count
  35→37. Also ran the guide's 4-bucket score-topology survival-ceiling
  check (not previously done explicitly, only the single 17.2% mutant
  score): package/existence=3, local-rule=10, integrated execution=91,
  decision/reconciliation=18; worst case (perfect local-rule knowledge,
  wrong global execution) survives at roughly 36%, under the 50%
  reject threshold, because this program's cascading structure corrupts
  bucket 3 regardless of which specific bug caused the wrong execution.
  Everything else in the guide's 30-item final audit checked out:
  both explicit prompt prohibitions have dedicated traps, the
  generalization-rule prohibition is correctly left untrapped (already
  documented redundancy reasoning), no MECE/polarity/hash-discipline
  violations found.
- `platform/prompt.md` — 468 words, zero internal hyphens (Playbook
  mistake #64).
- `platform/ideal-flow.md` — Analyze/Execute & Generate/Synthesize.
- `artifact/typechain9_v1.pdf` — 6 pages (4 rasterized figures: grammar,
  type system, generalization-rule flowchart, the fixed program's
  source text; 2 text spec pages). Verified byte-level: empty Info
  dict, null XMP, zero vector drawing objects on every figure page, no
  tool/path signatures, no leaked computed values (no binding's type,
  no hash) anywhere in extracted text — only the stated grammar, rules,
  and the program's own source as input. Filename carries a revision
  suffix from the first draft (Playbook mistake #46).

## Remaining

- Real pilot run(s) (task #27-equivalent for this task) — the actual
  test of whether the redesigned cascade holds up against a real
  frontier model, not just synthetic mutants.
