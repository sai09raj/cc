# ATRIUM-9 semantic contract

Building: 8 floors (0=ground .. 7=top), 4 elevator cars (A=0, B=1, C=2, D=3).
Every rule below is fully deterministic given a configuration; there is no
free scheduling choice inside one run. The only genuine decision space is
the CONFIGURATION SWEEP (S07): which cars are in service, zoning, the
reassignment timeout, and the power budget.

## S01 — Call generation (workload, algorithmic)

Four campaigns `s=0..3`, twenty calls each (`k=0..19`), 80 calls total,
indexed by `gidx = 20*s + k`. Calls are grouped in threes that share the
same origin floor and direction (a burst of near-simultaneous requests at
one floor), so `group = k // 3` (the last group in each campaign has only 2
members, since 20 is not a multiple of 3).

```
origin(s,k)   = (3*group + 2*s) mod 8, where group = k // 3
direction(s,k) = UP   if origin == 0
               = DOWN if origin == 7
               = UP   if (group + s) is even, else DOWN     (otherwise)
arrival(s,k)  = 200*s + 8*k
span(s,k)     = 1 + ((5*k + 3*s) mod 7)
dest(s,k)     = min(7, origin + span)   if direction == UP, and if this
                equals origin, min(7, origin+1) instead
              = max(0, origin - span)   if direction == DOWN, and if this
                equals origin, max(0, origin-1) instead
```

A call's destination is only REVEALED at boarding (S05); it is not known to
the dispatch policy at assignment time (S02), matching how a real hall call
only states origin+direction, not destination.

## S02 — Hall-call assignment (which car serves this call)

A car is ELIGIBLE for a pending call `(floor, direction)` at tick `t` iff:

- the car is ACTIVE (S07) and has no committed stops in either direction
  (idle): always eligible, cost = `|car.pos - floor| * T_FLOOR`; or
- the car is currently scanning `direction` (has a nonempty commitment set
  in that direction and last moved that way) AND `floor` still lies ahead
  of the car's current position in that direction (`floor >= pos` if UP,
  `floor <= pos` if DOWN): cost = travel distance in ticks plus
  `(T_DOOR_OPEN+T_DWELL+T_DOOR_CLOSE)` for every already-committed stop of
  that same direction lying between the car's position and `floor`
  inclusive.
- A car scanning the OPPOSITE direction, or that has already passed
  `floor` in its current direction, is NOT eligible this tick (no
  backtracking mid-scan; the call must wait for a fresh eligible car).

Assign to the minimum-cost eligible car; tie-break by lowest car ID. A call
with no eligible car this tick is retried every subsequent tick until one
becomes eligible. Assignment adds `floor` to the assigned car's commitment
set for `direction` (S03) and the call to that car's waiting set for
`(direction, floor)`.

## S03 — Per-car movement (independent state machine, one per active car)

Each car tracks TWO SEPARATE commitment sets, `committed[UP]` and
`committed[DOWN]` — a floor needed while scanning up is a different
commitment from the same floor needed while scanning down, because a call's
direction is fixed at assignment (S02) and must not be confused with
whichever way the car physically happens to be facing when it later reaches
that floor. Boarding (S05) only serves calls whose OWN required direction
matches the SPECIFIC commitment set the car is currently scanning.

Every tick, an idle-or-just-freed car (doors CLOSED, not mid-hop) picks its
next action, freshly re-derived (not persisted): continue the current scan
direction only while a commitment remains ahead of it in THAT direction's
own set; otherwise switch to whichever direction holds the nearest
remaining commitment (ties broken toward the lower floor number... more
precisely: nearest by floor distance, then by direction UP before DOWN);
otherwise, with no commitments in either direction, head toward the car's
home floor (S06) and go idle there.

If the car's current position is already a member of the commitment set for
the direction it is about to scan, it opens its doors there (S04) instead
of moving. Otherwise it moves exactly one floor toward that commitment,
taking `T_FLOOR` ticks, uninterruptible once started (S08 exempts an
in-progress hop from power admission).

## S04 — Door cycle (per car)

Fixed sequence once a stop starts: OPENING (`T_DOOR_OPEN` ticks) -> DWELL
(`T_DWELL` ticks, boarding+alighting happen atomically at its first tick,
S05) -> CLOSING (`T_DOOR_CLOSE` ticks) -> CLOSED. No dwell extension exists
in this packet. Starting OPENING and starting CLOSING (the transition out
of DWELL once its ticks have elapsed) are each their own power-admission
events (S08); DWELL itself draws no power and, once OPENING has been
admitted, proceeds to DWELL unconditionally after `T_DOOR_OPEN` ticks.
Closing is NOT automatic: a car that has finished its dwell only leaves
DWELL once its door-close is itself admitted by the power budget that tick;
until then it continues to sit in DWELL (this is the packet's single most
commonly mis-implemented rule — see the negative-trap criterion).

## S05 — Boarding and alighting (atomic, at the first DWELL tick)

At the instant a car enters DWELL at floor `F` scanning direction `D`:
first BOARD, in ascending call-`gidx` order, every call currently waiting
in the car's `(D, F)` waiting set, up to the car's remaining capacity
(`CAPACITY=6`, fixed for every configuration, not swept); a call that
cannot board due to capacity remains assigned and waiting, to be attempted
again the next time this same car reopens at `(D, F)`. Each boarded call
adds its own `dest` floor to `committed[D]` (a car call). Then ALIGHT: any
already-boarded call whose `dest == F` under this same `(car, D)` pair
completes; its passenger leaves, freeing capacity. Boarding and alighting
in the same dwell do not interact (a boarding passenger cannot alight at
the same stop, since every call's destination differs from its origin by
construction).

## S06 — Zoning (idle parking policy, a sweep knob)

| Policy | Home floors (car A,B,C,D) |
|---|---|
| SPLIT | 0, 2, 5, 7 |
| GROUND | 0, 0, 0, 0 |
| TOP | 7, 7, 7, 7 |

An inactive car (S07) never moves and is never eligible for assignment.

## S07 — Active car count (a sweep knob)

`ACTIVE_CARS` in {2,3,4} selects the LOWEST-ID cars into service (2 = A,B
only; 3 = A,B,C; 4 = all). An inactive car plays no role in any tick.

## S08 — Power admission (shared cross-car resource, one ordered pass/tick)

Building power budget `G` (a sweep knob) caps total simultaneous draw.
Draws: a car mid-floor-hop = 2/tick for every tick of that hop (mandatory,
already admitted when the hop started); a car in OPENING or CLOSING = 1/tick
(mandatory once admitted); DWELL and CLOSED draw 0. Each tick, mandatory
ongoing draws are honored first (never interrupted). Any NEW event this
tick — starting a floor-hop, starting door-OPENING, or transitioning DWELL
to CLOSING once its dwell ticks have elapsed — is admitted from whatever
budget remains, in fixed car priority A, B, C, D. A refused new event simply
waits (retries next tick); it is never cancelled or penalized. Total draw
must never exceed `G` in any tick.

## S09 — Timeout reassignment (non-combinable, cost-compared)

Every tick, for every call still `assigned` (not yet boarded) whose current
assignment is `>= WAIT_TIMEOUT` ticks old (a sweep knob), recompute the
best ALTERNATIVE eligible car (S02's cost formula, excluding the
incumbent). Reassign ONLY if that alternative's cost is strictly lower than
the incumbent's OWN current recomputed cost (a car already optimal for a
call is not artificially bounced to a different, equally- or less-suitable
car merely because the clock ran out — see the negative trap). On genuine
reassignment: retract the call from the incumbent's waiting/commitment
sets (dropping the commitment entirely if no other call or car-call still
needs it), assign it fresh to the new car with a new assign-tick, and
increment its attempt counter. If the incumbent remains best, its
assign-tick is simply refreshed (no reassignment, no attempt increment) so
the same call is not re-evaluated every single tick indefinitely. A call
already reassigned away from a car is never later served by that car, even
if that car happens to still be en route to the same floor for an unrelated
reason.

## S10 — Energy accounting

Every tick a car is mid-hop: `energy += 3 + 1*load` if moving UP, `energy +=
3 - 1*load` if moving DOWN (net regenerative credit for a loaded descent,
via the counterweight). Door-cycling and dwell draw power (S08) but are not
separately counted in the energy total. `net_energy` is the running sum
over the whole run, and may be reduced by regeneration but the simulation
never produces a negative running total for any of the 144 legal
configurations (an incidental fact, not a rule to special-case).

## S11 — Termination and metrics

A run ends the first tick every one of the 80 calls has alighted and no car
is mid-hop, mid-door-cycle, or holding any commitment (`makespan` = that
tick + 1). `avg_wait = (sum over all 80 calls of (board_tick - arrival)) /
80`. Report `avg_wait` to at least 4 decimal places; tolerance for
comparison is ±0.01.

## S12 — Investment selection (the search)

The configuration space is the Cartesian product `ACTIVE_CARS x ZONING x
WAIT_TIMEOUT x POWER_BUDGET` = `{2,3,4} x {SPLIT,GROUND,TOP} x
{50,75,100,125} x {6,8,10,12}` = 144 legal configurations, `CAPACITY=6`
fixed across all of them. Execute every one. Three selections, each
minimized lexicographically over `(primary metric, secondary metric,
active_cars, zoning, wait_timeout, power_budget)` for a deterministic
tie-break:

- **Wait-optimal**: minimize `avg_wait`, tie-break by `net_energy`.
- **Energy-optimal**: minimize `net_energy`, tie-break by `avg_wait`.
- **Budget-constrained**: minimize `avg_wait` among only configurations
  with `net_energy <= 3800`, tie-break by `net_energy`.

These three selections are not required to agree, and in the reference
they do not: more cars in service lowers wait but raises energy draw, a
genuine non-monotonic tradeoff a solver must actually search for, not
assume.

## S13 — Trace-integrity hash (fully specified so a solver can compute it)

For the BASELINE configuration `(active_cars=3, zoning=TOP, wait_timeout=50,
power_budget=8, capacity=6)` only: serialize the complete per-tick trace as
one line per tick, `t,power,energy`, in execution order (`energy` is that
tick's own signed energy contribution from S10, not a running total),
preceded by a single header line `CONFIG:{'active_cars': 3, 'zoning':
'TOP', 'wait_timeout': 50, 'capacity': 6, 'power_budget': 8}` (Python
`dict.__str__` formatting, this exact key order), each line separated by
`\n`, UTF-8 encoded, hashed with SHA-256. Report the first 16 hex
characters.
