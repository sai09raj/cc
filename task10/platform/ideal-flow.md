## Analyze

```text
Read the packet and recover the fixed battery pack model: capacity,
charge mode currents and voltage/current thresholds, thermal
coefficients (heat generation per mode, cooling rate), the derate
temperature and factor, the fault latch engage and release
temperatures, and the required consecutive tick hysteresis on release.
Recover the exact order of ten per tick update rules: mode transition
based on the previous tick's voltage, mode commanded current, CV
current taper down, thermal derating and fault gating, the overcurrent
clamp applied after derating not before, heat generation with TAPER
mode's own exception, temperature update, fault latch hysteresis, state
of charge integration, and terminal voltage. Treat every tick's state as
depending on the immediately preceding tick's state, not as an
independent per tick computation: a wrong value at tick t is the input
to tick t plus one. Recover the fully mechanical certificate
serialization: literal header, one line per tick in order, exact field
names and rounding.
```

## Execute & Generate

```text
Implement a deterministic, offline battery charge and thermal
controller simulation that threads state across all 320 ticks under
this packet's own update rules, not a generic or textbook charge
controller model. Build a separately coded independent verifier that
reimplements the per tick update rules itself, in its own code, and
checks several checkpoint ticks by independently replaying from tick
one using only its own logic, never importing or reading any state
computed by the primary engine. Run the two required adversarial
mutations against the verifier: a claimed fault release after two
consecutive cool ticks instead of four, and a claimed delivered current
above the overcurrent clamp as if it were never applied. Confirm the
verifier rejects both while still accepting the true trace's own correct
checkpoint states. Deliver engine source, verifier source, the full
320 tick trace, certification evidence (both rejection results plus the
SHA256 trace integrity hash), and a memo. Equivalent languages and
source organization all pass; exactly one physically valid trace exists
for this fixed model under these rules.
```

## Synthesize

```text
Using your own executed engine's actual reported temperatures and
tick numbers, explain why TAPER mode's heat generation never follows
the derated heat rate even while the pack is above the derate
temperature, contrary to what a reader might assume given every other
mode does follow that rule once hot. Explain why the fault latch
released at the specific tick it did, not at the first tick temperature
dropped to or below the release threshold, citing the required
consecutive tick counter and what resets it. Explain exactly which CC
phase ticks the overcurrent clamp actually changes the delivered
current on, and why it stops changing it once derating has engaged and
already reduced current below the clamp -- confirm this with your own
engine's own incoming temperature values, not an assumption that the
clamp binds uniformly across the whole CC phase. Report your
verifier's agreement on the true trace, both adversarial mutation
rejection results, and the final trace integrity hash, reconciling all
of it against the same ten update rules and the trace's actual
dependency chain, not as four separate facts but as one coherent causal
story from the stated rules to the final certificate.
```
