# QUORUM-7 rubric

Positive total **197**; six negative criteria totaling **-37** (**-4**,
**-10**, **-4**, **-10**, **-4**, **-5**), plus a negative trap **-8**.
**43 criteria** (within the platform's 12-50 range; not padded --
coverage was complete at 43). Every weight is capped at 10. Every
criterion body is 301 characters or fewer. Criteria are binary. Accept
equivalent correct work throughout: equivalent languages, source
organization, output schemas, file layout, and formula notation.

Every prohibition below (skipping pre-vote, using the wrong quorum size,
ignoring per-follower replication tracking, committing an entry from a
prior term) was given its own dedicated negative criterion from this
rubric's first draft, not added round-by-round after a linter finding --
matching the lesson recorded in `Playbook/07-MISTAKE-REGISTER.md` #59.

### Package (1-2, weight 3)

| # | Wt | Criterion |
| --- | --- | --- |
| 1 | +2 | Executes the delivered offline protocol engine with a documented, reproducible command, records actual tool versions in a declared offline, stdlib-only environment, includes the memo's layout interpretation of the packet's diagrams, and delivers all six named products as files. |
| 2 | +1 | The delivered sweep table contains exactly 15 rows (3 election-timeout settings x 5 named scenarios), no duplicate, no missing combination. |

### Local semantics/rules/scaffolding (3-12, weight 30)

| # | Wt | Criterion |
| --- | --- | --- |
| 3 | +2 | A node reaching its own effective election timeout becomes PRECANDIDATE and requests pre-votes; it only becomes CANDIDATE (incrementing `current_term`) after winning a majority of pre-votes, never directly on timeout. |
| 4 | +2 | Resets `election_elapsed` to 0 only on granting a vote, receiving a valid AppendEntries at term >= its own, or starting a fresh pre-vote round -- never merely from receiving any other message. |
| 5 | +3 | Grants a real vote only when the requester's term is >= its own, `voted_for` allows it, AND the requester's log is at least as up-to-date (by the stated term-then-index rule); resolves same-tick concurrent requests in ascending requester-ID order. |
| 6 | +6 | Uses exactly a 3-of-5 majority (itself included) for pre-vote success, real-election success, and leader commit-index advancement -- the same threshold in all three places. |
| 7 | +6 | A leader tracks `next_index`/`match_index` independently per follower and sends at most `K=4` log entries per AppendEntries round, requiring multiple rounds to catch up a far-behind follower. |
| 8 | +3 | A leader advances `commit_index` to index N only when a majority has `match_index >= N` AND the entry at N is from the leader's own current term -- never for an earlier-term entry merely because a majority already has it. |
| 9 | +2 | A crashed node's `current_term`, `voted_for`, `log`, and `commit_index` are exactly as they were at the crash tick on recovery; its `role` and timers reset to FOLLOWER/0. |
| 10 | +2 | A scripted partition window drops every message between nodes on opposite sides for its whole duration, regardless of any other per-message override; a scripted crash window means the node sends and processes nothing at all. |
| 11 | +2 | A client command is broadcast to all 5 nodes at its stated tick; only the node that is LEADER at that exact tick appends it to its own log, and every other node ignores it (no queueing, no forwarding). |
| 12 | +2 | A leader sends an AppendEntries round to each follower every `HEARTBEAT_INTERVAL=10` ticks, or immediately after appending a new command, whichever is sooner. |

### Integrated production execution — 15-run sweep (13-18, weight 23)

| # | Wt | Criterion |
| --- | --- | --- |
| 13 | +3 | Reports the recovery-optimal timeout setting as `SHORT`, with a CRASH_RECOVER new-leader latency of `172` ticks (±2) from the crash-window start. |
| 14 | +3 | Reports the overhead-optimal timeout setting as `LONG`, with a combined 5-scenario message count of `7355` (±20). |
| 15 | +1 | Reports explicitly whether the two selections in criteria 13-14 agree or diverge; this packet's reference has them diverge — the criterion tests the disclosure, not agreement itself. |
| 16 | +6 | Reports the `(SHORT, PARTITION)` row's own final state as `max_commit_index=5, max_term=1, leader=N0, message_count=1660` (±10). |
| 17 | +6 | Reports the `(MEDIUM, CLEAN)` row's own final state as `max_commit_index=5, max_term=1, leader=N0, message_count=1736` (±10). |
| 18 | +6 | Reports the `(MEDIUM, MESSAGE_LOSS)` row's own final state as `max_commit_index=5, max_term=1, leader=N0, message_count=1704` (±10). |

### Whole-sweep aggregate totals (19-28, weight 100)

Each total sums one or two metrics across a stated subset of the 15-run
sweep. Report to the stated tolerance. Each of these 10 facts is wrong
under every plausible-wrong mutant tested — the rubric's main
discriminating bloc.

| # | Wt | Criterion |
| --- | --- | --- |
| 19 | +10 | Reports the sum of message counts across all 15 runs as `24027` (±50). |
| 20 | +10 | Reports the sum of each run's own max final `commit_index` across all 15 runs as `67` (±1). |
| 21 | +10 | Summed over only `election_timeout=SHORT` (5 runs): message counts total `8573` (±20), commit-index sums total `24` (±1). |
| 22 | +10 | Summed over only `election_timeout=LONG` (5 runs): message counts total `7355` (±20), commit-index sums total `19` (±1). |
| 23 | +10 | Summed over only `election_timeout=SHORT` AND `scenario` in `{PARTITION, COMPETING_CANDIDATES}` (2 runs): message counts total `3284` (±20), commit-index sums total `10` (±1). |
| 24 | +10 | Summed over only the `PARTITION` scenario (3 runs): message counts total `4692` (±20), commit-index sums total `14` (±1). |
| 25 | +10 | Summed over only `election_timeout=MEDIUM` AND `scenario` in `{PARTITION, COMPETING_CANDIDATES}` (2 runs): message counts total `3120` (±20), commit-index sums total `10` (±1). |
| 26 | +10 | Summed over only the `MESSAGE_LOSS` scenario (3 runs): message counts total `5063` (±20), commit-index sums total `14` (±1). |
| 27 | +10 | Summed over only the `COMPETING_CANDIDATES` scenario (3 runs): message counts total `4580` (±20), commit-index sums total `14` (±1). |
| 28 | +10 | Summed over only `election_timeout=MEDIUM` (5 runs): message counts total `8099` (±20), commit-index sums total `24` (±1). |

### Production witnesses from the baseline trace (29-33, weight 26)

Baseline configuration for the hash and for witnesses 30 and 32:
`(election_timeout=MEDIUM, scenario=PARTITION)`. Witnesses 29 and 31 name
their own scenario explicitly, since each depends on a fault type the
baseline scenario does not contain.

| # | Wt | Criterion |
| --- | --- | --- |
| 29 | +4 | In the `CRASH_RECOVER` scenario at this same timeout setting, shows the leader (N0) crashing at `t=457`, and a new node (N1) establishing LEADER for a higher term at exactly `t=729` (272 ticks later). |
| 30 | +4 | Shows no tick anywhere in the baseline run where two nodes are simultaneously LEADER for the same term. |
| 31 | +6 | In the `COMPETING_CANDIDATES` scenario at this same timeout setting, shows the isolated pair `{N2,N3}` remaining at `current_term=1` (unchanged) for the entire ~500-tick isolation window, never electing a leader between themselves. |
| 32 | +2 | Shows the baseline's final delivered log identical across all 5 nodes, at `commit_index=5`. |
| 33 | +10 | Matches the first 16 hex characters of the baseline's canonical trace-integrity hash (algorithm in the packet) to `3243b745aaf9e7e2`. |

### Independent verification and decision/causal reconciliation (34-36, weight 13)

| # | Wt | Criterion |
| --- | --- | --- |
| 34 | +3 | Delivers a separately-coded verifier, sharing only immutable input constants, that independently re-derives the 5-node state trace or checks a feasibility certificate, rejects both adversarial mutations with the original preserved and accepted, and reports this evidence in the memo. |
| 35 | +8 | Explains, citing the baseline trace's own numbers, why the recovery-optimal and overhead-optimal timeout settings diverge, AND explains why a shorter timeout speeds crash recovery but raises message overhead from more frequent election attempts. |
| 36 | +2 | Explains in the memo, tied to the COMPETING_CANDIDATES witness (criterion 31), why the pre-vote phase prevents a partitioned minority from inflating its term and disrupting the majority once the partition heals. |

### Negative criteria — protocol-correctness prohibitions (37-40)

| # | Wt | Criterion |
| --- | --- | --- |
| 37 | −4 | Increments `current_term` and requests real votes directly on election timeout, skipping the pre-vote phase entirely. |
| 38 | −10 | Uses a majority threshold other than 3-of-5 for pre-vote success, real-election success, or leader commit-index advancement, in any of the three. |
| 39 | −4 | Advances `commit_index` for a log entry from an earlier term merely because a majority already has it, without requiring a same-current-term entry to be committed first. |
| 40 | −10 | Resends AppendEntries from a fixed starting index instead of tracking each follower's own `next_index`/`match_index` independently, silently stalling commit progress past the first batch window. |

### Negative criteria — architecture and execution prohibitions (41-42)

| # | Wt | Criterion |
| --- | --- | --- |
| 41 | −4 | Delivers a verifier that shares anything beyond immutable input constants with the primary implementation (importing or wrapping its internal state, classes, or in-memory objects) rather than independently re-deriving the state trace or certificate. |
| 42 | −5 | Runs any of the 15 legal (timeout, scenario) combinations as a shortened, truncated, or sampled subset of its own scenario length, rather than one continuous run to completion. |

### Negative trap (43)

| # | Wt | Criterion |
| --- | --- | --- |
| 43 | −8 | Embeds precomputed sweep rows, selection values, or the trace-integrity hash as literals substituting for executing the delivered protocol engine. Immutable input constants don't trigger this; omission alone doesn't either. |
