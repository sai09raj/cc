# Task 09 architecture attack

## Why LEDGER-8 was shelved (one sentence)

LEDGER-8's facts were largely independent (one wrong elimination entry
left most other accounts correct), which is exactly what let two real
pilots score 98%/100% once a packaging bug was fixed: nothing forced a
single early mistake to corrupt the rest of the submission. See
`task08/STATUS.md`'s "Fourth finding."

## The one property task-09 must have

**Genuine cascading/compounding state**, the same property that made
QUORUM-7 real: a single early error must corrupt most of what comes
after it, so a submission that is wrong anywhere is very likely wrong in
many places at once, not just the one place it slipped. This is not
negotiable this time -- it gets checked empirically (via the mutant
audit) before a single line of rubric or platform text is written, not
assumed and discovered the hard way after real pilots run.

Explicit targets set for this task, going in: real pilot scores **below
50%**, and every tested single-bug mutant **below 33%**. QUORUM-7 hit
31%/32% real and 25.9%/27.9%/32.0% mutant -- that is the bar, not a
stretch goal.

## Domain choice: type inference for a small functional language

**Domain:** Programming Languages / Compilers.
**Subdomain:** Hindley-Milner-style type inference with let-polymorphism
over a fixed, hand-written program in a small functional language.

This is a new domain for this project (QUORUM-7 was distributed
systems/networking, LEDGER-8 was accounting/finance, KILNWORKS/ATRIUM-9/
CISTERN-7 were manufacturing/industrial-process simulation -- none of
them touch programming-language theory or static analysis).

### Why this has genuine cascading structure, unlike LEDGER-8

Hindley-Milner inference threads **one global substitution** through
the entire program. Concretely: inferring the type of binding N
produces a substitution that must be applied to the typing environment
used for every binding after N. A single wrong unification step at
binding 3 (say) doesn't just produce one wrong fact the way an isolated
accounting error did in LEDGER-8 -- it corrupts the substitution itself,
which then silently corrupts the inferred type of every later binding
that references binding 3, directly or transitively, through however
many further let-bindings use it. This is structurally the same
"corruption propagates forward" property that made QUORUM-7 hard (a
protocol-state bug early in a run corrupts most of the rest of that
run's trace) -- just in a completely different mechanism (substitution
composition over an AST, not message-passing over ticks).

To make this property actually bite (not just theoretically present),
the fixed program this task ships must have **real reference chains**:
binding N's body must call/use earlier bindings polymorphically (each
call site potentially instantiating a let-bound polymorphic type
differently), not just be N independent, unrelated expressions sharing
a file. A program that's "20 unrelated one-liners" would just be
LEDGER-8 again with different syntax. The chosen program is built
explicitly as a dependency graph where most bindings use 2-4 earlier
ones, so a single wrong inferred type has many chances to be consumed
downstream, and the final serialized certificate (all N bindings' final
types) will diverge across most of the N entries when that happens.

### Why this breaks QUORUM-7's meta-shape too

QUORUM-7 (and KILNWORKS/ATRIUM-9/CISTERN-7 before it) shared: tick-by-
tick simulator, parameter sweep across named settings, lexicographic
selection among sweep rows, independent verifier, adversarial mutations,
hash certificate. Task-09 has no time dimension, no ticks, no sweep, no
selection among rows -- it's a single static elaboration pass over one
fixed program, closer in surface shape to LEDGER-8 (one fixed input,
one correct answer) than to QUORUM-7. What makes it NOT repeat LEDGER-8's
failure is the substitution-threading cascade described above, not
surface mechanics. This is deliberately a third task *shape* in this
project: temporal/concurrent state machine (QUORUM-7), static
many-independent-facts reconciliation (LEDGER-8, now known to be the
wrong choice), and now static-but-threaded elaboration with one global,
order-dependent piece of shared state (task-09).

### Perfect-semantics ablation: the real risk here

Hindley-Milner / Algorithm W is extremely well-known -- a frontier model
has almost certainly seen many correct textbook implementations in
training. If this task shipped *vanilla* Hindley-Milner, a model could
plausibly reproduce a textbook implementation from memory and get it
right without ever needing to carefully read the packet, which is
exactly the "generic solver already exists" trap this project's own
playbook warns against (the same concern that ruled out KILNWORKS R2's
CP-SAT formulation, and that QUORUM-7 avoided by never implementing
*vanilla* Raft -- its pre-vote phase, 3-of-5 quorum used in three
distinct places, K=4 bounded-batch replication, and specific tie-break
rules are not standard Raft, they're this packet's own stated variant).

Task-09 must do the same thing: deviate from vanilla Hindley-Milner in
several load-bearing, stated-only-in-the-packet ways, so a model that
"knows the textbook algorithm" still has to read and follow this
packet's specific rules to get a correct answer, and a model that
doesn't read carefully will confidently apply the standard rule and get
a specific, predictable, wrong answer (a strong adversarial-mutation
candidate in its own right). Planned deviations (finalized in
`semantic-contract.md`):

1. **A custom, non-standard generalization restriction** beyond the
   usual value restriction -- a specific, stated rule for exactly when a
   let-bound type may be generalized (quantified) versus must stay
   monomorphic, that doesn't match any single textbook's exact phrasing.
2. **A bespoke, small set of built-in type constructors** specific to
   this language (not just arrow types and a couple of base types) --
   enough that the exact shape of several inferred types can't be
   guessed from knowing the general algorithm alone.
3. **An explicit, fully mechanical certificate/canonicalization rule**
   for naming type variables in the final serialized output (learning
   directly from LEDGER-8's Playbook mistake #66 -- this gets specified
   as precisely and mechanically as that fix required, from the first
   draft, not patched in after a real pilot exposes the gap).
4. **A specific, stated unification tie-break / order rule** for
   multi-way constraints (which occurs-check / composition order to use
   when more than one unification step is available at once), so the
   "obviously correct" generic algorithm still has one specific
   procedural rule to follow, not just "do unification" left implicit.

### Oracle feasibility

Unlike CP-SAT-style search problems, Hindley-Milner with a fixed program
has exactly one correct output: principal types are unique up to
consistent renaming of type variables (a standard, well-established
result), and with this packet's bespoke canonicalization rule (point 3
above) the serialized certificate is byte-identical for any two correct
implementations -- there is no ambiguity to rediscover the way LEDGER-8's
certificate did, because this time the canonicalization rule is written
precisely into the design before any pilot ever runs, not inferred from
what two independent pilots happened to disagree about.

## Independent verification shape

Mirroring this project's house style (QUORUM-7's structurally different
verifier, LEDGER-8's structurally different auditor): the independent
checker will NOT be a second type *inferencer* using the same
algorithm -- it will be a type *checker* (bidirectional checking mode),
which takes the primary's claimed types as given and verifies each
expression type-checks against them, a genuinely different algorithm
(checking vs. inference) with a different failure mode (a checker can
accept a type the inferencer never would have produced, so this
actually tests something inference-only self-consistency can't).

Required adversarial mutations (exact two, finalized in
`semantic-contract.md`): an occurs-check omission (lets a type unify
with a type containing itself, producing a cyclic/infinite type that
must be rejected) and a let-generalization violation (generalizes a
type variable that is still constrained by an unsolved outer
constraint -- the classic unsoundness bug this task's custom
generalization rule in point 1 above is specifically designed to catch).

## Deliverables (unchanged shape from QUORUM-7/LEDGER-8)

Inference engine source; independent type-checker source; the full
typing output for every binding in the fixed program; a findings
report; certification evidence (the trace hash plus both
adversarial-mutation rejection results); an engineering memo explaining
the causal chain from the program's actual dependency structure through
specific unification/generalization steps to the final inferred types.

## Next steps

1. Write `design/semantic-contract.md`: the small language's grammar,
   the bespoke type-constructor set, the exact (non-standard)
   generalization rule, the exact unification order/tie-break rule, and
   the exact certificate canonicalization rule -- all precisely enough
   that two independent correct implementations cannot disagree on
   output, learning directly from mistake #66.
2. Design the fixed program itself as a real dependency graph (not N
   independent one-liners), sized so that the cascading property is
   checkable and significant (plan: ~20-25 bindings).
3. Build the reference inference engine (primary implementation).
4. Build the independent bidirectional type checker.
5. Run the score-topology / mutant audit BEFORE writing a word of the
   rubric -- confirm single-mutant scores land under 33% using real
   execution, the same discipline already established, but this time as
   a gate before committing to this architecture, not a late audit.
