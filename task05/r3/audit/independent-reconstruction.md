# R3 independent reconstruction — two rounds to full convergence

Per the playbook's permanent independent-audit gate (`Playbook/README.md`) and
Phase 4 (`Playbook/01-END-TO-END-SOP.md`), a reviewer technically isolated from the
reference code and goldens must reconstruct the semantics from the visible
specification alone, and every decision-relevant finding must be repaired before
freezing goldens.

## Round 1

A fresh agent (no access to `reference/`, in an isolated git worktree) was given only
the S00-S12 rule prose and asked to implement its own stdlib-only simulator and
report results plus any ambiguity it had to resolve by guessing.

Its results diverged from the reference on 5 of 6 designs (only D0's makespan
matched by coincidence; bills differed everywhere). Its disclosed ambiguity list
(8 items) matched my own implementation's choices on 6 of 8 points. Comparing its
actual code directly (both agents share this session's scratchpad) surfaced one real
bug in the *reference*: `S05`'s nearest-target rule ("move toward the nearest node
holding a waiting prepared lot") was coded as "move toward whichever reachable
target has the lowest next-hop id," not true shortest-distance-then-tie-break. Fixed
in `reference/kilnworks_sim.py` (`bfs_distance_and_next_hop`); did not change any
design's numbers in this instance, but was a genuine source-to-code mismatch.

Two further prose ambiguities were identified and closed in
`design/semantic-contract.md`:

- **Power-gated pool independence (S03):** whether a power-deferred machine still
  removes its candidate lot from the other machine's pool this minute. Resolved:
  it does not — only an actually-started (power-admitted) job claims a lot.
- **Power/collision integration order (S08):** whether power admission is one
  ordered pass integrated with same-minute collision resolution, or two separate
  passes. Resolved: one ordered pass (P start, Q start, Robot 0, Robot 1, oven
  start), each step seeing the previous steps' finalized outcomes.

## Round 2

A second fresh agent, in a new isolated worktree, was given the tightened
specification (round 1's three fixes folded in) and repeated the exercise.

Results still diverged on 5 of 6 designs (D0's makespan matched again; bills and
other designs' makespans did not). Its disclosed ambiguity list this time matched
my implementation on all 5 points it raised — meaning the remaining divergence was
not in anything either of us recognized as ambiguous. Diffing its code directly
(again via the shared scratchpad) against the reference found two further real bugs
in the *reference*, not genuine ambiguity:

1. **Node-capacity accounting on same-minute vacate-and-enter (S05).** The reference
   computed the second-deciding robot's capacity check against the first robot's
   *pre-minute* position, not its *finalized destination* this minute -- contradicting
   the reference's own stated rule ("following into a node vacated that same minute
   is legal") and blocking a legal move. The independent build read the prose
   correctly; the reference code did not implement its own prose. Fixed by tracking
   `robot_final_pos` and checking against it instead of raw `robot_pos` for the
   second-deciding robot.
2. **Oven pairing deadline anchor (S06).** The reference computed a newly-selected
   anchor's deadline from the current decision minute (`t + WAIT_TICKS`), not from
   the lot's actual arrival minute -- so a lot that arrived while the oven was busy
   with an earlier batch got a fresh 2-minute grace period once the oven finally
   freed up, instead of the deadline it should already have been running down while
   it waited. Fixed by storing `Lot.arrival_time` and anchoring the deadline to it.

Both fixes were made directly to `reference/kilnworks_sim.py` and
`design/semantic-contract.md` was tightened to state both rules unambiguously
(explicit vacate-and-enter accounting; explicit "deadline runs even while the oven is
busy" note).

## Result: full convergence

Re-running the reference after both round-2 fixes reproduces the second independent
agent's numbers **exactly** on every reported figure, for all six designs:

| Design | Makespan | Bill | Oven batches | Paired | Mixed-campaign pairs |
|---|---:|---:|---:|---:|---:|
| D0 | 187 | 1331 | 20 | 0 | 0 |
| D1 | 165 | 1294 | 16 | 4 | 2 |
| D2 | 187 | 1447 | 20 | 0 | 0 |
| D3 | 185 | 1401 | 20 | 0 | 0 |
| D4 | 155 | 1413 | 19 | 1 | 1 |
| D5 | 142 | 1290 | 17 | 3 | 1 |

This is the frozen golden table for R3. No further bugs were surfaced by the second
round; the specification is now source-complete in the sense Gate 2 requires (every
material rule traces to visible prose, and an independent implementation built from
that prose alone reproduces the reference exactly).

## What this evidence establishes, and what it does not

- It establishes **fairness**: the visible packet, as written, determines one
  unambiguous grading-equivalence class (Gate 4). A competent solver reading only the
  packet can reach the exact reference trace.
- It does **not** establish frontier difficulty. Both independent builds were
  produced by a capable coding agent working carefully and iteratively from a fully
  specified contract -- exactly the "perfect semantic knowledge" condition the
  perfect-semantics ablation asks about. That the specification is fair and
  reconstructable says nothing about whether Opus 4.8 Max, under the actual prompt
  and packet (denser prose, an image to parse, one shot, no pre-tightened spec, and
  real time/tool-budget pressure), will compose all of S02/S05/S06/S07/S08 correctly
  on a from-scratch attempt. That is exactly what the target-model pilot has to show.
