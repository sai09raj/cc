# QUORUM-7 — architecture attack and perfect-semantics ablation

## Why CISTERN-7 is shelved

CISTERN-7 (wastewater lift-station wet-well level control) was fully
built — reference simulator, independent verifier, score-topology-audited
rubric, metadata-stripped artifact, prompt/ideal-flow — and its four
synthetic mutants all scored under 50%. It is shelved anyway, before any
platform submission, because a direct comparison against ATRIUM-9
(task06) found the two share the same underlying **task shape**, not just
a coincidentally similar domain:

```text
build a deterministic simulator
  -> exhaustively sweep a ~50-150-row configuration space
  -> three competing lexicographic selection objectives
  -> independently-coded verifier + two required adversarial mutations
  -> rubric weighted heavily onto whole-sweep aggregate totals
```

The domain differed (elevator dispatch vs. wet-well control) and the
underlying physical mechanism differed (discrete event dispatch vs.
continuous mass-balance integration), but a solver who had just built
ATRIUM-9 could largely pattern-match CISTERN-7's file/module structure
without re-deriving anything domain-specific about *how to approach the
problem*. That is a genuine finding, not a cosmetic one — see the new
"Domain diversity is not the same as task-shape diversity" section added
to `Playbook/00-START-HERE-EVERY-FUTURE-TASK.md` this round. CISTERN-7's
files are left in place (`design/semantic-contract.md`'s prior content,
`reference/cistern_sim.py`, `reference/cistern_verify.py`,
`reference/score_counterfactual.py`, `platform/rubric.md`,
`platform/prompt.md`, `platform/ideal-flow.md`,
`artifact/cistern7.pdf`) for the record, exactly as KILNWORKS R2 was kept
rather than deleted when R3 replaced it. Do not resurrect the sweep
template for a future task07-family revision without a new comparison
against whatever shape ships here.

## The replacement: a genuinely different mechanism

QUORUM-7 is a **message-passing distributed-systems protocol**, not a
physical or economic simulation: a custom-specified, Raft-family
consensus protocol for a 5-node replica cluster, executed as a handful of
long, fully deterministic, scripted-fault scenarios (not a config sweep),
graded primarily on whether delivered safety and liveness invariants hold
across the whole scripted run. This reuses the one pattern this project's
own history calls out as the most reliably validated
(`README.md`, "The Task 04 discovery": one long uninterrupted trace +
production witnesses + independent verification + adversarial mutation,
not an exhaustive parameter grid) while testing a completely different
kind of correctness: concurrent/partial-failure state-machine reasoning,
not numerical integration or request dispatch.

Domain: **Systems & Technology Engineering** (or **Computer Engineering**
— both are valid entries on the platform's fixed domain picker list, see
`00-START-HERE-EVERY-FUTURE-TASK.md`). Subdomain: distributed consensus
protocol correctness under network faults.

### Avoiding the two known traps for this domain

1. **Not textbook Raft verbatim.** A frontier model has near-perfect
   recall of vanilla Raft (election timeout -> RequestVote -> majority ->
   AppendEntries -> commit). Two well-documented, real (not invented)
   Raft extensions are added and must be followed exactly as the packet
   states them, not as the model remembers a textbook variant stating
   them: a **pre-vote phase** (a candidate must win a non-binding
   majority pre-vote before incrementing its term and requesting real
   votes — used in production systems such as etcd and CockroachDB, but
   less commonly memorized than basic Raft) and **bounded-batch
   AppendEntries with per-follower `nextIndex`/`matchIndex` tracking** (a
   leader may replicate at most K log entries per message, requiring
   multiple rounds to catch up a lagging follower — a standard
   real-implementation detail, and a common source of off-by-one and
   over-eager-commit bugs).
2. **Not CP-SAT-solvable.** This project's own history (KILNWORKS R2, see
   `README.md` and the commit that replaced it) already hit the failure
   mode of an architecture a model could solve by reaching for an
   off-the-shelf exact solver. A consensus protocol has no such shortcut:
   there is no general-purpose library call that takes "5 nodes, this
   fault script" and returns the correct term/log/commit trace — it must
   be executed by simulating the actual protocol tick by tick.

## Architecture canvas

```text
TASK WORKING TITLE: QUORUM-7 -- custom Raft-family consensus protocol
  correctness under scripted network faults
DOMAIN: Systems & Technology Engineering / Computer Engineering --
  distributed systems, fault-tolerant replication
REAL ENGINEERING DECISION: which of three election-timeout base settings
  to adopt for this cluster, trading safety margin, worst-case time to
  re-elect a leader after a network partition heals, and total message
  overhead against each other -- not a free re-design of the protocol
  itself, which is fixed.

FOUR PILLARS
1. Genuine visual interpretation:
   - the node state-machine diagram (FOLLOWER/CANDIDATE/LEADER
     transitions, pre-vote sub-state) recovered from a transition-arrow
     drawing, not printed as a transition table;
   - the message-timing diagram (pre-vote round -> real vote round ->
     AppendEntries, with round-trip timing) measured against its own
     axis;
   - each of the 5 scenario scripts' fault timeline (delay/drop/
     duplicate/crash-recover/partition windows) read off a timeline
     chart, not printed as a table of tick numbers;
   - the election-timeout comparison chart (3 settings x their effect on
     recovery time) requiring the same axis-reading discipline as
     ATRIUM-9/CISTERN-7's charts.
2. Iterative tool use: build the protocol engine, run all 5 scenarios x
   3 timeout settings (15 long runs), diagnose against an independently-
   coded verifier checking safety invariants across all 5 replicas' full
   logs, find disagreement, fix, rerun.
3. Expert knowledge: pre-vote gating, per-follower replication-progress
   tracking, the log-completeness vote-granting rule, majority-quorum
   commit-index advancement, and correctly distinguishing "this node is
   partitioned and cannot hear the leader" from "this node crashed" (the
   former must not lose persisted term/voted_for/log state; a crash must
   also preserve it on recovery, matching Raft's persistence guarantee).
4. Long horizon: 5 independent scripted scenarios, each a continuous
   ~2,000-3,000 tick run with no early termination and no resampling,
   cross-file reconciliation of protocol engine output, verifier
   invariant report, timeout-comparison decision, and causal memo.

DIFFICULTY STACK
- distributed specification: state-machine diagram in one panel, message
  timing in another, per-scenario fault scripts in timeline charts, the
  vote-granting/commit rules in prose;
- stateful interaction: each of 5 nodes independently tracks term,
  voted_for, role, log, commit_index, and (while leader) per-follower
  nextIndex/matchIndex -- none of it resettable mid-scenario;
- generated/scripted workload: fixed, fully deterministic per-tick
  network-event scripts (not randomized) driving message delay, drop,
  duplication, node crash/recover, and partition/heal;
- search/decision space: 3 timeout settings x 5 scenarios = 15 long runs,
  a materially smaller row count than ATRIUM-9/CISTERN-7's sweeps but
  each row individually far more complex, matching KILNWORKS' proven
  "few long continuous traces" shape rather than "many short rows";
- coupled targets: safety margin (must never be violated, any scenario),
  worst-case partition-recovery time, and total message overhead trade
  against each other non-monotonically;
- tie-break: an explicit vote-granting tie-break and pre-vote quorum rule
  stated with no ambiguity;
- cross-file consistency: protocol engine output, verifier invariant
  report, timeout-comparison decision file, and memo must reconcile;
- causal synthesis: explain why a shorter timeout speeds recovery but
  risks more competing-candidate churn, and why skipping the pre-vote
  phase would let a partitioned node's stale higher term disrupt the
  majority side upon healing.

POST-SEMANTICS DIFFICULTY (granting every local rule correctly)
- work remaining: composing roughly a dozen interacting deterministic
  rules (pre-vote gating, vote-granting log-completeness check, per-
  follower bounded-batch replication tracking, majority-quorum commit
  advancement, crash/partition state persistence) correctly across 5
  independent ~2,000-3,000-tick scripted scenarios, with no per-scenario
  reset of a shared "did I get this right last time" assumption;
- interacting persistent state domains: 5 nodes' full Raft state each,
  all evolving under a fixed but intricate fault script;
- workload scale and execution: 15 long runs (5 scenarios x 3 timeout
  settings), each one continuous execution to completion;
- search/optimization and coupled decision: no free per-tick choice
  remains (the protocol is fully deterministic once the script and
  timeout setting are fixed), but the three-way timeout comparison across
  a non-monotonic tradeoff is still a real decision depending on every
  scenario's own numbers being right;
- debugging/iteration: the interaction between pre-vote gating and
  crash-recovery persistence (a recovering node must not skip pre-vote
  just because it remembers a high term from before its crash) is a
  genuinely easy edge case to get subtly wrong without inspecting an
  actual multi-node trace;
- independent verification: a second, differently-structured
  implementation must reproduce the same safety-invariant verdicts (and
  ideally the same full state trace) for all 5 scenarios;
- cross-file reconciliation: engine output, verifier report, decision
  file, and memo must agree, including at every scripted fault boundary;
- causal engineering synthesis: explain the timeout tradeoff and the
  pre-vote/crash-persistence interaction using actual events from the
  delivered scenario traces, not a generic restatement.

Could a clean small rewrite now solve the task? NO -- there is no small
  module to discard; correctly composing pre-vote gating, bounded-batch
  replication tracking, and crash/partition persistence across five long
  scripted scenarios is the task itself.
Could direct enumeration or an off-the-shelf solver replace execution?
  NO -- unlike KILNWORKS R2's CP-SAT-solvable exact-optimization
  architecture, there is no general-purpose solver call that takes a
  fault script and returns the correct term/log/commit trace; it must be
  simulated tick by tick.
Could copied headline literals retain >=50%? Must be checked and kept
  below 50% in the score-topology audit before any submission, exactly as
  done for ATRIUM-9 and CISTERN-7 -- weight must sit on per-scenario
  safety-invariant verdicts and trace witnesses, not the three-way
  timeout comparison alone.
Are at least three post-semantics difficulty layers unavoidable? YES --
  long-horizon multi-node state composition, broad-enough executed
  scenario coverage, and coupled decision-making under a hard safety
  constraint.
Does any planned low score depend mainly on semantic omission/
  misreading? NO -- every rule (pre-vote quorum, vote-granting tie-break,
  batch size, persistence-on-crash) will be stated plainly and positively
  in the packet; the difficulty is long-horizon multi-node composition
  volume under a fault script, not a hidden convention.

DISPOSITION: accept architecture, proceed to semantic contract and
  reference build.
RATIONALE: genuinely different mechanism class from both task06 (ATRIUM-9,
  discrete request dispatch swept across configs) and the now-shelved
  CISTERN-7 (continuous mass-balance integration swept across configs):
  QUORUM-7's core difficulty is concurrent, partial-failure, message-
  passing state-machine correctness, graded over a small number of long
  scripted scenarios rather than an exhaustive configuration grid. It
  reuses this project's single most validated structural principle (one
  long uninterrupted trace, heavy production-witness weighting,
  independent verification, required adversarial mutation) while testing
  a reasoning skill neither prior task06-family attempt touched, and
  explicitly avoids the one architecture class (CP-SAT-solvable exact
  optimization) this project has already confirmed fails to stump a
  frontier model.
REVIEWER / DATE: author self-review at proposal time, prompted directly
  by the user questioning task07/task06 similarity; pending independent
  packet-only reconstruction once the artifact and semantic contract are
  frozen (see audit/ once populated).
```

## Reusable-shape checklist (02-DIFFICULTY-ENGINEERING.md)

```text
dense but complete visual specification        -> state-machine diagram +
                                                    message-timing diagram
                                                    + per-scenario fault
                                                    timelines + timeout-
                                                    comparison chart
  + measured constants and one explicit override -> fault-script timing
                                                    measured off timeline
                                                    charts; crash-recovery
                                                    persistence as the
                                                    explicit override to
                                                    the "state resets"
                                                    default a model might
                                                    otherwise assume
  + multi-component stateful model               -> 5 independent node
                                                    state machines, each
                                                    with pre-vote sub-
                                                    state and per-follower
                                                    replication tracking
                                                    while leader
  + author-owned invariant/mutant suite           -> election-safety,
                                                    log-matching, leader-
                                                    completeness checks;
                                                    stale-vote and commit-
                                                    overwrite mutants
  + algorithmic workload generation               -> deterministic
                                                    per-tick fault scripts,
                                                    not randomized and not
                                                    a discrete arrival list
  + exhaustive constrained search                 -> 5 scenarios x 3
                                                    timeout settings, all
                                                    15 executed to
                                                    completion
  + coupled thresholds and explicit tie-break     -> safety (hard
                                                    constraint) vs.
                                                    recovery speed vs.
                                                    message overhead;
                                                    explicit vote-
                                                    granting tie-break
  + integrated witnesses from ordinary execution  -> full state trace +
                                                    hash per scenario, to
                                                    be built
  + a plausible-wrong survival ceiling below 50%  -> to be verified via
                                                    score_counterfactual.py
                                                    before any submission
  + executable + structured outputs + causal      -> protocol engine +
    report                                           verifier + decision
                                                    file + memo
```

## Open design decisions to resolve in the semantic contract

1. Exact pre-vote quorum rule: does a pre-vote failure reset any local
   state, or just prevent the term increment this round?
2. Exact vote-granting tie-break when logs are equally up-to-date: lowest
   node ID, or first-come-first-served within the tick?
3. Exact bounded-batch size K for AppendEntries, and what happens when a
   follower's log conflicts with what the leader sends (truncate-and-
   overwrite rule, stated precisely).
4. Exact commit-index advancement rule: does a leader need at least one
   entry from its OWN current term replicated to a majority before it can
   advance commit_index for older-term entries (the real Raft rule that
   is easy to get wrong)? State it explicitly either way.
5. Exact crash/recover and partition/heal semantics: what state survives
   a crash (must state persisted vs. volatile fields precisely); does a
   partitioned node keep attempting elections while cut off (and what
   happens to its term when it reconnects)?

Do not proceed to `reference/quorum_sim.py` until all five are answered in
`design/semantic-contract.md` with no residual ambiguity.
