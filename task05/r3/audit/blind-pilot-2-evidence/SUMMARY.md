# SUMMARY — KILNWORKS R3 blind test

Full engineering memo: `MEMO.md`. This file is the condensed run record
requested for hand-off.

## Graph / rule interpretation

3x3 grid (Section A): permanent edges `0-3,1-4,2-5,3-4,3-6,4-7,5-8,6-7,7-8`;
open-aisle designs (D3,D5) add `4-5`. Docking bays P(3)/Q(5)/K(1) hold 2
robots; interior junction node 4 holds 1 (the only ever-binding capacity
constraint, since the plant has just 2 robots). K's only edge is to node 4,
so every delivery passes through the junction in every design.

Node-4 disruption (Section E): the illustrative chart's shaded span runs
gridline x=3 to x=9 -> 6 minutes, read directly off the axis. It applies
once, only to Robot 0, starting at its first arrival at node 4 (inclusive of
that arrival minute, which itself follows the plant's default t->t+1 action-
visibility rule). Verified in-trace: e.g. D0 -- Robot 0 decides its move into
node 4 at t=6, is frozen t=7..12 (6 minutes), resumes t=13.

Timing conventions actually implemented (deliberately checked per-mechanism,
not assumed uniform): robot-action effects and the Q-freeze onset (a
derived effect) are visible at t+1; machine-finishes and oven-finishes (a
primary boundary event) take effect immediately at their own boundary
minute -- this reading is what makes Section E's and Section H's superficially
different phrasing consistent (see MEMO.md section 3 for the full derivation).

## Six designs' (makespan, bill)

| Design | F | G | Aisle | Capital | Makespan | Bill |
|---|---|---|---|---|---|---|
| D0 | 2 | 5 | closed | 0  | 187 | 1398 |
| D1 | 3 | 5 | closed | 7  | 171 | 1313 |
| D2 | 2 | 6 | closed | 9  | 187 | 1427 |
| D3 | 2 | 5 | open   | 6  | 188 | 1329 |
| D4 | 3 | 6 | closed | 16 | 152 | 1465 |
| D5 | 3 | 6 | open   | 22 | 152 | 1307 |

## Investment selections

Key formula (Section G): (makespan, bill + 3*capital, capital, design_id),
minimized lexicographically.

* Unrestricted: D5, key = (152, 1373, 22, 'D5') -- ties D4 on makespan
  152, wins tiebreak on bill+3*capital (1373 < 1513).
* Budget (capital <= 9): D1, key = (171, 1334, 7, 'D1') -- strictly
  lowest makespan among {D0, D1, D2}, no tie needed.

Both computed by selection.py from the primary simulator's actual
executed output (case_matrix.csv / case_matrix.json), never hardcoded.

## Verifier match

kw_verifier_sim.py is a second, independently-architected implementation
(flat structure-of-arrays state, array-based BFS, independent tie-break
code) sharing only kw_constants.py's immutable inputs with the primary.
compare_traces.py diffs both traces minute-by-minute across 18 state
fields plus all 20 lots' 9 lifecycle timestamps, for all six designs:

D0: MATCH  minute_mismatches=0  lot_mismatches=0  (187 minutes)
D1: MATCH  minute_mismatches=0  lot_mismatches=0  (171 minutes)
D2: MATCH  minute_mismatches=0  lot_mismatches=0  (187 minutes)
D3: MATCH  minute_mismatches=0  lot_mismatches=0  (188 minutes)
D4: MATCH  minute_mismatches=0  lot_mismatches=0  (152 minutes)
D5: MATCH  minute_mismatches=0  lot_mismatches=0  (152 minutes)

certificate_checker.py additionally re-derives, purely from the recorded
trace (not by re-running any dispatch policy), that release constraints,
edge/node capacity, the power ceiling, the fixture ceiling, and the Q-freeze
window all held in all six real runs, and independently recomputes the bill
from sum(power(t)*multiplier(t)), matching exactly in all six
(certification_summary.json).

## Adversarial experiments

* Negative-start (D0, D3): rewrote a real trace's lot4 start time to 3
  minutes before its release; checker caught it
  (NEGATIVE-START: lot4 started at t=1 before its release minute 4), plus
  the resulting fixture-ceiling overshoot as a knock-on effect.
* Route-collision (D0, D3), two sub-cases: forcing both robots onto
  node 4 (capacity 1) simultaneously, and forcing both robots to traverse
  the same edge in the same minute. Both caught in both designs
  (ROUTE-COLLISION: node 4 held 2 robots..., ...traversed edge (3, 4)...).
  The same traces were confirmed violation-free before corruption.
  ALL ADVERSARIAL CHECKS CAUGHT: True. Full detail: adversarial/adversarial_report.json.

## Causal explanation (condensed; full version with more events in MEMO.md section 8)

D0's bottleneck is the fixture ceiling F=2, not travel distance or
power: lot6 (released t=35) does not start prep until t=113 -- a 78-minute
wait -- because F=2 fixtures are held continuously from prep-start through
curing-end by earlier lots, including ones from other campaigns (the plant
is one shared pipeline). D1 (F=3, same G/aisle) removes exactly this
bottleneck: Q's job count rises 2->5, oven size-2 batches appear (0->8, more
lots in flight within the 2-minute pairing window), and makespan drops 187->171
for only 7 capital. D5's further improvement to 152 comes from combining
F=3, G=6 (more concurrent power headroom) and the open aisle's short Q<->K
path; D5 beats D4 (same F/G, closed) on bill despite an identical makespan
because the open aisle shifts more of Robot 1's deliveries earlier in the
tariff cycle, landing more power draw in the x1/x2 windows instead of x3.

Independent-reset fallacy: campaigns share machine family-memory,
plant-wide held_fixtures, the once-only node-4 disruption and Q-freeze
triggers, and continuing robot/oven state -- none of which are per-campaign.
D0's lot6 stall (above) is itself cross-campaign congestion; a per-campaign
reset would zero it away and understate makespan.

Distance-only relaxation loses the fixture ceiling entirely: D3 (open
aisle, F=2) has makespan 188, one minute worse than D0 (closed, F=2) at
187, despite Q's robot having a strictly shorter path to K in D3. At F=2 the
pipeline's fixture slots -- not robot travel time -- set the pace, so shaving
transit time buys nothing. A distance-only model, plus the power ceiling's
ordered admission refusals, the node-4 disruption's fixed 6-minute cost, and
the tariff's time-of-day shape, are all invisible to a pure shortest-path
metric.

## Deliverable files (all under /tmp/kilnworks-blind-test-2/work/)

* kw_constants.py -- shared immutable inputs only (graph, lot formulas, draws, tariff, F/G/capital table)
* kw_primary_sim.py -- primary simulator (source + `python3 kw_primary_sim.py` prints headline numbers)
* kw_verifier_sim.py -- independent verifier (second implementation)
* certificate_checker.py -- independent feasibility-certificate checker
* compare_traces.py, verification_report.json -- full trace-match evidence
* adversarial_tests.py, adversarial/adversarial_report.json -- negative-start & route-collision experiments
* selection.py, case_matrix.json, case_matrix.csv -- six-design case matrix and both selections
* run_all.py, dump_verifier_traces.py -- reproduction drivers
* traces/<D>_minute_trace.csv, traces/<D>_lot_schedule.csv -- full primary per-design schedules
* traces_verifier/<D>_minute_trace.csv, traces_verifier/<D>_lot_schedule.csv -- full verifier per-design schedules
* certification_summary.json -- clean-trace certificate + trace-match summary, all six designs
* MEMO.md -- full engineering memo
* page1_graph.png, page4_chart.png -- cropped source figures used for the graph and disruption-window reads
