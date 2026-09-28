## Analyze

```text
Read the packet and reconstruct the 8-floor shaft layout, the door-timing
waveform (opening/dwell/closing spans measured off the axis, not printed as
numbers), and the power-draw bar chart. Recover the fully deterministic
dispatch policy already in force: hall-call assignment by minimum eligible
cost with a strict same-direction-ahead-only eligibility rule (no
backtracking mid-scan), each car's INDEPENDENT per-direction commitment
state (a floor needed while scanning up is a different commitment from the
same floor needed while scanning down -- conflating them is the packet's
most common failure mode), atomic boarding/alighting at the first dwell
tick, and timeout-based reassignment that only switches cars when a
genuinely better one exists (never bounces a call to an equally-good car
merely because a clock expired). Recover the shared power budget: a car
mid-floor-hop or mid-door-cycle keeps its power once admitted, but starting
a NEW hop, a NEW door-open, or the DWELL-to-closing transition are each
their own power-gated event in fixed car-priority order -- door-closing is
not automatic. Treat the 144-configuration sweep as one genuine
multi-objective search: more active cars lowers wait but raises energy
draw, so the wait-optimal, energy-optimal, and budget-constrained
selections are not guaranteed to agree and must each be found by executing
the full legal space, not assumed from one run.
```

## Execute & Generate

```text
Implement a deterministic, offline, tick-by-tick event simulator executing
the packet's policy exactly, generating the 80-call workload from its
formulas -- for each of the 144 legal configurations, one continuous run of
all 80 calls on a shared power budget. Build a separately-coded verifier
that independently re-derives the call table from the same public formulas
and either fully re-simulates or checks a complete feasibility certificate
(power never exceeds budget, no car ever exceeds capacity, every call
boards no earlier than its own arrival and alights strictly after
boarding), sharing only immutable input constants with the primary
implementation. Run the two required adversarial mutations -- a call
boarding before its own arrival, and a tick whose power exceeds that
configuration's budget -- against a preserved original and confirm the
verifier rejects both while accepting the original. Deliver simulator
source, verifier source, the complete 144-row sweep table, a decision file
with all three selections and their keys, certification evidence (the
baseline configuration's full trace plus its stated SHA-256 trace-integrity
hash, computed by the algorithm the packet specifies), and a memo.
Equivalent languages, source organization, output schemas, and physically
valid tie-broken orderings all pass; only one policy-conformant trace per
configuration exists.
```

## Synthesize

```text
Using the 144 executed results, apply the three lexicographic selection
keys (wait-optimal, energy-optimal, budget-constrained under the stated
energy ceiling) and report all three, explicitly noting whether they
agree. Explain, using actual event times from your delivered baseline
trace, at least one concrete instance of the shared power budget forcing
one car's action to wait for another's, and at least one concrete instance
of a call being reassigned away from its original car because a strictly
better car became available (name the call, its origin/direction, both
assigned cars, and the tick each assignment happened). Explain why treating
door-closing as automatic rather than power-gated would understate real
contention, and why a call reassigned away from a car must never later be
served by that original car even if it is still physically nearby.
Reconcile your sweep, selections, verifier agreement, and baseline
witnesses against the same underlying dispatch and power rules. Any
accurate, evidence-tied causal argument is acceptable; no particular
configuration beyond the three selections is required.
```
