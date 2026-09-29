# CISTERN-7 semantic contract

Executable contract for the reference oracle. Every rule below must be
visibly recoverable from the packet (chart, table, or stated prose); this
file is the internal design source, not the artifact itself.

## S01 — Simulation resolution and horizon

One simulated day is exactly `1440` ticks of `1` minute each, `t=0` (00:00)
through `t=1439` (23:59), run to completion with no early termination. Each
of the 108 legal configurations (S08) is one continuous, independent
1440-tick run — never a shortened or sampled run.

## S02 — Wet-well geometry and level state

The wet well is a vertical tank of constant plan area `A = 12.0 m^2`.
`level(t)` (meters, measured from the invert) is a single continuous state
variable, carried tick-to-tick (never reset within a run):

```
level(t+1) = clamp(level(t) + (Q_in(t) - Q_out(t)) * dt / A, LOW_CUTOFF, HIGH_HIGH)
```

with `dt = 1` minute, `LOW_CUTOFF = 0.4 m`, `HIGH_HIGH = 4.2 m` (the overflow
elevation, S06). `Q_in(t)` is the inflow hydrograph (S01a below); `Q_out(t)`
is the sum of every currently-running pump's discharge at `level(t)` (S03).

## S01a — Inflow hydrograph (the workload)

`Q_in(t)` for `day_type=DRY` is linearly interpolated (m^3/min) between these
anchor points on the 24h axis (minutes since 00:00):

| minute | 0 | 180 | 330 | 480 | 600 | 780 | 1080 | 1200 | 1320 | 1439 |
|---|---|---|---|---|---|---|---|---|---|---|
| Q_in | 0.5 | 0.5 | 2.5 | 6.0 | 3.5 | 3.0 | 5.5 | 4.0 | 1.5 | 0.5 |

For `day_type=WET`, add a triangular storm surcharge on top of the DRY
curve, zero outside `[300,420]`, ramping linearly to a peak of `+8.0 m^3/min`
at minute `360`, back to zero at minute `420`. `Q_in` is never generated as a
discrete list; it is this continuous function, sampled once per tick — a
materially different "workload" shape from a discrete arrival list.

## S03 — Pump curve and staging (the control loop)

Three identical pumps A, B, C. Each pump's discharge while running is
interpolated (m^3/min) from `level(t)` against its own curve:

| level (m) | 0.4 | 2.0 | 4.2 |
|---|---|---|---|
| Q_pump | 3.0 | 4.0 | 5.0 |

(Static lift decreases as the well fills, so discharge rises with level;
linear interpolation between breakpoints, no extrapolation needed since
`level` is clamped to `[0.4, 4.2]`.) A pump that is not running discharges
zero regardless of level. A pump may never start while `level < LOW_CUTOFF`
(dry-run protection) — this is already enforced by the clamp in S02, since
level never goes below `LOW_CUTOFF`.

Each pump fills one of three staging roles each tick: LEAD, LAG1, LAG2, or
OFF-ROSTER (S08's `duty_pump_count` limits how many roles beyond LEAD are
ever assignable). Role assignment is re-derived fresh at the instant a new
lead is selected (S05); LAG1/LAG2 are always assigned to the remaining
in-roster pumps in ascending pump-ID order among those not filling LEAD.

Start/stop elevations per role are set by the swept `deadband` (S08):

| deadband | LEAD start / stop | LAG1 start / stop | LAG2 start / stop |
|---|---|---|---|
| TIGHT | 1.2 / 0.8 | 1.8 / 1.4 | 2.4 / 2.0 |
| MEDIUM | 1.5 / 0.7 | 2.2 / 1.2 | 3.0 / 1.8 |
| WIDE | 2.0 / 0.6 | 3.0 / 1.0 | 3.8 / 1.6 |

A pump in a given role starts when `level(t) >= role_start` and it is
currently off; it stops when `level(t) <= role_stop` and it is currently
running — EXCEPT that a stop is deferred while the pump is blocked by its
minimum-run timer (S04). `role_start > role_stop` for every role in every
deadband setting (hysteresis; no exceptions to verify).

A pump beyond `duty_pump_count` roles (i.e., filling no role because the
concurrency ceiling S08 has been reached) never starts, full stop — the
ceiling is a hard limit representing the station's shared electrical/
hydraulic service capacity, not a preference.

## S04 — Per-pump timers

Each pump tracks its own `last_transition_tick`. Two independent rules:

- **Minimum run time** (`MIN_RUN`, swept — S08): once a pump starts, it
  cannot stop for `MIN_RUN` ticks even if `level(t) <= role_stop` during
  that window; it continues running (and continues discharging at the
  level-dependent rate, S03) until `MIN_RUN` ticks have elapsed, at which
  point the ordinary stop condition is re-evaluated every subsequent tick.
- **Minimum off time** (`MIN_OFF = 4` ticks, fixed, not swept): once a pump
  stops, it cannot start again for `MIN_OFF` ticks even if its role's start
  condition is met.

A pump that is timer-blocked from stopping still counts against
`duty_pump_count` for the purposes of staging additional pumps (S03) — it
occupies its duty slot for the full duration it is physically running,
timer-blocked or not.

## S05 — Lead rotation policy (swept — S08)

The rotation index `next_lead` (initially pump A) determines which pump is
offered the LEAD role the next time a NEW lead-selection event occurs. A
lead-selection event occurs only at a tick where no pump currently fills
LEAD and `level(t) >= (that would-be lead's own role_start)` for at least
one in-roster pump — i.e., exactly when a lead pump is about to start from
cold. **The rotation index advances by exactly one position immediately
after a genuine LEAD-START transition completes for the pump it selected —
never on a LAG start, never on any stop event, and never merely because a
tick elapsed.** Advancing it on any other event is the task's core
anti-pattern (see the negative criterion this rule owns in the rubric).

Three swept policies select the offered lead pump among in-roster,
currently-eligible-to-start pumps:

- `STRICT_ALTERNATE`: the pump named by `next_lead`, in fixed cyclic order
  A -> B -> C -> A.
- `RUNTIME_BALANCED`: the in-roster pump with the LOWEST cumulative running
  minutes so far this run (ties broken by lowest pump ID).
- `FIXED_LEAD`: always pump A (no rotation; `next_lead` is never consulted
  or advanced under this policy).

## S06 — Overflow accounting

Whenever the unclamped tick update in S02 would exceed `HIGH_HIGH`, the
excess is a spill: `overflow_volume += (unclamped_level - HIGH_HIGH) * A`
for that tick, and `level` is clamped to exactly `HIGH_HIGH`.
`overflow_duration` is the count of ticks where this clamp was active. Mass
balance must close for every run: total inflow volume equals total pumped
volume plus total overflow volume plus the net change in stored volume
(`(level(1439) - level(0)) * A`) — this is the verifier's primary
feasibility check (S10).

## S07 — Time-of-use tariff and energy cost

Each pump draws a constant `15 kW` while running, regardless of level.
Energy cost accrues per tick as `(running pump count) * 15 kW * (1/60 h) *
rate(t)`, where `rate(t)` is set by the tariff band containing tick `t`'s
START minute:

| band | minutes (start-inclusive) | $/kWh |
|---|---|---|
| OFF-PEAK | [1380,1439] union [0,419] | 0.08 |
| MID-PEAK | [420,959] union [1260,1379] | 0.14 |
| ON-PEAK | [960,1259] | 0.22 |

(i.e. off-peak 23:00-06:59, mid-peak 07:00-15:59 and 21:00-22:59, on-peak
16:00-20:59.) `total_energy_cost` is the sum over all 1440 ticks.

## S08 — Sweep dimensions (the legal configuration space)

Full Cartesian product, no exclusions, `3 x 3 x 3 x 2 x 2 = 108` legal
configurations:

- `duty_pump_count` in `{1,2,3}` — how many of the 3 installed pumps are in
  service; pumps are taken into service by lowest ID first (pump C is the
  first excluded at `duty_pump_count=2`, etc.).
- `rotation_policy` in `{STRICT_ALTERNATE, RUNTIME_BALANCED, FIXED_LEAD}`.
- `deadband` in `{TIGHT, MEDIUM, WIDE}`.
- `min_run_time` in `{SHORT=3, LONG=6}` ticks.
- `day_type` in `{DRY, WET}`.

## S09 — Three competing selection objectives

Computed over the full 108-row sweep; the packet's reference has all three
diverge:

1. **Energy-optimal**: among configurations with `overflow_volume == 0`,
   minimize `total_energy_cost`.
2. **Reliability-optimal**: minimize `peak_level` (the maximum `level(t)`
   over the run) across ALL 108 configurations; ties broken by lower
   `total_energy_cost`.
3. **Wear-constrained**: among configurations with `overflow_volume == 0`
   AND `max(pump starts across the 3 pumps) <= 15` (starts/pump/day
   ceiling), minimize `total_energy_cost`.

## S10 — Independent verification (feasibility certificate)

A separately-coded verifier, sharing only immutable input constants with
the primary implementation, must: re-derive `Q_in(t)` from the stated
hydrograph/storm formula; and either fully re-simulate or check a
feasibility certificate confirming, for the baseline configuration and
every swept configuration: (a) mass balance closes (S06) to a stated
tolerance; (b) no pump ever starts while timer-blocked by `MIN_OFF`, and no
pump ever stops before its `MIN_RUN` has elapsed; (c) `level(t)` never
leaves `[LOW_CUTOFF, HIGH_HIGH]`; (d) reported `overflow_volume` and
`total_energy_cost` match independently recomputed values. Two required
adversarial mutations: a tick where the recorded level update is
inconsistent with `Q_in - Q_out` (a mass-balance violation), and a pump
recorded as stopping before its own `MIN_RUN` ticks have elapsed — the
verifier must reject both while still accepting the true baseline.
