## Analyze

```text
Read kilnworks.pdf and reconstruct the solid/dashed aisle graph from the drawing. Distinguish docking bays from capacity-one interior nodes and undirected edge occupancy from endpoint occupancy. Reconstruct release, setup memory, fixture lifetime, atomic minute actions, pickup/unload visibility, fixed same-family batches, aggregate power and tariff arithmetic. Treat routes, machine assignments, starts, waiting and batch membership as joint decisions. Generate all five lots for each of four campaigns and all six design IDs. Define the lexicographic makespan/bill objective and separate unrestricted versus capital<=9 selection populations. A distance matrix alone cannot establish a feasible joint route.
```

## Execute & Generate

```text
Build an offline exact optimizer and a separately runnable independent verifier, sharing only immutable input data. Execute all24 design/campaign cases. Establish each minimum makespan, then its minimum tariff-weighted bill; preserve both feasible schedules and complete independent lower-bound evidence. Justify state merging and pruning rather than treating a search digest as proof. Deliver optimizer source, verifier source, schedules with every robot-minute, full case matrix and decisions, certification evidence with production traces, and an engineering memo. Reconcile each schedule with starts/completions, robot cargo/positions, machine/oven activity, fixture conservation, aggregate power and final bill. Run the negative-start and collision mutations, preserving the originals; identify the collision mutation's first invalid minute. Record commands/tool versions and a debugging or adversarial-check iteration. Equivalent offline algorithms, source organization, output schemas and optimal schedules pass.
```

## Synthesize

```text
Use executed optimal results to recommend D5 with key (33,1116,22,D5), and choose D1 under capital<=9 with key (37,1110,7,D1). Compare D0 against both selected designs using their executed objectives. Explain at least one actual routing, batching or resource interaction using event times from delivered schedules, and connect it to the recommendation. Explain why distance-only travel is a lower bound rather than a joint collision-feasible routing certificate. Reconcile schedules, traces, metrics, proofs and selection arithmetic. Describe an executed debugging or adversarial-check iteration. Any accurate supported interaction is acceptable; no particular route, optimal schedule or additional design comparison is required.
```
