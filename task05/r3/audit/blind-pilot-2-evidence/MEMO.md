# KILNWORKS R3 — Retrofit Engineering Memo

**From:** Production-optimization engineering
**Re:** D0–D5 retrofit evaluation, investment selection
**Basis:** `kw-r3b.pdf` (Revision R3), sections A–H, read at full resolution

---

## 1. Graph interpretation (Section A)

3×3 layout, nodes 0–8:

```
0     K(1)   2
P(3)  4      Q(5)
6     7      8
```

Edges present in **both** aisle layouts (solid in the drawing):
`0-3, 1-4, 2-5, 3-4, 3-6, 4-7, 5-8, 6-7, 7-8`.
The dashed edge **4-5** exists only in the open-aisle retrofit (D3, D5).
Node 1 (K) has only the edge 1-4 in both layouts — confirmed by the drawing
and restated in prose — so **every** delivery to K passes through node 4.

Capacities: docking bays P(3), Q(5), K(1) hold 2 robots each; the interior
junction node 4 holds **1**. With only two robots total in the whole plant,
node 4's capacity of 1 is the only capacity constraint that can ever bind
(dock capacity 2 is never binding). All other nodes are treated as
unconstrained.

Shortest robot-only distances to K: P→K = 2 (3-4-1) in both layouts.
Q→K = 4 (5-8-7-4-1) closed, or **2** (5-4-1) open. This asymmetry — Q's
robot must detour through 8 and 7 in the closed layout — combined with the
node-4 bottleneck, is the mechanical heart of every design's dynamics.

## 2. Node-4 disruption (Section E)

The illustrative chart's shaded span was read directly off the pixel grid
(`page4_chart.png` in this directory): it runs from gridline x=3 to x=9,
i.e. **6 minutes wide**, and per Section H's contrast ("Section E's node-4
disruption... explicitly states its freeze is inclusive of the triggering
arrival minute") this window starts **at** Robot 0's first-arrival minute,
inclusive. Robot 0's arrival minute follows the plant's default
next-minute visibility rule (a move decided at t is visible at t+1), so if
Robot 0 decides `3→4` at minute t, it is physically at node 4 — and
frozen there, occupying the capacity-1 junction — for minutes
`[t+1, t+6]` inclusive, resuming at `t+7`. This is confirmed in the
delivered traces: e.g. in D0, Robot 0 decides its move into node 4 at
t=6, is offline for t=7..12 (6 rows), and resumes at t=13 — matching the
chart exactly. Because Robot 0 occupies node 4 for the whole window and
node 4 has capacity 1, **Robot 1 is physically blocked from delivering
anything to K during that window in every design** (closed or open aisle),
which is the actual mechanism, not merely a delay applied to Robot 0.

## 3. Key timing/boundary conventions actually implemented

| Event | Convention used | Basis |
|---|---|---|
| Robot action (move/pickup/unload) | Effect visible at **t+1** | Section E, explicit |
| Node-4 forced-offline window | **Inclusive** of arrival minute (itself already t+1-delayed) | Section E illustrative chart + Section H's explicit contrast |
| Machine (P/Q) finishes a job | Machine free **and** lot buffered **immediately** at the boundary minute (no extra delay) | Section H: "the triggering completion minute itself is unaffected" — i.e. normal assignment eligibility applies at the very boundary minute, establishing that boundary-minute-immediate is the plant's baseline for completions |
| Oven finishes curing | Fixture releases, oven frees **immediately** at boundary minute | Same boundary-immediate baseline; "releasing only when that lot's curing ends" — no stated extra delay |
| Lot's arrival at the oven queue (K-queue) | **t+1** after the unload decision | Section F, explicit and reiterated ("not the minute that action was decided") |
| Q-freeze onset (Section H) | **t+1** after the triggering completion (a *derived* secondary effect) | Section H, explicit: "so the DEFAULT timing convention applies... the triggering completion minute itself is unaffected" |

The general rule that emerges: a **primary** state transition (a machine or
oven finishing what it was already doing) takes effect immediately at its
own boundary minute; a **derived/robot** effect (a chosen action's
consequence, or a rule that explicitly *reacts* to a primary event, like
the Q-freeze) takes effect the following minute. We applied this
consistently and it is what makes the two boundary rules in Sections E/H,
which look superficially different, actually agree.

## 4. Dispatch/assignment/batching logic implemented (Sections D, E, F, H)

* **Machine assignment** (each minute, P before Q): setup 0/2 by family
  memory (never reset across campaigns), cost = setup+duration, tie-break
  lowest global index (5s+j); fixture gate `held < F` checked before
  candidate selection; power-gated at start, non-blocking of the other
  machine on refusal.
* **Robot priority stack** (6 rules, first match wins), with Robot 0 fully
  resolved — position, pickup/unload, and power admission — before Robot 1
  is even computed, per the packet's explicit ordering. Edge capacity ("no
  swap, no shared direction") and node-4 capacity are enforced by giving
  Robot 0's resolved outcome to Robot 1's same-minute decision.
* **Power admission**, one ordered pass per minute: mandatory
  already-ongoing draws (P/Q/oven continuing operations, never
  re-contested) subtracted first, then new-starts in the stated order
  (P start, Q start, R0, R1, oven start), each checked against the
  remaining budget.
* **Oven bounded-pairing timer**: anchor = earliest-arrived uncured lot
  (tie lowest gidx), deadline = arrival+2; every idle minute, pair with any
  same-family waiting partner immediately, else start alone once the
  current minute ≥ deadline; a power refusal never forfeits the anchor or
  its deadline.
* **Fixture accounting**: held increments at actual prep start, decrements
  only at that lot's **curing end** — a fixture is tied up through the
  entire prep→transit→queue→batch→cure pipeline, not just processing.
* **Section H Q-freeze**: Q_cumulative sums *processing only* (never
  setup), continuously across the whole run; first crossing ≥12 fires a
  13-minute freeze starting the minute after the triggering completion.
  Fires at most once. Confirmed to fire in all six designs (see §7).

## 5. Commands and tool versions

```
Python 3.11.15  (no third-party packages used by the simulators/verifier)
pymupdf 1.28.2  (used only to read the PDF at high resolution; not part
                 of the simulation/verification code path)

# from /tmp/kilnworks-blind-test-2/work :
python3 kw_primary_sim.py          # primary sim, all 6 designs, headline numbers
python3 kw_verifier_sim.py         # independent verifier, all 6 designs
python3 compare_traces.py          # full minute-by-minute + lot-by-lot diff, both sims
python3 selection.py               # investment selection (both scopes), case_matrix.json
python3 run_all.py                 # full deliverable set: traces/*.csv, case_matrix.csv,
                                    # certification_summary.json
python3 dump_verifier_traces.py    # persists the verifier's own trace to traces_verifier/*.csv
python3 adversarial_tests.py       # negative-start & route-collision adversarial experiments
```

## 6. Six-design case matrix and results

| Design | F | G | Aisle | Capital | Makespan | Bill | bill+3·capital | Key (makespan, bill+3cap, capital, id) |
|---|---|---|---|---|---|---|---|---|
| D0 | 2 | 5 | closed | 0  | 187 | 1398 | 1398 | (187, 1398, 0, D0) |
| D1 | 3 | 5 | closed | 7  | 171 | 1313 | 1334 | (171, 1334, 7, D1) |
| D2 | 2 | 6 | closed | 9  | 187 | 1427 | 1454 | (187, 1454, 9, D2) |
| D3 | 2 | 5 | open   | 6  | 188 | 1329 | 1347 | (188, 1347, 6, D3) |
| D4 | 3 | 6 | closed | 16 | 152 | 1465 | 1513 | (152, 1513, 16, D4) |
| D5 | 3 | 6 | open   | 22 | 152 | 1307 | 1373 | (152, 1373, 22, D5) |

**Unrestricted selection:** min makespan is 152, tied by D4 and D5; tie
broken on `bill+3·capital` — D5's 1373 < D4's 1513, so **D5 wins**,
key = `(152, 1373, 22, D5)`.

**Budget (capital ≤ 9) selection:** candidates D0, D1, D2. D1's makespan
171 strictly beats D0/D2's 187 — no tie needed. **D1 wins**,
key = `(171, 1334, 7, D1)`.

## 7. Baseline (D0) vs. both selected designs

| | D0 (baseline) | D1 (budget pick) | D5 (unrestricted pick) |
|---|---|---|---|
| F / G / aisle | 2 / 5 / closed | 3 / 5 / closed | 3 / 6 / open |
| Capital | 0 | 7 | 22 |
| Makespan | 187 | 171 (−16) | 152 (−35) |
| Bill | 1398 | 1313 (−85) | 1307 (−91) |
| Q_cumulative freeze trigger | after lot5, ready t=47 | after lot7, ready t=44 | after lot7, ready t=43 |
| P/Q job split | 18/2 | 15/5 | 14/6 |
| Oven batches size-1 : size-2 | 20:0 | 12:8 | 16:4 |

D1 isolates the effect of **raising F alone** (2→3, same G=5, same closed
aisle): more concurrently-held fixtures let more lots be in the pipeline
at once, so P and Q both get more work in parallel (Q's job count goes
2→5), and the oven starts pairing same-family lots (8 size-2 batches
appear) because more lots are simultaneously in flight and can arrive
within the 2-minute pairing window. Result: −16 minutes of makespan for
only 7 capital, no aisle capital spent at all.

D5 adds the open aisle (D4's F=3,G=6,closed retrofit plus the 4-5 edge).
Against D0, its makespan drop (−35, exactly one campaign cadence) comes
from the *combination* of F=3 (more concurrent pipeline slots), G=6 (one
more minute-unit of power headroom, e.g. letting P/Q/robot/oven draws
co-occur that D0's G=5 would refuse), and the short Q↔K path (D5 has both
robots at distance 2 from K, so the plant is not lopsided the way the
closed layouts are). D4 (same F/G, closed aisle) also reaches makespan 152
— aisle alone is not what buys the time here, F and G are — but D5's bill
is lower than D4's (1307 vs 1465) because the open aisle lets Robot 1
reach K faster on average, which shifts more of the run's power draw into
the low-tariff (×1) early windows and avoids some of the ×2/×3 windows
that D4's slower Q-side deliveries fall into. That is exactly why D5, not
D4, wins the unrestricted tie-break on `bill+3·capital` despite costing
6 more capital.

## 8. Causal explanation, tied to delivered trace events

Concrete events from `traces/D0_minute_trace.csv` and
`traces/D0_lot_schedule.csv` (D0; same mechanism recurs in all six):

* t=0: P starts lot0 (family 0, cost 0+5) and Q starts lot1 (family 1,
  cost 0+7) in the same minute — draws 2+3=5=G exactly, so no other new
  start or robot move can be admitted at t=0 even though both robots are
  otherwise idle.
* t=5: P frees (busy_until=5); lot0 enters the P buffer; Robot 0 (sitting
  at its home dock, node 3) picks it up the same minute.
* t=6: Robot 0 moves 3→4 — this is the move that triggers the node-4
  disruption. Its arrival (visible t=7) sets `offline_from=7,
  offline_until=12`.
* t=7..12: Robot 0 does nothing at all (priority 1). Robot 1, which had
  been working its way 5→8→7 toward K with lot1, reaches node 7 at t=9 and
  is then **blocked outright** for t=10,11,12 — not by power, but because
  node 4 (capacity 1) is occupied by the frozen Robot 0. This is a pure
  routing/capacity effect that a distance-based model would not predict:
  Robot 1 is geometrically two steps from K and simply cannot proceed.
* t=13: Robot 0 resumes (vacates node 4, moves to K); in the very same
  minute Robot 1 advances into the now-empty node 4 — the sequential
  robot-0-then-robot-1 resolution captures this hand-off correctly.
* t=14/15: Robot 0 unloads lot0 at K (arrival visible t=15); Robot 1
  unloads lot1 at K (arrival visible t=16).
* t=15: oven idle, no anchor; lot0 (arrived t=15) becomes anchor,
  deadline=17. t=16: lot1 arrives but is family 1 vs. anchor's family 0 —
  no partner. t=17: deadline reached, oven starts lot0 **alone** (size 1),
  drawing 3 of G=5's budget that minute.
* Later in the run (D0's `t_start` column), lot6 does not start until
  t=113 even though it was released at t=35 — a 78-minute wait caused not
  by lack of release but by the F=2 fixture ceiling: with only two
  fixtures plant-wide and each one held from prep-start through
  cure-*end* (not just processing), campaigns 1–3's lots queue up behind
  campaign 0's still-curing lots. This is the F=2 bottleneck visible
  directly in the trace, and it is why D1 (F=3, same G, same aisle) cuts
  16 minutes off the makespan without spending a single unit of capital on
  the aisle.
* The Q-freeze (fires after lot5's completion at t=47, window
  [48,60]) has essentially no visible effect on D0's makespan, because Q
  is already fixture-starved and idle for most of the run (only 2 lots
  ever reach Q) — a second illustration that F, not the Q-freeze or the
  aisle, is D0's binding constraint.

## 9. Why treating the four campaigns as independent resets would be wrong

Section C is explicit that the four campaigns "share one clock" and are
"NOT four independent resets," and the delivered traces confirm exactly
why a reset-per-campaign implementation would produce a different (wrong)
answer:

1. **Machine family memory never resets.** Campaign 1's first lot's setup
   cost depends on whichever family P or Q last processed — which, in our
   traces, is frequently a campaign-0 lot still on the machine's memory
   when campaign 1 releases (campaign s's tail routinely extends past
   campaign s+1's release window, exactly as Section C warns). A
   per-campaign reset would incorrectly zero this memory and give
   campaign s+1's first job setup=0 even when the true remembered family
   differs.
2. **held_fixtures is a single plant-wide counter across the whole run.**
   In D0, campaign 0's lot6 (belongs to s=1) cannot start until t=113
   because F=2 fixtures are tied up by earlier, still-curing lots from
   *other* campaigns. A per-campaign reset would zero `held_fixtures` at
   each campaign boundary, freeing fixture slots that are, physically,
   still occupied by curing lots — understating congestion and producing
   an artificially short makespan.
3. **The node-4 disruption and the Q-freeze each fire at most once for
   the entire run**, not once per campaign. A reset-per-campaign
   implementation would either re-trigger Robot 0's 6-minute freeze up to
   four times (once per campaign) or lose the "first-time" semantics of
   Q_cumulative ≥ 12 entirely, both of which change the bill and makespan.
4. **Robot state (position, cargo) and oven state (mid-cure batch) do not
   reset.** A robot mid-transit or an oven mid-cure at a campaign boundary
   is a real, physical, continuing constraint; resetting it would
   silently free capacity that is not actually free.
5. **Campaigns genuinely contend for the same two machines, two robots,
   and one oven concurrently** — release windows overlap in time by
   design (campaign 1 releases at t=35 while campaign 0's lots are often
   still curing well past t=100 in these results), so at almost every
   minute past t≈35 the pool being evaluated for P/Q assignment mixes
   lots from multiple campaigns, exactly as `global_index = 5s+j` implies
   the plant should treat them: one flat, ordered pool.

We ran a direct empirical check of point 2 above: `certificate_checker.py`
recomputes `held_fixtures` purely from each lot's `[t_start, t_cure_end)`
interval, independent of the simulators' own internal counters, and
confirms F is never exceeded across the whole 20-lot run in any design —
this recomputation would be meaningless/incorrect under a per-campaign
reset, since it depends on cross-campaign overlap being real.

## 10. What a distance-only relaxation loses

A relaxation that scores designs purely by graph distance (e.g., "shorter
Q↔K path ⇒ better") would confidently rank every open-aisle design above
its closed-aisle counterpart on makespan, because Q→K drops from 4 to 2
edges. Our results falsify that at F=2: **D3 (open, F=2, G=5) has
makespan 188, one minute *worse* than D0 (closed, F=2, G=5) at 187** —
despite D3's robot 1 having a strictly shorter path to K. The reason,
visible in the traces, is that with F=2 the fixture ceiling — not robot
travel time — is the binding constraint on throughput; shaving robot
transit time only lets robots idle sooner, it does not let more lots be
*in the pipeline* at once. A distance-only model has no notion of F at
all, so it cannot see this.

More generally, a distance-only relaxation loses:

* **The fixture ceiling F**, which (per §8) is the actual bottleneck at
  F=2 and is completely orthogonal to graph distance.
* **The power ceiling G and the ordered admission pass**, which routinely
  refuses a robot's otherwise-legal move (see `wait(power-refused...)`
  rows in the traces) — a robot can be adjacent to its target and unable
  to move purely because P+Q+oven already exhausted the minute's budget.
* **The node-4 capacity-1 constraint and the one-time 6-minute
  disruption**, whose cost is a *fixed 6 minutes* independent of how far
  away either robot starts — a distance metric assigns it zero cost.
* **The oven's bounded pairing timer**, whose 2-minute window makes
  cure-batch count (and hence total curing minutes) depend on *delivery
  timing coincidence* between two robots, not on any single path length.
* **The tariff's time-of-day structure**, which means two designs with
  identical total power draw can have very different bills purely from
  *when* in the 21-minute tariff cycle that draw lands (this is exactly
  why D5 beats D4 on the tie-break in §7 despite an identical makespan).

## 11. Independent-verifier trace match (all six designs)

`compare_traces.py` runs both `kw_primary_sim.py` and `kw_verifier_sim.py`
— two independently-architected implementations (OOP/deque-BFS vs.
flat-dict/array-BFS; see file docstrings) that share only
`kw_constants.py`'s immutable inputs — and diffs every minute of every
design across 18 state fields (positions, cargo, buffers, K-queue, held
fixtures, busy-until clocks, freeze flag, power draws, oven anchor/
deadline) plus every one of the 20 lots' 9 lifecycle timestamps. Robot
action *labels* are free text and differ cosmetically between the two
files by construction (that is deliberate, to prove independence of
authorship); `compare_traces.py` normalizes those labels to their
semantic action kind (move/pickup/unload/wait-reason/offline) before
comparing, and the underlying position/cargo/power fields are compared
raw, unnormalized, minute by minute.

```
D0: MATCH  makespan(p=187,v=187)  bill(p=1398,v=1398)  minutes=187  minute_mismatches=0  lot_mismatches=0
D1: MATCH  makespan(p=171,v=171)  bill(p=1313,v=1313)  minutes=171  minute_mismatches=0  lot_mismatches=0
D2: MATCH  makespan(p=187,v=187)  bill(p=1427,v=1427)  minutes=187  minute_mismatches=0  lot_mismatches=0
D3: MATCH  makespan(p=188,v=188)  bill(p=1329,v=1329)  minutes=188  minute_mismatches=0  lot_mismatches=0
D4: MATCH  makespan(p=152,v=152)  bill(p=1465,v=1465)  minutes=152  minute_mismatches=0  lot_mismatches=0
D5: MATCH  makespan(p=152,v=152)  bill(p=1307,v=1307)  minutes=152  minute_mismatches=0  lot_mismatches=0
```

Full machine-readable evidence: `verification_report.json`,
`certification_summary.json`. Raw side-by-side evidence: `traces/*.csv`
(primary) vs. `traces_verifier/*.csv` (verifier).

`certificate_checker.py` additionally re-derives, from the trace alone
(not by re-running any dispatch policy), that release constraints,
edge/node capacity, the power ceiling, the fixture ceiling, and the
Q-freeze window all held throughout every one of the six real runs, and
independently recomputes the bill from first principles
(`sum(power(t)·multiplier(t))`) and matches it exactly in every design —
see §12 and `certification_summary.json`.

## 12. Adversarial experiments

**Negative-start experiment** (D0 and D3): took a real, clean, certified
trace and rewrote one lot's recorded start minute to 3 minutes *before*
its release minute (simulating a release-gate bypass). The checker caught
it immediately:
```
NEGATIVE-START: lot4 started at t=1 before its release minute 4
```
(and, as a knock-on consequence of the same corruption, also caught the
resulting fixture-ceiling overshoot — `FIXTURE: held=3 > F=2` — since the
corrupted lot now overlaps two others in the pipeline).

**Route-collision experiment** (D0 and D3), two sub-cases:
* forced both robots' recorded positions to node 4 (capacity 1) at the
  same minute boundary — caught: `ROUTE-COLLISION: node 4 held 2 robots
  (capacity 1) after minute 93` (D0);
* forced both robots to traverse the same physical edge in the same
  minute — caught: `ROUTE-COLLISION: both robots traversed edge (3, 4) at
  minute 6` (D0).

All four corruption sub-experiments across both designs were caught
(`ALL ADVERSARIAL CHECKS CAUGHT: True`); the clean, uncorrupted traces
they were derived from were separately confirmed violation-free before
corruption, so the checker is neither silently permissive nor
over-triggering on valid schedules. Full evidence:
`adversarial/adversarial_report.json`.

## 13. Reproducing every deliverable

```bash
cd /tmp/kilnworks-blind-test-2/work
python3 run_all.py                # traces/*.csv, case_matrix.csv, certification_summary.json
python3 dump_verifier_traces.py   # traces_verifier/*.csv
python3 compare_traces.py         # verification_report.json (+ console MATCH summary)
python3 adversarial_tests.py      # adversarial/adversarial_report.json
python3 selection.py              # case_matrix.json, console selection summary
```

No case answer is embedded anywhere as a shortcut: `kw_constants.py`
holds only inputs taken directly from the packet (graph edges, lot
formulas, draws, tariff function, F/G/capital table); every reported
number is produced by actually executing `kw_primary_sim.py`, and
independently re-produced by actually executing `kw_verifier_sim.py`.
