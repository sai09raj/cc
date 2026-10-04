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

An `opus`-alias blind pilot on the frozen packet is running to confirm from
the solver side which of these gaps actually change a careful solver's
answer.
