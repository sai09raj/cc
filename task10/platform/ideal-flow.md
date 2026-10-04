## Analyze

```text
Read the packet and recover the fixed two-cell battery pack model: each
cell's own capacity, charge mode currents and voltage/current
thresholds, thermal coefficients, the derate temperature and factor,
the fault latch engage and release temperatures and required
consecutive tick hysteresis, and the cell balancing threshold and bleed
amount. Recover the exact order of eleven per tick update rules: mode
transition based on whichever cell's previous voltage is higher, mode
commanded current, CV current taper down (unconditional, not gated by
fault status), thermal derating and fault gating producing one shared
base current, the overcurrent clamp applied after derating, cell
balancing splitting that base current unevenly between the two cells
based on their own running state of charge, heat generation driven by
the base current with TAPER's own exception, temperature update, fault
latch hysteresis, and per-cell state of charge and voltage updates
using each cell's own capacity. Treat every tick's state, for both
cells, as depending on the immediately preceding tick's state -- a
wrong value at tick t is the input to tick t+1 for both cells.
```

## Execute & Generate

```text
Implement a deterministic, offline two-cell battery charge and thermal
controller simulation that threads state across all 320 ticks under
this packet's own update rules. Build a separately coded independent
verifier that reimplements the per tick update rules itself, in its own
code, and checks several checkpoint ticks by independently replaying
from tick one using only its own logic, never importing or reading any
state computed by the primary engine. Run the two required adversarial
mutations against the verifier: a claimed fault release after two
consecutive cool ticks instead of four, and a claimed state where both
cells report identical current throughout as if balancing were never
applied. Confirm the verifier rejects both while still accepting the
true trace's own correct checkpoint states. Deliver engine source,
verifier source, the full 320 tick two-cell trace, certification
evidence, and a memo. Equivalent languages and source organization all
pass; exactly one physically valid trace exists for this fixed model
under these rules.
```

## Synthesize

```text
Using your own executed engine's actual reported temperatures and tick
numbers, explain why TAPER mode's heat generation never follows the
derated heat rate even while the pack is above the derate temperature.
Explain why the fault latch released at the specific tick it did, not
the first tick temperature dropped to or below the release threshold,
citing the required consecutive tick counter and what resets it.
Explain exactly which CC phase ticks the overcurrent clamp actually
changes the delivered current on, and why it stops once derating has
engaged and already reduced current below the clamp -- confirm this
with your own engine's incoming temperature values, not an assumption
that the clamp binds uniformly. Explain, citing specific ticks where
balancing activates and deactivates, why it does not settle permanently
once triggered -- tie this to the two cells' differing capacities and
the fact that the comparison is re-evaluated every tick. Report your
verifier's agreement on the true trace, both adversarial mutation
rejection results, and the final trace integrity hash, reconciling all
of it against the same eleven update rules and the trace's actual
dependency chain, not as separate facts but as one coherent causal
story from the stated rules to the final certificate.
```
