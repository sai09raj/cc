# LEDGER-8 architecture attack

## Why this shape

QUORUM-7, CISTERN-7 (shelved), and ATRIUM-9 all shared one meta-shape:
deterministic tick simulator -> parameter sweep -> lexicographic
selection -> independent verifier -> adversarial mutations -> SHA-256
certificate -> memo. LEDGER-8 deliberately breaks that shape: there is
no time dimension, no simulator, and no parameter sweep. The difficulty
instead comes from correctly threading six interacting elimination rules
(S06) through a moderately large, cross-referenced static dataset (four
entities' trial balances, one currency translation, six intercompany
facts) to one single consolidated answer. This tests a genuinely
different kind of reasoning: rule-application and double-entry
consistency over a static structure, not state-machine/temporal
reasoning over a fault-injected run.

Domain: **Finance** (the platform's fixed domain picker list, see
`Playbook/00-START-HERE-EVERY-FUTURE-TASK.md`). Subdomain: corporate
accounting consolidation and elimination-entry audit.

## Why a generic solver can't shortcut this

There is no optimization objective, no search space, and no solver
formulation that applies. This is exactly the KILNWORKS R2 lesson (an
architecture that reduced to a CP-SAT-solvable formulation was
trivially defeated by a generic solver) inverted for a different reason:
LEDGER-8 has no free variable to search over at all. Every account's
final value is fully determined once the six elimination entries (S06)
are applied in accordance with S07-S08. A "solver" would have nothing
to solve; the task is pure, deterministic rule-following at
scale, exactly the kind of task where a careful-looking but incomplete
application of the rules produces a plausible, internally-consistent,
but wrong final balance sheet -- which is what the score-topology audit
(mutant set) is designed to exploit.

## Perfect-semantics ablation

If a submission perfectly reconstructs S01-S12 from the packet and
executes them exactly as stated, the only possible outcome is the one
reference consolidated balance sheet and income statement (S09's
balance invariant plus the frozen S04 input facts fully determine every
account). There is no equally-valid alternative correct answer, unlike
a genuine multi-objective search (QUORUM-7's two selections, which are
allowed to diverge) -- here, divergence from the reference means an
error, not a legitimate alternative, which is exactly what the "only one
physically valid trace" framing from the tick-simulator tasks becomes in
a static-reconciliation task: "only one physically valid consolidated
balance sheet."

## Known failure modes this rubric must catch (from real debugging, not
## speculation)

Building the reference engine itself surfaced four real, distinct bugs
before it balanced (see `reference/ledger8_engine.py`'s docstrings and
comments for exactly where): a sign error in the dividend-elimination
entry (E5), two different intercompany receivables conflated into one
account (the loan receivable and the trade receivable), a double-counted
net income (added to retained earnings both as part of an
"ending-inclusive" input and again separately), and an inconsistent
currency-translation formula for the foreign subsidiary's CTA plug
(pre-absorbing net income inconsistently with the other three
entities). Each of these is now a strong, real candidate for the
score-topology audit's mutant set (`reference/score_counterfactual.py`,
task #30) precisely because they are not hypothetical "a model might
possibly do this" guesses -- they are bugs a careful, rigorous
implementation (mine) actually made and had to catch via the balance
invariant (S09) before shipping. A submission that makes any one of
these mistakes will very likely still produce an internally
plausible-looking (if not exactly balanced) result unless it checks the
fundamental accounting equation as rigorously as this process did.
