# CELLGUARD-10 rubric (v2, two-cell hardened design)

Positive total **122**; two negative criteria, **-4** (independence
prohibition) and **-8** (negative trap). **32 criteria** (within the
platform's 12-50 range). Every weight is capped at 10. Every criterion
body is 301 characters or fewer. Criteria are binary. Accept equivalent
correct work throughout: equivalent languages, source organization, and
output schemas unambiguously equivalent to this packet's stated format.

Hardening note: the single-cell design (v1-v3 of this packet) was fully
solved, correctly, by two consecutive local blind pilots once its two
packaging bugs were fixed (see `STATUS.md`) -- the same shape of signal
that preceded TYPECHAIN-9's 99%/100% (Playbook mistake #67). Hardened
by adding a sixth genuinely interacting rule (cell balancing between
two series cells with different capacities) rather than just adding
volume: a model that handled the original five rules correctly could
still get the balancing direction backwards, apply it to the wrong
cell, forget to re-evaluate it every tick, or collapse back to treating
both cells identically. This is a reasoned hypothesis, not a claim of
certainty (mistake #67's own lesson) -- a real pilot is still the
authoritative test.

Score-topology note: confirmed by actually running all six required
single-rule mutants against this exact rubric's weights (not
estimated): 14.8% / 23.8% / 16.4% / 18.0% / 30.3% / 13.9% -- all under
the 33% target. The new balancing-drop mutant alone corrupts 300/320
ticks, the second-strongest divergence after the overcurrent clamp. See
`STATUS.md` and `design/semantic-contract-cellguard.md` S07/S08 for the
full audit.

Redundancy note: no dedicated negative criterion restates any of the
six local rules as a "must never" prohibition, because dropping any one
necessarily corrupts an already-tested value (the checkpoint/event/
final-state/hash criteria below) -- confirmed by execution for all six.
Adding a negative would score the same root-cause bug twice.

Score-topology 4-bucket partition (plausible-wrong survival ceiling):
package/existence = 3 (criteria 1-3); local rules = 20 (criteria 4-9);
integrated production execution = 48 (criteria 10-21, the 8 checkpoint
records plus the 4 event ticks); final decision/causal reconciliation =
51 (criteria 22-30: final state, hash, verifier x3, memo x4). A
submission granted perfect local-rule knowledge but wrong global
execution keeps bucket 1+2 (23) and the three verifier criteria (15,
tested via standalone crafted scenarios independent of the main trace),
but the memo criteria require citing the submission's own actual
computed values, so a wrong execution plausibly also fails those, along
with final state, hash, and most checkpoints/events (generously
estimate 2 of 12 survive by coincidence). Worst-case survival: roughly
(3+20+10+15)/122 ~ 39%, under the 50% reject threshold. This
theoretical ceiling is secondary evidence; the six real executed mutant
scores (13.9-30.3%, see above) are the authoritative gate.

### Package (1-3, weight 3)

| # | Wt | Criterion |
| --- | --- | --- |
| 1 | +1 | Delivers all six required files: the engine source, the independent verifier source, the full 320-tick two-cell state trace, a findings report, certification evidence (both adversarial rejection results and the trace-integrity hash), and an engineering memo. |
| 2 | +1 | Executes the delivered engine and verifier end to end with a documented, reproducible command. |
| 3 | +1 | Records the language/runtime tool version used, in a declared offline, dependency-free (stdlib-only) execution environment. |

### Local rules (4-9, weight 20)

| # | Wt | Criterion |
| --- | --- | --- |
| 4 | +3 | During CV mode, the delivered engine reduces the CV regulation current by exactly 1.2 every tick, floored at zero -- it never holds the CV regulation current constant. |
| 5 | +3 | In TAPER mode, the delivered engine always applies a heat contribution of 1 for that tick, never the derated or full-mode heat rate, regardless of temperature. |
| 6 | +3 | The delivered engine releases a latched fault only after 4 consecutive ticks at or below temperature 520, never fewer. |
| 7 | +2 | The delivered engine's fault-release hysteresis counter resets to zero immediately if temperature rises back above 520 while the fault is still latched. |
| 8 | +3 | The delivered engine applies the 45-unit overcurrent clamp after thermal derating, not before, to the shared base current each tick. |
| 9 | +6 | The delivered engine recomputes, every tick, whether cell A or cell B currently leads in state of charge, and bleeds 8 units only from whichever cell is currently ahead, never a fixed cell. |

### Certified checkpoint facts (10-17, weight 40)

Each row is one unitary state-snapshot record (mode, both cells' state
of charge, temperature, both cells' delivered current, both cells'
terminal voltage, fault status) at a single named tick, exactly as this
packet's S03 serialization format requires.

| # | Wt | Criterion |
| --- | --- | --- |
| 10 | +5 | Reports the full state at t=175 exactly: mode=CV, soc_a=86.04, soc_b=84.57, temp=575, current_a=17.80, current_b=17.80, voltage_a=4180.63, voltage_b=4171.85, fault=True. |
| 11 | +5 | Reports the full state at t=198 exactly: mode=TAPER, soc_a=86.04, soc_b=84.57, temp=529, current_a=0.00, current_b=0.00, voltage_a=4216.23, voltage_b=4207.45, fault=True. |
| 12 | +5 | Reports the full state at t=206 exactly: mode=TAPER, soc_a=86.04, soc_b=84.57, temp=513, current_a=0.00, current_b=0.00, voltage_a=4216.23, voltage_b=4207.45, fault=False. |
| 13 | +5 | Reports the full state at t=230 exactly: mode=TAPER, soc_a=86.64, soc_b=85.15, temp=489, current_a=1.50, current_b=1.50, voltage_a=4216.86, voltage_b=4207.88, fault=False. |
| 14 | +5 | Reports the full state at t=250 exactly: mode=TAPER, soc_a=87.12, soc_b=85.62, temp=469, current_a=1.50, current_b=1.50, voltage_a=4219.71, voltage_b=4210.73, fault=False. |
| 15 | +5 | Reports the full state at t=280 exactly: mode=TAPER, soc_a=88.06, soc_b=86.57, temp=439, current_a=3.00, current_b=3.00, voltage_a=4222.39, voltage_b=4213.45, fault=False. |
| 16 | +5 | Reports the full state at t=300 exactly: mode=TAPER, soc_a=89.01, soc_b=87.53, temp=419, current_a=3.00, current_b=3.00, voltage_a=4228.07, voltage_b=4219.16, fault=False. |
| 17 | +5 | Reports the full state at t=315 exactly: mode=TAPER, soc_a=89.70, soc_b=88.24, temp=404, current_a=0.00, current_b=3.00, voltage_a=4238.18, voltage_b=4223.45, fault=False. |

### Certified event facts (18-21, weight 8)

| # | Wt | Criterion |
| --- | --- | --- |
| 18 | +2 | Reports the CC-to-CV mode transition as occurring at exactly t=163. |
| 19 | +2 | Reports the CV-to-TAPER mode transition as occurring at exactly t=198. |
| 20 | +2 | Reports the fault latch engaging at exactly t=175. |
| 21 | +2 | Reports the fault latch releasing at exactly t=206. |

### Certification and independent verification (22-30, weight 51)

| # | Wt | Criterion |
| --- | --- | --- |
| 22 | +6 | Reports the full state at t=320 (the final tick) exactly: mode=TAPER, soc_a=89.96, soc_b=88.48, temp=399, current_a=3.00, current_b=3.00, voltage_a=4233.76, voltage_b=4224.88, fault=False. |
| 23 | +10 | Matches the first 16 hex characters of the trace-integrity hash (algorithm in the packet) to `bdce369d719f73af`. |
| 24 | +5 | The independently-coded verifier accepts the true 320-tick trace's own correct checkpoint states in full. |
| 25 | +5 | The independently-coded verifier rejects a claimed fault-release that reports the fault clearing after only 2 consecutive cool ticks instead of 4. |
| 26 | +5 | The independently-coded verifier rejects a claimed state where both cells report identical delivered current throughout, as if cell balancing were never applied. |
| 27 | +5 | Explains in the memo, citing its own reported temperatures, why TAPER mode never uses the derated or full heat rate even while above the derate temperature. |
| 28 | +5 | Explains in the memo, citing its own reported fault-latch tick numbers, why the fault released at t=206 and not at the first tick temperature dropped to or below 520. |
| 29 | +5 | Explains in the memo, citing its own reported currents, that the overcurrent clamp changes the shared base current only for t=1 through t=50, and is a no-op for the rest of the CC phase once derating already brings it below the clamp. |
| 30 | +5 | Explains in the memo, citing at least two specific ticks where balancing activates and at least one where it deactivates, why it does not settle permanently once triggered. |

### Negative criteria (31-32)

| # | Wt | Criterion |
| --- | --- | --- |
| 31 | -4 | Delivers a verifier that imports or reuses the primary engine's computed per-tick state (rather than independently re-implementing the per-tick update rules in its own code) to decide checkpoint consistency. |
| 32 | -8 | Embeds a precomputed final state, checkpoint value, event tick, or the trace-integrity hash, as a literal substituting for executing the delivered engine. Immutable input constants (circuit/model constants) don't trigger this. |
