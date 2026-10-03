# TYPECHAIN-9 rubric

Positive total **122**; three negative criteria, **-4** (independence
prohibition), **-4** (eligibility-rule prohibition), and **-8**
(negative trap). **39 criteria** (within the
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
estimated): dropping S02's exclusion rule scores **18.9%** against this
exact rubric's weights -- well under the 33% target. See `STATUS.md`
for the full score-topology audit, including a second, weaker mutant
(76.2%) that was tested and honestly excluded as a non-discriminating
scenario for this program's specific structure, rather than hidden.

Redundancy note: S02 can be violated three distinct ways, and only two
are redundant with the positive criteria. (1) Dropping the
environment-exclusion clause (quantifying a variable still free in the
enclosing environment) and (2) dropping the occurs-check both
necessarily corrupt an already-tested value (confirmed by execution:
the former cascades to 23/27 wrong bindings, the latter produces a real
unification error) -- no dedicated negative needed for either, since
one would score the same root-cause bug twice. (3) Applying standard
ML's actual value restriction (treating a let-bound literal, pair, or
list as generalization-eligible, not just lambdas and bare polymorphic
aliases) is different in kind: confirmed by execution that it produces
a byte-identical certificate and hash on this program (every non-lambda
top-level binding already has a concrete type with no free variable to
quantify, so broader eligibility changes nothing observable here). That
violation can hide fully behind a correct-looking result, so it gets
its own dedicated negative below, the same distinction LEDGER-8's own
rubric needed a real pilot to learn, caught here before any pilot by
testing all three ways S02 could be dropped, not just the one that was
assumed load-bearing.

Score-topology 4-bucket partition (run before platform entry, per the
rubric guide's plausible-wrong survival ceiling): package/existence =
3 (criteria 1-3); local parsing/isolated rules = 10 (criterion 4);
integrated production execution = 91 (criteria 5-31, the 27 certified
facts, plus criterion 32, the hash); final decision/causal
reconciliation = 18 (criteria 33-36: checker accept/reject-A/reject-B,
each now its own row, plus the memo). A submission granted perfect
local-rule knowledge but wrong global execution still fails nearly all
of bucket 3 (the same cascading structure the 18.9% mutant measured),
putting worst-case survival at roughly (3+10+12+18)/122 ≈ 36% --
under the 50% reject threshold.

### Package (1-3, weight 3)

| # | Wt | Criterion |
| --- | --- | --- |
| 1 | +1 | Delivers all six required files: the inference engine source, the independent checker source, the full 27-binding typing output, a findings report, certification evidence (both adversarial rejection results and the trace-integrity hash), and an engineering memo. |
| 2 | +1 | Executes the delivered inference engine and checker end to end with a documented, reproducible command. |
| 3 | +1 | Records the language/runtime tool version used, in a declared offline, dependency-free (stdlib-only) execution environment. |

### Local semantics/rules (4, weight 10)

| # | Wt | Criterion |
| --- | --- | --- |
| 4 | +10 | The delivered engine generalizes a `let`-bound name only when the bound expression is syntactically a lambda or a bare reference to an already-polymorphic binding, excluding from quantification any type variable still free in the enclosing environment -- never the standard ML value restriction. |

### Certified program facts (5-31, weight 81)

Each binding's final type, exactly as this packet's S06 serialization
format requires (fixed field order, full parenthesization, per-binding
`t0 t1 ...` numbering in first-occurrence order, `forall` prefix only
when the binding is both generalization-eligible and has at least one
quantified variable remaining).

| # | Wt | Criterion |
| --- | --- | --- |
| 5 | +3 | Reports `five` as `Int` (exact). |
| 6 | +3 | Reports `mk1` as `forall t0 . (t0->(t0*t0))` (exact). |
| 7 | +3 | Reports `r1` as `Int` (exact). |
| 8 | +3 | Reports `mk2` as `forall t0 . (t0->(t0*t0))` (exact). |
| 9 | +3 | Reports `r2` as `Int` (exact). |
| 10 | +3 | Reports `mk3` as `forall t0 . (t0->List(t0))` (exact). |
| 11 | +3 | Reports `r3` as `Int` (exact). |
| 12 | +3 | Reports `mk4` as `forall t0 . (t0->(t0*t0))` (exact). |
| 13 | +3 | Reports `r4` as `Int` (exact). |
| 14 | +3 | Reports `mk5` as `forall t0 . (t0->(t0*t0))` (exact). |
| 15 | +3 | Reports `r5` as `Int` (exact). |
| 16 | +3 | Reports `mk6` as `forall t0 . (t0->List(t0))` (exact). |
| 17 | +3 | Reports `r6` as `Int` (exact). |
| 18 | +3 | Reports `mk7` as `forall t0 . (t0->(t0*t0))` (exact). |
| 19 | +3 | Reports `r7` as `Int` (exact). |
| 20 | +3 | Reports `mk8` as `forall t0 . (t0->(t0*t0))` (exact). |
| 21 | +3 | Reports `r8` as `Int` (exact). |
| 22 | +3 | Reports `mk9` as `forall t0 . (t0->List(t0))` (exact). |
| 23 | +3 | Reports `r9` as `Int` (exact). |
| 24 | +3 | Reports `mk10` as `forall t0 . (t0->(t0*t0))` (exact). |
| 25 | +3 | Reports `r10` as `Int` (exact). |
| 26 | +3 | Reports `wrap_in_list` as `forall t0 . (t0->List(t0))` (exact). |
| 27 | +3 | Reports `list_of_r10` as `List(Int)` (exact). |
| 28 | +3 | Reports `id` as `forall t0 . (t0->t0)` (exact). |
| 29 | +3 | Reports `use_id_on_r10` as `Int` (exact). |
| 30 | +3 | Reports `alias_id` as `forall t0 . (t0->t0)` (exact). |
| 31 | +3 | Reports `use_alias_id_on_pair` as `(Int*Int)` (exact). |

### Certification and independent verification (32-36, weight 28)

| # | Wt | Criterion |
| --- | --- | --- |
| 32 | +10 | Matches the first 16 hex characters of the trace-integrity hash (algorithm in the packet) to `bb271eaf3a8043e6`. |
| 33 | +4 | The independently-coded checker accepts the true 27-binding program's own correct claimed types in full. |
| 34 | +4 | The independently-coded checker rejects the self-application adversarial mutation (`(fun x (x x))`, requiring an infinite/cyclic type). |
| 35 | +4 | The independently-coded checker rejects an over-generalized claimed scheme (a binding that wrongly quantifies a type variable still free in its enclosing environment). |
| 36 | +6 | Explains in the memo why each nested-let `keep` binding inside `mk1` through `mk10` may only generalize over its own argument's type variable, never over the outer parameter's, naming each binding's own reported type rather than a generic rule restatement. |

### Negative criteria (37-39)

| # | Wt | Criterion |
| --- | --- | --- |
| 37 | -4 | Delivers a checker that imports or reuses the primary engine's computed substitution, environment, or internal types (rather than independently implementing its own checking logic) to decide acceptance or rejection. |
| 38 | -4 | Treats a let-bound literal, pair, list, or other non-lambda, non-alias value form as generalization-eligible (standard ML's value restriction), rather than restricting eligibility to lambdas and bare polymorphic aliases as this packet requires. |
| 39 | -8 | Embeds a precomputed final type for any binding, or the trace-integrity hash, as a literal substituting for executing the delivered engine. Immutable input constants (the grammar, built-in operator signatures) don't trigger this. |
