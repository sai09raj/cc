# KILNWORKS Retrofit Engineering Memo (Revision R3 evaluation)

**Prepared by:** production-optimization engineering (offline simulation study)
**Inputs:** `kw-r3.pdf` (5-page packet) and the assignment brief, and nothing else.
**Tools:** Python 3.11.15, standard library only (no third-party packages), Ubuntu 24.04 LTS, x86_64.
**Reproduce everything below with:** `bash work/reproduce.sh` (runs in <1s; regenerates every file this memo cites).

---

## 1. Graph interpretation

The packet's Section A diagram is vector-drawn (matplotlib PDF backend, no
raster images), so the aisle graph was extracted by parsing the actual PDF
path coordinates rather than eyeballing the picture — see
`work/EXTRACTION_NOTES.md` and the reproducible `work/extract_graph.py`.

**Nodes:** 0..8 laid out as a 3x3 grid. P=node 3, K=node 1, Q=node 5, and
node 4 is the interior junction.

**Edges present in every design:** `0-3, 3-6, 3-4, 4-7, 6-7, 7-8, 5-8, 2-5, 1-4`
(9 edges). Node 1 (K) has degree 1 (only 1-4) in **both** layouts, so every
delivery to K passes through node 4.

**Edge 4-5:** absent in the closed-aisle layout (D0, D1, D2, D4) — drawn only
as a fine dotted "ghost" line (dash array `[1.2 2.4]`) that is explicitly
*not* a traversable edge — and present in the open-aisle layout (D3, D5),
drawn with a real dash pattern (`[6.4 4.8]`). This is confirmed at the
coordinate level: the ghost/real line's endpoints land exactly on node 4's
and node 5's column positions in each subplot.

**Capacities:** docking bays P, Q, K hold up to 2 robots each; the junction
node 4 holds at most 1 robot; all other nodes are uncapacitated (irrelevant
anyway with only 2 robots in the plant). Each edge carries at most one robot
traversal per minute in either direction.

**The one graphically-only datum — forced-offline duration:** Section E's
illustrative timeline never prints Robot 0's forced-offline duration as a
number; the text explicitly says only the shaded span's *length* is
normative. The shaded rectangle's fill path runs from PDF x=189.72 to
x=422.28, and the axis gridlines for tick labels "3" and "9" sit at exactly
those two x-coordinates (spacing 38.76 pt/data-unit, verified across all 12
ticks). So the span is exactly 9−3 = **6 minutes** wide. This is the single
number in the whole packet that can only be recovered by reading a
plotted/shaded region against its axis — see `EXTRACTION_NOTES.md` §2 for
the full coordinate derivation and `extract_graph.py` for a script that
re-derives it mechanically from the PDF bytes.

## 2. Rule reconstruction (summary; full transcription in `sim/common.py`)

- **Campaigns:** 4 campaigns × 5 lots = 20 lots, one shared clock,
  `release_abs(j,s) = 35s + 2*floor(j/2)`, `family = (j+s) mod 2`,
  `Pbase = 5 + (j² + 2s) mod 4`, `Qbase = 4 + (3j+s) mod 5`.
- **Machine assignment**, evaluated P-then-Q every minute: a busy machine is
  skipped; an idle machine picks, from released/unassigned lots with
  `held_fixtures < F`, the one minimizing `setup + duration` (setup 0 if the
  machine's remembered family matches, else 2; tie-break lowest global index
  `5s+j`); a fixture is held from the minute a lot's prep **starts** until
  its batch's cure **ends**.
- **Robot dispatch**, Robot 0 always resolved before Robot 1 every minute,
  6-rule priority cascade (forced-offline → unload-at-K → pickup-here →
  move-toward-K-if-carrying → move-toward-nearest-waiting-lot →
  move-toward-home). Robot 0 gets a one-time 6-minute forced-offline window
  starting the first minute it is *at* node 4 (never re-triggers).
- **Oven pairing:** bounded 2-minute anchor timer, family-only batching,
  cures `4+family` minutes, a power refusal never forfeits the anchor.
- **Power admission:** one ordered pass per minute — P start, Q start,
  Robot 0, Robot 1, oven start — each spending from whatever of G remains
  after already-mandatory ongoing draws (continuing P/Q/oven operations) and
  after the earlier steps in the same pass. We resolved the one real
  ambiguity here (whether mandatory ongoing draws are pre-committed before
  the ordered pass, or interleaved into it) in favor of pre-commitment,
  since only that reading keeps the packet's invariant "total draw must
  never exceed G" satisfiable in general; see `kiln_sim.py`'s `run()` for
  the exact mechanics.
- **Tariff:** `multiplier(t) = 1 + (floor(t/7) mod 3)`, printed directly in
  the packet — no graphical reading needed for this one.

## 3. Implementation

Two genuinely separate codebases, sharing only literal constants
(`sim/common.py`, transcribed once from the packet):

- **Primary** — `sim/kiln_sim.py`: class-based (`Lot`, `Machine`, `Robot`,
  `Oven`, `Simulator`), BFS-per-call shortest paths.
- **Verifier** — `sim/verifier_sim.py`: flat dict-of-dicts world state, an
  all-pairs Floyd-Warshall + explicit next-hop table computed once up front,
  the five-step power pass expressed as a generic budget walk, and the
  robot-priority cascade re-transcribed independently from the packet text
  (not from the primary's code).

Both were run for all six designs. **Every one of the 6×(187,165,187,185,152,142)
= 1,018 simulated minutes is byte-identical** between the two
implementations, across all logged fields (robot action/position/cargo,
machine/oven busy state, power draw, tariff multiplier, running bill,
fixture count) — see `certification/trace_diff_report.txt`
(`sim/diff_traces.py`, exit code 0). Per-lot timing (release, prepared,
picked-up, delivered, cure-start, cure-end, assigned machine, setup) also
matches exactly for all 20 lots × 6 designs (0 mismatches).

A third, independently-written **feasibility certificate checker**
(`sim/certificate_checker.py`) re-derives nothing decision-wise; it reads
only the emitted trace files and checks, from first principles, release
timing, setup/duration arithmetic, the fixture-ceiling invariant
(cross-validated two ways: the logged counter *and* an independent
recomputation from each lot's prep-start/cure-end lifecycle window — they
agree at every minute), the power budget invariant, edge/node capacity,
tariff/bill arithmetic, cure-duration correctness, and completeness. **All
six designs, both implementations' traces: 0 violations.**

## 4. Case matrix and selections

| Design | F | G | Aisle | Capital | Makespan | Bill |
|---|---|---|---|---|---|---|
| D0 | 2 | 5 | closed | 0  | 187 | 1331 |
| D1 | 3 | 5 | closed | 7  | 165 | 1336 |
| D2 | 2 | 6 | closed | 9  | 187 | 1447 |
| D3 | 2 | 5 | open   | 6  | 185 | 1401 |
| D4 | 3 | 6 | closed | 16 | 152 | 1362 |
| D5 | 3 | 6 | open   | 22 | 142 | 1290 |

**Lexicographic key:** (makespan ascending, bill ascending) — the packet
asks to report exactly these two numbers per design and then select by them;
with no other metric defined, this is the natural (and only well-formed)
key over that report.

- **Unrestricted selection: D5**, key (142, 1290). D5 is the pointwise best
  design overall — lowest makespan *and* lowest bill among all six, so the
  lexicographic choice is unambiguous (no bill tie-break was even needed).
- **Capital ≤ 9 selection: D1**, key (165, 1336), from the eligible pool
  {D0 (0), D1 (7), D2 (9), D3 (6)} — D1's makespan (165) strictly beats the
  next-best eligible design's (D3, 185), so again no tie-break was needed.

Both selections and their full ranked pools are in
`case_matrix_and_selections.json` / `case_matrix.csv`.

## 5. D0 baseline vs. the two selected designs

| | D0 (baseline) | D1 (capital≤9 pick) | D5 (unrestricted pick) |
|---|---|---|---|
| F / G / aisle | 2 / 5 / closed | 3 / 5 / closed | 3 / 6 / open |
| Capital | 0 | 7 | 22 |
| Makespan | 187 | 165 (−22, −11.8%) | 142 (−45, −24.1%) |
| Bill | 1331 | 1336 (+5, +0.4%) | 1290 (−41, −3.1%) |
| Minutes with `fixture_held ≥ F` | 176/187 (94.1%) | 140/165 (84.8%) | 118/142 (83.1%) |
| Robot actions refused for **power** | 0 | 31 | 0 |
| Robot actions refused for **node/edge capacity** | 3 / 0 | 11 / 2 | 11 / 2 |
| Oven batches (paired / solo) | 0 / 20 | 5 / 10 | 3 / 14 |

(Full per-design diagnostics: `certification/design_diagnostics.json`.)

D1 buys 22 fewer minutes of makespan for 7 capital units at essentially flat
bill (+0.4%). D5 buys 45 fewer minutes for 22 capital units and *also* cuts
the bill by 3.1% — it dominates every other design on both reported metrics,
which is why it wins the unrestricted comparison outright.

## 6. Causal explanation, tied to the delivered traces

**F, not G, is D0's bottleneck.** In D0 (F=2, G=5), `fixture_held` sits at
the ceiling (2) for 94.1% of the run's minutes, and **zero** robot actions
are ever refused for lack of power (`certification/design_diagnostics.json`,
D0: `robot_action_refusals.power = 0`). Raising G alone confirms this
directly: D2 (F=2, G=6, otherwise identical to D0) reproduces D0's **exact**
187-minute makespan and still shows 0 power refusals — the extra power
headroom is simply never spent, because with only 2 fixture slots the plant
can never have more than ~2 lots in flight regardless of how much power is
available. D2's bill is *higher* than D0's (1447 vs 1331) for the same
makespan: the extra power lets P/Q start marginally earlier in some minutes,
which shifts some draws into higher-tariff windows without buying any
schedule length — a pure loss.

**F=3 is the lever that matters.** D1 (F=3, G=5) drops the fixture-binding
share to 84.8% and, for the first time, actually exhausts the power budget
(31 refused robot actions) — relaxing F exposes G as a real constraint. Five
of D1's 15 oven batches manage to pair (vs. D0's 0 of 20): with 3 fixture
slots instead of 2, more lots are in flight simultaneously, so two
same-family lots are much more likely to both be waiting at K inside the
2-minute pairing window. D0 never pairs a single batch — under F=2 there's
essentially never a second same-family lot at K in time.

**Opening the aisle helps less than intuition suggests, because F still
dominates.** D3 (open aisle, otherwise = D0) shortens Q's route to K from
distance 4 (5→8→7→4→1) to distance 2 (5→4→1), yet only trims makespan by 2
minutes (187→185) and *raises* the bill by 70 (1331→1401). The trace shows
why: node-4 contention (`robot_action_refusals.node_capacity`) actually
**triples**, from 3 in D0 to 9 in D3, because the shorter path lets Robot 1
cycle through the single-capacity junction more *often* per unit time — more
frequent, individually-cheap collisions with Robot 0, not fewer. And because
F=2 still caps `fixture_held` at 97.3% binding (even higher than D0), the
faster junction transit has almost nothing to accelerate: the plant still
can't have more than 2 lots in flight, so shaving a robot's travel time
barely moves the makespan. D5, by contrast, pairs the open aisle with F=3 —
now the shorter path *does* matter, because the fixture ceiling is no longer
strangling throughput, and D5 posts the best makespan and bill of all six.

**Net causal chain:** F caps concurrent in-flight lots → that caps how often
P/Q/oven/robots have anything to do → that caps both power draw and node-4
traffic. G and the aisle retrofit are real levers, but only once F stops
being the binding constraint; spent alone (D2, D3) they either do nothing
(D2) or actively cost money without much schedule benefit (D3). This is
exactly why the unrestricted winner (D5) needed *both* F=3 and the open
aisle together, and why the cheaper, capital-conscious win (D1) came from
F=3 alone.

## 7. Adversarial verifier experiments (from `certification/adversarial_results_*.json`)

Run against D0's and D5's genuine, certified-feasible traces via
`sim/adversarial_experiments.py`:

- **Negative-start:**
  - (a) a `machine_start` event moved to a time *before* its lot's
    `release_abs` (but still ≥ 0) — caught: `NEGATIVE-START/EARLY-START:
    lot5 machine_start at t=32 < release 35`.
  - (b) a `machine_start` event moved to a literally negative minute
    (t = −5) — caught by two independent rules simultaneously (early-start
    *and* explicit negativity): `NEGATIVE-START: lot5 has negative start
    time t=-5`.
- **Route-collision:**
  - (a) both robots' positions forced onto node 4 (capacity 1) in the same
    minute — caught: `ROUTE-COLLISION/NODE-CAPACITY at t=93: node 4 holds 2
    robots (cap 1)`.
  - (b) both robots' positions/actions forced to traverse edge (3,4) in the
    same minute — caught by both the node-capacity and the dedicated
    edge-capacity rule simultaneously: `ROUTE-COLLISION/EDGE-CAPACITY at
    t=62: both robots traversed the same edge [(3, 4), (3, 4)]`.

All 4 injected corruptions, on both designs tested, were caught
(`"ALL ADVERSARIAL INJECTIONS CAUGHT": true`). This demonstrates the
checker is a real certificate — it rejects invalid schedules, not just
rubber-stamps whatever it's handed.

## 8. Why treating the four campaigns as independent resets is wrong

`sim/campaign_reset_experiment.py` builds, for every design, four
*separately reset* simulations — each campaign's 5 lots alone, machine
memory/fixtures/robot positions/oven state all back at their t=0 initial
condition, release times rebased to a local clock starting at 0 — and sums
their individual makespans and bills. Result (`certification/campaign_reset_experiment.json`):

| Design | Continuous makespan | Independent-resets Σmakespan | Continuous bill | Independent-resets Σbill |
|---|---|---|---|---|
| D0 | 187 | 223 (+36) | 1331 | 1268 (−63) |
| D1 | 165 | 194 (+29) | 1336 | 1170 (−166) |
| D5 | 142 | 177 (+35) | 1290 | 1225 (−65) |

Both errors run in opposite, equally misleading directions:

- **Makespan is overstated** by independent resets (by 29–36 minutes across
  designs) because a real continuous run lets a campaign's completion tail
  overlap the next campaign's early work on the *same* shared machines,
  robots, and oven — exactly what the packet's Section C note flags
  ("a campaign's own completion tail routinely extends past the next
  campaign's release window"). Resetting discards that overlap and also
  discards the machine-memory carryover (remembered family) that lets later
  campaigns sometimes avoid a family-mismatch setup penalty that a fresh
  machine (memory reset to "none") would have to pay differently.
- **Bill is understated** by independent resets (by 63–166) because each
  reset campaign gets its *own* fresh t=0 — i.e. it always starts inside the
  cheapest tariff window (`multiplier(0..6)=1`) instead of wherever the real
  continuous clock actually is by then. Four campaigns each re-exploiting
  the low-tariff opening minutes is not physically available to a plant
  running one real clock.

Both distortions stem from the same root cause: the four campaigns share
one clock, one pair of machines with persistent memory, one fixture pool,
two robots, and one oven — that shared, stateful resource pool is exactly
what "independent resets" erases, and it erases it asymmetrically (helping
the makespan number, hurting the bill number), so no post-hoc correction
factor could fix it — the two errors don't even point the same way.

## 9. What a distance-only relaxation loses

`sim/distance_only_relaxation.py` computes, per design, the earliest
possible completion of every lot keeping *only* the graph-distance geometry
and discarding every capacity/contention/timing rule (infinite F and G,
uncapacitated nodes/edges, a dedicated idealized robot per lot, no
forced-offline disruption, no oven pairing wait — cure starts the instant a
lot reaches K). Results (`certification/distance_only_relaxation.json`):

| Design | Relaxed lower bound | Actual makespan | Gap |
|---|---|---|---|
| D0 | 122 | 187 | 65 min (34.8%) |
| D1 | 122 | 165 | 43 min (26.1%) |
| D2 | 122 | 187 | 65 min (34.8%) |
| D3 | 121 | 185 | 64 min (34.6%) |
| D4 | 122 | 152 | 30 min (19.7%) |
| D5 | 121 | 142 | 21 min (14.8%) |

Two things stand out. First, the relaxed bound is nearly *flat* across all
six designs (121–122) — it is almost entirely insensitive to F, G, and the
aisle retrofit, because none of those show up in pure graph distance. A
planner using only this relaxation would see essentially no reason to
prefer D5 over D0, when in reality D5 finishes 45 minutes sooner and costs
41 less. Second, the gap to the real makespan is large everywhere (15–35%)
and *shrinks* exactly where the real constraints matter less (D4/D5, F=3),
confirming the gap is capacity-driven, not geometry-driven. A distance-only
relaxation therefore loses: the fixture ceiling's throughput cap, the power
budget's admission gating, the node-4/edge capacity contention (including
the one-time forced-offline disruption, which alone removes the junction
from service for 6 minutes at a moment that matters), and the oven's
2-minute bounded pairing wait — i.e. it loses every mechanism this memo's
§6 causal story actually turns on, and with it, all ability to
differentiate the six designs from each other.

## 10. Deliverables index

| Product | Path |
|---|---|
| Primary simulator | `sim/kiln_sim.py` (+ shared constants `sim/common.py`) |
| Independent verifier | `sim/verifier_sim.py` |
| Full per-design schedules | `traces/D*_minute_trace.csv`, `traces/D*_events.jsonl`, `traces/D*_lot_log.csv` (mirrored under `traces_v2/` from the verifier) |
| Case matrix + selections | `case_matrix.csv`, `case_matrix_and_selections.json` |
| Certification evidence | `certification/trace_diff_report.txt`, `certification/adversarial_results_D0.json`, `certification/adversarial_results_D5.json`, `certification/campaign_reset_experiment.json`, `certification/distance_only_relaxation.json`, `certification/design_diagnostics.json` |
| Compressed evidence bundle | `evidence/full_traces_and_certification.tar.gz` |
| Graph/duration extraction proof | `EXTRACTION_NOTES.md`, `extract_graph.py` |
| This memo | `MEMO.md` |
| One-command full reproduction | `reproduce.sh` |
