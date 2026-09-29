# CISTERN-7 rubric

Positive total **234**; seven negative criteria totaling **-30** (**-4**,
**-5**, **-4**, **-4**, **-4**, **-5**, **-4**), plus a negative trap
**-8**. **48 criteria** (within the platform's 12-50 range; not padded to
50 -- coverage was complete at 48). Every weight is capped at 10. Every
criterion body is 301 characters or fewer. Criteria are binary. Accept
equivalent correct work throughout: equivalent languages, source
organization, output schemas, file layout, and formula notation.

Every prohibition below (rotation-advance timing, minimum-run-timer
compliance, TOU-tariff use, level-dependent pump discharge) was given its
own dedicated negative criterion from this rubric's first draft, not added
round-by-round after a linter finding -- the corresponding positive
criteria state only the mechanism, never the prohibition, to avoid
double-charging the same fact from the first draft.

### Package (1-2, weight 3)

| # | Wt | Criterion |
| --- | --- | --- |
| 1 | +2 | Executes the delivered offline simulator with a documented, reproducible command, records the actual tool versions used in a declared offline, stdlib-only environment, includes the memo's own layout interpretation of the packet's charts, and delivers all six named products as accessible files. |
| 2 | +1 | The delivered sweep table contains exactly 108 rows (54 legal `(duty_pump_count, rotation_policy, deadband, min_run_time)` configurations, each with one `DRY` row and one `WET` row), no duplicate, no missing combination. |

### Local semantics/rules/scaffolding (3-12, weight 21)

| # | Wt | Criterion |
| --- | --- | --- |
| 3 | +2 | Generates `Q_in(t)` for `DRY` by linearly interpolating the packet's hydrograph anchor points; for `WET`, adds the triangular storm surcharge (zero outside `[300,420]`, peaking `+8.0 m^3/min` at `t=360`) on top of the `DRY` curve. |
| 4 | +2 | Interpolates each running pump's discharge linearly from the pump curve against `level(t)` (breakpoints `(0.4,3.0),(2.0,4.0),(4.2,5.0)`, pump C scaled to 85%); a non-running pump discharges zero regardless of level. |
| 5 | +2 | Puts only the lowest-ID `duty_pump_count` pumps into service; a pump OUTSIDE that roster never runs and never fills any role, regardless of level. |
| 6 | +2 | Assigns LAG1/LAG2 to the in-roster non-lead pumps in ascending pump-ID order, re-derived fresh each tick from the current lead identity. |
| 7 | +2 | Starts a role's pump when `level(t)` reaches that role's own start elevation from the swept deadband table, and stops it when `level(t)` falls to that role's own stop elevation, using the exact TIGHT/MEDIUM/WIDE elevations stated in the packet. |
| 8 | +2 | Once a pump starts, keeps it running until its own swept `min_run_time` ticks have elapsed even if level has already fallen to its stop elevation; re-evaluates the stop condition every tick after that. |
| 9 | +2 | Once a pump stops, keeps it from restarting until 4 ticks have elapsed (`MIN_OFF`), independent of and not swept with `min_run_time`. |
| 10 | +2 | Selects the LEAD-role pump per the swept `rotation_policy`: `STRICT_ALTERNATE` cycles in-roster pumps by fixed ID order; `RUNTIME_BALANCED` picks lowest cumulative run-minutes so far (ties to lowest ID); `FIXED_LEAD` always picks lowest-ID in-roster pump. |
| 11 | +2 | Whenever the tick's unclamped level update would exceed `4.2 m`, adds the excess volume (times the `60 m^2` plan area) to `overflow_volume` and clamps `level` to exactly `4.2 m` for that tick. |
| 12 | +3 | Costs each tick as `(running pump count) * 15 kW * (1/60 h) * rate(t)`, where `rate(t)` is set by which of the three stated TOU bands contains that tick's own start minute. |

### Integrated production execution — 54-configuration sweep (13-19, weight 19)

| # | Wt | Criterion |
| --- | --- | --- |
| 13 | +2 | Reports the energy-optimal configuration as `(duty=2, rotation=FIXED_LEAD, deadband=WIDE, min_run=LONG)` with combined (`DRY`+`WET`) energy cost `$93.51` (±0.05) and worst-day peak level `3.5474 m` (±0.01). |
| 14 | +2 | Reports the reliability-optimal configuration as `(duty=3, rotation=FIXED_LEAD, deadband=TIGHT, min_run=LONG)` with worst-day peak level `2.4101 m` (±0.01) and combined energy cost `$98.685` (±0.05). |
| 15 | +2 | Reports the wear-balance-constrained configuration (feasible on both days, worst-day fleet run-time imbalance `<=0.80`) as `(duty=2, rotation=RUNTIME_BALANCED, deadband=TIGHT, min_run=SHORT)` with combined energy cost `$96.74` (±0.05). |
| 16 | +1 | Reports explicitly, for each pair among the three selections in criteria 13-15, whether it agrees (identical configuration) or diverges; this packet's reference has all three diverge — the criterion tests the disclosure, not agreement itself. |
| 17 | +4 | Reports configuration `(2,FIXED_LEAD,WIDE,LONG)`'s own `WET` row as `total_energy_cost=47.93, overflow_volume=0, peak_level=3.5474`. |
| 18 | +4 | Reports configuration `(3,FIXED_LEAD,TIGHT,LONG)`'s own `DRY` row as `total_energy_cost=48.22, overflow_volume=0, peak_level=1.8154`. |
| 19 | +4 | Reports configuration `(2,RUNTIME_BALANCED,TIGHT,SHORT)`'s own `WET` row as `total_energy_cost=49.46, overflow_volume=0, peak_level=2.8625, starts={A:16,B:9}`. |

### Whole-sweep aggregate totals (20-32, weight 130)

Each total sums one or two metrics across a stated subset of the
54-configuration sweep (both day-rows combined). Report to the stated
tolerance. Pump C's discharge curve is scaled to 85% of pumps A/B's shared
curve (packet fact), so `rotation_policy` genuinely affects these
aggregates whenever pump C is in the roster (`duty_pump_count=3`), not just
per-pump wear distribution. Each of these 13 facts is wrong under every
plausible-wrong mutant tested — the rubric's main discriminating bloc.

| # | Wt | Criterion |
| --- | --- | --- |
| 20 | +10 | Reports the sum of combined two-day energy cost across all 54 configurations as `$5024.80` (±0.5). |
| 21 | +10 | Reports the sum of worst-day peak level across all 54 configurations as `187.4774 m` (±0.05). |
| 22 | +10 | Reports the sum of worst-day fleet run-time imbalance across all 54 configurations as `46.3073` (±0.05). |
| 23 | +10 | Summed over only `duty_pump_count=1` (18 configs): energy totals `$1506.27` (±0.5), worst-day peak totals `75.60 m` (±0.05). |
| 24 | +10 | Summed over only `duty_pump_count=3` (18 configs): energy totals `$1795.75` (±0.5), worst-day peak totals `54.891 m` (±0.05). |
| 25 | +10 | Summed over only `deadband=TIGHT` (18 configs): energy totals `$1706.81` (±0.5), imbalance totals `14.0612` (±0.05). |
| 26 | +10 | Summed over only `deadband=WIDE` (18 configs): energy totals `$1658.70` (±0.5), imbalance totals `16.1731` (±0.05). |
| 27 | +10 | Summed over only `rotation_policy=FIXED_LEAD` (18 configs): energy totals `$1651.735` (±0.5), imbalance totals `16.7808` (±0.05). |
| 28 | +10 | Summed over only `rotation_policy=STRICT_ALTERNATE` (18 configs): energy totals `$1684.445` (±0.5), imbalance totals `14.8384` (±0.05). |
| 29 | +10 | Summed over only `rotation_policy=RUNTIME_BALANCED` (18 configs): energy totals `$1688.62` (±0.5), imbalance totals `14.688` (±0.05). |
| 30 | +10 | Summed over only `min_run_time=SHORT` (27 configs): energy totals `$2503.12` (±0.5), worst-day peak totals `93.7619 m` (±0.05). |
| 31 | +10 | Summed over only `duty_pump_count=1 AND deadband=WIDE` (6 configs): energy totals `$499.68` (±0.5); exactly `0` of the `6` are feasible on both days. |
| 32 | +10 | Summed over only `duty_pump_count=3 AND rotation_policy=STRICT_ALTERNATE` (6 configs): energy totals `$608.095` (±0.5), imbalance totals `4.4443` (±0.05). |

### Production witnesses from the baseline trace (33-40, weight 48)

Baseline configuration for every witness below and for the hash:
`(duty_pump_count=3, rotation_policy=STRICT_ALTERNATE, deadband=TIGHT,
min_run_time=LONG, day_type=WET)`.

| # | Wt | Criterion |
| --- | --- | --- |
| 33 | +10 | Shows the LEAD role assigned strictly cyclically: pump A at `t=25`, B at `t=123`, C at `t=211`, A at `t=248`, B at `t=280`, C at `t=308` — each a genuine START, two complete `A,B,C` cycles confirming `STRICT_ALTERNATE`. |
| 34 | +10 | Shows pump A starting at `t=25`, continuing to run past its own role's stop elevation (`0.8 m`) once `level` falls below it (by `t=34`) because `min_run_time=LONG` has not yet elapsed, and finally stopping at exactly `t=40` (15 ticks after `t=25`). |
| 35 | +8 | Shows `level(t)` reaching its run-wide peak of `2.4336 m` (±0.005) at exactly `t=358`, during the storm surcharge window. |
| 36 | +10 | Shows that, across the sweep, every one of the 18 `duty_pump_count=1` configurations is infeasible on `WET` (nonzero overflow) while every `duty_pump_count=2` and `duty_pump_count=3` configuration is feasible on both days. |
| 37 | +10 | Matches the first 16 hex characters of the baseline's canonical trace-integrity hash (algorithm in the packet) to `6a880d5a0cb10b6c`. |

### Independent verification and decision/causal reconciliation (38-40, weight 13)

| # | Wt | Criterion |
| --- | --- | --- |
| 38 | +3 | Delivers a separately-coded verifier, sharing only immutable input constants, that re-derives `Q_in(t)`, checks a feasibility certificate or re-simulates the baseline trace, rejects both adversarial mutations with the original preserved and accepted, and reports this evidence in the memo. |
| 39 | +8 | Explains, citing the baseline trace's own numbers, why energy-optimal and reliability-optimal diverge (fewer duty pumps, wider deadband cut energy but raise peak level), AND why wear-balance-constrained trades energy savings for lower fleet run-time imbalance. |
| 40 | +2 | Explains in the memo, tied to the baseline trace's rotation-sequence witness (criterion 33), why treating the rotation index as advancing every tick rather than only on a genuine LEAD-START would concentrate wear unevenly across the pump fleet. |

### Negative criteria — control-loop prohibitions (41-44)

| # | Wt | Criterion |
| --- | --- | --- |
| 41 | −4 | Advances the `STRICT_ALTERNATE` rotation index on any tick or event other than a genuine LEAD-START transition (e.g. every tick, or on a LAG start/stop), rather than exactly once per LEAD-START. |
| 42 | −5 | Lets any pump stop before its own swept `min_run_time` has elapsed since it started, instead of continuing to run (and continuing to discharge) until that timer clears. |
| 43 | −4 | Costs energy using a single flat rate instead of the three stated time-of-use tariff bands, or otherwise ignores which band contains a tick's own start minute. |
| 44 | −4 | Uses a constant pump discharge instead of interpolating from the level-dependent pump curve, for any running pump at any tick. |

### Negative criteria — architecture and execution prohibitions (45-47)

| # | Wt | Criterion |
| --- | --- | --- |
| 45 | −4 | Delivers a verifier that shares anything beyond immutable input constants with the primary implementation (importing or wrapping its internal state, classes, or in-memory objects) rather than independently re-deriving the hydrograph and trace or certificate. |
| 46 | −5 | Runs any of the 54 legal configurations as a shortened, truncated, or sampled subset of its own 1440-tick day, on either day-type, rather than one continuous run to completion. |
| 47 | −4 | Treats `day_type` as a free dimension a selection may optimize over (picking whichever of `DRY`/`WET` is cheaper or safer for a given configuration) rather than evaluating every configuration on both days together. |

### Negative trap (48)

| # | Wt | Criterion |
| --- | --- | --- |
| 48 | −8 | Embeds precomputed sweep rows, selection values, or the trace-integrity hash as literals substituting for executing the delivered simulator. Immutable input constants don't trigger this; omission alone doesn't either. |
