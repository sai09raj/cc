# CISTERN-7 — architecture attack and perfect-semantics ablation

## Why this must be a different shape from task05 and task06

Task05 (KILNWORKS, shelved) was a fault-driven manufacturing dispatch/reroute
trace over a fixed aisle graph. Task06 (ATRIUM-9, real-pilot-confirmed at
20%/21%/sub-50%) was a multi-car elevator dispatch policy exhaustively swept
over a 144-configuration space. Both are, underneath the domain dressing,
**discrete-event request-dispatch simulations**: a request arrives, an agent
(robot or car) is assigned by a fixed priority/cost rule, and the agent
executes a bounded action sequence. Reusing that mechanism a third time in a
row would test the same reasoning skill in a new costume, not a genuinely
different failure surface — the playbook's own rule (`02-DIFFICULTY-
ENGINEERING.md`, "Reusable future-task shape") says to transfer the method,
not the surface architecture.

CISTERN-7 is a **continuous-state control-loop simulation**, not a discrete
request-dispatch simulation: there is no queue of discrete arriving jobs to
assign to agents. Instead, a single continuously-varying physical quantity
(wet-well level) is integrated forward under a hysteresis-band control policy
that starts/stops a shared pool of pumps. The genuine difficulty comes from
correctly composing continuous numerical integration, discrete on/off control
transitions with two independent timers per pump (minimum run time, minimum
off time), a *rotating* (not fixed-priority) lead-agent selection rule, and a
time-of-use tariff — over a 24-hour trace, swept across a real multi-
dimension configuration space, with three competing selection objectives.
This is a different mechanism class from both prior tasks, while still
fitting the reusable pattern's ten ingredients (see the bottom of this file).

## Architecture canvas

```text
TASK WORKING TITLE: CISTERN-7 -- wastewater lift-station level control and
  energy-tariff/overflow-risk optimization
DOMAIN: Civil/Environmental Engineering -- Water Resources & Public Works
  (wastewater collection systems)
REAL ENGINEERING DECISION: which pump-station control configuration (duty-pump
  count, lead-rotation policy, level deadband, minimum-run-time setting) to
  adopt for a given catchment, trading energy cost under a time-of-use tariff
  against sanitary-sewer-overflow (SSO) risk and pump-wear (starts/day), given
  the station's fixed pump curves and a realistic diurnal inflow hydrograph --
  not a free re-design of the station's hydraulics.

FOUR PILLARS
1. Genuine visual interpretation:
   - the diurnal inflow hydrograph (24h curve, dry-weather and wet-weather
     variants) must be measured off its own axis, not printed as a table;
   - the pump curve (discharge flow vs. wet-well level, since static lift
     changes as the well drains/fills) is a plotted curve with a small number
     of labeled breakpoints, requiring interpolation, not a lookup table;
   - the level-setpoint diagram (start/stop elevations per pump per deadband
     setting, high-high alarm elevation, tank geometry) is a labeled cross-
     section drawing;
   - the time-of-use tariff is a small multi-band chart aligned to the same
     24h axis as the hydrograph, not a printed $/kWh table.
2. Iterative tool use: build the tick-based simulator, run the full sweep,
   diagnose against an independently-coded verifier (mass-balance closure,
   timer compliance, overflow accounting), find disagreement, fix, rerun.
3. Expert knowledge: hysteresis control with independent per-pump minimum-
   run/minimum-off timers, lead-rotation-on-START-event-only (not every tick),
   level-dependent pump discharge (not a constant rated flow), TOU-tariff-
   aware energy costing, and correctly distinguishing "pump commanded to stop"
   from "pump timer-blocked from stopping."
4. Long horizon: one continuous 24-hour tick-by-tick trace per configuration,
   a full legal sweep across the configuration space, cross-file
   reconciliation of sweep table / decision file / baseline trace / verifier
   report / memo.

DIFFICULTY STACK
- distributed specification: hydrograph in one chart, pump curve in another,
  level setpoints in a cross-section drawing, tariff bands in a third chart,
  timer/rotation rules in prose;
- stateful interaction: wet-well level is a running numerical integral (not
  resettable per tick), each pump carries its own independent run/off timer
  state and last-started timestamp, the rotation index persists across the
  whole 24h run;
- generated/measured workload: the inflow hydrograph is a continuous function
  sampled at every simulation tick, not a discrete arrival list -- a
  materially different "workload" shape from either prior task's discrete
  call/lot lists;
- search/design space: a legal multi-dimension sweep (duty-pump count x
  rotation policy x deadband setting x minimum-run-time setting x day-type),
  with illegal combinations excluded (e.g. duty-pump count cannot exceed the
  number of installed pumps);
- coupled targets: energy cost, peak-level safety margin, and pump starts/day
  are three genuinely different metrics that trade against each other
  non-monotonically;
- tie-break/rotation rule: an explicit, stated rule for which pump becomes
  lead next, and an explicit rule for exactly which event advances that
  rotation (a real anti-pattern trap: advancing it every tick instead of only
  on a genuine lead-pump START event biases the rotation);
- cross-file consistency: sweep table, decision file, baseline trace, verifier
  report, and memo must all reconcile;
- causal synthesis: explain why the energy-optimal and reliability-optimal
  configurations diverge, why a config that minimizes energy can still
  violate the pump-wear ceiling, and a concrete tick where the TOU tariff
  boundary changed the controller's effective cost trade-off.

POST-SEMANTICS DIFFICULTY (granting every local rule correctly)
- work remaining: composing roughly a dozen interacting deterministic rules
  (mass-balance integration, level-dependent pump curve interpolation,
  hysteresis start/stop, two independent per-pump timers, rotation-on-START-
  only, overflow accounting, TOU costing) correctly across one continuous
  1,440-tick (24h at 1-minute resolution) trace per configuration, for every
  configuration in the legal sweep, with no per-config reset to bound error
  propagation within a design's own family of related configs (day-type is
  the only axis that legitimately restarts the hydrograph);
- interacting persistent state domains: wet-well level (continuous), each
  pump's run/off timer and last-started tick, the rotation index, cumulative
  energy cost, cumulative overflow volume/duration -- all must be carried
  correctly tick-to-tick for the full 24h;
- workload scale and execution: a legal sweep on the order of 100+
  configurations (duty-pump count in {1,2,3} x rotation policy in {3
  variants} x deadband setting in {3 variants} x minimum-run-time in {2
  variants} x day-type in {DRY,WET} = 108), each one continuous 1,440-tick
  run, full sweep table reconciliation;
- search/optimization and coupled decision: no free-form search remains (the
  control policy is fully fixed once a configuration is chosen), but the
  three-way lexicographic selection across a non-monotonic 108-row space is
  still a real decision that depends on every row being correct;
- debugging/iteration: the interaction between the minimum-run timer and the
  hysteresis stop condition (a pump whose level has dropped below its stop
  setpoint but is still timer-blocked from stopping continues drawing power
  and continues discharging, which itself affects the level trajectory the
  next tick) is a genuinely easy edge case to get subtly wrong without
  inspecting an actual trace;
- independent verification: a second, differently-structured implementation
  must reproduce the same 24h trace (or an equivalent feasibility
  certificate) for the baseline configuration and agree on sweep aggregates
  across the full 108-row space -- a nontrivial n-version cross-check;
- cross-file reconciliation: sweep table, decision file, baseline trace,
  verifier report, and memo must agree, including at TOU tariff-band
  boundaries and at the tick where any overflow event begins/ends;
- causal engineering synthesis: explain the energy/reliability divergence and
  the wear-ceiling tradeoff using actual event times from the delivered
  baseline trace, not a generic restatement of the tradeoff.

Could a clean small rewrite now solve the task? NO -- there is no small
  module to discard; correctly integrating the continuous mass balance under
  a level-dependent pump curve, with two independent per-pump timers and a
  rotation rule that must advance on exactly the right event, against a
  24h/108-configuration workload, is the task itself.
Could direct enumeration without a correct interacting model solve it? NO --
  the wet-well level trajectory is a genuine numerical integral of a
  time-varying inflow against a level-dependent outflow; there is nothing to
  enumerate in place of actually running the integration.
Could copied headline literals retain >=50%? Must be checked and kept below
  50% in the score-topology audit (score-topology.md, once built) exactly as
  done for ATRIUM-9 -- weight must sit on whole-sweep aggregates and baseline-
  trace witnesses, not the three headline selections alone.
Are at least three post-semantics difficulty layers unavoidable? YES --
  continuous-state temporal composition (mass balance + timers + rotation),
  broad executed sweep (100+ full 24h runs), and coupled multi-objective
  decision-making under a hard wear-ceiling constraint.
Does any planned low score depend mainly on semantic omission/misreading?
  NO -- every rule (pump curve, timer durations, rotation-advance event,
  tariff bands, overflow definition) will be stated plainly and positively in
  the packet; the difficulty is volume and correctness of long-horizon
  continuous-state composition, not a hidden convention.
```

## Perfect-semantics ablation

```text
TASK: CISTERN-7 (task07)
CURRENT REQUIRED FRONTIER MODEL / EFFORT: Claude Opus 4.8, maximum effort

GRANT THE HYPOTHETICAL SOLVER:
- every local rule and measured constant (hydrograph curve, pump curve
  breakpoints, level setpoints per deadband setting, timer durations, TOU
  tariff bands, rotation-advance rule, overflow definition), stated with no
  ambiguity;
- correct local implementation of each rule in isolation (e.g. it can
  correctly implement "a pump's discharge is interpolated from the pump
  curve at the current wet-well level" as a unit test, or "the rotation
  index advances only on a genuine lead-pump START event" as a unit test).

WORK THAT STILL REMAINS:
- integrated temporal composition: carrying wet-well level, per-pump timer
  state, rotation index, cumulative energy cost, and cumulative overflow
  volume correctly across one continuous 1,440-tick trace, where the
  minimum-run-timer/hysteresis-stop interaction and the level-dependent pump
  curve mean the level trajectory itself depends on decisions made many
  ticks earlier -- there is no independent per-tick calculation that avoids
  this coupling;
- workload scale and execution: a 100+ row legal configuration sweep, each
  one continuous 24h run at 1-minute resolution, full sweep-table
  reconciliation;
- search/optimization and coupled decision: no free per-tick choice remains,
  but the three-way lexicographic selection (energy-optimal subject to zero
  overflow, reliability-optimal, wear-constrained) across a non-monotonic
  108-row space is still a real decision that depends on every row's number
  being right;
- debugging/iteration: the minimum-run-timer vs. hysteresis-stop edge case,
  and the level-dependent pump curve's interaction with staging additional
  pumps mid-event, have enough subtlety that a first implementation is
  unlikely to be correct without inspecting its own trace against the
  verifier and revising;
- independent verification: a second, differently-structured implementation
  must reproduce the baseline's full trace (or an equivalent feasibility
  certificate covering mass-balance closure, timer compliance, and overflow
  accounting) and agree on sweep aggregates across the full 108-row space;
- cross-file reconciliation: sweep table, decision file, baseline trace,
  verifier report, and memo must all agree, including at TOU tariff-band
  boundaries and overflow-event ticks;
- causal engineering synthesis: explain the energy/reliability divergence and
  the wear-ceiling tradeoff using actual event times from the delivered
  baseline trace, and why treating the rotation index as advancing every
  tick (instead of only on a genuine lead-pump START event) would bias pump
  wear unevenly across the fleet.

Could a clean small rewrite now solve the task? NO -- see architecture
  canvas above; there is no small module to discard.
Could direct enumeration without a correct interacting model solve it? NO --
  the level trajectory is a genuine running numerical integral; nothing to
  enumerate in its place.
Could copied headline literals retain >=50%? Must be checked and kept below
  50% in the score-topology audit before any submission.
Are at least three post-semantics difficulty layers unavoidable? YES --
  continuous-state temporal composition, broad executed sweep, coupled
  multi-objective decision-making under a hard wear-ceiling constraint.
Does any planned low score depend mainly on semantic omission/misreading?
  NO -- every rule will be stated plainly and positively; difficulty is
  long-horizon continuous-state composition volume, not a hidden convention.

DISPOSITION: accept architecture, proceed to semantic contract and reference
  build.
RATIONALE: genuinely different mechanism class from task05 (fault-driven
  discrete dispatch/reroute) and task06 (discrete multi-agent request
  dispatch): CISTERN-7's core difficulty is continuous-state numerical
  integration composed with discrete hysteresis control and independent
  per-agent timers, not request assignment. It still fits every ingredient
  of the reusable future-task shape (02-DIFFICULTY-ENGINEERING.md): dense
  complete visual spec with measured constants, multi-component stateful
  model, author-owned invariant/mutant suite (to be built), algorithmic
  (continuous-function) workload generation, exhaustive constrained search,
  coupled thresholds with an explicit hard constraint (wear ceiling) and
  tie-break, integrated witnesses from one uninterrupted 24h execution, a
  plausible-wrong survival ceiling to be verified below 50% before any
  submission, and executable + structured + causal-report outputs.
REVIEWER / DATE: author self-review at proposal time; pending independent
  packet-only reconstruction once the artifact and semantic contract are
  frozen (see audit/ once populated), matching the process used for
  ATRIUM-9.
```

## Reusable-shape checklist (02-DIFFICULTY-ENGINEERING.md)

```text
dense but complete visual specification        -> hydrograph + pump curve +
                                                    level-setpoint drawing +
                                                    TOU tariff chart
  + measured constants and one explicit override -> pump curve breakpoints
                                                    measured off the chart;
                                                    wet-weather override
                                                    multiplies the DRY
                                                    hydrograph for the WET
                                                    day-type
  + multi-component stateful model               -> level integral + N
                                                    independent pump timer
                                                    state machines + rotation
                                                    index
  + author-owned invariant/mutant suite           -> to be built in
                                                    reference/ (mass-balance
                                                    invariant, timer-
                                                    compliance invariant,
                                                    rotation-advance mutant,
                                                    flat-tariff mutant)
  + algorithmic workload generation               -> continuous hydrograph
                                                    function sampled every
                                                    tick, not a discrete list
  + exhaustive constrained search                 -> duty-pump count x
                                                    rotation policy x
                                                    deadband x min-run-time x
                                                    day-type, illegal combos
                                                    excluded
  + coupled thresholds and explicit tie-break     -> energy vs. overflow vs.
                                                    wear-ceiling, lowest-
                                                    pump-ID tie-break on
                                                    equal lead-eligibility
  + integrated witnesses from ordinary execution  -> baseline 24h trace +
                                                    hash, to be built
  + a plausible-wrong survival ceiling below 50%  -> to be verified via
                                                    score_counterfactual.py
                                                    before any submission
  + executable + structured outputs + causal      -> simulator + verifier +
    report                                           sweep table + decision
                                                    file + memo
```

## Open design decisions to resolve in the semantic contract

These are flagged here, before any numeric constant is frozen, so the
semantic contract can answer each one explicitly rather than leaving an
implicit convention for a solver to guess:

1. Exact pump curve shape: how many breakpoints, and is interpolation
   linear between them (simplest, avoids an unstated curve-fit convention)?
2. Exact rotation policy variants: what does each of the 3 swept policies
   (e.g. STRICT_ALTERNATE, RUNTIME_BALANCED, FIXED_LEAD) mean precisely, and
   what is the tie-break when two pumps have equal eligibility?
3. Exact overflow definition: does overflow volume accumulate continuously
   above the high-high elevation, or is it a binary event flag plus a
   separate duration? (Pick one; state it plainly.)
4. Exact minimum-run/minimum-off interaction: if a pump is timer-blocked
   from stopping and the level keeps dropping well past its stop setpoint,
   does it still count toward the duty-pump concurrency limit for staging
   additional pumps? (Must be stated, since it changes staging decisions.)
5. Exact TOU tariff tick-boundary convention: is the rate for a tick
   determined by the tick's start time, end time, or midpoint? (Pick one
   consistent convention, matching the packet's own timing convention.)

Do not proceed to `reference/cistern_sim.py` until all five are answered in
`design/semantic-contract.md` with no residual ambiguity.
