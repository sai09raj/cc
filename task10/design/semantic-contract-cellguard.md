# CELLGUARD-10 semantic contract (v2, two-cell model)

(Supersedes the original single-cell `semantic-contract-cellguard.md`,
hardened after two clean local blind-pilot solves against the
single-cell design — see `STATUS.md`. Also supersedes
`semantic-contract.md`, which documents the shelved STATIC10 design.)

## S01 — Simulation model

A battery pack of **two series-connected cells, A and B**, discrete
ticks `t = 1..320`, fully deterministic. Shared pack-level state: charge
mode (`CC`/`CV`/`TAPER`), temperature `temp` (0.1 degC units), and
fault-latch status `fault` (boolean) plus its internal hysteresis
counter. Per-cell state: state of charge `soc_a`/`soc_b` (%, 0-100),
delivered current `current_a`/`current_b`, and terminal voltage
`voltage_a`/`voltage_b`. Every tick's state is computed from the
immediately preceding tick's state — there is no independent per-tick
computation; a wrong value at tick `t` is the input to tick `t+1`'s
computation.

Fixed constants (all given, packet input, never derived):
`CAPACITY_A=5700`, `CAPACITY_B=6300` (the two cells' manufacturing
variance — never assume they are equal), `CC_CURRENT=50`,
`CV_VOLTAGE_THRESHOLD=4150`, `CV_DECAY_STEP=1.2`,
`TAPER_CURRENT_THRESHOLD=8`, `TAPER_CURRENT=3`, `IR_DROP_PER_UNIT=2.0`,
`BASE_VOLTAGE=3700`, `VOLT_PER_SOC_PCT=6.0`, `AMBIENT=250`,
`HEAT_FULL=6`, `HEAT_DERATED=3`, `HEAT_TAPER=1`, `COOL_PER_TICK=2`,
`DERATE_TEMP=450`, `DERATE_FACTOR=0.5`, `FAULT_TEMP_HIGH=575`,
`FAULT_TEMP_LOW=520`, `FAULT_RELEASE_TICKS=4`, `OVERCURRENT_MAX=45`,
`BALANCE_THRESHOLD=1.5`, `BALANCE_BLEED=8`.

Initial state (before tick 1): `soc_a=0`, `soc_b=0`, `temp=AMBIENT`,
`mode=CC`, `fault=False`, hysteresis counter `0`, reference voltages
`voltage_a=voltage_b=BASE_VOLTAGE`.

## S02 — Per-tick update rules (six genuinely distinct, interacting rules)

Applied in this exact order, every tick:

1. **Mode transition.** If `mode==CC` and the *previous* tick's reported
   voltage, taken as the MAX of `voltage_a` and `voltage_b` (regulate on
   whichever cell is higher — standard over-voltage protection logic),
   `>= CV_VOLTAGE_THRESHOLD`, switch to `CV` and set the CV regulation
   current to `CC_CURRENT`. If `mode==CV` and the CV regulation current
   (before this tick's decay, rule 3) is `<= TAPER_CURRENT_THRESHOLD`,
   switch to `TAPER`. A mode never reverts (CC -> CV -> TAPER is
   one-way). This mode/current pipeline (rules 1-5) is pack-level and
   shared — both cells follow the same mode and the same
   pre-balancing base current.
2. **Mode-commanded current.** `CC`: `CC_CURRENT`. `CV`: the current CV
   regulation current value (before this tick's decay). `TAPER`:
   `TAPER_CURRENT`.
3. **CV current taper-down.** Only in `CV` mode, after computing this
   tick's mode-commanded current: reduce the CV regulation current by
   `CV_DECAY_STEP` (floor zero) for use on the *next* tick's check in
   rule 1/2. `CC` and `TAPER` modes have no decaying regulation current.
   Unconditional for every CV-mode tick, never gated by fault status
   (see S03b).
4. **Thermal derating and fault gating.** If `fault` is latched this
   tick, base current is `0` regardless of mode. Else if this tick's
   *incoming* temperature (before this tick's own heat/cool update,
   rule 7) is `>= DERATE_TEMP`, base current is the mode-commanded
   current times `DERATE_FACTOR` — applied in every mode, `TAPER`
   included. Else base current is the mode-commanded current
   unmodified. This is a single shared **base current**, computed once
   per tick, before cell balancing splits it (rule 6).
5. **Overcurrent clamp.** Base current (after rule 4) is capped at
   `OVERCURRENT_MAX` — applied last in the shared pipeline, after
   derating, not before.
6. **Cell balancing.** Compute `diff = soc_a - soc_b` using the
   *previous* tick's reported state of charge for each cell. If base
   current is `> 0` and `abs(diff) >= BALANCE_THRESHOLD`: the higher-SoC
   cell's delivered current is `max(0, base_current - BALANCE_BLEED)`
   (a passive bleed resistor draws down the leading cell); the other
   cell's delivered current stays at the full base current. If base
   current is `0`, or the two cells are within `BALANCE_THRESHOLD` of
   each other, both cells deliver the same, unmodified base current.
   This is the central correctness trap: do not assume both cells
   always share one current value — they diverge whenever the
   imbalance condition is met, and this condition must be re-evaluated
   every tick from each cell's own running SoC, not decided once.
7. **Heat generation.** Shared, pack-level, driven by whichever current
   value is relevant: if the *base* current (pre-balancing) is `0`, no
   heat this tick. Else if `mode==TAPER`, heat is `HEAT_TAPER` regardless
   of temperature (this packet's own rule: never apply `HEAT_DERATED` to
   a TAPER-mode tick just because temperature is above `DERATE_TEMP`).
   Else if incoming temperature is `>= DERATE_TEMP`, heat is
   `HEAT_DERATED`. Else heat is `HEAT_FULL`. Heat generation does not
   depend on which cell is bled by balancing — it is one shared pack
   temperature, not per-cell.
8. **Temperature update.** `temp = temp_incoming + heat - COOL_PER_TICK`.
9. **Fault-latch hysteresis.** If not already latched and the *new*
   temperature (after rule 8) is `>= FAULT_TEMP_HIGH`: latch the fault,
   reset the hysteresis counter to `0`. While latched, both cells
   deliver zero current (rule 4) every tick until released. Release
   requires the temperature to be at or below `FAULT_TEMP_LOW` for
   `FAULT_RELEASE_TICKS` CONSECUTIVE ticks — the counter increments only
   while temperature stays at or below `FAULT_TEMP_LOW` every tick in a
   row; a single tick where temperature rises back above
   `FAULT_TEMP_LOW` resets the counter to zero immediately. The counter
   itself resets to zero in the same tick the fault releases.
10. **State of charge (per cell).** `soc_a`/`soc_b` each increase by that
    cell's own delivered current (post-balancing, rule 6) divided by
    that cell's own capacity (`CAPACITY_A`/`CAPACITY_B` — not shared),
    times 100, capped at 100.
11. **Terminal voltage (per cell).** `voltage_a`/`voltage_b` are each
    `BASE_VOLTAGE` plus that cell's own state of charge times
    `VOLT_PER_SOC_PCT`, minus that cell's own delivered current times
    `IR_DROP_PER_UNIT` — this tick's own voltage for each cell, which
    becomes "the previous tick's voltage" for the NEXT tick's rule-1
    mode-transition check (via the MAX of the two), never used for this
    same tick's own transition decision.

## S03 — Certificate serialization (mechanical, from the first draft)

Header line: `CELLGUARD10-CERT-V2`

Then one line per tick, `t=1` through `t=320`, in order:

```text
t={t};mode={mode};soc_a={soc_a};soc_b={soc_b};temp={temp};current_a={current_a};current_b={current_b};voltage_a={voltage_a};voltage_b={voltage_b};fault={fault}
```

`soc_a`, `soc_b`, `current_a`, `current_b`, `voltage_a`, and `voltage_b`
are fixed-width 2-decimal-place strings — ALWAYS exactly two digits
after the decimal point (`50.00`, `25.00`, `0.00`), never a bare `50`,
`50.0`, or any other width, even when the underlying value has zero or
one significant decimal digits (found genuinely ambiguous by a Phase 8.5
blind pilot against the single-cell design — mistake #69 — this
sentence is the fix, stated explicitly this time rather than relying on
"rounded to exactly 2 decimal places" alone). `temp` is an integer (0.1
degC units, always integral under these constants); `fault` is `True`
or `False` (Python-style capitalization, matching the reference
engine's own `str()` output — any clearly equivalent boolean rendering,
e.g. `true`/`false`, is accepted).

Certificate hash: SHA-256 of the full serialized text (header through
the `t=320` line, newline-joined, trailing newline included), first 16
hex characters.

### S03a — Clarifications (closed proactively, carried over from the
single-cell design's own blind-pilot findings, all still apply)

1. **CV regulation-current availability.** When the CC-to-CV transition
   fires on a given tick (rule 1), that tick's own rule 2 reads the
   regulation current immediately, in the same tick — it is not
   deferred to the next tick.
2. **CV-to-TAPER check and taper-down timing.** Both the mode-transition
   check in rule 1 and the mode-commanded-current read in rule 2 use the
   regulation current as it enters the tick, before that tick's own
   rule-3 decay — the same "previous value" convention rule 1 already
   uses for voltage.
3. **Internal precision.** Full (unrounded) numeric precision is carried
   between ticks for every state variable, per cell. The 2-decimal-place
   rounding in S03 is a certificate/display rule only, applied once at
   serialization.
4. **Hysteresis counter at release.** The moment the counter reaches
   `FAULT_RELEASE_TICKS` and the fault un-latches, the counter itself
   resets to `0` in that same tick.

### S03b — One more clarification (closed after a blind pilot against
the single-cell design flagged it; still applies here)

5. **CV taper-down runs even while a fault is latched.** Rule 3 is
   unconditional for every CV-mode tick — it is not gated by the
   fault-latch check in rule 4, which only zeroes the delivered
   current, never the regulation current. The CV-to-TAPER mode
   transition can therefore fire while the fault is still latched; do
   not assume mode progression pauses during a fault.

### S03c — Cell balancing specifics (new in the two-cell hardening)

6. **Balancing uses the previous tick's SoC, not a value updated
   mid-tick.** `diff` in rule 6 is computed from `soc_a`/`soc_b` as they
   stood entering the tick (i.e., after the previous tick's rule 10),
   before this tick's own rule-10 update — the same "previous value"
   convention used throughout.
7. **Balancing only ever bleeds the higher cell, never tops up the
   lower one.** The lower-SoC cell always receives the full,
   unmodified base current (post-clamp); only the higher cell's
   delivered current is reduced. There is no mechanism that increases
   either cell's current above the shared base current.
8. **Which cell leads follows from the capacities, and is not given as
   a separate fact.** The cell with the SMALLER capacity gains state of
   charge faster from equal current (same current, smaller denominator
   in the percentage), so it structurally becomes, and stays, the
   leading cell once an imbalance first opens — balancing only ever
   narrows the gap back toward the threshold, it never reverses which
   cell is ahead. **Correction, found by a Phase 8.5 blind pilot against
   this hardened design**: an earlier draft of this document claimed the
   lead "is not fixed for the whole run" and "can flip" — false for this
   specific constant set and 320-tick horizon, confirmed by execution
   (cell A, the smaller-capacity cell, leads at every one of the 63
   active ticks; retuning threshold/bleed/capacities across several
   combinations never produced a flip, since the mechanism is
   structurally one-directional). The rule itself must still be
   evaluated fresh every tick from each cell's own running SoC (not
   hardcoded to "cell A" as a shortcut) and the comparison's sign must
   still be computed, not assumed — but do not expect, or design a
   check around, the leader actually changing mid-run.

## S04 — Independent verification (independently re-coded, never
importing or calling the primary's implementation)

The independent verifier re-implements S02's eleven per-tick update
rules itself, from scratch, in its own code — never importing, calling,
or reading any state computed by the primary engine. It replays the
simulation from `t=1` up to each of several chosen checkpoint ticks
(crafted to land on both mode transitions, the fault-latch engage and
release ticks, and several ordinary ticks spanning the rest of the run)
and checks its own independently-computed state (all nine per-tick
fields, both cells) at each checkpoint against the primary's claimed
state for that same tick.

## S05 — Required adversarial mutations against the verifier (crafted
standalone, not derived from corrupting the main circuit)

1. A claimed state at the fault-release checkpoint that reports the
   fault released after only 2 consecutive cool ticks instead of 4. The
   verifier must reject.
2. A claimed state at an early checkpoint that reports both cells
   receiving identical delivered current throughout, as if cell
   balancing were never applied (consistent with the true trace's own
   earlier balancing activity having been skipped). The verifier must
   reject.

## S06 — Deliverables

Primary engine source; independent verifier source; the full 320-tick,
two-cell state trace; a findings report; certification evidence (both
adversarial rejection results, plus the SHA-256 trace-integrity hash);
an engineering memo explaining, with specific ticks from its own
output: why TAPER mode never follows the derated-heat rule even while
hot; why the fault latch released at the specific tick it did; exactly
which CC-phase ticks the overcurrent clamp actually changes the
delivered current on, and why it stops partway through; and why cell
balancing activates and deactivates repeatedly across the run rather
than settling permanently once triggered.

## S07 — Score-topology gate (S08), run before any rubric text

Six required mutants, each applied to the real engine and run against
the real model, each scored against the real (not estimated) rubric
weights in `reference/score_counterfactual.py`:

| Mutant | Ticks differing (of 320) | First divergence | Score |
|---|---|---|---|
| Drop thermal derating | 270 | t=51 | 14.8% |
| Fault releases instantly, no hysteresis | 118 | t=203 | 23.8% |
| CV current never decays (TAPER never reached) | 158 | t=163 | 16.4% |
| Skip overcurrent clamp | 320 | t=1 | 18.0% |
| TAPER uses full-heat rate, not TAPER-specific | 114 | t=207 | 30.3% |
| Drop cell balancing | 300 | t=21 | 13.9% |

All six clear the 33% target. The new balancing mutant alone corrupts
300/320 ticks, the strongest single-rule divergence after the
overcurrent clamp — confirming the new rule is genuinely load-bearing,
not just added complexity.

## S08 — Why this is harder than the single-cell design, not just bigger

Two local blind pilots fully solved the single-cell design once its
packaging bugs were fixed — the same shape of signal that preceded
TYPECHAIN-9's 99%/100%. The two-cell hardening adds a *sixth* genuinely
interacting rule (not just more volume): cell balancing requires
tracking two independent, diverging state threads simultaneously,
conditionally routing different current to each based on a comparison
that must be re-evaluated every tick, with no guarantee which cell leads
at any given point (S03c.8). This is qualitatively different from the
five existing rules, which all operate on one shared pack-level state —
a model that handled those five correctly could still plausibly get the
balancing direction backwards, apply it to the wrong cell, forget to
re-decay the comparison each tick, or silently collapse back to treating
both cells identically. A real pilot is still the authoritative test
(see mistake #67 — this section is a reasoned hypothesis, not a claim
of certainty).
