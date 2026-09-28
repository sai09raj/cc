# R3 visible-requirement coverage ledger

| Visible source / requirement | Rubric IDs | Evidence |
|---|---|---|
| Prompt: offline deterministic simulator, executed | 1, 4 | Command, execution, versions |
| Prompt: six logical products | 2 | Accessible files, no fixed schema |
| Prompt: each design is one continuous four-campaign run, not resets | 3, 6, 8, 9, 13 | Structural + trace evidence |
| Packet Section A: aisle graph, docks, node-4 junction | 5 | Graph recovery |
| Packet Section B: six design tuples | 7 | Explicit tuples |
| Packet Section C: lot generation formulas + cadence | 6 | Programmatic 20-lot generation |
| Packet Section D: preparation, setup memory, fixtures | 8, 9, 26, 32 (W3) | Assignment policy + persistence witness |
| Packet Section E: robot priority order, collision rules, tie-breaks | 10 | Dispatch policy replay |
| Packet Section E: node-4 fault (measured window) | 13, 28 (W1) | Fault mechanism + witness |
| Packet Section F: oven pairing timer, tie-breaks | 11, 30 (W4) | Timer logic + mixed-campaign witness |
| Packet Section F: power admission order | 12 | Ordered-pass admission |
| Packet Section G: lexicographic selection key formula | 43, 44 | Both selection criteria state the exact formula |
| Packet Section H: Q maintenance trigger/tracking | 14 | Cumulative processing-only sum, threshold 12 |
| Packet Section H: Q maintenance boundary convention | 15, 31 (W5) | Default (non-inclusive) timing rule + delay witness |
| Prompt: per-design makespan/bill from executed simulator | 16-21 | Six named result pairs |
| Prompt: full trace reconciliation | 22-27 | Per-design reconciliation (own record; witnesses owned separately by 28-32) |
| Prompt: full-trace exact integrity check | 37-42 | Per-design SHA-256 hash |
| Prompt: cross-campaign interleaving evidence | 29 (W2) | Overlap witness |
| Prompt: independent verifier, sharing only immutable inputs | 33, 34 | Independence + agreement |
| Prompt: negative-start and route-collision experiments | 35, 36 | Executed adversarial checks, preserved originals |
| Prompt: both investment selections and keys | 43, 44 | Lexicographic selection, two populations |
| Prompt: baseline comparison | 45 | D0 vs both selections |
| Prompt: causal explanation tied to production events | 46 | Any accurate supported interaction |
| Prompt: distance-only relaxation explanation | 47 | Occupancy/feasibility distinction |
| Prompt: explain why per-campaign reset would not work | 48 | Continuous-run necessity argument, incl. Q maintenance clock |
| Prompt: commands/tool versions | 4 | Reproduction record |
| Prompt: prohibition on embedding precomputed answers | 49 (-8) | Only active substitution triggers |

Physical feasibility constraints (no preemption, no illegal edge, no impossible
cargo state) are enforced as positive predicates inside criteria 9, 10, 28, 33-36,
not as additional standalone author-behavior traps. Independent reconstruction
(33-34) is positively assessed; a wrapper around the primary's own internals cannot
establish it. There is no rubric requirement for one particular physically-valid
route, tie-break outcome beyond what the packet specifies, or extra design
comparisons beyond the two selections and the baseline.

Each of the five named-witness criteria (28-32, W1/W2/W4/W5/W3) is owned by exactly
one criterion; no witness is also re-charged inside a per-design reconciliation
criterion (16-27). This was a real duplicate in an earlier draft (W5 was checked
both inside D1's reconciliation and by its own witness criterion) and a real
inconsistency (W3 was folded into D4's reconciliation instead of getting its own
row like every other witness) — both fixed per the rubric guidelines' atomicity
and nonduplication rules; see `revision-delta.md`.

Equivalent implementation language, schema, filename organization, trace
compression, and any physically-valid policy-conformant schedule are accepted
throughout.
