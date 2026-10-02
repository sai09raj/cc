# TYPECHAIN-9 rubric

Positive total **122**; two negative criteria, **-4** (independence
prohibition) and **-8** (negative trap). **35 criteria** (within the
platform's 12-50 range). Every weight is capped at 10. Every criterion
body is 301 characters or fewer. Criteria are binary. Accept equivalent
correct work throughout: equivalent languages, source organization,
output schemas, and type-printing notation that is unambiguously
equivalent to this packet's stated grammar.

Score-topology note: this task was built specifically to avoid
LEDGER-8's failure (a well-specified task a frontier model solves too
reliably because its facts were largely independent). The task's
single global substitution means a dropped generalization-exclusion
rule corrupts most of the program, not just the one binding where the
bug lives. Verified by actually running the real mutant (not
estimated): dropping S02's exclusion rule scores **17.2%** against this
exact rubric's weights -- well under the 33% target. See `STATUS.md`
for the full score-topology audit, including a second, weaker mutant
(76.2%) that was tested and honestly excluded as a non-discriminating
scenario for this program's specific structure, rather than hidden.

Redundancy note: no dedicated negative criterion restates "drops S02's
exclusion rule" or "drops the occurs-check" as their own prohibitions,
because both violations necessarily corrupt an already-tested value
(the per-binding certificate facts below, and the independent-checker
rejection criteria respectively) -- adding one would score the same
root-cause bug twice. The one dedicated negative below (independence)
is the one violation that can hide behind a correct-looking result, the
same distinction LEDGER-8's own rubric needed a real pilot to learn.

### Package (1, weight 3)

| # | Wt | Criterion |
| --- | --- | --- |
| 1 | +3 | Executes the delivered offline inference engine and checker with a documented, reproducible command, records tool versions in a declared offline, stdlib-only environment, and delivers all six named products as files. |

### Local semantics/rules (2, weight 10)

| # | Wt | Criterion |
| --- | --- | --- |
| 2 | +10 | At every `let`, generalizes only when the bound expression is syntactically a lambda or a bare reference to an already-polymorphic binding, excluding from quantification any type variable still free in the enclosing environment -- never the standard ML value restriction. |

### Certified program facts (3-29, weight 81)

Each binding's final type, exactly as this packet's S06 serialization
format requires (fixed field order, full parenthesization, per-binding
`t0 t1 ...` numbering in first-occurrence order, `forall` prefix only
when the binding is both generalization-eligible and has at least one
quantified variable remaining).

| # | Wt | Criterion |
| --- | --- | --- |
| 3 | +3 | Reports `five` as `Int` (exact). |
| 4 | +3 | Reports `mk1` as `forall t0 . (t0->(t0*t0))` (exact). |
| 5 | +3 | Reports `r1` as `Int` (exact). |
| 6 | +3 | Reports `mk2` as `forall t0 . (t0->(t0*t0))` (exact). |
| 7 | +3 | Reports `r2` as `Int` (exact). |
| 8 | +3 | Reports `mk3` as `forall t0 . (t0->List(t0))` (exact). |
| 9 | +3 | Reports `r3` as `Int` (exact). |
| 10 | +3 | Reports `mk4` as `forall t0 . (t0->(t0*t0))` (exact). |
| 11 | +3 | Reports `r4` as `Int` (exact). |
| 12 | +3 | Reports `mk5` as `forall t0 . (t0->(t0*t0))` (exact). |
| 13 | +3 | Reports `r5` as `Int` (exact). |
| 14 | +3 | Reports `mk6` as `forall t0 . (t0->List(t0))` (exact). |
| 15 | +3 | Reports `r6` as `Int` (exact). |
| 16 | +3 | Reports `mk7` as `forall t0 . (t0->(t0*t0))` (exact). |
| 17 | +3 | Reports `r7` as `Int` (exact). |
| 18 | +3 | Reports `mk8` as `forall t0 . (t0->(t0*t0))` (exact). |
| 19 | +3 | Reports `r8` as `Int` (exact). |
| 20 | +3 | Reports `mk9` as `forall t0 . (t0->List(t0))` (exact). |
| 21 | +3 | Reports `r9` as `Int` (exact). |
| 22 | +3 | Reports `mk10` as `forall t0 . (t0->(t0*t0))` (exact). |
| 23 | +3 | Reports `r10` as `Int` (exact). |
| 24 | +3 | Reports `wrap_in_list` as `forall t0 . (t0->List(t0))` (exact). |
| 25 | +3 | Reports `list_of_r10` as `List(Int)` (exact). |
| 26 | +3 | Reports `id` as `forall t0 . (t0->t0)` (exact). |
| 27 | +3 | Reports `use_id_on_r10` as `Int` (exact). |
| 28 | +3 | Reports `alias_id` as `forall t0 . (t0->t0)` (exact). |
| 29 | +3 | Reports `use_alias_id_on_pair` as `(Int*Int)` (exact). |

### Certification and independent verification (30-33, weight 28)

| # | Wt | Criterion |
| --- | --- | --- |
| 30 | +10 | Matches the first 16 hex characters of the trace-integrity hash (algorithm in the packet) to `bb271eaf3a8043e6`. |
| 31 | +6 | The independently-coded checker rejects the self-application adversarial mutation (`(fun x (x x))`, requiring an infinite/cyclic type) while still accepting the true program. |
| 32 | +6 | The independently-coded checker rejects an over-generalized claimed scheme (a binding that wrongly quantifies a type variable still free in its enclosing environment) while still accepting the true program's own correct schemes. |
| 33 | +6 | Explains in the memo, citing the actual claimed types for `mk1` through `mk10`, why each nested-let `keep` binding may only be generalized over its own argument's type variable, never over the outer parameter's. |

### Negative criteria (34-35)

| # | Wt | Criterion |
| --- | --- | --- |
| 34 | -4 | Delivers a checker that imports or reuses the primary engine's computed substitution, environment, or internal types (rather than independently implementing its own checking logic) to decide acceptance or rejection. |
| 35 | -8 | Embeds a precomputed final type for any binding, or the trace-integrity hash, as a literal substituting for executing the delivered engine. Immutable input constants (the grammar, built-in operator signatures) don't trigger this. |
