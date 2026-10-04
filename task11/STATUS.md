# Task 11 — TENURE-11 (generational garbage-collector tuning)

**State: draft packet built; early `opus`-alias difficulty probe running.**
No rubric, Ideal Flow, or platform text yet, by design. Per mistake #70
and the updated Phase 8.5, the architecture has to survive one strong-model
blind pilot before any of that is written. A clean content solve on the
probe means redesign, not packaging fixes.

## What is built

- `design/architecture-attack.md` — mechanism choice, shape-diversity
  check against tasks 05–10, perfect-semantics ablation, prototype gate.
- `design/semantic-contract.md` — every rule, with its artifact location.
- `reference/tenure_engine.py` — reference engine; `make_goldens.py`
  writes `reference/goldens/` (sweep CSV, selections and aggregates,
  baseline GC log). Two full regenerations are byte-identical.
- `artifact/tenure11_v1.pdf` (from `artifact/make_packet.py`) — five prose
  pages plus six rasterized figures; metadata stripped; zero vector
  drawings.
- `platform/prompt.md` — draft prompt, 392 words, no hyphens.
- `audit/prototype/` — the scratch prototype used for the prototype gate.

## Reference results

| Item | Value |
|---|---|
| Configurations | 96; 12 end in OOM |
| Cost optimal | (EDEN 49152, SURV 24576, T 3, PT 768): total pause 147851, max pause 2244 |
| Latency optimal, total pause ≤ 220000 | (49152, 24576, 3, 1024): max pause 1867, total pause 173865 |
| Footprint optimal, max pause ≤ 2400 | (32768, 8192, 3, off): max pause 2396, total pause 317818 |
| Baseline (24576, 8192, 2, off) | 202 minor, 85 major, 287 log events, hash `21792195d928aa2b` |
| Sums over feasible configs | total pause 22936277; major GCs 6449; bytes copied 158850216; bytes promoted 216580000 |

## Gate evidence so far

- Tenuring threshold is non-monotonic in total pause in 15 of 24
  (eden, survivor, pretenure) groups.
- Each of five single-rule deviations changes 96/96 sweep rows on the
  reference: depth-first copy order, remembered-set scan order, promoting
  at age > T, no coalescing, and a promotion guard on the largest free
  block instead of total free bytes.
- Both prompt-required adversarial logs (age > T; depth-first evacuation)
  differ from the true baseline log (`051f94b582dcb620`, 285 events;
  `f13b448283bc4b0a`, 288 events).

These show the blast radius is broad. They do not show a strong model
will actually make any of these slips — CELLGUARD-10 had the same
blast-radius property and was still solved. The probe is the real test.

## Next

1. Grade the probe's deliverables against the goldens (diff its sweep
   table row by row, its log line by line, find the first divergence).
2. Clean content solve → reopen the architecture. Real divergence → check
   whether it traces to a packet ambiguity (fix) or a genuine composition
   slip (evidence of difficulty), then write the rubric with score
   topology, reverse coverage, and the rest of the platform package.
