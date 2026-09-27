## Analyze

```text
Read the packet and reconstruct the solid/dashed aisle graph, docking bays P/Q/K,
and the shared junction node 4 that every delivery to K must cross in both aisle
configurations. Recover the fully deterministic dispatch policy already in force:
machine assignment priority and persistent per-machine family memory, the six-rule
robot priority order with same-minute collision resolution, and the oven's bounded
pairing timer anchored to each lot's own arrival minute. There is no free scheduling
choice to search for. Recover the one-time node-4 disruption: on Robot 0's first
arrival there, it freezes for a fixed window read from the packet's timeline, not
printed as a number. Recover the independent machine-Q maintenance freeze triggered
by cumulative processing time, and notice it uses the packet's default t-to-t+1
timing convention rather than the node-4 rule's explicitly stated inclusive
exception -- the two disruptions are deliberately timed differently. Treat each of
the six designs as one continuous run covering
all four campaigns on a shared clock, shared fixture pool, and shared machine memory
-- overlapping campaign release windows mean lots from two campaigns are routinely
in the plant at once. A distance-only relaxation cannot certify a feasible joint
robot schedule because it ignores shared-edge and interior-node occupancy.
```

## Execute & Generate

```text
Implement a deterministic, offline, minute-by-minute event simulator executing the
packet's policy exactly -- for each of the six designs, one continuous trace across
all 20 lots (four campaigns). Build a separately-coded verifier that independently
re-derives each design's full trace from the same visible rules, sharing only
immutable input constants with the primary implementation, and confirm the two agree
exactly. Run the required negative-start and route-collision adversarial mutations
against preserved originals, and identify the collision mutation's first invalid
minute. Deliver simulator source, verifier source, full per-design schedules with
every robot-minute and machine/oven activity, the six-design case matrix with both
selections and keys, certification evidence (traces plus adversarial results), and a
memo. Reconcile each trace's starts/completions, robot cargo/position, fixture
holdings, minute power, and cumulative bill against the reported case values.
Equivalent languages, source organization, output schemas, and physically-valid
tie-broken routes all pass; only one policy-conformant trace per design exists.
```

## Synthesize

```text
Using the six executed results, apply the lexicographic key (makespan, bill plus
three times capital, capital, design ID) to select the unrestricted recommendation
and, separately, the best design with capital at most nine. Compare the baseline
design against both selections using their executed objectives. Explain at least one
actual routing, batching, or resource interaction using event times from a delivered
trace -- for example how the node-4 disruption forces a reroute, or how a design's
fixture ceiling determines whether the oven ever pairs two lots -- and connect it to
the recommendation. Explain why a distance-only travel bound cannot certify the
achieved schedule, and why treating the four campaigns as independent resets would
not reproduce the required continuous-run results (cite a concrete consequence, such
as a machine losing its cross-campaign setup memory or a cross-campaign oven pairing
becoming impossible). Reconcile schedules, traces, verifier agreement, and selection
arithmetic against both disruption mechanisms as well as the ordinary machine/robot/
oven rules. Any accurate, evidence-tied causal argument is acceptable; no particular
route or additional design comparison is required.
```
