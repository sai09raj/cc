# Task 11

## Current direction: offshore array-cable layout optimization (prototype, probe running)

After TENURE-11 failed and the calibration audits showed that no fully
specified simulation in this project has held the target model below 50%
(see the calibration section further down, and Playbook mistake #71), the
user chose to try difficulty that lives in *solving* rather than reading:
an exact combinatorial optimization, fully specified, standard library
only, whose optimum must be found and proven.

Problem: connect 48 turbines to an offshore substation with cable trees;
cable types C1/C2/C3 (capacity 3/5/8 turbines, price 100/145/210 per
metre); a cable uses the cheapest type whose capacity covers its load;
turbine-to-turbine spans at most 1300 m; no two cables may cross; a feeder
bay limit at the substation. Four scenarios (bay limits, a missing cable
type, an alternative platform). This is a capacitated minimum spanning tree
with step costs and a non-crossing constraint.

Prototype (`opt-prototype/`), author side only:

| Finding | Evidence |
|---|---|
| A plain single-flow CP-SAT model cannot certify 30-turbine compact layouts | 15–21% optimality gap after 300 s on 4 cores; on one instance its best layout (2,765,585) was not optimal |
| A capacity-indexed model certifies them quickly | 30–36 turbines in 0.3–6 s; 48 turbines in 1–32 s per scenario |
| Simple heuristics miss the optimum | Esau–Williams 12% above optimal on a 30-turbine instance, plus local search still 2% above; 4% above on a 36-turbine scenario |
| Optima (48-turbine set) | S1 4,732,590; S2 4,759,920; S3 4,758,405; S4 6,667,570, all CP-SAT OPTIMAL and each recomputed exactly by a separate stdlib checker (`check.py`) |

OR-Tools is installed only in a private author virtualenv; the system
Python the probes use has no solver libraries. A second, independent exact
certification (different formulation or engine) is still owed before any
optimum is used for grading.

Gate: an `opus`-alias probe on the text-only problem (`probe-prompt.txt`,
`field.json`) is running. If it proves all four optima, this direction
fails too; if it cannot prove them or reports a non-optimal cost, check
whether that is legitimate difficulty or a fairness problem (unwinnable
within reason), then decide.

---

# TENURE-11 (generational garbage-collector tuning) — shelved

**State: FAILED the early difficulty gate.** The `opus`-alias blind pilot
solved the draft packet cleanly in about 10 minutes. Per Gate 8.5 and
mistake #70 this means the architecture is reopened, not patched. No rubric
or platform text was written, so nothing else was spent on it.

## Early probe result (probe 1, `opus` alias, `tenure11_v1.pdf`)

Deliverables archived in `audit/probe-1-opus/`. Verified by me, not taken
from the probe's own report:

- Its baseline GC log is **byte-identical** to `reference/goldens/baseline_gclog.txt`
  (287 events, hash `21792195d928aa2b`).
- All 84 feasible sweep rows match the reference on every metric; the same
  12 configurations end in OOM at the same operation indexes.
- All three selections and all four whole-sweep sums match exactly.
- Every figure-only constant was measured correctly by pixel measurement
  (old-generation size, header length, all six base payloads, slot counts,
  phase boundaries), each within 0.1 of the round value.
- It built a second implementation in JavaScript with a different data
  model (real copies with forwarding pointers) and both agreed on all 96
  rows; both adversarial logs were rejected.

Its ambiguity list is useful for any future revision, but none of the
items changed its answer: on every one it chose the reading the reference
uses. The selections being within a few units of their cut-offs did not
matter, because its numbers were exact.

## What this falsifies

The design bet was that roughly 40 interacting policy micro-rules across
a 96-configuration sweep would not survive exact transcription, which is
the mechanism credited for ATRIUM-9 (20/21%) and QUORUM-7 (31/32%).
TENURE-11 had every blast-radius property the prototype gate checked
(each single-rule slip changes 96/96 rows) and the model simply made no
slips. The packet was complete and unambiguous, and a complete,
procedural spec of a deterministic simulation is transcribed correctly
regardless of rule count. Rule count, nonlocal consequences, sweep
aggregates, and figure-only constants were all necessary-looking but none
was sufficient.

## Calibration probe result (QUORUM-7 packet, `opus` alias)

Run to check whether the local probe is harsher than the real target.
Result: it is not. On QUORUM-7 the alias diverged from the reference the
same way both real Opus 4.8 Max pilots did: the same off-reference LONG
crash latency (422 vs 419) and LONG message totals in the same direction
and size (alias 7550; real pilots 7578 and 7638; reference 7355). Together
with CELLGUARD-10 (alias and real target both 121/122), the alias tracks
the real target closely enough to use as the gate. TENURE-11's clean solve
therefore stands as a genuine "too easy".

The calibration also exposed that QUORUM-7's packet omits the client
command schedule, the MESSAGE_LOSS override list, and the definition of
"message count" — the very facts its 100-point aggregate block depends on
(details in `task07/STATUS.md`, Playbook mistake #71). So QUORUM-7's
31%/32% is not clean evidence that composition over scale defeats the
target model, and the template TENURE-11 was built on is weaker than it
looked. ATRIUM-9 (task06, 20%/21%) has not yet been audited the same way.

---

Historical record of the build follows.

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
