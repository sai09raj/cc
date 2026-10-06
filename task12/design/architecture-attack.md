# Task 12 — architecture attack (COHERE-12, working title)

## What the evidence actually says (after rereading the whole playbook)

| Task | Shape | Real result | Clean evidence of difficulty? |
|---|---|---|---|
| 03 TempestLog | 3-replica journal, crashes, retries, in-flight messages | 65/68/71, then 59/63/68 | Yes, partial: genuine composition errors with a complete packet (probes passed, full runs wrong) |
| 04 Relay F | Credit fabric, U/V shards, rendezvous, expiry, retries, shared serializers | three sub-50 (user-reported) | Yes: complete packet after clarification; failures in temporal composition |
| 06 ATRIUM-9 | Elevator dispatch sweep | 20/21 | No: hidden semantics (#71) |
| 07 QUORUM-7 | Raft under faults | 31/32 | No: hidden semantics (#71) |
| 09 TYPECHAIN-9 | Type inference | 99/100 | Solved: one deviation point |
| 10 CELLGUARD-10 | Single battery pack | 121/122 | Solved: rule list = perfect-semantics summary (#70) |
| 11 TENURE-11 | GC simulation, ~40 micro-rules, single thread | solved by probe in 10 min | Solved: single-threaded procedure, transcribed |
| 11 ARRAY-11 | Exact optimization | 98% when finished; passed on 5/6 9000 s timeouts | Solved when time allowed (#72, #73) |

The only clean evidence of a fully specified task holding a frontier model
down is the **concurrent message-passing family with races** (03, 04):
many entities act in the same cycle, messages are in flight while state
changes underneath them, and correctness depends on handling crossing
messages, retries and same-cycle order. Single-threaded procedures (GC,
battery, inference) and pure search were transcribed or solved.

## Candidates

| Candidate | Rejected / selected because |
|---|---|
| Railway interlocking | Rejected in task11 as same "agents reserving a resource" family as KILNWORKS/ATRIUM-9; weaker race structure |
| Another Raft/Paxos | Same mechanism as QUORUM-7; shape repeat |
| Relay fabric variant | Same mechanism as Task 04 |
| **Directory cache coherence with transient states** | **Selected**: the textbook source of crossing-message races (a forwarded request meets a writeback, an invalidation meets a data reply, a NACKed request retries while ownership moves). Different mechanism from 03/04/07 (no consensus, no credits/shards) |

## Selected: COHERE-12 — directory MESI on a small mesh

**Domain:** Computer Engineering. **Subdomain:** multicore memory
systems — directory coherence protocol verification and directory
provisioning.

**Engineering decision:** choose directory request-queue depth, NACK retry
backoff, and directory placement (which mesh node hosts each directory
bank) to minimize total completion time of a fixed multi-core workload
subject to a tail-latency ceiling, with zero protocol-invariant violations.

### System (all rules visible; distributed across panels, never one list)

- 8 cores, each with a small private cache (few sets, LRU) and one MSHR per
  line; misses issue GetS/GetM; evictions issue PutS/PutM (writeback).
- Directory banks (address-interleaved) with stable states I/S/M and
  transient states (e.g. waiting for invalidation acks, waiting for
  writeback); a bounded request queue per bank; NACK when busy or full.
- Cores have transient states (IS_D, IM_AD, IM_A, SM_AD, MI_A, SI_A, II_A)
  that must handle crossing messages: Fwd-GetS/Fwd-GetM/Inv arriving while
  a Put is in flight, data arriving before acks, acks counted down.
- 2x4 mesh, XY routing, per-link latency, per-port round-robin arbitration,
  messages ordered only per link (not end-to-end), so races are real.
- Retry with deterministic backoff after NACK; per-core program of loads,
  stores and compute delays (workload generated from compact rules).

### Genuine visual content (visual-ablation must pass)

- Protocol state diagrams for core and directory (transient states, edge
  labels = event / actions / next state). Arrow direction and edge
  endpoints carry the rules.
- Mesh floorplan: link latencies drawn as wire lengths against a scale bar
  (measured), router positions.
- A message sequence chart of one race, as a worked example with times
  read from its time axis.

### Perfect-semantics ablation

Grant every transition, latency and arbitration rule. Remaining work:
1. Build a concurrent event engine where many controllers act per cycle and
   in-flight messages cross state changes (temporal composition).
2. Generate the workload; run it to completion for every configuration in
   the sweep (e.g. queue depth x backoff x placement ≈ 100+ runs).
3. Verify invariants on the live run (single writer, data value, no
   deadlock) and build an independent checker that replays a trace.
4. Pick the constrained optimum; explain why one-knob changes fail.
Grading: whole-sweep aggregates, production-trace witnesses spread over
early/middle/late races, the constrained selection, invariant results.

### Risks named up front

- **Transcription risk (TENURE-11, CELLGUARD-10):** a fully specified
  simulation may be implemented correctly first time. Mitigation is not
  hiding rules; it is genuine concurrency (same-cycle multi-controller
  interaction, unordered network) where 03/04 showed composition errors.
  This is a hypothesis until an early `opus`-alias probe.
- **Hidden-semantics risk (#71):** every same-cycle order, queue rule,
  arbitration and metric must be visible; run the code→source audit before
  any pilot.
- **Probe calibration (#73):** the alias tracked the real model on
  simulations, underestimated it on search. Here the core is simulation.

## Gate plan

1. Prototype the engine and the race set; confirm races actually occur in
   ordinary runs (activation coverage) and that aggregates move under
   single-rule mutants.
2. Draft packet; early `opus`-alias blind pilot before any rubric.
3. Only if the probe fails on composition (not on a spec gap) build the
   full package.
