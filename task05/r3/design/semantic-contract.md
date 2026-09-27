# KILNWORKS R3 — visible semantic contract

This is the executable constitution. Every material branch in `reference/kilnworks_sim.py`
must trace to a row here, and every row here must be visible in the packet (not private
intent). Reused-from-R2 rows are marked `[R2]`; new/changed rows are marked `[NEW]`.

## S00 — Designs `[R2, reused]`

Six retrofit designs, each an input tuple `(F, G, aisle, capital)`:

| Design | F | G | aisle | capital |
|---|---:|---:|---|---:|
| D0 | 2 | 5 | closed | 0 |
| D1 | 3 | 5 | closed | 7 |
| D2 | 2 | 6 | closed | 9 |
| D3 | 2 | 5 | open | 6 |
| D4 | 3 | 6 | closed | 16 |
| D5 | 3 | 6 | open | 22 |

`F` = fixture ceiling. `G` = aggregate power ceiling. `aisle=open` adds edge 4-5.
`capital` = investment cost used only in the selection key, never in simulation.

## S01 — Aisle graph `[R2, reused]`

Nodes `0..8` with `node = 3y + x`. Solid undirected edges (closed designs):
`{0-3, 3-6, 3-4, 4-7, 6-7, 7-8, 5-8, 2-5, 1-4}`. Open designs (D3, D5) add `4-5`.
Docking bays (capacity 2): `P=3, Q=5, K=1`. All other nodes are interior (capacity 1).
Because node 1 (`K`) has only the edge `1-4` in both topologies, **every delivery to
the oven dock must pass through node 4** regardless of aisle configuration — this
structural fact is what the R3 fault mechanism (S07) exploits, and it is unaffected by
the open/closed retrofit choice.

## S02 — Lot generation `[R2 formulas, R3 release semantics changed]`

For campaign `s=0..3`, lot `j=0..4`:

- `family(j,s) = (j+s) % 2`
- `release_local(j) = 2 * floor(j/2)`
- `Pbase(j,s) = 5 + (j*j + 2s) % 4` (duration if processed on P)
- `Qbase(j,s) = 4 + (3j + s) % 5` (duration if processed on Q)

`[NEW]` **Absolute release** (replaces R2's independent per-case reset):
`release_abs(j,s) = s * CADENCE + release_local(j)`, with `CADENCE = 35` minutes, fixed
per design. Campaign `s+1`'s lots begin releasing at `35*(s+1)` regardless of whether
campaign `s`'s lots have finished. A design's continuous run therefore contains all
`20` lots (`5 lots x 4 campaigns`) sharing one clock, one fixture pool, one pair of
machine setup-memory states, one robot pair, and one oven, from `t=0` until the last
lot of campaign 3 finishes curing.

## S03 — Preparation and machine assignment `[R2 rules reused, R3 policy added]`

`[R2]` Each lot is prepared exactly once, on P or Q, in one uninterrupted
setup-plus-processing operation. Setup: machine family memory starts unset; setup
duration is `0` if this is the machine's first job or the job's family matches the
machine's last-processed family, else `2`. Processing duration is `Pbase`/`Qbase` for
the chosen machine. The machine frees on completion; prepared output waits in an
unlimited buffer at the machine's dock node until picked up.

`[NEW]` Setup memory is **not reset between campaigns** — it persists for the whole
continuous design run (previously R2 reset it per independent case).

`[NEW]` **Deterministic assignment policy** (removes R2's free "assign to P or Q"
choice). At each minute `t`, evaluate `P` first, then `Q`:

1. If the machine is not idle, skip it this minute.
2. Build the eligible pool: lots with `release_abs <= t`, not yet assigned, and for
   which a fixture is currently available (`current fixture holdings < F`; see S05).
3. If the pool is empty, the machine stays idle this minute.
4. Otherwise select the lot minimizing `(setup + duration on this machine)`, tie-break
   by lowest global index `s*5 + j`. Assign it, occupying the machine for
   `setup + duration` minutes starting at `t`.

`P`'s assignment is resolved before `Q`'s in the same minute. The power-budget gate
(S08) is checked *before* a machine selects a lot from its pool, not after: if `P`
cannot currently afford to start anything, it claims nothing and leaves `Q`'s pool
unchanged; only an actually-started `P` job removes that lot from `Q`'s pool this
minute. A fixture is counted as held only from an actually-started (power-admitted)
preparation, never from a merely-selected-but-deferred candidate.

## S04 — Fixture conservation `[R2, reused]`

A lot holds exactly one fixture continuously from the **start of its preparation**
through waiting, transport, and curing, releasing it only at cure completion. Total
fixture holdings must never exceed `F` at any minute. This is enforced structurally by
S03 step 2 (a machine cannot start a lot without an available fixture) rather than as
a separate late check.

## S05 — Robot mechanics `[R2 rules reused, R3 collision/dispatch policy added]`

`[R2]` Two robots with fixed identities: Robot 0 starts empty at node 3 (`P`), Robot 1
starts empty at node 5 (`Q`), once at the start of the continuous run (not reset per
campaign). Each minute, each robot executes exactly one action: wait, move along one
adjacent drawn edge, pickup, or unload. Pickup/unload/wait keep the robot at its
current node; empty repositioning is allowed. Cargo capacity is 1; duplicate pickup is
forbidden. A pickup action at minute `t` becomes visible cargo at `t+1`; an unload
action at minute `t` (only legal at node `K`) makes the lot available for curing at
`t+1`. Each undirected edge carries at most one robot traversal per minute (no swaps,
no same-direction sharing); boundary/interior node capacity is 1 except `P/Q/K`
capacity 2; following into a node vacated that same minute is legal.

`[NEW]` **Deterministic dispatch/routing policy** (removes R2's free "optimize
routing" choice). Robot 0's action for minute `t` is decided first, then Robot 1's,
using Robot 0's already-chosen action as a same-minute constraint. For each robot, in
this order, first applicable rule wins:

1. If the robot is inside its fault-offline window (S07), it takes no action (forced
   wait in place, cargo/position frozen).
2. If carrying cargo and at node `K`: unload.
3. If empty and at least one prepared-but-unpicked lot is available at the robot's
   current node: pick up the eligible lot with the earliest preparation-completion
   time, tie-break by lowest global lot index.
4. If carrying cargo (and not at `K`): move one step along a shortest path (by edge
   count, ties broken by lowest next-hop node id, both computed on the static edge
   set for this design's aisle configuration) toward `K`. If the required edge is
   already reserved this minute by the other robot, or the destination node's
   capacity is already full this minute, or the move would be a same-edge swap with
   the other robot, take `wait` instead.
5. If empty and no lot is available at the current node: among all nodes currently
   holding at least one prepared-but-unpicked lot, move one step toward the one at
   the shortest edge-count distance (tie-break by lowest **target node id**, then
   execute that target's own shortest-path next hop, itself tie-broken by lowest
   next-hop node id), applying the same same-minute collision check as step 4.
6. If empty and no lot is available anywhere in the plant right now: move one step
   (same rule) toward the robot's home dock (node 3 for Robot 0, node 5 for Robot 1).
   If already at its home dock, wait. This keeps an idle robot from parking
   indefinitely on the shared junction (node 4) and blocking the other robot's only
   route to `K`.

There is no path replanning within a minute beyond the single collision check in
steps 4-5; a blocked robot simply waits that minute and re-evaluates next minute.

## S06 — Oven and same-family batching `[R2 rule reused, R3 policy resolved]`

`[R2]` The oven holds one batch at a time; a batch is fixed at start (membership never
changes) and cures for `4 + family` minutes, after which all members finish together.
Curing lots come from any campaign (S02); the family attribute alone determines
eligibility, so a batch may legitimately mix lots from two different campaigns when
their arrivals overlap under S02's cadence.

`[NEW]` **Deterministic start policy with a bounded pairing timer** (removes R2's
implicit "select one or two" choice, and gives cross-campaign pairing a real chance to
occur under S02's overlapping cadence). When the oven is idle and has no pending
anchor, the earliest-arrived uncured lot (tie-break lowest global index) becomes the
pending anchor with deadline `arrival_time + WAIT_TICKS` (`WAIT_TICKS = 2`), where
`arrival_time` is the lot's own actual arrival minute (when its unload action took
effect) -- **not** the minute it happens to be picked up as anchor. If the oven was
busy curing an earlier batch when this lot arrived, its deadline clock was already
running during that busy period; the deadline may therefore already be in the past
the instant the oven becomes idle and picks this lot as anchor, in which case it
starts alone on the very next evaluation rather than waiting `WAIT_TICKS` more
minutes. Each subsequent minute while a pending anchor exists and the oven is still
idle:

1. if another already-arrived, uncured, same-family lot exists, start the batch now
   with the anchor and that partner (tie-break lowest global index among candidates);
2. else if `t >= deadline`, start the batch now with the anchor alone;
3. otherwise keep waiting (no start this minute).

A pending anchor, once chosen, is never replaced by a later-arriving lot before its
own start. The oven never waits past its own deadline, and never pairs across more
than one partner (batches are exactly 1 or 2 members).

## S07 — Node-4 fault `[NEW]`

The first minute at which Robot 0 occupies node 4 for any reason (arrival via a move;
this is necessarily its first visit, since it starts at node 3), Robot 0 immediately
goes offline for that minute and the next `W - 1` minutes (`W = 6` minutes total,
counting the arrival minute itself): it can take no action for any of those `W`
minutes (S05 rule 1: forced wait, position and cargo frozen at node 4). Normal
one-action-per-minute dispatch (S05) resumes at the first minute after the window
ends (the `W+1`-th minute counting from arrival). Because node 4 has capacity 1 and is the sole approach to `K` in both aisle
configurations (S01), **no robot can reach or pass through node 4 while Robot 0 is
offline there** — every delivery to the oven is blocked for the whole window,
regardless of design. This mechanism triggers exactly once per design's continuous
run (Robot 0 does not return to node 4 needing a second trigger; the fault fires only
on the first occupancy).

## S08 — Aggregate power `[R2, reused; R3 admission order made explicit]`

Every minute, across ongoing operations and all new starts/actions: `P=2`, `Q=3`,
`oven=3`, each robot `move/pickup/unload=1`, `wait=0`; the setup phase of a
preparation draws the same full power as its machine's processing. Total power drawn
in any minute must never exceed the design's `G`. Idle resources draw zero.

`[NEW]` **Admission is one ordered pass, integrated with collision resolution, not
two separate passes.** Already-ongoing operations from a strictly earlier minute are
mandatory and always keep their power (they were already admitted when they started).
New admissions this minute draw from what remains, strictly in this order: machine
`P` start, machine `Q` start, Robot 0's action, Robot 1's action, new oven start.
Each robot's action is finalized — including whether the power budget admits it — in
this same order before the next robot's turn: **Robot 1's same-minute collision
avoidance (S05 step 4-5) is evaluated against Robot 0's fully finalized action**
(after Robot 0's own power check), not against a power-unaware first pass. A robot
whose intended move/pickup/unload is refused for lack of power is downgraded to
`wait` for that minute only (its edge/destination reservation is released, so it does
not block Robot 1 from using it).

## S09 — Timing convention `[R2, reused]`

Operations complete at boundary `t` before simultaneous new starts/actions occupying
`[t, t+1)`; a duration-`d` operation occupies `[t, t+d)`. Starts use resources
released at `t`. The whole design run shares one clock from `t=0`.

## S10 — Objective and selection `[R2 formula reused, R3 scope changed]`

`[NEW]` Per design (not per campaign — R2's four independent per-campaign profiles
are replaced by one end-to-end value per design, since the four campaigns are now one
continuous run): `makespan` = the final cure-completion boundary across all 20 lots.
`bill = sum over t=0..makespan-1 of (total minute power) * (1 + (floor(t/7) % 3))`.

`[R2]` Lexicographic selection key per design: `(makespan, bill + 3*capital, capital,
ID)`, minimized. Two populations: unrestricted (all six designs) and `capital <= 9`
(`D0, D1, D2, D3`, including the `D2` boundary at equality).

## S11 — Independent verification `[R2 requirement reused, R3 target changed]`

`[NEW]` Because there is no free optimization decision left (S03-S07 are fully
deterministic), the independent-verification obligation is **exact reproduction**: a
separately-coded second implementation, sharing only immutable input constants with
the primary, must re-derive the entire minute-by-minute trace for all six designs and
agree with the primary exactly. This replaces R2's "independently prove global
optimality" framing (criteria 30-31), which is what invited a generic combinatorial
solver in the first place — there is no optimum to prove here, only a specified
function to execute correctly twice.

## S12 — Adversarial/mutation obligations `[R2 reused]`

Same two experiments as R2, replayed against the R3 system: (a) a copied schedule
with its earliest preparation start changed to `-1` must be rejected by the verifier
while the original is accepted; (b) a copied route mutation causing an edge or
interior-node conflict must be rejected, with the first invalid minute identified,
while the original is accepted.
