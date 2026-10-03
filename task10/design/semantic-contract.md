# Task 10 — STATIC10 semantic contract

## S01 — Circuit description format

A fixed synchronous digital circuit, given as packet input (analogous to
task09's `program.ty` or LEDGER-8's trial balance — stated data, not
something to derive):

- **Clocks**: a named list, each with a period (ps) and a clock
  uncertainty/derate margin (ps, combined jitter+skew, subtracted from
  setup margin). Clocks not explicitly related by a stated integer ratio
  are asynchronous to each other.
- **Flip-flops**: a named list, each assigned to one clock, with a
  clock-to-Q delay (`Tcq`), a setup time (`Tsu`), and a hold time (`Th`),
  all in ps.
- **Gates**: a named list forming a DAG between flip-flop outputs. Each
  gate has one or more input nodes (a flip-flop's `.Q` output, or another
  gate's output) and exactly one propagation delay (ps) applied once at
  that gate, regardless of which input changed. A gate has exactly one
  output, which may fan out to multiple downstream gates or flip-flop `.D`
  inputs. Each flip-flop `.D` input is driven by exactly one source
  (directly a flip-flop `.Q`, or one gate's output) — never two.
- **Constraints**: a list of path exceptions, each naming a specific
  (launch flip-flop, capture flip-flop) pair and its regime (see S02).
  Any (launch, capture) pair with real combinational connectivity and no
  listed exception uses the DEFAULT regime.

## S02 — The four path regimes

Every register-to-register **timing arc** — one specific (launch
flip-flop, capture flip-flop) pair connected through the gate DAG — is
governed by exactly one of four regimes. Classify every arc from the
constraints list before computing anything; an arc with no matching
constraint entry is DEFAULT.

1. **DEFAULT** (same clock domain, no exception):
   - `setup_slack = T - Tsu - uncertainty - Tcq - max_comb`
   - `hold_slack = Tcq + min_comb - Th`
   - where `T` is the shared clock's period, `max_comb`/`min_comb` are
     this arc's worst-case/best-case combinational delay (S03), and
     `Tcq`/`Tsu`/`Th`/`uncertainty` are the launch flip-flop's `Tcq`, the
     capture flip-flop's `Tsu`/`Th`, and the shared clock's uncertainty.

2. **MULTICYCLE(N)** (same clock domain, setup relaxed to N cycles):
   - `setup_slack = N*T - Tsu - uncertainty - Tcq - max_comb`
   - `hold_slack = Tcq + min_comb - Th` — **identical formula to
     DEFAULT's hold check, not shifted by N or N-1.** This packet's rule:
     a multicycle setup exception relaxes the setup check only; it never
     relaxes or shifts the hold check unless a separate, explicitly
     stated hold exception says so (none exists in this packet — every
     MULTICYCLE arc here uses the plain DEFAULT hold formula). Do not
     assume a multicycle path's hold check is shifted by N or N-1 cycles
     from training knowledge of other conventions; this packet does not
     shift it at all.

3. **FALSE** (excluded from both checks): report as `EXCLUDED` — no
   setup or hold slack value. The arc's physical combinational delay
   still exists in the netlist and may be computed internally, but must
   never appear as a reported slack value; a false path is functionally
   unreachable in practice (e.g., two mutually exclusive mode-select
   inputs), not merely "not critical."

4. **CDC** (crosses between two asynchronous clock domains): no setup or
   hold slack is computed — the two clocks share no fixed phase
   relationship, so no fixed-period formula applies. Instead, report
   whether the arc is `SYNCHRONIZED` or `CDC_VIOLATION`, based on its
   stated synchronizer depth (an explicit constraints-file field, an
   input fact, not derived from gate delay): `SYNCHRONIZED` only if
   `synchronizer_depth >= 3`. This packet's rule is 3, not the commonly
   cited minimum of 2 synchronizer stages — do not assume 2 is
   sufficient from general hardware-design knowledge; recover the
   specific threshold from this section.

## S03 — Arc delay computation (arrival-time propagation)

For each candidate launch flip-flop `L`, compute two forward DAG
propagations over the gate network, each treating `L.Q` as the only
reached source (`arrival = 0`) and every other flip-flop's `.Q` as
unreached:

- **MAX propagation** (worst-case, for setup): for each gate, if any
  input is reached, `arrival(gate) = max(reached inputs' arrivals) +
  gate.delay`.
- **MIN propagation** (best-case, for hold): identical, but
  `arrival(gate) = min(reached inputs' arrivals) + gate.delay`, and a
  gate is reached only if *every one of its inputs that is reachable
  from any launch flip-flop at all* is reached from `L` — in this
  packet's circuit no gate has a mix of reachable-from-`L` and
  reachable-only-from-elsewhere inputs, so this never needs
  disambiguation; still implement it generally.

For a flip-flop `C` whose `.D` input is reached from `L` (directly or
through gates) in a given propagation, that is a real timing arc
`L -> C`; `max_comb` is its MAX-propagation arrival at `C.D`, `min_comb`
its MIN-propagation arrival at `C.D`. A pair with no reachability has no
arc — do not report one.

## S04 — Certificate serialization (mechanical, from the first draft)

Header line: `STATIC10-CERT-V1`

Then one line per arc, in a fixed order: **sorted first by launch
flip-flop name, then by capture flip-flop name, both plain
lexicographic string order.** Line format, by regime:

- DEFAULT: `{launch}>{capture}:DEFAULT:setup={setup_slack};hold={hold_slack}`
- MULTICYCLE(N): `{launch}>{capture}:MULTICYCLE{N}:setup={setup_slack};hold={hold_slack}`
- FALSE: `{launch}>{capture}:FALSE:EXCLUDED`
- CDC: `{launch}>{capture}:CDC:depth={synchronizer_depth};status={SYNCHRONIZED|CDC_VIOLATION}`

All slack values are signed integers (ps), no decimal point, no unit
suffix, no leading `+`.

Then two final lines:

- `CRITICAL_PATH={launch}>{capture}:{setup_slack}` — the DEFAULT or
  MULTICYCLE arc with the minimum `setup_slack` (FALSE and CDC arcs are
  never candidates, since neither has a setup slack). **Tie-break rule**
  (ties are possible and expected when two arcs share their entire
  worst-case route): the arc that sorts first under S04's own fixed
  ordering (launch name, then capture name) wins.
- `WORST_HOLD={launch}>{capture}:{hold_slack}` — the DEFAULT or
  MULTICYCLE arc with the minimum `hold_slack`, same tie-break rule if
  needed.

Certificate hash: SHA-256 of the full serialized text (header through
the `WORST_HOLD` line, newline-joined, trailing newline included),
first 16 hex characters — same convention as every prior task in this
project.

## S05 — Independent verification (invariant reconciliation, not a
second path-enumeration engine)

The independent verifier takes the primary's claimed per-arc table and
the raw circuit/constraints as input and checks a different, narrower
set of properties by a different method — it never re-runs S03's full
arrival-time propagation:

1. **Regime reclassification**: independently re-derive every arc's
   regime from the constraints file alone (not trusting the primary's
   stated regime); reject if any claimed regime disagrees.
2. **Formula consistency**: for every claimed DEFAULT/MULTICYCLE arc,
   recompute `setup_slack`/`hold_slack` from the claimed `max_comb`/
   `min_comb` (back-solved from the claimed slack and the known
   `T`/`Tcq`/`Tsu`/`Th`/`uncertainty`/`N`) and confirm internal
   consistency with the regime's own formula; reject a claim that used
   the wrong regime's formula.
3. **FALSE/CDC shape**: reject a claimed FALSE arc that reports a
   numeric slack, or a claimed CDC arc that reports one, or a CDC arc
   whose `SYNCHRONIZED` status disagrees with its own stated
   `synchronizer_depth >= 3`.
4. **Aggregate consistency**: confirm the claimed `CRITICAL_PATH` really
   is the minimum `setup_slack` among the claimed DEFAULT/MULTICYCLE
   arcs (applying the same tie-break), and the claimed `WORST_HOLD`
   really is the minimum `hold_slack` among them.

## S06 — Required adversarial mutations against the verifier (crafted
standalone, not derived from corrupting the main circuit)

1. A claimed table where one arc the constraints mark FALSE instead
   reports a numeric `setup`/`hold` value (as if DEFAULT). The verifier
   must reject.
2. A claimed `CRITICAL_PATH` that is not actually the minimum
   `setup_slack` among the claimed table's DEFAULT/MULTICYCLE arcs
   (i.e., some other claimed arc has a lower `setup_slack`, but the
   claimed table names a different one as critical). The verifier must
   reject.

## S07 — Deliverables

Primary engine source; independent verifier source; the full per-arc
timing table for all 14 arcs plus `CRITICAL_PATH`/`WORST_HOLD`; a
findings report; certification evidence (both adversarial rejection
results, plus the SHA-256 trace-integrity hash); an engineering memo
explaining, with specific arcs from its own output: why the multicycle
hold formula is not shifted despite the setup relaxation, why the two
CDC arcs classify differently under the packet's 3-stage threshold, and
why the chosen tie-break (not a different plausible one) correctly
resolves the A0>B1 / A1>B1 setup-slack tie.

## S08 — Score-topology gate (run before any rubric text is written)

Required mutants, each applied to the real engine and run against the
real circuit, each must score under 33% against the real (not yet
written) rubric weights:

1. Drop the multicycle setup relaxation (treat every MULTICYCLE arc as
   DEFAULT, N=1) — corrupts both multicycle arcs' setup slack and
   should flip `CRITICAL_PATH` or at least every multicycle arc's
   reported value.
2. Drop the "hold is not shifted for multicycle" rule (apply some
   shifted hold formula instead) — corrupts both multicycle arcs' hold
   values without affecting anything else; the real test of whether this
   specific rule is load-bearing on its own, not just a restatement of
   mutant 1.
3. Drop FALSE-path exclusion (report the false arc's real numeric
   values instead of `EXCLUDED`) — corrupts one arc's reported shape.
4. Drop the CDC 3-stage threshold, substituting the commonly-cited
   minimum of 2 — flips C1>D1's status from `CDC_VIOLATION` to
   `SYNCHRONIZED` (and would flip C0>D0 too if its depth were exactly
   2, which it is not, so this specifically tests whether the model
   recovers the number 3 rather than just copying one CDC arc's correct
   answer by chance).
5. Wrong tie-break direction (last in S04 order wins, not first) — for
   this specific circuit, A0>B1 and A1>B1 genuinely tie on
   `setup_slack`; this flips which one is reported as `CRITICAL_PATH`
   while every per-arc value stays correct, testing whether the
   aggregate-selection rule is actually checked, not just the per-arc
   facts.

Each mutant's real, executed score against the drafted rubric must be
recorded in `STATUS.md` before the rubric is finalized, not estimated.
If any mutant scores >=33%, the rubric's weight distribution (not the
mutant) is wrong and must be revised before writing prompt/ideal-flow.

## S09 — Perfect-semantics ablation note

Unlike task09 (one globally-uniform deviation), every one of S08's five
mutants targets a *different* one of the four regimes or the aggregate
selection rule — a model has to get all of: regime classification,
three distinct arithmetic formulas, one exclusion rule, one threshold
recovery, and one tie-break rule correct, simultaneously, across 14
arcs, for the certificate to match. Getting any single one of these
five independently-droppable behaviors wrong produces a real, checked,
divergent score — there is no single flag whose correct reading alone
guarantees full credit, unlike task09's S02.
