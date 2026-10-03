# Task 10 — architecture attack and perfect-semantics ablation

## Why TYPECHAIN-9 (task09) is shelved

Built fully — engine, independent checker, score-topology-audited
rubric, metadata-stripped artifact — and its score-topology gate passed
cleanly (17.7% primary mutant, well under the 33% target). Two real
Opus 4.8 pilots then scored 99% and 100%: confirmed genuine, full,
correct solves (exact hash match, both adversarial mutations correctly
implemented, the required divergence-from-ML memo section written
unprompted). Root cause, logged as Playbook mistake #67: the task's
entire difficulty hinged on one clearly-flagged, mechanically simple
predicate (the generalization-eligibility rule), stated unambiguously
everywhere on purpose. A careful frontier model just read it and applied
it correctly, so the cascading amplification — real and verified at the
synthetic-mutant level — never triggered, because the underlying mistake
it was built to amplify never happened. See `task09/STATUS.md`.

## The property task10 must have

Not just "amplifies a mistake once made" (task09 had that and still
failed) but **genuine likelihood that a careful frontier model still
gets something wrong**, even with an unambiguous spec. QUORUM-7 (31%/32%
real pilots) gets this from *many distinct, interacting rules* across a
long simulation — enough rules that at least one is likely to be slightly
misapplied even by a careful solver. Task10 needs the same property,
via a different mechanism.

## Avoiding reuse of every prior task's shape

Checked task10's candidate mechanism against every task actually built
in this project, not just domain labels (per
`00-START-HERE-EVERY-FUTURE-TASK.md`'s "domain diversity is not the same
as task-shape diversity" section):

| Task | Domain | Core mechanism |
|---|---|---|
| KILNWORKS (task05) | Industrial/kiln scheduling | discrete event dispatch |
| ATRIUM-9 (task06) | Elevator dispatch | discrete event dispatch |
| CISTERN-7 (shelved, task07) | Wastewater lift-station | continuous mass-balance integration |
| QUORUM-7 (task07) | Distributed consensus | message-passing protocol / stateful simulation over time |
| LEDGER-8 (shelved, task08) | Consolidated accounting | arithmetic bookkeeping, largely independent facts |
| TYPECHAIN-9 (shelved, task09) | Type inference | unification / constraint propagation, single global substitution |

Every "simulate state forward through time" mechanism (discrete-event
dispatch, continuous integration, protocol/consensus) has been used at
least once, including by two shelved tasks — reattempting any of them
risks looking like a reskin even with a new domain label and a different
pipeline. **Task10 uses graph/longest-path analysis: no simulated time
axis, no threaded global state, no event queue.** This is the one
mechanism category from the Playbook's own list (`discrete event dispatch
vs. continuous-state integration vs. ... constraint satisfaction,
graph/routing, protocol/consensus, statistical inference`) genuinely
untouched by this project so far.

## The task: static timing analysis (STA) on a fixed digital circuit

Domain: **Electrical Engineering** (platform's fixed list; also unused
by this project so far). Subdomain: static timing analysis for a
synchronous digital circuit with multiple clock domains and timing
exceptions.

A fixed netlist is given: flip-flop registers connected by combinational
logic paths (a DAG between register stages), annotated with gate
propagation delays, flip-flop setup/hold requirements, and a clock
network with **multiple clock domains** running at different periods.
A separate constraints file marks specific paths with **timing
exceptions**: some are multicycle paths (the default single-cycle setup
check is relaxed to N cycles), some are false paths (excluded from
timing checks entirely — functionally exercised but never
simultaneously, e.g. mutually exclusive mode-select logic), some cross
clock domains and require synchronizer treatment (excluded from the
normal setup/hold check, subject to a different metastability-margin
check instead).

The task: compute setup and hold slack for **every register-to-register
timing arc** in the circuit, applying the *correct rule regime per path*
— not one uniform rule — and report the worst (most negative, or least
positive) slack, the specific critical path that achieves it, and a
mechanical certificate/hash over the full per-arc slack table.

### Why this creates genuine, not-just-amplified difficulty

Task09 failed because it had **one** rule, applied the same way
everywhere, clearly flagged. STA instead requires correctly
**classifying which of four regimes governs each specific path** (default
single-cycle, multicycle, false-path exclusion, clock-domain-crossing)
and applying that regime's specific check — setup and hold checks use
*opposite* clock-edge relationships, a multicycle exception changes the
setup check's available time but not the hold check's, a false path is
excluded from both but must still appear in the delivered per-arc table
as excluded (not silently dropped), and a CDC path's "check" is a
different computation entirely (synchronizer stages vs. direct setup/hold
math). With dozens of paths and four possible regimes, the combinatorial
surface for misapplying a regime to the wrong path, or applying the
right regime with the wrong edge convention, is far larger than task09's
single globally-uniform predicate — much closer to QUORUM-7's "many
interacting rules" property than to task09's "one flagged deviation."

### Perfect-semantics ablation risk (and mitigation)

Risk: a frontier model has seen "setup and hold timing" and "critical
path" in training data (digital design courses, EDA literature) and
could pattern-match a generic STA explanation without engaging with
*this packet's specific* exception set and clock topology. Mitigation,
decided now rather than discovered after a pilot:

- the clock topology, exception list, and gate/flop timing numbers are
  packet-specific and must be recovered from the attached spec, not
  assumed from a textbook example;
- at least one exception type gets a **non-standard twist** stated only
  in the packet (to be fixed in the semantic contract) so textbook EDA
  knowledge alone is insufficient — mirroring task09's S02 deviation,
  but this time embedded inside a path-classification decision with
  three siblings competing for the same path, not a single globally-
  applied flag;
- hold-check analysis is commonly under-covered in generic explanations
  (most casual treatments focus on setup/max-delay); requiring full,
  correct hold-check treatment across every regime raises the floor on
  what "mostly right" looks like.

## Independent verification shape

Not a second path-enumeration-and-summation algorithm (too close to a
parallel reimplementation of the primary, the trap this project has
avoided since QUORUM-7's independently-different verifier and task09's
bidirectional, not re-inferencing, checker). Instead: an **invariant-
reconciliation verifier** that takes the primary's claimed per-arc table
and the raw netlist/constraints as input, and checks a different set of
properties by a different method — e.g., re-derives each claimed path's
regime classification independently from the constraints file (not
trusting the primary's classification), confirms claimed slack values
are internally consistent with the claimed regime's formula (without
re-walking the whole graph), and confirms the claimed critical path
really is the minimum across all claimed arcs. Required adversarial
mutations against the verifier (not derived from the main graph, crafted
standalone): (a) a claimed slack for a path that the constraints file
actually marks false — verifier must reject; (b) a claimed critical path
that is not actually the minimum of the claimed table — verifier must
reject.

## Oracle feasibility

Fully offline, deterministic, no stochastic elements: fixed netlist,
fixed delays, fixed clock periods, fixed exception list. A reference
implementation can enumerate every register-to-register path via
topological traversal of the combinational DAG between flip-flop stages,
apply the regime-specific formula per path, and produce an exact
canonical answer — same executable-oracle discipline as every other task
in this project.

## Deliverables (plan)

- `design/semantic-contract.md` — exact netlist/constraint format, the
  four path regimes and their precise setup/hold formulas (including the
  non-standard packet-specific twist), the certificate serialization
  rule (mechanical from the first draft, applying mistake #66), the
  independent verifier's invariant set, the required adversarial
  mutations, and the S08 score-topology gate requirement (<33% on every
  tested mutant, checked by actual execution before any rubric is
  written, applying mistake #67 — specifically checking that dropping
  *each* regime's special-case handling independently produces a real,
  non-trivial divergence, not just one of the four).
- `reference/sta_engine.py` — primary path enumeration and timing engine.
- `reference/circuit.*` — the fixed netlist and constraints (the packet's
  own stated input, analogous to task09's `program.ty`).
- `reference/sta_verify.py` — independent invariant-reconciliation
  verifier.
- `reference/score_counterfactual.py` — score-topology audit, run before
  any rubric text is written.
- `platform/` — rubric, prompt, ideal-flow, built and audited against
  the full `03-RUBRIC-AND-LINTER-GUIDE.md` checklist from the first
  draft (not retrofitted after a platform linter finding, applying the
  lessons from this session's task09 rubric work).
- `artifact/` — metadata-stripped, rasterized PDF packet.

## Addendum: STA shelved, replaced by CELLGUARD-10

STA (static timing analysis) was built in full and shelved at the S08
gate — see `STATUS.md`. Its arcs were structurally independent
(synchronous digital design deliberately breaks combinational
dependency into per-stage analyses), so no single-bug mutant could be
made to cascade, and no fair reweighting under the platform's
+-10-per-criterion cap could fix that. Logged as Playbook mistake #68.

Replacement: **CELLGUARD-10**, a discrete-tick battery pack
charge/thermal controller simulation (`reference/bms_engine.py`).
Domain: Electrical Engineering, subdomain battery management system
(BMS) charge control and thermal protection. Every tick's state (state
of charge, temperature, voltage, charge mode, fault-latch status) is
computed from the *previous* tick's state — genuine state-threading,
confirmed empirically before further build: all 5 candidate single-rule
mutants (drop thermal derating, drop fault-latch hysteresis, skip CV
current taper-down, skip the overcurrent clamp, wrong TAPER-mode
heating) corrupt 54-260 of 260 ticks each, not 1-2 arcs out of 14 like
STA. Five genuinely different interacting rules — mode transition
(CC/CV/TAPER), thermal derating, fault-latch hysteresis, overcurrent
clamping, and per-mode heat generation — give the same "many interacting
rules" property QUORUM-7 has, now paired with real cascading, which STA
lacked.

## Next steps

1. Write `design/semantic-contract.md` with the exact regime formulas,
   including the non-standard twist, and the certificate format.
2. Design the fixed circuit (sized for enough paths to make regime
   misclassification plausible — likely 15-25 register-to-register arcs
   across 2-3 clock domains) with deliberate path-regime diversity.
3. Build `sta_engine.py`, verify its canonical output by hand on a small
   sub-case before trusting the full circuit.
4. Build `sta_verify.py` with genuinely different verification logic.
5. Run the S08 score-topology gate (drop each regime's special-case
   handling independently, confirm each produces a real divergence
   under <33%) before writing any rubric text.
6. Write and audit the platform package.
