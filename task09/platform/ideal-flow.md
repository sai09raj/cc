## Analyze

```text
Read the packet and reconstruct the language's S-expression grammar
(literals, variables, lambdas, application, let, if, arithmetic, pairs,
lists) and its type system (Int, Bool, function, pair, list types, and
type variables). Recover this packet's own generalization rule for let
bindings -- stricter than standard ML's value restriction and not safe
to assume from memory: generalize only when the bound expression is
syntactically a lambda, or a bare reference to a name already bound to
a polymorphic scheme; every other form (literals, applications, ifs,
pair/list constructions) binds the name to its plain, unquantified
type, even where ordinary ML would generalize it. When generalizing,
quantify only the type variables not free in the current typing
environment -- quantifying one still shared with an outer, unresolved
lambda parameter is unsound and is this packet's central correctness
trap. Recover the occurs-check requirement and the fully mechanical
certificate format: literal header line, each of the 25 fields in one
fixed order (not alphabetical), full parenthesization, and per-binding
type-variable numbering in first-occurrence order. Treat the attached
27-binding program as one continuous dependency chain, not 27
independent facts: most bindings consume 2-4 earlier ones, and a wrong
generalization decision early in the chain corrupts the substitution
threaded through everything after it.
```

## Execute & Generate

```text
Implement a deterministic, offline Hindley-Milner-style inference
engine (Algorithm W or equivalent) that processes the 27-binding
program under one threaded substitution, applying this packet's own
generalization rule (not standard ML's) at every let, with a correct
occurs-check in unification. Build a separately-coded bidirectional
type checker -- not a second inferencer using the same algorithm, but
one that verifies each binding's claimed type by checking the body
against it top-down -- sharing only immutable input constants (the
grammar, the program text) with the primary implementation, never
importing its substitution, environment, or any computed type. Run the
two required adversarial mutations against the checker: a
self-application expression `(fun x (x x))` requiring an infinite type,
and a claimed scheme that over-generalizes a type variable still free
in its own enclosing environment (quantifying a variable that should
stay tied to an outer lambda parameter). Confirm the checker rejects
both while still accepting the true program's own correct types.
Deliver engine source, checker source, the full 27-binding typing
output, certification evidence (both rejection results plus the
SHA-256 trace-integrity hash computed by the packet's exact algorithm),
and a memo. Equivalent languages, source organization, and any
type-printing notation unambiguously equivalent to the packet's stated
grammar all pass; exactly one physically valid typing exists for this
fixed program under these rules.
```

## Synthesize

```text
Using your own executed engine's actual claimed types for mk1 through
mk10, explain why each nested-let `keep` binding inside those lambdas
may only generalize over its own helper argument's type variable, never
over the outer, not-yet-resolved parameter it closes over -- and why
quantifying that outer variable (the bug the over-generalization
mutation specifically targets) would let two calls to the same `keep`
with different arguments silently return two unrelated types, when in
reality `keep` always returns the exact same captured value regardless
of its argument. Explain, with specific bindings from your own output,
at least two places where this packet's stricter rule produces a
different (more monomorphic) result than standard ML's value
restriction would have, and why that's the correct behavior here.
Report your checker's agreement on the true program, both adversarial
mutation rejection results, and the final trace-integrity hash,
reconciling all of it against the same generalization rule and the
program's actual dependency chain -- not as three separate facts, but
as one coherent causal story from the stated rule to the final
certificate.
```
