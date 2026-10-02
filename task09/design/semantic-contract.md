# Task 09 (working name: TYPECHAIN-9) semantic contract

## S01 — The language

A small, pure (no effects, no mutation), statically-scoped functional
language. One fixed program, written in this language, is the task's
entire input (no sweep, no parameters). Expression grammar:

```
e ::= n                        -- integer literal
    | true | false
    | x                        -- variable
    | fun x -> e                -- lambda (curry multi-arg: fun x -> fun y -> e)
    | e1 e2                     -- application (left-associative)
    | let x = e1 in e2
    | if e1 then e2 else e3
    | e1 + e2 | e1 - e2 | e1 * e2
    | e1 < e2 | e1 == e2        -- both Int -> Int -> Bool
    | (e1, e2) | fst e | snd e
    | nil | cons e1 e2 | isnil e | head e | tail e
```

Types:

```
T ::= Int | Bool
    | T1 -> T2                 -- function
    | T1 * T2                  -- pair
    | List T
    | 'a, 'b, 'c, ...           -- type variables (inference-internal)
```

`nil : List 'a` (polymorphic in its element type at the point of
construction, before any constraint). `cons : 'a -> List 'a -> List 'a`.
`fst/snd` project a pair's own two component types. `head/tail`
require `List T` and yield `T` / `List T` respectively.

## S02 — The one load-bearing deviation: generalization rule

Standard ML generalizes at `let x = e1 in e2` whenever `e1` is any
syntactic value (literal, lambda, tuple of values, etc.). **This
task's rule is stricter and is the opposite of safe to assume from
memory:**

> At `let x = e1 in e2`: infer `e1`'s type `τ1` under the current
> substitution. Generalize (bind `x` to a quantified scheme) **only
> if `e1` is syntactically a lambda (`fun ... -> ...`, any curry
> depth) or a bare variable reference to a name already bound to a
> polymorphic scheme** (a direct alias of an existing polymorphic
> binding). For every other form of `e1` — an integer/boolean
> literal, an application, an `if`, a pair or list construction or
> projection, anything not covered by the two cases above — **do not
> generalize**, even though standard ML's value restriction would
> allow it: bind `x` to the plain, unquantified type `τ1` (after
> applying the current substitution) for inferring `e2`.
>
> When generalizing, quantify exactly the type variables free in
> `τ1` (post-substitution) that are **not** free in the current
> typing environment `Γ` (post-substitution) — the standard
> soundness-preserving exclusion. Omitting this exclusion (quantifying
> a variable that is still free in `Γ`) is this task's mutation B
> (S10).

A model that silently falls back to "standard ML value restriction"
will generalize several bindings this task's rule forbids (e.g. a
let-bound pair or list literal), producing wrong (too-polymorphic)
types for those bindings and everything downstream of them that relies
on the stricter, monomorphic behavior — a specific, predictable,
detectable wrong answer, not a vague approximation.

## S03 — Unification

Standard syntax-directed Robinson unification with occurs-check:
`unify('a, T)` fails if `'a` occurs free in `T` (unless `T = 'a`
itself). Omitting the occurs-check is this task's mutation A (S10) —
it would let a cyclic/infinite type unify successfully where it must
be rejected. Because the chosen program (S04) is fully well-typed
under the correct rules, the correctly-implemented engine never
actually triggers a unification failure on the true program; the
occurs-check's role is purely as a required mutation-rejection path
for S10, not part of the true program's own trace.

## S04 — The fixed program (structural requirement)

A single, hand-written program of **22 top-level `let` bindings**,
each a genuine dependency: the large majority of bindings call or
reference 2-4 earlier bindings in their own body (not independent
one-liners sharing a file -- the whole point is that one wrong
inferred type for an early binding corrupts the typing environment
used for most of what follows, the same cascading property that made
QUORUM-7 real and that LEDGER-8 lacked). At least two bindings are
`let`-expressions nested **inside a lambda body**, referencing that
lambda's own (not-yet-generalized) parameter, specifically to exercise
S02's environment-exclusion rule (the scenario mutation B breaks).
At least four bindings are only correctly typed under S02's stricter
rule (they would get a different, wrong, over-generalized type under
plain ML value restriction). Every binding's final type is fully
ground or validly polymorphic with no dangling unconstrained type
variables once the whole program is solved. The exact program text is
authored and frozen in `reference/program.ty` once the reference
engine exists to validate it end to end.

## S05 — Independent verification

A **separately-coded bidirectional type checker** (not a second
inferencer using the same algorithm): given the primary's claimed
final type for every binding, it checks each binding's body against
its claimed type in checking mode, re-deriving argument/result types
structurally rather than running unification-based inference from
scratch. This is a genuinely different algorithm (checking vs.
inference), sharing only immutable input constants (the program text
itself, the grammar, the built-in operator signatures) with the
primary -- never importing or wrapping the primary's substitution,
environment, or any computed intermediate value.

## S06 — Certification (fully mechanical from the first draft)

For each of the 22 bindings, in **source order** (the order they
appear in the program, not alphabetical, not dependency order):

1. If the binding was generalized (S02): print `forall `, then the
   quantified type variables in **first-occurrence order reading the
   type left to right**, renamed to `t0 t1 t2 ...` (fresh per binding
   -- each binding's own scheme numbers its own quantified variables
   starting at `t0`, independent of every other binding), separated by
   single spaces, then ` . `, then the type body using those names.
   If not generalized, print just the type body (no `forall` prefix).
2. The type body's grammar is fully parenthesized with no precedence
   elision: `Int`, `Bool`, `(T1->T2)`, `(T1*T2)`, `List(T)` — every
   function and pair former wrapped in parens, always, including when
   nested arbitrarily deep.
3. One line per binding: `BindingName=Type` (`Type` per 1-2 above),
   no spaces inside the `Type` string itself.

Full serialization: the literal header line `TYPECHAIN9-CERT-V1`, then
the 22 binding lines in source order, joined by a single `\n`, UTF-8
encoded, hashed with SHA-256; report the first 16 hex characters.

## S07 — Deliverables

Inference engine source; independent bidirectional checker source; the
full typing output (all 22 bindings, generalized-or-not and their
printed types per S06); a findings report; certification evidence (the
trace hash plus both adversarial-mutation rejection results); an
engineering memo explaining, citing the program's actual dependency
edges, why specific bindings are/aren't generalized under S02 and why
mutation A and mutation B each must be rejected.

## S08 — Score-topology gate (before any rubric is written)

Before writing `platform/rubric.md`, build the score-topology audit
(`reference/score_counterfactual.py`) against real mutants applied to
the actual reference engine and run it. Required: every tested
single-bug mutant scores **under 33%**. If any mutant exceeds that,
the program (S04) or the rule set (S02/S03) gets redesigned to
increase cascading reach -- not the rubric weights reverse-engineered
to force the number down (the mistake explicitly avoided this time,
per the LEDGER-8 postmortem).
