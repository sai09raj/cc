# Blind pilot 1 — local agent, cold solve

**This is not the required target-model pilot.** It is the local blind-calibration
step the playbook requires before spending a real Opus 4.8 Max run
(`Playbook/01-END-TO-END-SOP.md` Phase 10 calls this out explicitly: diagnose one
real attempt before committing acceptance runs). The solver here is a
general-purpose coding agent, not Opus 4.8 Max at max effort, and it was not under
the same time/attempt constraints a real platform run would face. Treat the result
as a lower bound on how hard R3 currently is, not as platform-equivalent evidence.

## Setup

A fresh agent was given exactly two files — `prompt.md` (as `prompt.txt`) and the
rendered `kw-r3.pdf` — copied into an isolated scratch directory, with explicit
instructions not to read anything else on the filesystem. It had no access to
`design/`, `reference/`, `audit/`, or any rubric. It was told to solve for real:
build a simulator, an independent verifier, run the adversarial checks, and write a
memo — the same deliverables the prompt asks for.

## Result: ~85% against the frozen rubric (52/61, criteria 33-34 read generously — see below)

| Design | Reference | Blind agent | Match |
|---|---|---|---|
| D0 | 187 / 1331 | 187 / 1331 | exact |
| D1 | 165 / 1294 | 165 / **1336** | makespan only |
| D2 | 187 / 1447 | 187 / 1447 | exact |
| D3 | 185 / 1401 | 185 / 1401 | exact |
| D4 | 155 / 1413 | **152** / **1362** | neither |
| D5 | 142 / 1290 | 142 / 1290 | exact |

4 of 6 designs matched exactly. The agent's graph/rule extraction was genuinely
careful — it parsed the PDF's vector path data directly (not OCR) to prove the
open/closed aisle edge from dash-array geometry, and read the node-4 fault window
as 6 minutes from the shaded rectangle's coordinates against the axis, exactly the
intended visual-extraction mechanism. Its own verifier (independently coded, not a
wrapper) reproduced its own primary implementation byte-for-byte across all six
designs, and both required adversarial mutations were correctly rejected.

## What actually caused the D1/D4 divergence

Not architecture-level confusion — a specific, confirmed boundary-condition bug in
the agent's own code, found by pulling its `kiln_sim.py` and diffing minute-by-minute
against the reference:

1. `lot.delivered_at = t` — set to the minute the unload action is *decided*, not
   `t+1` when the packet says the effect becomes visible. This makes a lot eligible
   for oven pairing one minute earlier than it should be.
2. `elif t > self.oven.anchor_deadline:` — strictly greater-than, where the packet
   says "if the deadline has passed" (intended as `>=`, reached-or-passed).

Both are real implementation slips despite the agent's own prose notes showing it
understood the rules correctly — exactly the class of error R3's architecture is
designed to expose (careful composition of many precise boundary rules over a long
trace, not any single hard-to-find fact). Total power draw across the whole run was
identical in both cases (660 units), confirming this was a pure timing/attribution
bug, not a missing mechanism.

## A second, more serious finding: a real gap in the packet (now fixed)

The rubric's lexicographic selection key `(makespan, bill + 3*capital, capital, ID)`
was defined in the private semantic contract and the prompt referred to "the
lexicographic key in the packet" — but the key formula was **never actually
rendered into the PDF**. The blind agent used `(makespan, bill)` instead, a
reasonable substitute given what it was actually shown. This was my error, not a
solver failure, and it is exactly what a blind test is for: it surfaced a genuine
Gate 6 violation ("could a competent solver construct a valid answer from only this
prompt and attachment?") before any real platform run.

**Fixed:** `artifact/kw-r3.pdf` now has a new Section G stating the key formula
explicitly. The oven-timer paragraph (Section F) was also tightened: "arrival
minute" now explicitly cross-references the t→t+1 visibility rule, and "deadline
has passed" now explicitly reads ">= the deadline... not strictly greater than" —
closing the exact ambiguity this agent's bug exploited. New PDF hash recorded in
`platform/frozen-packet-manifest.json`; `platform/prompt.md` and
`platform/score-topology.md` content is unchanged by this fix.

## Scoring detail (against the frozen 61-point rubric)

- Package (1-4): 4/4.
- Local (5-13): 10/11 — fails 11 (oven timer) for the reasons above.
- Per-design values (14-25): 16/24 — D0/D2/D3/D5 full marks, D1/D4 zero (bill wrong
  on both; makespan also wrong on D4).
- Witnesses/verify/feasibility (26-32): 16/16 — full marks, including agreement
  between the agent's own two implementations and both adversarial rejections.
- Decision (33-38): 6/6, generously — criteria 33/34 ask for the exact key tuple,
  which the agent could not have produced correctly without the (missing) formula;
  granted here because neither design's selection actually had a tie for capital to
  break (D5 and D1 each dominate their population on makespan alone), so the
  agent's simplified key produced the correct ID either way. **This generosity
  applied only because the packet gap was mine; a future run against the fixed
  packet gets no such allowance.**
- **Total: 52/61 = 85.2%.**

## Assessment — this is a real concern, not a pass

An 85% blind score is far above the <50% target. Two of the three things that cost
this run points were a genuine implementation slip in one mechanism (oven timing)
and a spec gap I have now closed (which, if anything, makes the *next* run's job
easier, not harder). Taken together, this is evidence that R3's current density of
boundary-condition rules may not be sufficient to reliably stump Opus 4.8 Max at
max effort, even though the CP-SAT shortcut that solved R2 is genuinely closed.

This does not mean R3 is worthless — the architecture fix (removing the free
optimization decision) is still necessary and the four exactly-matching designs show
the core mechanics (graph, cadence, fault, verification) are sound and correctly
specified. But a single local blind run scoring this high, from a solver under no
real time pressure, is not something to spend a real platform pilot against without
either (a) further hardening the density/subtlety of interacting boundary rules, or
(b) accepting the risk and treating a real Opus 4.8 Max pilot as the next diagnostic
step regardless. That decision is recorded here, not made unilaterally.
