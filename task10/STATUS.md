# Task 10 — STATIC10 (shelved before any rubric/platform work)

**SHELVED at the S08 gate**, before writing any rubric or platform text —
the cheapest possible point to catch this. Reference engine
(`reference/sta_engine.py`), independent verifier
(`reference/sta_verify.py`), and a 14-arc fixed circuit
(`reference/circuit.py`) were built and verified correct (engine output
matches an independent hand computation exactly; verifier correctly
accepts the true program and rejects both required adversarial
mutations). The score-topology audit then failed outright: all five
required single-bug mutants scored 40-66% against every reweighting
attempted, all far above the 33% target.

## Why this isn't a reweighting problem

Static timing analysis is, structurally, an **independent-facts** domain:
each register-to-register arc's classification and delay is a function of
that specific arc's own data (its gates, its constraint-file entry) and
nothing else. Synchronous digital design is deliberately built this way —
registers exist specifically to break combinational dependency chains
into independent per-stage analyses, so a wrong regime classification on
one arc has no natural channel to corrupt any other arc's value.

The certificate hash does detect every one of the five mutants
(`hash_match=False` in all cases) — the problem isn't sensitivity, it's
that a hash is capped at +10 like any other criterion (the platform's
own per-criterion limit, honored throughout this project), and no fair
reweighting can make +10 outweigh the 70-90 points of content a narrow,
single-regime bug honestly leaves untouched (13 of 14 arcs, both
aggregate selections, unrelated local-rule and memo criteria, two of
three verifier checks). Worked the algebra explicitly: clearing 33% for
the narrowest mutant (drop FALSE-path exclusion, corrupting exactly one
arc) would require either violating the ±10 cap or assigning that one
arc 15-20x the weight of every other arc — not a defensible rubric,
just hidden difficulty-manufacturing. Confirmed this is the same root
cause as LEDGER-8's original failure (independent facts), now caught at
the design stage instead of after a real pilot.

## What's being kept

`design/architecture-attack.md`, `design/semantic-contract.md`,
`reference/circuit.py`, `reference/sta_engine.py`,
`reference/sta_verify.py`, `reference/score_counterfactual.py` — all
correct and fully verified, kept as the historical record. Do not reuse
the "many independently-classified items, no state threading" shape for
a future task without first confirming genuine cross-item dependency
exists in the domain, the same check this file itself is evidence for.

## Replacement

Needs genuine temporal/state-threading cascading (QUORUM-7's proven
property), via a mechanism and domain that doesn't reskin QUORUM-7's
protocol/consensus shape. See the updated `design/architecture-attack.md`
addendum for the new direction.
