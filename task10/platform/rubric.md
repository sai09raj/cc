# CELLGUARD-10 rubric

Positive total **117**; two negative criteria, **-4** (independence
prohibition) and **-8** (negative trap). **30 criteria** (within the
platform's 12-50 range). Every weight is capped at 10. Every criterion
body is 301 characters or fewer. Criteria are binary. Accept equivalent
correct work throughout: equivalent languages, source organization, and
output schemas unambiguously equivalent to this packet's stated format.

Blind-pilot note (Phase 8.5): a cold subagent with no access to the
reference solution found two real packet bugs before any platform
submission. (1) "Rounded to exactly 2 decimal places" was ambiguous --
it computed a fully correct trace (every checkpoint, event, and final
state here matched canonically) but a different, equally defensible
string format (`25.0` vs `25.00`) produced a different hash. Fixed:
S03 now states fixed-width 2-decimal display explicitly; hash and all
value strings below updated. (2) The packet's own prose claimed the
overcurrent clamp "binds on every CC-phase tick by a constant margin,"
which the pilot correctly identified as false once derating engages
partway through the CC phase (confirmed: binds only t=1-50, a no-op
for t=51-160). Criterion 28 and the packet text were rewritten to ask
for the accurate, more demanding story instead of restating a false
premise. See `STATUS.md` for the full account.

Score-topology note: built around genuine state-threading (every tick's
state is computed from the previous tick's), confirmed by actually
running all five required single-rule mutants against this exact
rubric's weights (not estimated): 15.4% / 24.8% / 21.4% / 14.5% / 31.6%
-- all under the 33% target. See `STATUS.md` and
`design/semantic-contract-cellguard.md` S07 for the full audit,
including the earlier shelved STATIC10 design that failed this same
gate and could not be fixed by reweighting (Playbook mistake #68).

Redundancy note: no dedicated negative criterion restates any of the
four local rules (CV taper-down, TAPER heat exception, fault-release
hysteresis, overcurrent-clamp ordering) as a "must never" prohibition,
because dropping any one of them necessarily corrupts an already-tested
value (the checkpoint/event/final-state/hash criteria below) --
confirmed by execution for all four (S07's mutant table). Adding a
negative would score the same root-cause bug twice.

Score-topology 4-bucket partition (plausible-wrong survival ceiling):
package/existence = 3 (criteria 1-3); local rules = 20 (criteria 4-8);
integrated production execution = 48 (criteria 9-20, the 8 checkpoint
records plus the 4 event ticks); final decision/causal reconciliation =
46 (criteria 21-28: final state, hash, verifier x3, memo x3). A
submission granted perfect local-rule knowledge but wrong global
execution keeps bucket 1+2 (23) and the three verifier criteria (15,
tested via standalone crafted scenarios independent of the main trace),
but the memo criteria require citing the submission's own actual
computed values, so a wrong execution plausibly also fails those, along
with final state, hash, and most checkpoints/events (a few early ticks
might coincidentally still match before the wrong execution's own
divergence point, generously estimate 2 of 12). Worst-case survival:
roughly (3+20+10+15)/117 ~ 41%, under the 50% reject threshold. This
theoretical ceiling is secondary evidence; the five real executed
mutant scores (14.5-31.6%, see S07) are the authoritative gate.

### Package (1-3, weight 3)

| # | Wt | Criterion |
| --- | --- | --- |
| 1 | +1 | Delivers all six required files: the engine source, the independent verifier source, the full 320-tick state trace, a findings report, certification evidence (both adversarial rejection results and the trace-integrity hash), and an engineering memo. |
| 2 | +1 | Executes the delivered engine and verifier end to end with a documented, reproducible command. |
| 3 | +1 | Records the language/runtime tool version used, in a declared offline, dependency-free (stdlib-only) execution environment. |

### Local rules (4-8, weight 20)

| # | Wt | Criterion |
| --- | --- | --- |
| 4 | +5 | During CV mode, the delivered engine reduces the CV regulation current by exactly 1.2 every tick, floored at zero -- it never holds the CV regulation current constant. |
| 5 | +5 | In TAPER mode, the delivered engine always applies a heat contribution of 1 for that tick, never the derated or full-mode heat rate, regardless of temperature. |
| 6 | +3 | The delivered engine releases a latched fault only after 4 consecutive ticks at or below temperature 520, never fewer. |
| 7 | +2 | The delivered engine's fault-release hysteresis counter resets to zero immediately if temperature rises back above 520 while the fault is still latched. |
| 8 | +5 | The delivered engine applies the 45-unit overcurrent clamp after thermal derating, not before, to every tick's delivered current. |

### Certified checkpoint facts (9-16, weight 40)

Each row is one unitary state-snapshot record (mode, state of charge,
temperature, delivered current, terminal voltage, fault status) at a
single named tick, exactly as this packet's S03 serialization format
requires.

| # | Wt | Criterion |
| --- | --- | --- |
| 9 | +5 | Reports the full state at t=161 exactly: mode=CV, soc=83.75, temp=561, current=25.00, voltage=4152.50, fault=False. |
| 10 | +5 | Reports the full state at t=175 exactly: mode=CV, soc=88.53, temp=575, current=16.60, voltage=4198.00, fault=True. |
| 11 | +5 | Reports the full state at t=206 exactly: mode=TAPER, soc=88.53, temp=513, current=0.00, voltage=4231.20, fault=False. |
| 12 | +5 | Reports the full state at t=230 exactly: mode=TAPER, soc=89.13, temp=489, current=1.50, voltage=4231.80, fault=False. |
| 13 | +5 | Reports the full state at t=250 exactly: mode=TAPER, soc=89.63, temp=469, current=1.50, voltage=4234.80, fault=False. |
| 14 | +5 | Reports the full state at t=280 exactly: mode=TAPER, soc=90.63, temp=439, current=3.00, voltage=4237.80, fault=False. |
| 15 | +5 | Reports the full state at t=300 exactly: mode=TAPER, soc=91.63, temp=419, current=3.00, voltage=4243.80, fault=False. |
| 16 | +5 | Reports the full state at t=315 exactly: mode=TAPER, soc=92.38, temp=404, current=3.00, voltage=4248.30, fault=False. |

### Certified event facts (17-20, weight 8)

| # | Wt | Criterion |
| --- | --- | --- |
| 17 | +2 | Reports the CC-to-CV mode transition as occurring at exactly t=161. |
| 18 | +2 | Reports the CV-to-TAPER mode transition as occurring at exactly t=196. |
| 19 | +2 | Reports the fault latch engaging at exactly t=175. |
| 20 | +2 | Reports the fault latch releasing at exactly t=206. |

### Certification and independent verification (21-28, weight 38)

| # | Wt | Criterion |
| --- | --- | --- |
| 21 | +6 | Reports the full state at t=320 (the final tick) exactly: mode=TAPER, soc=92.63, temp=399, current=3.00, voltage=4249.80, fault=False. |
| 22 | +10 | Matches the first 16 hex characters of the trace-integrity hash (algorithm in the packet) to `3e2d011d887d98d6`. |
| 23 | +5 | The independently-coded verifier accepts the true 320-tick trace's own correct checkpoint states in full. |
| 24 | +5 | The independently-coded verifier rejects a claimed fault-release that reports the fault clearing after only 2 consecutive cool ticks instead of 4. |
| 25 | +5 | The independently-coded verifier rejects a claimed delivered current that exceeds 45 as if the overcurrent clamp had never been applied. |
| 26 | +5 | Explains in the memo, citing its own reported temperatures, why TAPER mode never uses the derated or full heat rate even while above the derate temperature. |
| 27 | +5 | Explains in the memo, citing its own reported fault-latch tick numbers, why the fault released at t=206 and not at the first tick temperature dropped to or below 520. |
| 28 | +5 | Explains in the memo, citing its own reported currents, that the overcurrent clamp changes delivered current only for t=1 through t=50, and is a no-op for the rest of the CC phase once derating already brings current below it. |

### Negative criteria (29-30)

| # | Wt | Criterion |
| --- | --- | --- |
| 29 | -4 | Delivers a verifier that imports or reuses the primary engine's computed per-tick state (rather than independently re-implementing the per-tick update rules in its own code) to decide checkpoint consistency. |
| 30 | -8 | Embeds a precomputed final state, checkpoint value, event tick, or the trace-integrity hash, as a literal substituting for executing the delivered engine. Immutable input constants (circuit/model constants) don't trigger this. |
