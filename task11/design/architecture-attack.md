# Task 11 — architecture attack (TENURE-11, working title)

## What the last six tasks teach

| Task | Mechanism | Outcome | Why |
|---|---|---|---|
| KILNWORKS (05) | Job-shop dispatch, two robots on a 9-node graph, oven batching, design sweep | Blind pilot only | n/a |
| ATRIUM-9 (06) | 4-car elevator dispatch, 144-config sweep, 3 competing selections | **20% / 21%** real | Dozens of eligibility/cost/tie-break micro-rules compounding over a long run; graded on whole-sweep aggregates |
| QUORUM-7 (07) | 5-node Raft under scripted faults, timeout sweep | **31% / 32%** real | Many protocol micro-rules over time; message counts drifted |
| LEDGER-8 (08) | Accounting consolidation | 92–100% real, shelved | Facts structurally independent |
| TYPECHAIN-9 (09) | Hindley–Milner inference | 99% / 100% real, shelved | One clearly flagged deviation point |
| CELLGUARD-10 (10) | One battery pack, 11 formula rules, single trace | 121/122 target-model, shelved | Rule list was the perfect-semantics summary; no arbitration, search, or decision; no measured visual (mistake #70) |

The two tasks that held below 50 share four properties. CELLGUARD-10 had
none of them:

1. Dozens of **policy micro-rules** that choose among competing candidates
   (eligibility, ordering, tie-breaks, thresholds, timers), not a handful
   of arithmetic update formulas.
2. **Long-lived state with nonlocal consequences**: an early choice changes
   what is possible much later.
3. A **configuration sweep graded on whole-sweep aggregates**, so one small
   deviation anywhere moves nearly every row.
4. **Competing or constrained selections** whose answers disagree.

Task 11 must have all four, plus a constant or relationship that can only be
recovered from geometry in the artifact, and its mechanism must not be a
reskin of anything above.

## Candidates considered

| Candidate | Mechanism | Rejected because |
|---|---|---|
| Warehouse robot fleet (MAPF) | Agents moving on a grid with collision rules | KILNWORKS already had robots on a graph with collision avoidance; order-to-robot assignment echoes ATRIUM-9 call assignment |
| Single-track railway dispatch | Trains reserving blocks, meets and passes | Same "agents reserving a spatial resource" family as KILNWORKS and ATRIUM-9 |
| Distribution-feeder protection coordination | Relays racing on inverse-time curves | Mostly formula evaluation per fault (CELLGUARD failure mode); same Electrical domain as task10 |
| Truss progressive collapse | Stiffness re-solve after member failure | Few policy micro-rules; mostly linear algebra a model transcribes reliably |
| DB lock manager (2PL, deadlock victims) | Transactions contending for locks | Agent contention again; weak genuine visual |
| **Generational garbage collector tuning** | Bump allocation, copying minor GC, tenuring, free-list old generation, mark-sweep with coalescing, write barrier | **Selected** |

## Selected: generational GC tuning for a fixed mutator workload

**Domain:** Computer Engineering. **Subdomain:** Runtime systems —
generational garbage-collector configuration for a latency-bounded service.

**Engineering decision:** pick an eden size, survivor size, tenuring
threshold, and old-generation placement policy that minimize GC cost for a
fixed allocation workload, subject to a pause-time ceiling and no
out-of-memory failure.

### The system

- **Young generation:** eden (bump-pointer allocation) and two survivor
  spaces. A minor GC fires when an allocation does not fit in eden. Live
  young objects are copied breadth-first (Cheney order) into the empty
  survivor space; each copy increments the object's age.
- **Tenuring:** an object whose age reaches the threshold is promoted to the
  old generation instead of the survivor space. An object that does not fit
  in the survivor space is promoted early (overflow promotion).
- **Old generation:** a non-moving free-list allocator with address-ordered
  first-fit placement; block splitting has a minimum remainder, and freed
  blocks coalesce with neighbours only during a major GC sweep. Placement
  decides fragmentation, and fragmentation decides when promotion fails.
- **Pretenuring:** objects at or above a configured size are allocated
  directly in the old generation, skipping eden.
- **Major GC:** fires when a promotion cannot be placed: mark from roots,
  sweep and coalesce the old generation, retry the promotion; if it still
  fails, the run ends in OOM and the configuration is infeasible.
- **Write barrier / remembered set:** storing a young reference into an old
  object records that old object; minor-GC root scanning visits the
  remembered set in a specified order, and the set is rebuilt after each GC.
- **Mutator:** a deterministic operation stream generated from compact phase
  rules (temporaries, ring-buffered sessions, a long-lived registry, and a
  cache whose old entries are repointed at young objects), so old-to-young
  references and medium-lived objects both occur.
- **Pause model:** each GC's pause is a stated linear function of bytes
  copied, objects marked, roots scanned, and remembered-set entries.

### Sweep and selections

96 configurations: eden size (4 values) × survivor size (2) × tenuring
threshold (4) × pretenure threshold (3; see the prototype result below for
why this replaced placement policy). Every
configuration runs the full workload. Reported per configuration: minor and
major GC counts, bytes copied, bytes promoted, total pause, maximum pause,
peak old-generation occupancy, OOM flag.

Three selections that should disagree:

1. minimum total pause among non-OOM configurations;
2. minimum maximum pause subject to a total-pause budget;
3. smallest young-generation footprint subject to a maximum-pause ceiling.

Expected non-monotonic behavior (confirmed by the prototype below): a low
tenuring threshold promotes medium-lived session objects that then die in
the old generation and fragment it; a high threshold copies them back and
forth and overflows the survivor space, which also promotes them.
Pretenuring trades copying cost against old-generation garbage and
fragmentation.

### Genuine visual content (visual-ablation test)

- **Heap map:** regions drawn to scale on an address axis. The old-generation
  size and object header size are measured from the axis, not printed.
- **Object-kind chart:** payload size per object kind as bars against
  gridlines; reference-slot count per kind as markers.
- **Mutator phase timeline:** phase boundaries along an operation-count axis,
  measured from the drawing.
- **Object lifecycle diagram:** eden → survivor → old transitions as labelled
  arrows; the overflow-promotion edge exists only in the diagram.

If the prose were OCR-extracted alone, the old-generation size, the header
size, the payload sizes, and the phase lengths would all be missing.

## Perfect-semantics ablation

Grant the solver a flawless executable summary of every rule and every
measured constant. What remains:

- **Implementation depth:** heap regions with exact address arithmetic and
  alignment; Cheney copying with a specified root, remembered-set, and field
  scan order; three placement policies with splitting and a roving pointer;
  mark-sweep with coalescing; write barrier; workload generator; pause model.
  Several hundred lines across interacting modules, not one loop.
- **Nonlocal consequences:** a single object placed at a different old
  address changes fragmentation, which changes when a promotion fails, which
  changes every later major GC and pause. Copy order changes survivor
  addresses and which objects overflow.
- **Scale:** tens of thousands of operations per run, ~96 full runs.
- **Coupled selection:** three constrained selections over the sweep, with
  infeasible (OOM) rows excluded.
- **Verification:** an independent re-implementation must reproduce
  aggregates and production witnesses; adversarial mutations must be
  rejected.
- **Causal synthesis:** explain the tenuring non-monotonicity and why the
  placement policy flips feasibility, with the solver's own numbers.

Could a small clean rewrite solve it? No. Could direct enumeration without a
correct model? No; every metric depends on the full simulation. Could copied
literals retain 50%? Not if the bulk of the weight sits on sweep aggregates
and production witnesses. Does a planned low score depend mainly on misreading
one rule? No; the bet is that exact composition of ~40 micro-rules across
~96 long runs does not survive intact, which is the mechanism behind the
20%/21% and 31%/32% results.

**Disposition:** accept, pending the prototype gate below.

## Shape-diversity check (playbook 00, "Domain diversity is not task-shape diversity")

- **Core mechanism:** memory management with address-dependent
  fragmentation. Not dispatch, not agents moving on a graph, not a protocol,
  not formula integration. New in this project.
- **Pipeline:** simulate → sweep → constrained selections → independent
  verification is shared with ATRIUM-9, KILNWORKS, and QUORUM-7. This is
  deliberate: it is the pipeline that produced the only sub-50 real pilots
  here. The risk the playbook names is someone solving it by pattern-matching
  an earlier task's module layout; that does not transfer, because none of
  the GC machinery exists in any earlier task.
- **Nearest neighbour:** TYPECHAIN-9 is also language-implementation
  flavoured, but it was static inference with one global substitution; this
  is runtime state with thousands of objects and address-level effects.

Flagged for the user rather than hidden: the pipeline shape repeats; the
mechanism does not.

## Prototype gate result (scratch model, not the reference)

Run in the session scratchpad (`proto11/gcp.py`), 26,000 mutator
operations per configuration, 96 configurations in about 13 s.

**Design change from the first draft.** With placement policy as a sweep
dimension, first fit / best fit / next fit only differed near OOM: the high
end of the old generation stays one large free block, so placement moved
total pause by under 3% in every feasible group. Placement is now a single
fixed rule (address-ordered first fit with a minimum split remainder), and
the fourth dimension is a **pretenuring threshold** (objects at or above it
are allocated directly in the old generation). Pretenuring places
variable-size blobs in the old generation, so fragmentation and placement
now matter in every run.

Sweep: eden {16, 24, 32, 48 KiB} × survivor {8, 24 KiB} × tenuring threshold
{1, 2, 3, 5} × pretenure threshold {off, 768, 1024 B} = 96 configurations.

| Check | Result |
|---|---|
| Pretenure effect within each (eden, survivor, tenuring) group | total-pause spread median 50%, max 94% |
| Tenuring non-monotonic in total pause | 14 of 24 (eden, survivor, pretenure) groups |
| Three selections (min total pause; min max pause under a total-pause budget; smallest young footprint under a max-pause ceiling) | three different configurations |
| Breadth-first vs depth-first copy order | 96/96 rows change |
| Promote at age > T instead of ≥ T | 96/96 rows change |
| No coalescing in the sweep | 96/96 rows change |
| Promotion guard on largest free block instead of total free | 96/96 rows change |
| Remembered set scanned in insertion order instead of address order | 53/96 rows change |

The single-rule deviations above are exactly the kind of small, plausible
implementation differences the architecture depends on, and each one moves
most of the sweep. This is the same blast-radius property CELLGUARD-10 had,
so it is necessary but not sufficient; the open question is whether a strong
model actually makes any of these slips when ~40 rules interact. Only the
early `opus` probe answers that.

## Gates before the full build

1. **Prototype gate** (mistake #68): a scratch model must show non-monotonic
   tenuring behavior, policy-dependent OOM or major-GC differences, and that
   each single-rule deviation (copy order, overflow promotion, coalescing
   timing, placement tie-break, remembered-set handling) changes a large
   share of sweep rows. If deviations only touch a few rows, redesign before
   writing the engine.
2. **Early difficulty probe** (mistake #70): once the engine and a draft
   artifact exist, run an `opus`-alias blind pilot before writing the rubric
   or platform text. A clean content solve means redesign, not patching.
3. Standard gates afterwards: semantic contract, bidirectional
   source↔code audit, independent reconstruction, score topology,
   reverse coverage (every criterion traces to a prompt or artifact clause).
