# QUORUM-7 — Engineering memo

Every number below was copied from files the code wrote under `out/`. None was worked out by hand. Run `bash run_all.sh` to regenerate all of them.

## 0. Deliverables and reproduction

| # | Deliverable | File(s) |
|---|---|---|
| 1 | Protocol engine source (Python) | `engine/quorum7_engine.py` (plus helpers `engine/analyze_tradeoff.py` and `engine/make_reports.py`) |
| 2 | Independent verifier source (JavaScript/Node) | `verifier/quorum7_verify.js` |
| 3 | Complete 15-row sweep table | `out/sweep_table.csv`, `out/sweep_table.json`, `out/sweep_table.md` |
| 4 | Decision file (both selections and whether they agree) | `out/decision.json` (engine-only version: `out/decision_engine.json`) |
| 5 | Certification evidence | `out/baseline_trace_MEDIUM_PARTITION.txt` (the exact bytes that are hashed), `out/baseline_certificate.json`, `out/certification_evidence.json`, `out/verifier_report.json`, `out/certificates/*.json.gz` (per-tick snapshots and event log for all 15 runs) |
| 6 | This memo | `MEMO.md` |
| – | Shared immutable inputs (the only thing the engine and verifier share) | `constants.json` |
| – | Sensitivity runs and a no-pre-vote counterfactual | `sensitivity.sh` → `out/sensitivity.txt`; `out_keep/counterfactual_no_prevote/` |

Commands (run from `work/`):
```
bash run_all.sh                                      # does everything below
python3 engine/quorum7_engine.py --out out           # 15 runs, sweep table, certificates, baseline trace and hash
python3 engine/analyze_tradeoff.py out               # facts this memo cites
node verifier/quorum7_verify.js --engine-out out     # independent re-derivation and mutations; exit code 0 = all pass
python3 engine/make_reports.py out                   # decision.json, certification_evidence.json, sweep_table.md
bash sensitivity.sh                                  # alternative readings of the packet's gaps
```
Tool versions: Python 3.11.15 (standard library only; PyMuPDF 1.28.2 and Pillow/numpy were used only to read the PDF and measure the figures) and Node v22.22.2 (built-in modules only). A full run takes about 6 seconds.

## 1. Layout interpretation (what was read from where)

* **Fig. 1 (state machine).** States are F, P, C and L. The edges are:
  * (1) F→P when the node's own timeout elapses.
  * (2) P→P when the timeout elapses again: a fresh pre-vote round with the term unchanged.
  * (3) P→C on a pre-vote majority of at least 3/5: increment the term, vote for self, request votes.
  * (4) C→P on a split vote followed by a timeout: the term is unchanged.
  * (5) C→L on a real-vote majority of at least 3/5.
  * (6) L→F on an AppendEntries or vote request at a term ≥ own.
  * (7) C→F on an AppendEntries at a term ≥ own.
  * (8) P→F on an AppendEntries at a term ≥ own.
* **Fig. 2 (bounded batch).** K=4 entries per round. A rejection sets next_index −= 1. An acceptance sets match = reported matchIndex and next = match+1. A lagging follower needs several rounds to catch up.
* **Fig. 3 (stagger).** I measured the bar labels. Effective timeouts are SHORT 150/170/190/210/230, MEDIUM 250/270/290/310/330 and LONG 400/420/440/460/480 for N0..N4. These match BASE + 20·id.
* **Fig. 4 (fault windows).** All offsets are relative to the anchor, which is CLEAN's own first stable-leader tick for the same setting:
  * PARTITION: anchor+200..+600, {N0,N1,N2} vs {N3,N4}, 400 ticks.
  * CRASH_RECOVER: anchor+200..+500, CLEAN's first leader is crashed, 300 ticks.
  * MESSAGE_LOSS: anchor+200..+600, 400 ticks.
  * COMPETING_CANDIDATES: anchor+200..+700, {N2,N3} vs {N0,N1,N4}, 500 ticks.

  I checked the printed labels against the bar geometry in the raw 2460×1380 image. The anchor dashline is at x≈752 px, every bar starts at x=1169 px and the bars end at 1998, 1790, 1998 and 2206 px. At 417 px per 200 ticks, the bar lengths are 398, 298, 398 and 498 ticks, which agrees with 400, 300, 400 and 500 to pixel rounding. I therefore treat each window as half-open: [anchor+start, anchor+end).
* I scanned the PDF for hidden text, annotations, attachments, white-on-white text and faint image layers. There are none. Pages 5–7 hold all of the text.

## 2. Results (executed)

The anchor is N0 becoming LEADER (term 1) at t=158 (SHORT), t=258 (MEDIUM) and t=408 (LONG). In CLEAN, that first leader is never displaced.

| setting | CRASH_RECOVER crash→new leader | new leader | total messages sent, 5 scenarios | feasible (engine / verifier) |
|---|---|---|---|---|
| SHORT | **172** ticks (crash at 358, N1 leader at t530, term 2) | N1 | 8763 | yes / yes |
| MEDIUM | **272** ticks (crash at 458, N1 leader at t730, term 2) | N1 | 8283 | yes / yes |
| LONG | **422** ticks (crash at 608, N1 leader at t1030, term 2) | N1 | 7550 | yes / yes |

* **Recovery-optimal: SHORT.**
* **Overhead-optimal: LONG.**
* **The two selections diverge** (`out/decision.json`).
* The engine and the verifier agree on every criterion value and on both selections.
* **Baseline certificate (MEDIUM/PARTITION):** SHA-256 = `7cdc4e3d9a3d4ff8a160c8ba222d232e3a174c50210c22b6eb73de64c2d771ff`, so the **certificate (first 16 hex) is `7cdc4e3d9a3d4ff8`**. The verifier's own re-derivation produces the same hash, and its text is byte-identical to the engine's trace file.
* The per-run trace hashes for all 15 runs (same algorithm, header `QUORUM7|<setting>|<scenario>`) are in the `trace_sha256_16` column of the sweep table.

Full 15-row table: `out/sweep_table.md`. Message totals per run (SHORT/MEDIUM/LONG):

| scenario | SHORT | MEDIUM | LONG |
|---|---|---|---|
| CLEAN | 1816 | 1736 | 1616 |
| PARTITION | 1746 | 1666 | 1536 |
| CRASH_RECOVER | 1681 | 1531 | 1296 |
| MESSAGE_LOSS | 1784 | 1704 | 1576 |
| COMPETING_CANDIDATES | 1736 | 1646 | 1526 |

## 3. Verification evidence

The verifier (`verifier/quorum7_verify.js`) is a separately written JavaScript program. It reads only `constants.json`, and it derives the anchor and the crashed node from its own CLEAN run. It does four things:

1. **Re-derives all 15 runs** with its own simulator. On every tick of its own trace it checks:
   * election safety, both per tick and "one leader node per term over the whole run";
   * log matching over all pairs of logs;
   * leader completeness: every LEADER, on every tick, holds every entry committed anywhere;
   * that a node's committed index never disagrees with an entry already committed at that index;
   * that a committed entry is never removed from or changed in any log that held it;
   * the real-vote rule: the request term is ≥ the voter's term, with one vote per term.

   Result: all 15 runs pass.
2. **Checks the engine's certificate for each of the 15 runs.** First it applies the rule checks above to the engine's own per-tick snapshots and replayed log events. Then it compares those snapshots, logs, vote events and message totals exactly against its own re-derivation. Result: **all 15 engine certificates accepted.** It also cross-checks every row of the engine's sweep table (message totals, hashes, anchors) and finds 0 mismatches.
3. **Mutation M1, a vote granted to a candidate whose term is below the recipient's current_term.** The verifier injects into the baseline certificate a grant at t=558, inside the partition: N1, at term 1, votes for N3 at request term 0. The verifier's snapshots are made consistent with the injected grant (voted_for set). **Result: REJECTED.** Reasons given:
   * `vote_rule: t558 N1 (term 1) granted vote to N3 at lower term 0`
   * `vote_events_differ_from_rederivation`
   * `trace_differs_from_rederivation_at_t558`
4. **Mutation M2, the leader overwriting an already-committed entry.** At t=1058, leader N0, whose commit_index is 16, overwrites index 14, changing (term 1, cmd 19) to (term 1, cmd 9999). **Result: REJECTED.** Reasons given:
   * `committed_overwrite: t1058 N0 index 14 [1,19] -> [1,9999]`
   * `log_matching: t1058 N0/N1 agree on term at 16 but differ at 14`, and the same for N2–N4
   * `leader_completeness: t1058 leader N0 lacks committed index 14`
   * a trace mismatch

**The unmutated original is ACCEPTED.** Both rejections come from rule checks alone, before any comparison with the re-derivation. The verifier's exit code is 0 only if the original is accepted and both mutations are rejected.

## 4. The two selections compared, and the recovery/overhead trade-off

Recovery-optimal is SHORT and overhead-optimal is LONG, so the two selections pull in opposite directions. The causes below are tied to executed trace events (`out/tradeoff_analysis.json`, `out/baseline_role_transitions.txt`).

**Why a shorter timeout speeds crash recovery.** In every setting, recovery is driven by the follower with the smallest timeout among the survivors, which is N1 (BASE+20). Taking MEDIUM as the example:
* The leader N0 sends its last AppendEntries at t=450. Its sends to N1 are at …, 430, 440, 450, found with an engine probe, and 450 is also a command tick.
* N1 hears it at t=452 and resets election_elapsed.
* N0 crashes at t=458.
* N1 has nothing else to reset its timer, so it reaches 270 ticks at t=722 and begins a pre-vote.
* The pre-vote and the real vote then take a fixed 4 one-way hops of 2 ticks each: pre-vote requests delivered at 724, grants at 726 (term 1→2, CANDIDATE), vote requests at 728, grants at 730 (LEADER).

The latency is therefore (timeout − time since the last heartbeat) + 8 ticks. That comes to 164+8=172 for SHORT, 264+8=272 for MEDIUM and 414+8=422 for LONG (from `latency_decomposition`). Only the timeout term varies, which is why SHORT wins.

**Why the same shorter timeout raises message overhead.** The runs show two mechanisms:
1. **Less leaderless time means more heartbeat traffic within the fixed 2400-tick run.** A leader exists on 11038 (SHORT), 10438 (MEDIUM) and 9538 (LONG) node-ticks, summed over the five runs. While a leader exists it emits 4 APPEND_REQ and 4 APPEND_RESP every 10 ticks. In the baseline trace (MEDIUM/PARTITION), N0 becomes leader at t=258, and from then on its AppendEntries traffic makes up 1640 of the run's 1666 messages. Under SHORT the same leader appears at t=158, 100 ticks earlier, and SHORT/PARTITION sends 1746 messages, 80 more, with identical election traffic (26 each). Under LONG it appears at t=408, 150 ticks later. The same effect appears after a crash: under SHORT a new leader resumes heartbeats at t=530, against t=1030 under LONG. This is the larger effect. Summed over the 5 scenarios, replication traffic is 8631 (S) vs 8161 (M) vs 7444 (L).
2. **More election chatter during faults.** A short timeout expires inside a fault window more often. In the baseline, N3 (310-tick timeout) and N4 (330) each expire inside the 400-tick partition: N3 goes F→P at t=762 and N4 goes F→P at t=782. Each sends 4 PREVOTE_REQs (the 3 sent across the partition are dropped) and gets the one same-side reply. They fall back to F at t=862, when the first post-heal heartbeat (sent at t=860) arrives. Under LONG, N3 and N4 time out at 460 and 480 ticks, both longer than the 400-tick window, so they never expire in PARTITION. LONG/PARTITION has only N0's initial pre-vote round. In COMPETING_CANDIDATES, SHORT produces 4 minority pre-vote rounds against 2 for MEDIUM and LONG. Summed election traffic (PREVOTE plus VOTE messages) is 132 (S), 122 (M) and 106 (L).

So in this model, fast recovery and high overhead have the same cause: a short timeout ends leaderless periods sooner, and every tick that has a leader costs 8 messages per 10 ticks. Being honest about magnitudes, mechanism 1 accounts for most of the difference (≈1187 of the 1213-message SHORT−LONG gap). Pre-vote chatter is the smaller part (26 messages).

## 5. Why current_term increments only after a pre-vote majority, and what it protects in COMPETING_CANDIDATES

When a node times out it becomes PRECANDIDATE with its term **unchanged**. It sends a pre-vote request carrying the *prospective* term+1, and granting a pre-vote changes no state. Only a node that collects ≥3 of 5 pre-grants may perform the one term increment. If a node incremented its term directly on timeout, a node cut off from the majority would raise its term every timeout period. As soon as the partition healed, its higher term (on any VOTE_REQ, or on the AppendEntries rejection it sends back) would force the healthy leader to step down. That is a disruption with no benefit: the isolated node's log is stale, so it cannot win the election anyway.

The executed COMPETING_CANDIDATES runs show the protection directly:
* **With pre-vote (delivered runs).** {N2,N3} are isolated for 500 ticks. N2 and N3 time out and run pre-vote rounds:
  * MEDIUM: t=742 (N2) and t=762 (N3).
  * SHORT: t=542, 562, 732 and 772.

  Each round can collect at most 2 grants (self and the other minority node), which is short of the 3 needed. N2's and N3's current_term stays at **1** for the whole run (`minority_max_term_in_run = 1,1` in every setting). After the heal, the majority leader N0 (term 1) is never displaced: there are 0 leader changes after the window starts, and the run ends with N0 as LEADER and commit_index 42/42 (MEDIUM). Even if N2 or N3 pre-voted after the heal, the majority nodes would refuse, because they appended commands during the window and their logs are now more up to date.
* **Counterfactual with pre-vote disabled** (`--ablate-prevote`, for illustration only; `out_keep/counterfactual_no_prevote/cc_medium_summary.txt`). Under MEDIUM:
  * Inside the window, N2 and N3 raise their terms 1→2 (t=742/744) with no pre-vote gate.
  * The partition heals at 954. At t=964, N2's AppendEntries rejection, which carries term 2, reaches N0 and deposes it: N0 goes from LEADER term 1 at t=962 to FOLLOWER term 2 at t=964.
  * There is then a run of elections (terms 3 at t=1032/1034, then 4). The cluster is **leaderless for 254 ticks (t964..t1217)** until N0 is re-elected at term 4.

  The PARTITION scenario under SHORT and MEDIUM shows the same pattern (terms reach 4). Pre-vote removes that disruption entirely.

A caveat that follows from the packet's literal rules: pre-vote grants depend **only** on log completeness. There is no "I recently heard from a leader" check. The protection after a heal therefore depends on the majority having appended entries during the window. With no client commands (`--schedule-every 0`), every log stays empty. Under SHORT and MEDIUM MESSAGE_LOSS, N4 (cut off from AppendEntries) then wins a pre-vote and becomes LEADER at term 2 (t=588 / t=788), deposing N0.

The packet says the minority "exceed[s] their own timeout repeatedly" in COMPETING_CANDIDATES. That holds only for SHORT (two rounds each). Under MEDIUM and LONG, each minority node times out only once inside the 500-tick window (N2's 290 ticks ×2 > the remaining window).

## 6. Ambiguities and the readings chosen

The sensitivity results are in `out/sensitivity.txt`.

1. **The client command schedule is not given anywhere in the packet.** Both the prompt and §8 refer to "fixed ticks". **Chosen:** one command every 50 ticks at t=50,100,…,2350, with ids 1..47, labelled ASSUMED in `constants.json`.
   * Sensitivity: both selections are unchanged under every schedule tried.
   * Crash latencies shift by at most ±2 ticks (170–173 / 270–273 / 420–423).
   * **The baseline certificate depends on the schedule's phase:** `7cdc4e3d9a3d4ff8` for every 50 from t=50, every 100, every 10 and every 20; `bc6bdcc41ca1ad9c` for every 50 from t=1; `728068839e5419c6` with no commands.
   * Message totals change for some schedules (for example, every 25 gives 10445/9871/8994).
2. **The MESSAGE_LOSS overrides are not specified.** The packet says only "targeted DROP/DUPLICATE/DELAY". **Chosen**, applied to messages *sent* within [anchor+200, anchor+600):
   * DROP every APPEND_REQ to N4;
   * DUPLICATE every APPEND_RESP from N1 (an extra copy arrives one tick later);
   * DELAY every APPEND_REQ to N3 by +6 ticks.

   These choices affect only the MESSAGE_LOSS rows and their message totals.
3. **The "first stable-leader tick" anchor.** **Chosen:** the tick at which the first node becomes LEADER in that setting's CLEAN run. I verified that this leader is never displaced in CLEAN, so it is also stable.
4. **Window bounds.** **Chosen:** half-open [start, end). This gives exactly the 400/300/400/500 ticks the figure labels state.
5. **Partition cut semantics.** **Chosen:** a cross-partition message is dropped if its send tick or its delivery tick lies in the window. The alternatives (send-only, delivery-only) give identical results.
6. **The tick and timer model.**
   * Ticks run t=0..2399.
   * Within a tick, each node handles its arriving messages first, then a client command (if it is LEADER), then its timers.
   * election_elapsed = t − last reset tick, and the node fires when that is ≥ its timeout. So with no resets, N0 fires at t=BASE exactly.
   * Messages sent at t arrive at t+2, so the order in which nodes are processed within a tick does not matter.
   * The snapshot is taken at the end of each tick.
   * The trace has the header plus 2400 lines t=0..2399, joined with "\n" and no trailing newline.

   Starting at t=1, or adding a trailing newline, would change the hash.
7. **Fig. 1 edge 6 vs §5 text.** The figure says a LEADER steps down on a *vote request at a term ≥ its own*. The text says a node steps down only if the term is strictly greater. **Chosen:** the text. The figure's reading (`--fig1-equal-term-stepdown`) gives identical results in all 15 runs, because that case never arises.
8. **Unstated details I filled in:**
   * Any VOTE/APPEND message or response carrying a higher term makes the receiver adopt it and step down. Pre-vote messages never change the term.
   * Pre-vote responses are tagged with the round, so grants from an earlier round do not count.
   * Duplicate grants from the same voter count once.
   * A LEADER that steps down restarts election_elapsed at 0, because a leader does not track it.
   * Candidates and pre-candidates that step down on a higher term keep their elapsed count. The reset list in §3 does not include stepping down.
   * Heartbeats are per follower: an AppendEntries goes to j when 10 ticks have passed since the last one sent to j. A command broadcast counts as a round. There is no extra send triggered by a response (§6 says "retries next round").
   * match_index is *set* to the reported matchIndex, as written, rather than max'ed. With duplicates or delays this can only slow commits, never break safety.
   * A follower updates commit_index to min(leaderCommit, last new index) and never lowers it. Truncation happens only on a real term conflict.
   * The leader counts itself in the majority with match = its own log length.
9. **The message count.** The packet does not define it. **Chosen:** every message a node sends, counting each send once. That includes messages later dropped by a partition or crash, and excludes network-made duplicate copies. Delivered and dropped counts are also reported. Any reading that differs only by drop/duplicate accounting leaves the selections unchanged here, because LONG has the lowest sent, delivered and APPEND counts.
10. **Crash display.** The trace marks a node as role `X` while it is inside its crash window. This appears only in CRASH_RECOVER, not in the baseline. On recovery the node is a FOLLOWER with elapsed 0 and its persisted term, vote, log and commit_index.
11. **Packet text.** It says the minority exceeds its timeout "repeatedly" in COMPETING_CANDIDATES. That is only true under SHORT; see §5.

## 7. Confidence

* **High** for the qualitative results: SHORT is recovery-optimal, LONG is overhead-optimal, the two diverge, and all three settings are safe. These are robust to every alternative reading I tried.
* **High** that the engine and verifier implement the *same* reading. Two separately written programs in different languages agree on every tick of all 15 runs.
* **Moderate to low** that the exact baseline certificate `7cdc4e3d9a3d4ff8` matches any reference answer. It depends on the tick origin and timer conventions in item 6 and, above all, on the phase of the client command schedule in item 1, which the packet never gives.
* The exact message totals likewise depend on items 1, 2 and 9.
