# R3 visible-requirement coverage ledger

| Visible source / requirement | Rubric IDs | Evidence |
|---|---|---|
| Prompt: offline deterministic simulator, executed | 1 | Command, execution, versions |
| Prompt: six logical products | 2 | Accessible files, no fixed schema |
| Prompt: each design is one continuous four-campaign run, not resets | 3, 5, 7, 8, 13 | Structural + trace evidence |
| Packet Section A: aisle graph, docks, node-4 junction | 4 | Graph recovery |
| Packet Section B: six design tuples | 6 | Explicit tuples |
| Packet Section C: lot generation formulas + cadence | 5 | Programmatic 20-lot generation |
| Packet Section D: preparation, setup memory, fixtures | 7, 8, 27, 33 (W3) | Assignment policy + persistence witness |
| Packet Section E: robot priority order, collision rules, tie-breaks | 9 | Dispatch policy replay |
| Packet Section E: node-4 fault (measured window) | 13, 29 (W1) | Fault mechanism + witness |
| Packet Section F: oven pairing timer, tie-breaks | 10, 11, 31 (W4) | Partner-matching + deadline-timing + mixed-campaign witness |
| Packet Section F: power admission order | 12 | Ordered-pass admission |
| Packet Section G: lexicographic selection key formula | 44, 45 | Both selection criteria state the exact formula |
| Packet Section H: Q maintenance trigger/tracking | 14 | Cumulative processing-only sum, threshold 12 |
| Packet Section H: Q maintenance boundary convention | 15, 16, 32 (W5) | Default (non-inclusive) timing rule, split trigger/window facts + delay witness |
| Prompt: per-design makespan/bill from executed simulator | 17-22 | Six named result pairs |
| Prompt: full trace reconciliation | 23-28 | Per-design reconciliation (own record; witnesses owned separately by 29-33) |
| Prompt: full-trace exact integrity check | 38-43 | Per-design SHA-256 hash |
| Prompt: cross-campaign interleaving evidence | 30 (W2) | Overlap witness |
| Prompt: independent verifier, sharing only immutable inputs | 34, 35 | Independence + agreement |
| Prompt: negative-start and route-collision experiments | 36, 37 | Executed adversarial checks, preserved originals |
| Prompt: both investment selections and keys | 44, 45 | Lexicographic selection, two populations |
| Prompt: baseline comparison | 46 | D0 vs both selections |
| Prompt: causal explanation tied to production events | 47 | Any accurate supported interaction |
| Prompt: distance-only relaxation explanation | 48 | Occupancy/feasibility distinction |
| Prompt: explain why per-campaign reset would not work | 49 | Continuous-run necessity argument, incl. Q maintenance clock |
| Prompt: commands/tool versions | 1 | Reproduction record (merged into criterion 1 with execution) |
| Prompt: prohibition on embedding precomputed answers | 50 (-8) | Only active substitution triggers |

Physical feasibility constraints (no preemption, no illegal edge, no impossible
cargo state) are enforced as positive predicates inside criteria 8, 9, 29, 34-37,
not as additional standalone author-behavior traps. Independent reconstruction
(34-35) is positively assessed; a wrapper around the primary's own internals cannot
establish it. There is no rubric requirement for one particular physically-valid
route, tie-break outcome beyond what the packet specifies, or extra design
comparisons beyond the two selections and the baseline.

Each of the five named-witness criteria (29-33, W1/W2/W4/W5/W3) is owned by exactly
one criterion; no witness is also re-charged inside a per-design reconciliation
criterion (17-28). Criteria 10/11 (oven partner-matching / deadline-timing) and
14/15/16 (Q-maintenance trigger / trigger-minute-unaffected / 13-minute window)
were each split from a single bundled criterion during a rubric-guidelines
atomicity audit, because a response can satisfy one half and fail the other
independently (e.g. correct tie-break with wrong deadline arithmetic, or correct
trigger detection with the wrong boundary convention). Criterion 1 merges what were
previously two criteria (documented execution command; recorded tool versions),
since both tested the same underlying reproducibility fact. See `revision-delta.md`
for the full accounting of every renumbering this caused.

Equivalent implementation language, schema, filename organization, trace
compression, and any physically-valid policy-conformant schedule are accepted
throughout.
