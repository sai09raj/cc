# CELLGUARD-10 semantic contract

(Supersedes `semantic-contract.md`, which documents the shelved STA
design and is kept for the record.)

## S01 — Simulation model

A single battery pack, discrete ticks `t = 1..320`, fully deterministic.
Per-tick state: charge mode (`CC`/`CV`/`TAPER`), state of charge `soc`
(%, 0-100), temperature `temp` (0.1 degC units), delivered current
`current`, terminal voltage `voltage`, and fault-latch status `fault`
(boolean) plus its internal hysteresis counter. Every tick's state is
computed from the immediately preceding tick's state — there is no
independent per-tick computation; a wrong value at tick `t` is the
input to tick `t+1`'s computation.

Fixed constants (all given, packet input, never derived):
`CAPACITY=6000`, `CC_CURRENT=50`, `CV_VOLTAGE_THRESHOLD=4150`,
`CV_DECAY_STEP=1.2`, `TAPER_CURRENT_THRESHOLD=8`, `TAPER_CURRENT=3`,
`IR_DROP_PER_UNIT=2.0`, `BASE_VOLTAGE=3700`, `VOLT_PER_SOC_PCT=6.0`,
`AMBIENT=250`, `HEAT_FULL=6`, `HEAT_DERATED=3`, `HEAT_TAPER=1`,
`COOL_PER_TICK=2`, `DERATE_TEMP=450`, `DERATE_FACTOR=0.5`,
`FAULT_TEMP_HIGH=575`, `FAULT_TEMP_LOW=520`, `FAULT_RELEASE_TICKS=4`,
`OVERCURRENT_MAX=45`.

Initial state (before tick 1): `soc=0`, `temp=AMBIENT`, `mode=CC`,
`fault=False`, hysteresis counter `0`, reference voltage `BASE_VOLTAGE`.

## S02 — Per-tick update rules (five genuinely distinct, interacting rules)

Applied in this exact order, every tick:

1. **Mode transition.** If `mode==CC` and the *previous* tick's reported
   voltage `>= CV_VOLTAGE_THRESHOLD`, switch to `CV` and set the CV
   regulation current to `CC_CURRENT`. If `mode==CV` and the CV
   regulation current (before this tick's decay, rule 3) is
   `<= TAPER_CURRENT_THRESHOLD`, switch to `TAPER`. A mode never reverts
   (CC -> CV -> TAPER is one-way).
2. **Mode-commanded current.** `CC`: `CC_CURRENT`. `CV`: the current CV
   regulation current value (before this tick's decay). `TAPER`:
   `TAPER_CURRENT`.
3. **CV current taper-down.** Only in `CV` mode, after computing this
   tick's mode-commanded current: reduce the CV regulation current by
   `CV_DECAY_STEP` (floor zero) for use on the *next* tick's check in
   rule 1/2. `CC` and `TAPER` modes have no decaying regulation current.
4. **Thermal derating and fault gating.** If `fault` is latched this
   tick, delivered current is `0` regardless of mode. Else if this
   tick's *incoming* temperature (before this tick's own heat/cool
   update, rule 6) is `>= DERATE_TEMP`, delivered current is the
   mode-commanded current times `DERATE_FACTOR` — applied in every mode,
   `TAPER` included. Else delivered current is the mode-commanded
   current unmodified.
5. **Overcurrent clamp.** Delivered current (after rule 4) is capped at
   `OVERCURRENT_MAX` — applied last, after derating, not before.
6. **Heat generation.** If delivered current is `0`, no heat this tick.
   Else if `mode==TAPER`, heat is `HEAT_TAPER` regardless of temperature
   (TAPER's low current means it never needs the higher derated-heat
   rate even while hot) — **this is this packet's own rule, not a
   generic assumption: do not apply `HEAT_DERATED` to a TAPER-mode tick
   just because temperature is above `DERATE_TEMP`.** Else if incoming
   temperature is `>= DERATE_TEMP`, heat is `HEAT_DERATED`. Else heat is
   `HEAT_FULL`.
7. **Temperature update.** `temp = temp_incoming + heat - COOL_PER_TICK`.
8. **Fault-latch hysteresis.** If not already latched and the *new*
   temperature (after rule 7) is `>= FAULT_TEMP_HIGH`: latch the fault,
   reset the hysteresis counter to `0`. Else if already latched: if the
   new temperature is `<= FAULT_TEMP_LOW`, increment the hysteresis
   counter; once the counter reaches `FAULT_RELEASE_TICKS`, un-latch and
   reset the counter to `0`. If the new temperature rises back above
   `FAULT_TEMP_LOW` while latched, reset the counter to `0` immediately
   (it does not keep partial credit toward release). **A fault does not
   release the instant temperature drops below the low threshold — it
   requires `FAULT_RELEASE_TICKS` *consecutive* ticks at or below it.**
9. **State of charge.** `soc = min(100, soc_prev + delivered_current /
   CAPACITY * 100)`.
10. **Terminal voltage.** `voltage = BASE_VOLTAGE + soc * VOLT_PER_SOC_PCT
    - delivered_current * IR_DROP_PER_UNIT`. This tick's own voltage,
    not next tick's — rule 1 reads the *previous* tick's voltage for its
    decision, never this tick's own just-computed value.

## S03 — Certificate serialization (mechanical, from the first draft)

Header line: `CELLGUARD10-CERT-V1`

Then one line per tick, `t=1` through `t=320`, in order:

```text
t={t};mode={mode};soc={soc};temp={temp};current={current};voltage={voltage};fault={fault}
```

`soc`, `current`, and `voltage` rounded to exactly 2 decimal places;
`temp` is an integer (0.1 degC units, always integral under these
constants); `fault` is `True` or `False` (Python-style capitalization,
matching the reference engine's own `str()` output — any clearly
equivalent boolean rendering, e.g. `true`/`false`, is accepted).

Certificate hash: SHA-256 of the full serialized text (header through
the `t=320` line, newline-joined, trailing newline included), first 16
hex characters.

## S04 — Independent verification (independently re-coded, never
importing or calling the primary's implementation)

The independent verifier re-implements S02's per-tick update rules
itself, from scratch, in its own code — never importing, calling, or
reading any state from the primary engine. It replays the simulation
from `t=1` up to each of five chosen checkpoint ticks (crafted to land
on a mode transition, a fault-latch engage tick, a fault-latch release
tick, and two ordinary ticks) and checks its own independently-computed
state at each checkpoint against the primary's claimed state for that
same tick. This is the same "independently re-derive, never share
computed state" discipline every prior task in this project uses for
its independent verifier — here applied to a fresh re-implementation of
the tick-update rules rather than a structurally different algorithm,
since the per-tick rules are themselves simple enough that the
independence has to come from separate code, not a different method.

## S05 — Required adversarial mutations against the verifier (crafted
standalone)

1. A claimed one-tick transition where the fault-latch hysteresis
   counter is reported as satisfied (fault released) after only 2
   consecutive cool ticks instead of the required `FAULT_RELEASE_TICKS`
   (4). The verifier must reject.
2. A claimed one-tick transition where the overcurrent clamp is skipped
   (reports a delivered current above `OVERCURRENT_MAX`) despite the
   claimed inputs otherwise being correct. The verifier must reject.

## S06 — Deliverables

Primary engine source; independent verifier source; the full 320-tick
trace; a findings report; certification evidence (both adversarial
rejection results, plus the SHA-256 hash); an engineering memo
explaining, with specific ticks from its own output: why TAPER mode's
heat generation does not follow the derated-heat rule even while hot
(rule 6's own-stated exception), why the fault latch released at the
specific tick it did and not earlier (rule 8's hysteresis), and why the
overcurrent clamp binds throughout the entire CC phase (rule 5 applied
after derating, not before — delivered current during undeprated CC
is `50 > OVERCURRENT_MAX=45`).

## S07 — Score-topology gate (S08), run before any rubric text

Five required mutants, each run against the real engine, real circuit:

| Mutant | Ticks differing (of 320) | First divergence | Score vs. drafted rubric |
|---|---|---|---|
| Drop thermal derating (`no_derate`) | 270 | t=51 | 15.4% |
| Fault releases instantly, no hysteresis counter (`fault_release_no_hysteresis`) | 118 | t=203 | 24.8% |
| CV current never decays, TAPER never reached (`cv_no_decay`) | 160 | t=161 | 21.4% |
| Skip overcurrent clamp (`no_overcurrent_clamp`) | 320 | t=1 | 14.5% |
| TAPER uses full-heat rate, not TAPER-specific rate (`taper_uses_full_heat`) | 114 | t=207 | 31.6% |

Every mutant corrupts a substantial, non-trivial fraction of the full
trace, and every mutant scores under the 33% target against the real,
executed rubric weights in `reference/score_counterfactual.py` — unlike
the shelved STA design, where every mutant corrupted at most 1-2 of 14
independent arcs and no fair reweighting could clear 33%. The
`taper_uses_full_heat` mutant required extending the simulation from
260 to 320 ticks: its divergence is numerically small and slow to build
at first (temperature drifts apart gradually, not an instant jump), but
by t=268 the accumulated heat difference pushes the mutant trajectory
into a second, spurious fault-latch cycle the canonical trace never
enters — a strong, late-arriving discriminator that the original
260-tick window was simply too short to capture. Checkpoint/event/
weight tuning for all five mutants is recorded in `STATUS.md`.
