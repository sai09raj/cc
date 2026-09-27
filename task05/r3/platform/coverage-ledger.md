# R3 visible-requirement coverage ledger

| Visible source / requirement | Rubric IDs | Evidence |
|---|---|---|
| Prompt: offline deterministic simulator, executed | 1, 4 | Command, execution, versions |
| Prompt: six logical products | 2 | Accessible files, no fixed schema |
| Prompt: each design is one continuous four-campaign run, not resets | 3, 6, 8, 9, 13 | Structural + trace evidence |
| Packet Section A: aisle graph, docks, node-4 junction | 5 | Graph recovery |
| Packet Section B: six design tuples | 7 | Explicit tuples |
| Packet Section C: lot generation formulas + cadence | 6 | Programmatic 20-lot generation |
| Packet Section D: preparation, setup memory, fixtures | 8, 9, 24 (W3) | Assignment policy + persistence witness |
| Packet Section E: robot priority order, collision rules | 10 | Dispatch policy replay |
| Packet Section E: node-4 fault (measured window) | 13, 26 (W1) | Fault mechanism + witness |
| Packet Section F: oven pairing timer | 11, 21, 28 (W4) | Timer logic + pairing/mixed-campaign witness |
| Packet Section F: power admission order | 12 | Ordered-pass admission |
| Prompt: per-design makespan/bill from executed simulator | 14-19 | Six named result pairs |
| Prompt: full trace reconciliation | 20-25 | Per-design reconciliation |
| Prompt: cross-campaign interleaving evidence | 27 (W2) | Overlap witness |
| Prompt: independent verifier, sharing only immutable inputs | 29, 30 | Independence + agreement |
| Prompt: negative-start and route-collision experiments | 31, 32 | Executed adversarial checks, preserved originals |
| Prompt: both investment selections and keys | 33, 34 | Lexicographic selection, two populations |
| Prompt: baseline comparison | 35 | D0 vs both selections |
| Prompt: causal explanation tied to production events | 36 | Any accurate supported interaction |
| Prompt: distance-only relaxation explanation | 37 | Occupancy/feasibility distinction |
| Prompt: explain why per-campaign reset would not work | 38 | Continuous-run necessity argument |
| Prompt: commands/tool versions | 4 | Reproduction record |
| Prompt: prohibition on embedding precomputed answers | 39 (-8) | Only active substitution triggers |

Physical feasibility constraints (no preemption, no illegal edge, no impossible
cargo state) are enforced as positive predicates inside criteria 9, 10, 26, 29-32,
not as additional standalone author-behavior traps. Independent reconstruction
(29-30) is positively assessed; a wrapper around the primary's own internals cannot
establish it. There is no rubric requirement for one particular physically-valid
route, tie-break outcome beyond what the packet specifies, or extra design
comparisons beyond the two selections and the baseline.

Equivalent implementation language, schema, filename organization, trace
compression, and any physically-valid policy-conformant schedule are accepted
throughout.
