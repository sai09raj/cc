## Analyze

```text
Read the packet and reconstruct the per-node role state machine
(FOLLOWER, PRECANDIDATE, CANDIDATE, LEADER), the pre-vote gate that a
node must clear (winning a non-binding majority of pre-votes) before any
real election is allowed to increment current_term, the per-node
election-timeout stagger (effective timeout = BASE_TIMEOUT + 20*node_id,
measured off the labeled chart for each of the three swept BASE_TIMEOUT
settings), the bounded-batch AppendEntries mechanism (K=4 entries per
round, independent next_index/match_index tracking per follower -- a
leader that resends from a fixed starting index instead is the packet's
most common failure mode), and the current-term-only commit-index
advancement rule (an earlier-term entry a majority already holds is never
committed directly; it only becomes committed indirectly once a
same-term entry after it is committed). Recover the 5 named fault
scenarios and their scripted windows (partition splits, a crash window,
targeted message-loss overrides), each expressed relative to a run-time-
derived anchor tick, not a literal number printed in the packet. Treat
the 3x5=15-row sweep as one genuine multi-objective search: a shorter
election timeout speeds crash recovery but raises message overhead from
more frequent election attempts, so the recovery-optimal and
overhead-optimal selections are not guaranteed to agree and must each be
found by executing the full legal space, not assumed from one run.
```

## Execute & Generate

```text
Implement a deterministic, offline, tick-by-tick protocol engine
executing the packet's pre-vote/election/replication/commit rules exactly
-- for each of the 3 election-timeout settings, one continuous 2400-tick
run per each of the 5 named scenarios (15 rows total), all feeding the
same two selection objectives. Build a separately-coded verifier that
independently re-derives the 5-node state trace (or checks a complete
feasibility certificate) and confirms, for every one of the 15 runs:
election safety (no two nodes LEADER for the same current_term
simultaneously), log matching (agreement at one index implies agreement
at every earlier index), and leader completeness (a committed entry
survives, unchanged, in every future leader's log at that index), sharing
only immutable input constants with the primary implementation. Run the
two required adversarial mutations -- a vote granted to a candidate whose
term is below the recipient's own current_term, and a leader overwriting
an already-committed log entry with a different one -- against a
preserved original and confirm the verifier rejects both while accepting
the original. Deliver protocol-engine source, verifier source, the
complete 15-row sweep table, a decision file with both selections and
their agreement/divergence disclosure, certification evidence (the
baseline (MEDIUM, PARTITION) configuration's full trace plus its stated
SHA-256 trace-integrity hash, computed by the algorithm the packet
specifies), and a memo. Equivalent languages, source organization, output
schemas, and physically valid tie-broken orderings all pass; only one
protocol-conformant trace per (election_timeout, scenario) combination
exists.
```

## Synthesize

```text
Using the 15 executed sweep rows, apply the two selection definitions
(recovery-optimal: minimizes CRASH_RECOVER's own crash-window-start to
new-higher-term-leader latency; overhead-optimal: minimizes total message
count across all 5 scenarios combined) and report both, explicitly noting
whether they agree. Explain, using actual event times from your delivered
baseline trace, why a shorter election timeout detects a crashed leader
and elects a replacement sooner, but costs more messages overall from
more frequent pre-vote/election rounds across all 5 scenarios. Cite the
COMPETING_CANDIDATES witness from your own trace and explain why the
pre-vote phase specifically prevents the isolated 2-node minority from
ever incrementing current_term while cut off, and why that matters once
the partition heals (a partitioned minority that could freely increment
its term would otherwise force the healed majority through needless
re-elections). Explain why per-follower next_index/match_index tracking
is required for correct bounded-batch replication, and why commit-index
advancement must require a same-current-term entry rather than trusting
majority replication of an earlier-term entry alone. Reconcile your
sweep, selections, verifier agreement, and baseline witnesses against the
same underlying protocol rules. Any accurate, evidence-tied causal
argument is acceptable; no particular sweep row beyond the two selections
and the stated baseline is required.
```
