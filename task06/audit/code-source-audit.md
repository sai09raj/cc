# ATRIUM-9 code→source audit (run during task11 calibration)

Method: every material branch, ordering, metric, and termination rule in
`reference/atrium_sim.py` was checked against the full text of
`artifact/atrium9.pdf` (two prose pages) and its three figures (shaft
elevation, door-timing waveform, power-draw bars). Playbook 04, "The
source-to-code audit", both directions.

## Reference behavior with no visible source

| ID | Reference behavior (`atrium_sim.py`) | What the packet says | Effect |
|---|---|---|---|
| H1 | A scanning car's assignment cost is travel distance **plus 7 ticks (door open 2 + dwell 3 + close 2) for every committed stop in that direction between the car and the call floor, inclusive** (`eligible_cost`, lines 114–136). | Cost is defined only for an idle car ("cost = distance in ticks"). | Every assignment and every timeout comparison involving a busy car; every sweep row. |
| H2 | `avg_wait` = sum over all 80 calls of (board tick − arrival tick) ÷ 80 (lines 263, 400). | `avg_wait` is the primary selection metric and is never defined (origin, end event, population, rounding). | Wait-optimal and budget-constrained selections; every `avg_wait` criterion and aggregate. |
| H3 | Fixed per-tick stage order: finish hops and door phases (with boarding and alighting) → assign new arrivals → retry pending calls → timeout reassignment → power admission (ongoing draws first) → energy accounting. | No stage order is given. | Same-tick interactions across the whole run. |
| H4 | Timeout fires at `t − assign_tick ≥ WAIT_TIMEOUT`; if no strictly cheaper car exists, the call's assignment clock **resets** to `t`; if the incumbent is no longer eligible, any eligible alternative wins. | "aged past WAIT_TIMEOUT" (suggests strictly greater); no reset rule; no ineligible-incumbent rule. | When and how often reassignment happens. |
| H5 | When switching direction, the nearest commitment is chosen with ties broken by direction name (DOWN before UP); at a committed floor, UP is preferred if committed there. | "switch to the nearer remaining commitment", no tie-break. | Car routing whenever two commitments are equidistant. |
| H6 | A car that finishes a hop onto a committed floor starts door OPENING **immediately, without power admission** (lines 230–235). | "starting door OPENING … [is] its own power-gated event". | Direct contradiction between packet and reference. |
| H7 | The run, its trace, and makespan end at the first tick where all calls are done and every car is closed with no commitments. | No termination rule; the baseline trace hash covers the whole trace. | Trace length, hence the certificate hash. |

## Visible rule the reference does not implement

| ID | Packet | Reference |
|---|---|---|
| U1 | "A call reassigned away from a car is never later served by that same car." | No ban is tracked anywhere; a later timeout can hand the call back to a car it was reassigned away from. |

## Consequence

H1 and H2 alone touch every sweep row and the primary selection metric, so
the whole-sweep aggregate block (130 of 266 positive points) and all three
selections depend on unstated rules. The two real pilots' 20% and 21% (with
different wrong answers from each other, consistent with each guessing
different unstated rules) cannot be read as legitimate difficulty evidence.
This is the same failure class as QUORUM-7 (Playbook mistakes #4 and #71)
and Task 02 Revision C.

## Solver-side confirmation (`opus`-alias blind pilot, frozen packet)

Deliverables archived in `audit/calibration-probe-opus/`. The pilot built a
simulator and an independent verifier that agree on all 144 runs, and it
listed 20 ambiguities. Those that line up with the gaps above:

| Gap | Pilot's reading | Reference |
|---|---|---|
| H1 busy-car cost | travel distance only, no stop overhead | distance + 7 ticks per committed stop in range |
| H2 avg_wait | board − arrival averaged over 80 calls (matches by luck) | same |
| H3 stage order | rollover → timeout → assignment → power → energy | completions → assignment → retry → timeout → power → energy |
| H4 timeout | `> timeout`, age reset only on reassignment | `≥ timeout`, age also reset when no switch happens |
| H5 direction tie-break | lower floor first, then UP | nearest, then DOWN before UP |
| H7 run end | when the 80th call alights (showed the alternative changes the hash and the energy-optimal pick) | first tick all calls done and all cars closed and uncommitted |

It also found gaps the code audit had not listed: no tie-break for the
three selections (12–16 configurations tie exactly on each key), and
whether "ahead" includes the car's own floor (it used strictly ahead; the
reference uses `>=`, inclusive).

Its results match the real pilots' failure pattern: wait-optimal
(4, SPLIT, 50, 8) with avg_wait 15.14, the same configuration real
trajectory 20 chose (15.25; trajectory 21 had 15.89), against the
reference's (4, SPLIT, 50, 6) at 8.1375; energy-optimal (2, SPLIT), the
same as trajectory 20. This is the second calibration (after QUORUM-7)
showing the `opus` alias fails where and how the real target model fails.

**Conclusion:** ATRIUM-9's 20% and 21% are substantially explained by
unstated rules, like QUORUM-7's 31% and 32%. Neither task is evidence that
a fully specified simulation holds the target model below 50%.
