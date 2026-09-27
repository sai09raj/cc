# KILNWORKS R3 — architecture attack and perfect-semantics ablation

## Why R2 must not be patched

R2 asked the solver to *find the exact global optimum* (lexicographic makespan then
tariff bill) of a small, fully-deterministic scheduling/routing instance: 5 lots x 4
campaigns x 6 designs, each case independently reset, horizons of 30-47 minutes, 2
robots on a 9-node graph. That is precisely the problem shape a constraint-programming
solver (OR-Tools CP-SAT) is built to close quickly and *prove* optimal for. Two supplied
Opus 4.8 Max trajectories did exactly that: built a CP-SAT model, solved all 24 cases to
a certified optimum in under three minutes, and passed every rubric row. The failure was
not a semantic gap — the trajectories show correct topology, fixture, robot, oven and
tariff reconstruction. It was an architecture-class failure: "prove the global optimum of
a small bounded combinatorial design" is a solved problem class for a frontier coding
agent with solver access, independent of how many rules decorate it. Scaling the same
shape (more lots, more designs) repeats Task 04 Revisions A-D ("added complexity without
changing solution path") and risks making the author's own reference unable to certify
optimality either.

## What R3 changes

R3 removes the free optimization decision entirely. There is no "best routing/assignment"
to search for: every dispatch decision (machine assignment, robot action, oven batch
start) is pinned to one explicit, deterministic priority/tie-break policy stated in the
packet. The solver's job becomes *correctly executing that policy* — a discrete-event
simulation problem, not a search problem — across a long, continuous, cross-campaign run
per design, with a state-triggered fault that forces genuine rerouting through the shared
junction. This is the shape that actually held in Task 04 (Revision F): deterministic
composition of many interacting stateful rules over a long uninterrupted trace, verified
by distributed production witnesses, with no scalar "optimum" a generic solver can emit.

Two structural levers carry the new difficulty:

1. **Continuous, overlapping campaign chaining.** R2 reset state independently per
   case (design x campaign), which lets a solver decompose 24 cases into 24 trivial
   independent subproblems. R3 chains a design's four campaigns into one continuous run:
   campaign s+1's lots release on a fixed cadence measured from the design's start,
   regardless of whether campaign s has finished, so lots from consecutive campaigns are
   frequently in the plant (and eligible for the same machines/robots/oven) at the same
   time. Machine setup memory, fixture holdings, robot position/cargo and oven state
   carry across the campaign boundary rather than resetting. There is no case-level
   decomposition left to exploit.
2. **State-triggered robot fault at the shared junction.** The first time Robot 0 ever
   occupies node 4 (the shared junction created by R2's aisle removal) during a design's
   run, it goes offline for a fixed window: no actions, position and cargo frozen, then
   resumes. This is not a fixed clock offset (which a solver could special-case per
   design) but a condition tied directly to the existing shared-junction bottleneck, so
   it is guaranteed to interact with real routing pressure in every design rather than
   being shielded by an early launch block (the Task 04 Revision B mistake).

## Architecture canvas

```text
TASK WORKING TITLE: KILNWORKS R3 — fault-driven reactive dispatch
DOMAIN: manufacturing production/retrofit engineering (kiln plant)
REAL ENGINEERING DECISION: which retrofit design to fund, given how the plant's
  actual (fixed, already-deployed) dispatch policy performs under realistic
  cross-campaign load and one shared-infrastructure fault, not a theoretical
  unconstrained re-optimization the plant cannot run in real time.

FOUR PILLARS
1. Genuine visual interpretation:
   - aisle graph (solid/dashed edges, docks, node capacities) recovered from the
     drawing, as in R2 (this part of R2 worked and is retained);
   - fault window duration measured from a small inset timeline against its own axis,
     not printed as a number;
   - priority/tie-break table and cadence value distributed across separate panels.
2. Iterative tool use: build simulator -> run -> diagnose against independent
   verifier -> find disagreement -> fix -> rerun, across 6 designs and ~150-200
   minute continuous traces each.
3. Expert knowledge: correctly sequencing setup-memory persistence, fixture
   conservation, edge/node collision avoidance under a frozen robot, same-family
   oven batching across overlapping campaigns, and tariff-boundary arithmetic.
4. Long horizon: one continuous multi-campaign trace per design (~150-200 minutes,
   ~20 lots), six designs, cross-file reconciliation of schedule/trace/verifier/
   decision/memo.

DIFFICULTY STACK
- distributed specification: graph in one panel, cadence/campaign chaining in
  another, priority policy in a table, fault mechanism in a note, tariff in another;
- stateful interaction: fixture conservation, setup memory, oven batch membership,
  aggregate power, cross-campaign lot pool, frozen-robot occupancy;
- generated workload/data: 20 lots per design from stated formulas, released on a
  fixed overlapping cadence;
- search/design space: none left as free choice — replaced by verification depth
  (independent full re-simulation across 6 designs must agree exactly);
- coupled targets: makespan first, then tariff-weighted bill, unchanged from R2;
- tie-break: explicit, total-order priority rules for every decision point;
- cross-file consistency: schedule, full trace, independent verifier output,
  decision file and memo must reconcile;
- causal synthesis: explain the fault-forced reroute and the interleaving effect
  using actual event times, and why a distance-only view still cannot certify a
  feasible joint schedule.

POST-SEMANTICS DIFFICULTY (granting every local rule correctly)
- work remaining: composing ~15 interacting deterministic rules correctly across a
  continuous 150-200 minute trace for 6 designs, with no per-case reset to bound
  error propagation;
- interacting persistent state domains: fixture pool, machine setup memory, robot
  position/cargo, oven membership, cross-campaign lot pool, all carried across
  campaign boundaries within a design;
- nonlocal/long-horizon consequences: an early wrong dispatch choice changes which
  lots are in the system when the fault hits, changing everything downstream;
- implementation/debugging burden: getting the fixed-order collision-aware robot
  dispatch right (robot 0 decides, robot 1 must replan around robot 0's action AND
  around the frozen robot during the fault window) is a real scheduling-with-
  obstacles implementation, not a lookup;
- coupled/non-monotonic search or optimization: none free-form, but the six-design
  lexicographic selection with two populations (unrestricted, capital<=9) remains a
  genuine coupled decision over the simulated (not searched) results;
- independent verification and reconciliation: a separately-coded re-simulation
  must reproduce the entire trace exactly, not merely check feasibility of a
  delivered schedule;
- why at least three layers are unavoidable: temporal composition (campaign
  interleaving), verification depth (exact independent re-simulation), and search/
  decision (lexicographic multi-population selection) are all structurally required
  regardless of how well the local rules are understood.

ANTI-SHORTCUTS
- why a clean rewrite does not trivialize it: there is no small reference module to
  replace — the state itself (persistent, interleaved, fault-affected) is the task;
- why one worked example does not reveal all cases: six designs differ in F/G/aisle
  topology/capital, changing whether and when the node-4 fault engages and how much
  campaigns interleave;
- author-owned checker/invariants: fixture conservation, edge/node capacity, cargo
  capacity, oven membership-once-fixed, aggregate power ceiling, all independently
  checked by the verifier;
- plausible mutants: per-campaign reset (ignoring interleaving), ignoring the fault,
  wrong tie-break order, wrong collision-resolution order between robots;
- legitimate alternative outputs: different source organization, equivalent
  formula/label notation, different physically-valid path choices when the policy's
  own tie-break is genuinely tied, are all accepted.

HARD STOP QUESTIONS
- Can prompt+artifact determine one decision-relevant answer class? YES — every
  decision point has an explicit total order; the resulting trace per design is
  unique.
- Does every private oracle rule have a visible source? Must be true before freeze
  (Gate 2 in 04-PREFLIGHT-AND-VALIDATION.md); tracked in semantic-contract.md.
- If given a flawless semantic summary, is substantial integrated implementation/
  search/debugging/decision work still required? YES — see POST-SEMANTICS section.
- Does any expected failure depend mainly on overlooking or misreading one rule?
  NO — the fault and cadence rules are simple and explicit; the difficulty is
  volume and correctness of composition over a long trace, not a hidden trick.
- Can the toolchain run in the target environment? YES — stdlib Python only, no
  network, no external solver required (there is nothing to optimize).
- Would a competent rival answer pass? YES if it reaches the same deterministic
  trace or an equally valid tie-broken variant; different code organization,
  labels, and file layout are explicitly accepted.
```

## Perfect-semantics ablation

```text
TASK / REVISION: KILNWORKS R3
CURRENT REQUIRED FRONTIER MODEL / EFFORT: Claude Opus 4.8, maximum effort

GRANT THE HYPOTHETICAL SOLVER:
- every local rule and measured constant (graph, formulas, priority order, fault
  trigger/duration, cadence, tariff schedule);
- every boundary, priority, tie-break, and reset rule, stated with no ambiguity;
- correct local implementation of each rule in isolation (e.g. it can correctly
  implement "oven starts immediately with 1 or 2 same-family arrived lots" as a
  unit test).

WORK THAT STILL REMAINS:
- integrated temporal/cross-component composition: chaining 4 campaigns per design
  into one 150-200 minute trace with persistent, non-reset state and an overlapping
  lot pool from two campaigns simultaneously in the system;
- workload scale and execution: 20 lots/design x 6 designs, minute-resolution
  simulation, full trace reconciliation;
- search/optimization and coupled decision: none free-form remains, but the
  lexicographic six-design selection across two populations is still a real
  decision that depends on getting all six traces right;
- debugging/iteration: the collision-aware, fault-aware robot dispatch has enough
  interacting edge cases (frozen robot blocking node 4, both robots contending for
  the same edge, campaign-boundary carryover) that a first implementation is very
  unlikely to be correct without inspecting its own trace against the verifier and
  revising;
- independent verification: a second, differently-structured implementation must
  reproduce the exact same 150-200 minute trace for all six designs — this is a
  nontrivial n-version cross-check, not a wrapper;
- cross-file reconciliation: schedule, full trace, verifier output, decision file
  and memo must all agree, including at the fault window and campaign boundaries;
- causal engineering synthesis: explain the fault-forced reroute and interleaving
  effect using actual event times from the delivered trace, and why distance-only
  travel still cannot certify the achieved schedule.

Could a clean small rewrite now solve the task? NO — there is no small module to
  discard; the specified system itself, run continuously and interleaved across
  campaigns, is the task.
Could direct enumeration without a correct interacting model solve it? NO — there
  is nothing to enumerate; the trace is a single deterministic function of the
  input that must be executed, not searched.
Could copied headline literals retain >=50%? Must be checked and kept below 50%
  in the score-topology audit (see score-topology.md once built); the makespan/
  bill values alone must not carry the bulk of positive weight.
Are at least three post-semantics difficulty layers unavoidable? YES — temporal
  composition, independent verification depth, and coupled multi-population
  decision-making.
Does any planned low score depend mainly on semantic omission/misreading? NO —
  every rule (cadence, fault trigger, tie-break order) is stated plainly and
  positively in the packet; the difficulty is volume and correctness of long-
  horizon composition, not a hidden convention.

DISPOSITION: accept architecture, proceed to semantic contract and reference build.
RATIONALE: removes the CP-SAT-shaped free-optimization decision entirely (the
  demonstrated failure mode) and replaces it with the deterministic long-horizon
  composition shape that is the only pattern in this project's history (Task 04
  Revision F) that has actually produced a fair sub-50 outcome against Opus 4.8 Max.
REVIEWER / DATE: author self-review, pending independent packet-only reconstruction
  after the artifact is frozen (see audit/ once populated).
```
