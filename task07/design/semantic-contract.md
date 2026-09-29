# QUORUM-7 semantic contract

Executable contract for the reference protocol engine. Every rule below
must be visibly recoverable from the packet (diagram, timeline chart, or
stated prose); this file is the internal design source, not the artifact
itself. Supersedes CISTERN-7's semantic contract (kept in git history,
not in this file) after the task07 shape-reuse finding recorded in
`design/architecture-attack.md`.

## S01 — Cluster and tick model

5 nodes, N0 through N4 (node IDs 0-4). Ticks are discrete integer time
units. Each of the 5 named scenarios (S11) is one continuous run of
exactly its own stated tick count, run to completion — never a shortened
or sampled run. There are 3 x 5 = 15 total sweep rows (3 election-timeout
settings x 5 scenarios).

## S02 — Per-node state

Each node maintains:

- `current_term` (int, starts 0) — **persisted** across a crash.
- `voted_for` (node ID or None) — **persisted**; reset to `None` every
  time `current_term` increases.
- `log` (list of entries `(term, cmd_id)`, 1-indexed; index 0 is an
  implicit empty sentinel) — **persisted**.
- `commit_index` (int, starts 0) — **persisted** (a stated simplification
  of the Raft paper's volatile-commit-index-with-majority-recompute rule,
  adopted here to keep crash-recovery unambiguous).
- `role` (FOLLOWER / PRECANDIDATE / CANDIDATE / LEADER) — **volatile**;
  resets to FOLLOWER on crash-recovery.
- `election_elapsed` (ticks since last valid reset) — **volatile**.
- While LEADER only: `next_index[j]`, `match_index[j]` for every other
  node `j` — **volatile**, reinitialized on becoming leader.

## S03 — Election timeout and its reset rule

Each node's own effective election timeout is
`BASE_TIMEOUT + 20 * node_id` ticks, where `BASE_TIMEOUT` is the swept
setting (S12: SHORT=150, MEDIUM=250, LONG=400). This per-node stagger is
fixed and deterministic (not randomized), so every scenario's outcome is
fully reproducible.

`election_elapsed` resets to `0` only when one of these occurs THIS tick:
the node grants a vote to a candidate (S05); the node receives a valid
AppendEntries (S06) from a term `>=` its own `current_term` (adopting
that term and stepping down to FOLLOWER first if it was higher); or the
node itself just began a fresh pre-vote round (S04). It is NOT reset by
receiving or sending a pre-vote message, and a LEADER does not track
`election_elapsed` at all while it remains leader.

## S04 — Pre-vote phase

When `election_elapsed` reaches a FOLLOWER's (or a CANDIDATE's, after a
failed election) own effective timeout: the node becomes PRECANDIDATE
(does NOT increment `current_term` or touch `voted_for` yet), resets
`election_elapsed` to `0`, and sends `PreVoteRequest(term=current_term+1,
last_log_index, last_log_term)` to every other node. A recipient grants
`PreVoteResponse(granted=True)` iff the requester's log is at least as
up-to-date as its own by the SAME log-completeness rule as a real vote
(S05) — regardless of the recipient's own `current_term` or `voted_for`;
granting a pre-vote never mutates `voted_for`. The PRECANDIDATE proceeds
to S05 the instant it has collected grants from a majority (>=3 of 5,
itself included); if its `election_elapsed` reaches the same effective
timeout again first (no majority yet), it stays PRECANDIDATE, resets
`election_elapsed` to `0`, and resends `PreVoteRequest` to every node
(a fresh pre-vote round, still without incrementing `current_term`).

## S05 — Real election (RequestVote)

On winning a pre-vote majority: increment `current_term` by 1, set
`voted_for = self`, become CANDIDATE, reset `election_elapsed` to `0`,
and send `RequestVote(term=current_term, last_log_index, last_log_term)`
to every other node. A recipient grants the vote iff ALL of: (a) the
request's term is `>=` the recipient's own `current_term` (if strictly
greater, the recipient first adopts that term, steps down to FOLLOWER,
and clears `voted_for` before evaluating this vote); (b) the recipient's
`voted_for` is `None` or already equals the requester for this term; (c)
log-completeness: requester's `last_log_term` is greater than the
recipient's own, OR equal AND requester's `last_log_index >=` the
recipient's own. If multiple `RequestVote`s from different candidates
arrive at the same recipient on the same tick, evaluate them in ascending
requester-node-ID order (the recipient can grant at most one; later ones
this term are then rejected by rule (b)). A CANDIDATE that wins a
majority (>=3, itself included) becomes LEADER immediately upon reaching
that majority (does not wait for all 5 responses): it initializes
`next_index[j] = len(own log) + 1` and `match_index[j] = 0` for every
other node `j`, and immediately sends an AppendEntries round (S06). A
CANDIDATE (or PRECANDIDATE) that receives an AppendEntries with term `>=`
its own steps down to FOLLOWER, adopting that term if higher. A CANDIDATE
whose `election_elapsed` reaches its effective timeout again without
winning (split vote) returns to S04 (a fresh pre-vote round; `current_term`
is not incremented again until a pre-vote succeeds).

## S06 — Log replication (bounded-batch AppendEntries)

LEADER only. For each other node `j`, the leader sends an AppendEntries
round to `j` every `HEARTBEAT_INTERVAL=10` ticks, or immediately after a
new command is appended to the leader's own log (S08), whichever is
sooner. The message carries `prevLogIndex = next_index[j] - 1`,
`prevLogTerm` (the leader's own log's term at that index, or `0` if
`prevLogIndex == 0`), up to `K=4` entries starting at `next_index[j]`
(bounded batch — a lagging follower needs multiple rounds to catch up),
and `leaderCommit = ` the leader's own `commit_index`.

A follower rejects (`success=False`) iff `prevLogIndex > 0` and either it
has no entry at `prevLogIndex` or that entry's term differs from
`prevLogTerm`. On rejection, the leader sets
`next_index[j] = max(1, next_index[j] - 1)` and retries on the next
round (linear backoff; no conflict-term optimization in this protocol).
On acceptance, the follower TRUNCATES any existing entry (and everything
after it) at an index the incoming batch also covers if that existing
entry's term differs from the incoming one, then appends the batch's
entries; if `leaderCommit >` its own `commit_index`, it advances its own
`commit_index` to `min(leaderCommit,` the index of the last entry it just
appended-or-already-matched`)`. It responds `success=True` with
`matchIndex = prevLogIndex + `(entries in this batch). The leader then
sets `match_index[j] = ` that `matchIndex` and `next_index[j] =
matchIndex + 1`.

## S07 — Commit-index advancement (leader)

The leader advances its own `commit_index` to the highest index `N` such
that a majority of nodes (>=3, itself included) have `match_index[j] >=
N` (the leader always counts as matching its own log), **AND** the log
entry at index `N` has `term ==` the leader's own CURRENT `current_term`.
A leader must never advance `commit_index` to an index whose entry is
from an earlier term merely because a majority already has it — that
entry only becomes committed indirectly, once a same-term entry after it
is committed by this rule. This is the protocol's single most commonly
mis-implemented rule.

## S08 — Client commands

A fixed, packet-stated schedule of `(tick, command_id)` submissions.
At the stated tick, the command is broadcast to all 5 nodes
simultaneously; any node that is LEADER at that exact tick appends
`(current_term, command_id)` to its own log and immediately triggers an
AppendEntries round (S06); every other node ignores the submission (no
queueing, no forwarding, no retry).

## S09 — Network model (deterministic, scripted)

Every message sent at tick `T` is delivered at `T + BASE_DELAY` (fixed,
`BASE_DELAY=2`) unless the active scenario's script states an override
for that message class/pair/window: `DELAY(extra ticks)`, `DROP` (never
delivered), or `DUPLICATE(offset)` (delivered a second time `offset`
ticks after the first delivery). A scripted **partition** window naming a
tick range and a 2-way split of the 5 nodes means every message between
nodes on opposite sides is DROPPED for that whole window, regardless of
any other per-message override; messages between nodes on the same side
are unaffected. A scripted **crash** window for one node means that node
processes no incoming message and sends none for that whole window (as if
powered off); its persisted state (S02) is exactly as it was at the crash
tick. On recovery (the window's end), it resumes as FOLLOWER with
`election_elapsed` starting fresh at `0`, using its persisted state
exactly as it was.

## S10 — Independent verification (safety invariants + certificate)

A separately-coded verifier, sharing only immutable input constants with
the primary implementation, must independently re-derive each scenario's
full 5-node state trace (or check a complete feasibility certificate) and
confirm, for every scenario and every timeout setting: **election
safety** (no two nodes are LEADER for the same `current_term`
simultaneously); **log matching** (if two nodes' logs both contain an
entry at the same index with the same term, every entry at every earlier
index in both logs is identical); **leader completeness** (once an entry
is committed by any node, every node that later becomes leader has that
entry in its own log at that index). Two required adversarial mutations:
a vote granted to a candidate whose term is BELOW the recipient's own
`current_term` (a stale-term vote, violating election safety indirectly)
and a leader overwriting an already-committed log entry with a different
one (violating log matching / leader completeness) — the verifier must
reject both while still accepting the true original.

## S11 — The 5 named scenarios (each one continuous run, no resampling)

Exact fault-window tick numbers are generated from the stated formulas
below and confirmed against real executed output before being frozen
into the rubric (never hand-derived) — see `reference/quorum_sim.py`.

1. **CLEAN** (2,400 ticks): no scripted faults; `BASE_DELAY=2`
   throughout. Commands at ticks 300, 600, 900, 1200, 1500.
2. **PARTITION** (2,400 ticks): `{N0,N1,N2}` vs `{N3,N4}` for a stated
   400-tick window starting once a stable leader has been observed for
   at least 200 ticks in the CLEAN scenario's own trace (a real,
   trace-derived tick, not assumed); commands both before, during, and
   after the window.
3. **CRASH-RECOVER** (2,400 ticks): the CLEAN scenario's own first
   elected leader is crashed for a stated 300-tick window once it has
   held leadership for at least 200 ticks; commands before, during
   (routed to whichever node becomes the new leader), and after recovery.
4. **MESSAGE-LOSS** (2,400 ticks): elevated scripted `DROP`/`DUPLICATE`
   overrides on specific message classes between specific node pairs
   over a stated window, chosen to stress AppendEntries and vote
   messages without partitioning any node entirely.
5. **COMPETING-CANDIDATES** (2,400 ticks): a 2-node minority (`{N2,N3}`)
   is partitioned away from the 3-node majority for a stated long window,
   long enough that both isolated nodes independently exceed their own
   effective timeout and repeatedly attempt pre-vote rounds against each
   other alone — since 2 of 5 can never reach the 3-node pre-vote
   majority (S04), neither may ever increment its `current_term` or hold
   an election while isolated: this is the pre-vote phase's whole
   purpose, preventing a partitioned minority from inflating its term and
   disrupting the majority once the partition heals. The majority side
   keeps its existing leader (or elects a new one) undisturbed throughout.

## S12 — Sweep dimension and selections

`election_timeout_setting` in `{SHORT, MEDIUM, LONG}` (S03) x the 5
named scenarios = 15 sweep rows, each one continuous run to completion.
A setting is FEASIBLE only if it violates none of the three safety
invariants (S10) in any of its 5 scenario runs. Among feasible settings:

1. **Recovery-optimal**: minimizes the tick-count from the
   CRASH_RECOVER scenario's own crash-window start to the tick a new
   node establishes LEADER for a higher term (the direct
   leader-loss-to-new-leader latency; PARTITION never loses its leader,
   since only the 2-node minority is isolated, so it is not part of this
   metric — see S11).
2. **Overhead-optimal**: minimizes total message count (all message
   classes, all 5 scenarios combined).

These two need not agree.
