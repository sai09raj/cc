# Task 12 — COHERE-12 (directory coherence on a 2x4 mesh)

## v3 package (cohere12_v4.pdf): 2,400 operations per core — ready for real pilots

Same system, rules and configuration space; each core now runs 2,400
operations instead of 400, so every simulation is about 6x longer. Sized
with the engine the real pilots actually wrote (`fast_2400.js`, 20.5 ms per
configuration locally, x0.655 platform factor, 17 threads): a full sweep
needs about 23,200 s, 2.6x the 9,000 s limit, and still about 9,300 s for an
engine 2.5x faster, before any development time.

- Answer key: `proto/cohere_fast.c` over all 29,360,128 configurations, 28
  parallel cloud workers (one per placement, branches
  `claude/cohere12-gt-p{a}{b}`), 448 chunk files, aggregated by
  `proto/aggregate_v4.py` into `reference/aggregate_v4.json`. 41 sampled
  entries plus baseline, variants and optimum identical in the JS engine
  and the real pilots' engine; the unoptimized `proto/cohere.c` recomputed the full
  N2/N6 Q4 B1 chunk (65,536 maps) with identical sum (2,314,432,507),
  histogram and top 20.
- Values: baseline 39,980 (p95 38, 58,447 messages, 2,181 Nacks, 9,609
  loads); variants 39,767 / 36,306 / 35,693; sum 1,234,126,567,296; below
  baseline 9,711,036; at most 36,000: 1,239,802; per Q 1,416,317 /
  2,396,296 / 2,825,944 / 3,072,479; per B 2,614,670 / 2,547,107 /
  2,395,093 / 2,154,166; optimum N2/N6 Q4 B1 map 63905, makespan 33,626.
- Memo facts: mean makespan by placement spans 11,820 cycles (N2/N6
  36,036 to N3/N7 47,856), by Q 2,082, by B 618; the line map's own mean
  effect is about 7,100 over 72 sampled maps including the all-one-bank
  extremes (provable bound 12,444), so placement is the largest knob.
- Prompt changes: file name v4, threshold 36,000. Rubric: same 50
  criteria and weights, values replaced. Ideal Flow: values replaced.

## Real pilot round 1 (v2 package, cohere12_v3.pdf): 94 / 100 / 100 — FAILED

All three real runs (claude-opus-5-5, 93-103 min each) built a correct
Node.js simulator, swept all 29,360,128 configurations in 61-66 minutes on
16-17 worker threads, and reported every whole-space value exactly, plus the
optimum, the checker results (including the 1,648-load count and both altered
traces) and the memo claims. Trajectories in `audit/real-pilot-1/`.

The design's premise was wrong: the local probe ran at ~5 ms per
configuration on 4 cores and I assumed ~12.6 effective platform cores. The
real runs achieved about 2.3 ms per configuration per thread on 17 usable
threads (about 7,400 configurations per second), so the full sweep fit in
about an hour. Compute-bound difficulty sized against a local probe does not
transfer (mistake #77).

## v2 (current): exhaustive design-space characterization — probe 35.8%

v1 failed (probe reproduced it exactly in 8 min). v2 keeps the validated
simulator and makes the deliverable a characterization of 29,360,128
configurations (any directory node pair x 65,536 line maps x Q 1..4 x B
1,2,4,8; 16 lines, 400 operations per core). The single optimum turned out
to be shortcut-able (placement N2/N6 dominates by any cheap test), so most
weight sits on whole-space counts and sums that need every configuration.

- Answer key: exhaustive C enumeration (448 chunks), aggregated in
  `reference/aggregate.json` and `reference/aggregates2.json`; 12 random
  stored entries plus baseline and optimum re-run by the independent JS
  engine, all identical.
- Packet `artifact/cohere12_v3.pdf` (v2 + p95 issue-cycle and Figure 2
  axis clarifications; values unchanged). Prompt, rubric (43 criteria,
  134 points) and Ideal Flow in `platform/`; v1 files in `platform/v1/`.
- Probe 2 (`audit/probe-2-opus-v2/`, packet v2, 2.5 h budget, Node/Python,
  4 cores): exact on figures, baseline, variants, optimum, checker, memo;
  simulated 16.5% of the space and reported estimates -> **48/134 = 35.8%**.
  Its Node simulator ran at about 5 ms per configuration, i.e. about 41
  core-hours for the full space (~3.2 h on ~12.6 effective platform cores
  before any build time).
- Risk: a run that writes a faster engine and parallelises perfectly could
  approach the 2.5 h limit; the per-Q and per-B counts give partial credit
  per quarter of the space covered (3 of 4 quarters plus everything else
  is about 54%).


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
