# Blind pilot 2 (against hardened R3b / `kw-r3b.pdf`)

## Setup

Fresh background agent (Sonnet, cold), given only `platform/prompt.md` (as
`prompt.txt`) and `artifact/kw-r3b.pdf`, in an isolated scratch directory with
no access to `reference/`, `design/`, or `platform/rubric.md`. One deliberate,
fair hint was included in the task instructions: to check whether different
mechanisms in the packet use different boundary-timing conventions rather than
assuming one applies uniformly (pointing at, without revealing, the S07-vs-S13
distinction) — the same class of hint a careful reader would get from the
packet itself just by reading both sections closely. Evidence copied to
`blind-pilot-2-evidence/`.

## Headline result

All six designs' `(makespan, bill)` pairs are wrong relative to the reference.
Two designs (D0, D2) got the makespan right but the bill wrong; the other four
got both wrong. Consequently all six trace-integrity hashes fail, and the
unrestricted investment selection lands on the wrong design (D5 instead of
D4).

| Design | Reference (makespan, bill) | Agent (makespan, bill) |
|---|---|---|
| D0 | 187, 1331 | 187, 1398 |
| D1 | 161, 1242 | 171, 1313 |
| D2 | 187, 1373 | 187, 1427 |
| D3 | 185, 1408 | 188, 1329 |
| D4 | 151, 1384 | 152, 1465 |
| D5 | 153, 1298 | 152, 1307 |

## Root cause (confirmed by direct code inspection, not assumed)

The agent's own two implementations (primary + independently-architected
verifier) agree with **each other** on all six designs, 0 mismatches, and
both adversarial mutation checks (negative-start, route-collision) were
correctly caught. Self-consistency was total. It was still wrong, because
both implementations share the same bug.

Traced by diffing the agent's `D0_minute_trace.csv` minute-by-minute against
`reference/kilnworks_sim.py`'s own trace for D0. First divergent minute: t=5.

At t=5, lot 0 finishes processing on P and becomes available in `P_buffer`
(a boundary event, handled first in both implementations). Robot 0 (already
parked at P's dock, node 3) correctly picks it up that same minute. In the
**reference**, the pickup mutates the lot's state to `"picked"` synchronously,
inside the same per-robot decision loop — so when Robot 1's turn is decided
immediately afterward (same minute), it no longer sees lot 0 as an available
target anywhere in the plant, and correctly stays put / does something else.

In the **agent's** implementation, Robot 0's and Robot 1's turns are each
computed against a live read of `P_buffer` / `Q_buffer`, but the actual
`buf.remove(lot)` is deferred to a shared `_apply_robot_result` step that
runs only after *both* robots' turns have been decided. Robot 1's decision
function therefore still sees lot 0 sitting in `P_buffer` at the moment it
evaluates "move toward nearest node with a waiting lot" (S05 priority 5), and
sets off toward node 3 to chase a lot Robot 0 is claiming in the very same
minute (`traces/D0_minute_trace.csv`, t=5: `R1_action=move(5->8):toward_lot@3`).

This is a genuine composition bug, not a packet ambiguity: the semantic
contract's collision-handling text ("Robot 0's action for minute t is decided
first, then Robot 1's, using Robot 0's already-chosen action as a same-minute
constraint") already covers this — and the agent *did* correctly implement
the same-minute-constraint propagation for **position** collisions (via an
`other_new_pos` parameter passed into Robot 1's turn), just not for **lot
claims**. It is exactly the kind of two-different-flavors-of-the-same-rule
trap the task is designed to expose: getting the collision-avoidance case
right does not automatically get the resource-claim case right, and the
agent's own extensive self-verification (independent verifier, adversarial
mutation tests) could not catch it, because both implementations share the
identical assumption.

The wasted minutes for Robot 1 change its position and timing for the rest of
the run, which cascades through robot collision outcomes, oven pairing
timing, and Q's cumulative-processing clock for the rest of each design's
187-minute (or so) continuous trace — explaining why every single design ends
up wrong despite every individually-checkable formula (lot generation, design
tuples, tariff, DRAW constants, node-4 fault window, Q-maintenance
threshold/window, oven anchor-deadline arithmetic) being byte-for-byte
correct in the agent's own `kw_constants.py`.

## What this confirms about the hardening

- **The packet itself is not the problem.** Every extractable fact (graph,
  design tuples, lot-generation formulas, tariff formula, DRAW constants,
  S07's inclusive exception, S13's default/non-inclusive convention) was
  independently and correctly recovered and correctly distinguished — the
  agent explicitly reasoned about the two mechanisms' different boundary
  conventions and got both individually right.
- **The difficulty is exactly where it was designed to be**: correctly
  composing many interacting deterministic rules across one long continuous
  trace, where a single same-minute ordering slip (that a generic, careful,
  well-tested implementation can still make) invisibly propagates through the
  rest of the run.
- Self-consistency (agreement between two independently-written
  implementations, adversarial mutation tests) is **not** a reliable proxy
  for correctness here — both of the agent's implementations made the same
  assumption, so cross-checking them caught nothing. This is a stronger
  validation of the task's robustness than a clean pass would have been: the
  "plausible wrong" failure mode that the score-topology audit worried about
  in the abstract just happened for real, unprompted, in a genuinely blind
  run.

## Rubric grading (by direct inspection against `platform/rubric.md`, not the
agent's self-report)

| Bucket | Criteria | Weight available | Weight earned |
|---|---|---:|---:|
| Package | 1-4 | 4 | 4 |
| Local semantics | 5-15 | 15 | 14 (criterion 10 fails — see root cause) |
| Per-design values | 16-27 | 120 | 0 (no design's pair matches) |
| Named witnesses | 28-31 | 12 | 12 (W1/W2/W4/W5 all structurally present despite wrong final numbers) |
| Verification/adversarial | 32-35 | 4 | 4 |
| Trace-integrity hashes | 36-41 | 60 | 0 |
| Decision/causal | 42-47 | 6 | 5 (criterion 43 fails — budget population omits D3, capital=6<=9) |
| Negative trap | 48 | -8 | 0 (no embedded precomputed values) |

**Total: 39 / 221 = 17.6%.**

Notably, criterion 43's failure is a *second*, independent error unrelated to
the dispatch bug: the agent's own selection step used `{D0,D1,D2}` as the
`capital<=9` population, omitting D3 (capital=6), even though it correctly
applied the lexicographic key formula to whichever population it used
(criterion 42's and 43's arithmetic both graded correct on the agent's own
numbers, per the rubric's explicit no-recharging rule). It happened not to
change the winning design (D1 wins outright on makespan), but the rubric
tests population correctness independently of whether it changes the answer.

## Conclusion

17.6% is comfortably under the 30% target, and — unlike the first pilot,
which failed mainly on a packet-completeness gap (missing selection-key
formula) — this failure is entirely attributable to the target task's
intended difficulty. No packet change is indicated. R3b is left as-is
pending an actual target-model (Opus 4.8 Max, maximum effort) pilot, which
has still not been run and remains the real acceptance gate per
`../../Playbook/01-END-TO-END-SOP.md` Phase 10.
