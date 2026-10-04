# ATRIUM-9 dispatch calibration: engineering memo

Every number below was produced by the delivered code (`out/` after `./run_all.sh`). Nothing was typed in by hand.

## 1. Deliverables and reproduction

| Product | File(s) |
|---|---|
| Simulator source | `atrium9_sim.py`, plus the shared immutable constants in `atrium9_constants.py` |
| Independent verifier source | `atrium9_verify.py`, which imports only `atrium9_constants.py` |
| 144-row sweep table | `out/sweep_144.csv` |
| Decision file | `out/decision.json`: three selections, their keys, every exact tie, and the tie rule |
| Certification evidence | `out/baseline_trace.txt` (the exact hashed serialization), `out/baseline_certificate.json`, `out/baseline_events.jsonl` (per-tick car states and events), `out/baseline_calls.json` (per-call assignment, boarding and alighting), `out/adversarial_results.json`, and the mutant files in `out/mutants/` |
| Memo evidence | `out/baseline_analysis.json`, `out/sensitivity_quiescent_end.json`, `out/figures/figure_measurements.json` |

Run `./run_all.sh` from `work/`. It calls, in order: `atrium9_measure_figures.py ../atrium9.pdf out/figures`, `atrium9_sim.py out`, `atrium9_verify.py out`, `atrium9_mutations.py out`, `atrium9_analysis.py out`, `atrium9_sensitivity.py out`. Run time is about 10 s.

Tools: Python 3.11.15. The simulator and verifier use only the standard library. Figure measurement uses PyMuPDF 1.28.2, Pillow 12.3.0 and numpy 2.4.6.

## 2. Layout and constants

I took these from the figures. `atrium9_measure_figures.py` measures them from the pixels.

* **Fig 1, shaft elevation.** 4 shafts (A to D) and 8 equally spaced floor lines (192 px pitch), labelled L0 to L7. The placard on car A reads "MAX OCCUPANCY 6", so **capacity = 6**. The placards on B, C and D are blank, and I assumed they are identical to A's (the packet says capacity is fixed).
* **Fig 2, door waveform.** The grid pitch is 185 px per tick. The phase edges fall at ticks 0, 4, 6, 9 and 11, which gives:
  * TRAVEL: 4 ticks per floor traversed
  * DOOR OPENING: 2 ticks
  * DWELL: 3 ticks
  * DOOR CLOSING: 2 ticks
* **Fig 3, power draw.** The grid pitch is 176 px per tick, and the y-axis ticks are 222 px per unit. Measured draws:
  * TRAVEL: 2 units/tick for ticks 0 to 4
  * OPENING: 1 unit/tick for ticks 4 to 6
  * DWELL: 0 for ticks 6 to 9
  * CLOSING: 1 unit/tick for ticks 9 to 11

  These line up with Fig 2 tick for tick.

Consequence: the largest possible draw is 2 per car. Budgets of 8, 10 and 12 can never bind for any car count. Budget 6 can bind only when 4 cars are active.

## 3. How I read the policy

The packet leaves the points marked (*) open. Section 7 of this memo lists all of them.

* **Tick order.**
  1. Phases that finished roll over: TRAVEL becomes CLOSED at the new floor, OPENING becomes DWELL, CLOSING becomes CLOSED.
  2. Timeout reassignment runs over assigned, unboarded calls in gidx order (*).
  3. Arrived calls with no assignment are assigned, in gidx order.
  4. Power: phases already in progress keep their draw. Then each car that wants a new hop, door opening or dwell-to-close is admitted in A, B, C, D order if it fits in the remaining budget. A car on its first DWELL tick alights passengers, then boards calls.
  5. Energy is booked for every car that is mid-travel.
* **Position and cost.** A car's position is measured in travel ticks (4 per floor), so a car partway through a hop sits between floors. Cost is the remaining ticks of the current hop plus 4 × |hop target − floor|. Door time is not included (*).
* **Idle** means the car has no commitment in either direction set. Passengers' destinations count as commitments.
* **Scanning D** means the car is not idle and its current scan direction is D.
* **Ahead** means strictly beyond the car's tick position (*).
* **Car just assigned while idle.** It has no scan direction until its next decision, so it is ineligible for other calls during that tick (*).
* **Commitments** are kept as two separate sets per car. UP holds assigned-unboarded UP hall-call origins plus the destinations of UP riders. DOWN holds the same for DOWN.
* **Decision for a stationary, doors-closed car**, at floor p with scan direction d:
  1. If p is in set[d], open the doors.
  2. Otherwise, if any commitment in either set lies strictly ahead in d, hop in d.
  3. Otherwise, switch to the nearest commitment. Ties go to the lower floor, then UP before DOWN (*). If that commitment is at p, set d to its direction and open; otherwise set d toward it and hop.
  4. Otherwise (no commitments), clear d and hop toward home, or stay put if already home.
* **Boarding.** At the first DWELL tick, riders whose destination is p alight. Then calls assigned to this car with origin p and direction d board in ascending gidx order, up to capacity. A call assigned after that first tick waits for the car to close and reopen (*). Capacity never bound: 0 calls were left behind across all 144 runs.
* **Timeout.** A call times out when `t − assigned_at > WAIT_TIMEOUT`. The best eligible alternative excludes the incumbent and every car the call was taken from before. It wins only if its cost is strictly below the incumbent's raw distance cost (*). A move resets `assigned_at` and bans the incumbent for good.
* **End of run.** The run ends at the end of the tick in which the 80th call alights (*). The baseline therefore runs t = 0 to 842, which is 843 trace lines after the header.
* **avg_wait** is the mean of (board tick − arrival tick) over all 80 calls.

## 4. Results

**Baseline (3 cars, TOP, timeout 50, budget 8):**
* avg_wait = 27.725
* net_energy = 4692
* max_wait = 90
* last tick = 842
* SHA-256 = `99ad92a22be75118b8fd8fbe578b75041a9f17f7b8b0995d3c3dbdcacb7ccd20`
* **Certificate = `99ad92a22be75118`**

Hash input: the header `CONFIG:{'active_cars': 3, 'zoning': 'TOP', 'wait_timeout': 50, 'capacity': 6, 'power_budget': 8}`, then `t,power,energy` lines joined with `\n`, no trailing newline, UTF-8.

**Selections (from `decision.json`):**

| Selection | Configuration | avg_wait | net_energy | Exact-key ties |
|---|---|---|---|---|
| Wait-optimal | 4 cars, SPLIT, timeout 50, budget 8 | 15.1375 | 5484 | 12 (4/SPLIT, any timeout, budget 8, 10 or 12) |
| Energy-optimal | 2 cars, SPLIT, timeout 50, budget 6 | 43.325 | 2952 | 16 (2/SPLIT, any timeout, any budget) |
| Budget-constrained (energy ≤ 3800) | 2 cars, TOP, timeout 50, budget 6 | 37.3 | 2988 | 16 (2/TOP, any timeout, any budget) |

Only 48 of the 144 configurations meet the 3800 ceiling, and all of them are 2-car runs. The cheapest 3-car run uses 4371.

**Whole-sweep totals:**
* Σ net_energy = 625380
* Σ total_wait = 322732
* 12 timeout reassignments, all in GROUND zoning with timeout 50
* 2740 power denials, all in the 12 configurations with 4 cars and budget 6
* 0 calls left behind by capacity

## 5. Verification

`atrium9_verify.py` is a separately written engine. It uses timer-based phases and per-direction commitment multisets that it updates incrementally, built from plain dicts. It shares only `atrium9_constants.py` with the simulator. It re-derives the 80-call table from the packet formulas and checks the following:

* the header text and that ticks run continuously
* power ≤ budget on every tick
* per-tick energy stays within physical bounds
* each call's origin, direction, arrival and destination match the formulas
* no call boards before it arrives, and every call alights after it boards
* the car a call boards is the car it is assigned to, and never a car it was reassigned away from
* no car exceeds capacity
* reported avg_wait and net_energy match the trace, and the certificate matches the hash
* the trace is byte-identical to the verifier's own re-simulation, and per-call board/alight ticks match it
* all 144 sweep rows (avg_wait, net_energy, per-run trace hash) and all three selections match its recomputation

Results (`out/adversarial_results.json`):

| Case | Mutation | Verdict | Violations reported |
|---|---|---|---|
| M0, control | none: primary's baseline as delivered | ACCEPT, exit 0 | none; independent hash `99ad92a22be75118…` is identical |
| M1 | call 1 boards at t=7; its arrival is t=8 (true boarding t=38) | REJECT, exit 1 | "call 1 boards at t=7 before its arrival t=8", plus a mismatch with the re-simulation |
| M2 | tick 16 power changed from 6 to 9; budget is 8 | REJECT, exit 1 | "tick 16 power 9 exceeds budget 8", plus a trace mismatch at line 17 |

The full verifier run, which includes the 144-row sweep check, returns ACCEPT.

## 6. Why the three selections diverge, tied to baseline events

**1. Under these rules, extra cars only rescue calls that sit unassigned, and every rescue is an empty trip.** A car scanning the opposite direction, or one that has already passed the floor, is ineligible. So a hall call can stay unassigned until some car goes idle, and the car that goes idle is usually far away.

* In the baseline, call 70 (L7 DOWN, arrived t=680) went unassigned until t=717. Car B was physically climbing to L7 to serve call 69 (L7 DOWN): it arrived at t=692 and boarded call 69 at t=694. B could not take call 70 because B was scanning UP, and once it reversed at L7, L7 was no longer "ahead".
* A went idle at L0 at t=717 and took call 70 at cost 28. It made an empty seven-floor climb and boarded call 70 at t=765, a wait of 85.
* Call 71 played out the same way through B from L0: assigned at t=744, boarded at t=778, a wait of 90, the baseline worst.

A fourth car lowers the chance that every car is unsuitable at once. That drives avg_wait down to 15.1375 for 4/SPLIT. The cost is more empty legs and more homing trips: 265 homing travel ticks versus 63 in the baseline, and 5484 energy units.

**2. TOP zoning makes every L0 UP burst expensive.**
* At t=0 car A leaves L7 for call 0 (L0 UP). Once it is moving down it counts as scanning DOWN, so it is ineligible for calls 1 and 2 (also L0 UP).
* B (t=8) and C (t=16) are each sent down empty as well. Trace lines t=16 to 27 show power 6 and energy 9: three empty cars descending at once. This is also the baseline's peak power.
* Call 2 waits 44.

Because of this, TOP costs energy relative to SPLIT, which parks A at L0. Across the baseline, empty service travel adds 1995 energy units, against 2508 from loaded travel.

**3. Energy-optimal versus budget-constrained.** With 2 cars, SPLIT is the cheapest (2952) but has the worst wait (43.325). 2/TOP costs only 36 units more (2988) and cuts avg_wait to 37.3, so it wins once the ceiling admits any 2-car run. No 3-car or 4-car run comes close to 3800, so the ceiling, not the zoning, decides the car count.

**4. The power budget matters only for 4 cars at budget 6.** Hops, openings and door-closes are delayed there: 161 power denials and 49 close denials in 4/SPLIT. That lowers energy to 5148 but raises wait to 19.5625. This is why the wait-optimal pick has budget ≥ 8. The baseline (3 cars) never draws more than 6, so its budget of 8 is slack.

## 7. Open points in the packet and the readings I chose

1. **Ties in the selection keys.** wait_timeout almost never changes the outcome, and the budget never does below 4 cars. That leaves exact ties of 12 or 16 configurations. The packet gives no third key. I used canonical sweep order (smallest car count, then SPLIT, GROUND, TOP, then smallest timeout, then smallest budget) and listed every tie in `decision.json`.
2. **End of run.** The packet does not say. I used the last alighting tick. If the run instead continues until every car is parked home with doors closed, the baseline certificate becomes `c86737e4a78ebd02` (avg_wait and energy unchanged), and energy-optimal flips to 2/TOP/50/6 (`out/sensitivity_quiescent_end.json`).
3. **Travel time per floor.** Fig 2 shows a single 4-tick TRAVEL bar labelled "per floor traversed". I read this as 4 ticks per floor.
4. **Capacity.** Only car A's placard is printed.
5. **Cost.** The packet says "distance in ticks". I left out door and dwell time and ignored the stops already planned along the way.
6. **"Ahead".** I used a strict comparison, so a car's current floor does not count as ahead.
7. **Incumbent's recomputed cost.** I used the incumbent's raw distance, even when the incumbent is not eligible itself.
8. **Order within a tick.** I ran reassignment before new assignment, and dispatch before car decisions.
9. **Scan direction of a car that has just been assigned.** It stays unset until the car's next decision.
10. **Tie-break for "switch to the nearer remaining commitment".** The packet gives none. I used lower floor first, then UP before DOWN.
11. **Late arrivals at a floor during DWELL.** Boarding is defined only for the first DWELL tick, so a call assigned later waits for the doors to close and reopen.
12. **Who boards.** Only calls assigned to that car board. Unassigned riders waiting at the same floor do not.
13. **What a trace line contains.** A line is the sum over cars of power and energy, one line for every tick from 0 to the end, including ticks where both are zero.
14. **Inactive cars.** They sit at their zoning home, draw nothing and never appear in the trace.

## 8. Why door-closing must be power-gated

If DWELL turned into CLOSING automatically, the close would draw power without being admitted. I tested this in the counterfactual engine in `atrium9_analysis.py`, with timeout 50:

| 4-car configuration at budget 6 | Ticks over budget | Peak power |
|---|---|---|
| SPLIT | 12 | 7 |
| GROUND | 19 | 7 |
| TOP | 22 | 7 |

The first breach comes at t=99 for SPLIT. Such a trace breaks the shared-budget contract and would be rejected, as M2 is. The breach happens because admission is checked only when a phase starts. A close that is not admitted stacks on top of hops that were admitted against the same tick's budget.

The waits would also change (18.3 versus 19.5625 for 4/SPLIT/6). That would contaminate the selections: a cheaper-looking configuration would actually be infeasible.

Gating also matters for correctness in another way. A car held in DWELL keeps its doors open and its position fixed, so cost and eligibility at that floor stay valid. An automatic close would let a car leave while the controller still believes it is there. In the baseline at budget 8 the gate never binds, so the baseline trace itself is unaffected.

## 9. Why a reassigned call must never return to its old car

When a call is reassigned, its commitment leaves the incumbent's direction set. The incumbent's scan plan moves on: it may switch direction, or go idle and head home. Concrete case, 2/GROUND/50/6 at t=125: call 8 (L6 UP) moved from A to B (cost 19 versus 12). A was still at L1, scanning UP, below L6, so it was "nearby".

If A were later allowed to take call 8 back, three things go wrong:

* **Ping-pong.** The timeout clock resets on every move. The call could bounce A → B → A without ever being served. That is the livelock the strict-improvement rule exists to prevent, and it is defeated if old incumbents are allowed back in.
* **Double stops.** A and B could both hold a stop for the same call. One car would open its doors at L6 for nobody, wasting door power from the shared budget and energy.
* **Broken determinism.** Ownership would then depend on which car arrives first rather than on the assignment record. The verifier's check "boarded by the assigned car, never by a banned car" would then be undecidable.

The ban makes each call's assignment history strictly monotone: each car can lose a call at most once, so a call can be reassigned at most 3 times. That keeps every run finite and certifiable.

## 10. Confidence

**High** that the code faithfully runs my stated reading:
* Two independently written engines agree on all 144 runs, matching the trace hash for every run.
* The verifier accepts the delivered baseline and rejects both mutations.

**Moderate** that my numbers match the packet author's intended reference values. Points 1, 2, 6, 7, 8, 9 and 10 in section 7 are genuine underspecifications, and several of them (end of run, strict "ahead", and when an idle car's scan direction is set) can move avg_wait, energy or the certificate. Point 2 is shown to do so.
