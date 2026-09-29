## Analyze

```text
Read the packet and reconstruct the wet-well cross-section (tank bounds,
per-role start/stop elevations for each of the three deadband settings,
measured against the labeled axis), the pump curve (discharge vs. level,
including pump C's reduced scale relative to pumps A/B, read by comparing
the two plotted curves), the diurnal inflow hydrograph (dry baseline and
the wet-day storm surcharge, measured off the same time axis), and the
time-of-use tariff bands. Recover the fully deterministic control policy
already in force: hysteresis start/stop staging per role (LEAD, LAG1,
LAG2, the latter two always assigned to the remaining in-roster pumps by
ascending ID), each pump's INDEPENDENT minimum-run and minimum-off timers
(a pump blocked from stopping keeps discharging and keeps occupying its
duty slot -- conflating "blocked from stopping" with "off" is the
packet's most common failure mode), and the three lead-rotation policies,
whose index advances only on a genuine lead-pump start transition, never
on any other event. Treat the 54-configuration sweep as one genuine
multi-objective search evaluated over BOTH day-types per configuration:
more duty pumps and a tighter deadband lower peak level but raise energy
and pump-cycling wear, so the energy-optimal, reliability-optimal, and
wear-balance-constrained selections are not guaranteed to agree and must
each be found by executing the full legal space, not assumed from one
run. day_type is weather, never a choosable dimension.
```

## Execute & Generate

```text
Implement a deterministic, offline, tick-by-tick (1-minute, 1440 ticks)
mass-balance simulator executing the packet's control policy exactly --
for each of the 54 legal configurations, one continuous run per day_type
(DRY and WET), both feeding the same selection objectives. Build a
separately-coded verifier that independently re-derives the inflow
hydrograph from the same public formulas and either fully re-simulates or
checks a complete feasibility certificate (mass balance closes every
tick, no pump violates its own minimum-run/minimum-off timers, level
never leaves its physical bounds), sharing only immutable input constants
with the primary implementation. Run the two required adversarial
mutations -- a tick whose recorded level is inconsistent with that tick's
own inflow minus outflow, and a pump recorded as stopping before its own
minimum-run time has elapsed -- against a preserved original and confirm
the verifier rejects both while accepting the original. Deliver simulator
source, verifier source, the complete 108-row sweep table, a decision
file with all three selections and their keys, certification evidence
(the baseline configuration's full trace plus its stated SHA-256
trace-integrity hash, computed by the algorithm the packet specifies),
and a memo. Equivalent languages, source organization, output schemas,
and physically valid tie-broken orderings all pass; only one
policy-conformant trace per configuration-per-day-type exists.
```

## Synthesize

```text
Using the 108 executed sweep rows (54 configurations, each scored by its
own DRY and WET rows together), apply the three lexicographic selection
keys (energy-optimal subject to zero overflow on both days,
reliability-optimal, wear-balance-constrained under the stated fleet
run-time imbalance ceiling) and report all three, explicitly noting
whether they agree. Explain, using actual event times from your delivered
baseline trace, at least one concrete instance of a pump's minimum-run
timer forcing it to keep running (and keep discharging) past its own
stop elevation, and cite the rotation-sequence witness from that same
trace. Explain why energy-optimal and reliability-optimal diverge, and
why the wear-balance-constrained pick trades away some energy saving for
a lower fleet run-time imbalance. Explain why the lead-rotation index
must advance only on a genuine lead-start transition, and why a
minimum-run-timer-blocked pump must still count toward the duty-pump
concurrency limit. Reconcile your sweep, selections, verifier agreement,
and baseline witnesses against the same underlying control and mass-
balance rules. Any accurate, evidence-tied causal argument is acceptable;
no particular configuration beyond the three selections is required.
```
