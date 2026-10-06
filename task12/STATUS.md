# Task 12 — COHERE-12 (directory coherence on a 2x4 mesh)

**State: FAILED the early difficulty gate (Gate 8.5). Do not upload.**

The `opus`-alias blind probe on `cohere12_v1.pdf` reproduced the reference
exactly in about 8 minutes: baseline makespan 685, every core finish
cycle, p95 44, all 11 message-type counts, all 64 sweep rows identical
(makespan, p95, messages, Nacks), sums 43,328 / 56,774 / 2,669, Fastest
P2/4/1 at 586, Leanest P2/4/4 at 795, decomposition 635 and 690, checker
passing. Under the v1 rubric it would score at or near 101/101. Archived
in `audit/probe-1-opus/`. Its ambiguity list chose the reference's reading
on every item (eviction repeat, issue cycle, message entry time).

Concurrency with races did not stop transcription: a fully specified
deterministic simulation was implemented exactly first time, as with
TYPECHAIN-9, CELLGUARD-10 and TENURE-11 (Playbook mistake #74).


- Design: `design/architecture-attack.md` (why the concurrent message-passing
  family; perfect-semantics ablation; risks).
- Engine: `proto/cohere.py` (MSI directory with transient states, per-line
  forward stalls, bounded directory queues with Nack and exponential
  backoff, XY mesh with three virtual networks, LRU caches with evictions).
  All 64 configurations complete, no deadlock, load values verified.
- Early fix: whole-queue forward stalls deadlocked one configuration
  (classic cross-line wait cycle); rule changed to per-line stalls.
- Race activation (ordinary runs): forwarded requests stalled at a cache
  awaiting data, Inv crossing an upgrade (SM_AD -> IM_AD) and an eviction
  (SI_A -> II_A), FwdGetS/FwdGetM meeting a writeback (MI_A), InvAck before
  Data, PutM from a non-owner, directory stalls in S_D.
- Blast radius (`proto/mutants.py`): makespan changes in 64/64 rows for
  forward-before-response, request-before-response at the directory and
  next-op-same-cycle; 63/64 without network priority; 59/64 with serial-only
  link tie-break; 47/64 with linear backoff.
- Reference (`proto/reference.py`): Fastest P2/Q4/B1 makespan 586 (p95 31,
  801 messages, 13 Nacks); Leanest (makespan <= 640, fewest messages)
  P2/Q4/B4 (638, 795 messages); sums makespan 43,328, messages 56,774,
  Nacks 2,669; baseline P1/Q2/B2 makespan 685, finishes
  [545, 552, 648, 685, 488, 622, 662, 669].
- Packet: `artifact/cohere12_v1.pdf` (2 text pages, floorplan, link-timing
  chart, cache and directory tables; link latencies, node coordinates and
  placements only in figures; metadata, ICC profile, file ID and header
  comment stripped; zero vector drawings).

**Gate:** if the probe reproduces the reference cleanly, the architecture
fails (Gate 8.5) and is reopened before any rubric work.
