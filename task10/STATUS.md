# Task 10 — CELLGUARD-10 (active), STATIC10 (shelved, kept as record)

Current active candidate: **CELLGUARD-10**, in `reference/`, `design/`,
`platform/`, `artifact/`. State: SCORE-TOPOLOGY GATE PASSED (S08),
ENGINE AND INDEPENDENT VERIFIER VERIFIED END TO END, FULL PLATFORM
PACKAGE COMPLETE (rubric, prompt, ideal-flow, metadata-stripped PDF
artifact). NOT YET pilot-tested; local blind pilot (Phase 8.5) planned
before any platform submission.

## CELLGUARD-10: discrete-tick battery charge/thermal controller

A single battery pack, 320 fully deterministic ticks, every tick's
state computed from the previous tick's state (genuine state-threading,
not independent per-item facts — the property STATIC10 lacked). Ten
per-tick update rules across five areas: mode transition (CC/CV/TAPER),
thermal derating, overcurrent clamping, TAPER-mode's heat exception, and
fault-latch hysteresis. Domain: Electrical Engineering.

### Score-topology audit (S08 gate, run before the rubric was written)

`reference/score_counterfactual.py`, scored against the actual executed
engine over the full 320-tick trace, not estimated:

| Mutant | Score |
|---|---|
| canonical (sanity) | 100.0% |
| drop thermal derating | 15.4% |
| fault releases instantly, no hysteresis | 24.8% |
| CV current never decays, TAPER never reached | 21.4% |
| skip overcurrent clamp | 14.5% |
| TAPER uses full-heat rate, not TAPER-specific | 31.6% |

All five clear the <33% target. Getting here required real tuning, not
a first-try success — recorded honestly:

- Two of the five rule-drop mutants were initially **silent** (zero
  effect on the trace) when first implemented: a "same-tick vs
  previous-tick voltage" CC→CV mutant turned out to read an identically
  stale value either way (a loop-variable bug in the mutant itself, not
  a real ambiguity), and the overcurrent clamp never bound because peak
  CC current (50) never exceeded the original threshold (60). Fixed by
  lowering `OVERCURRENT_MAX` to 45 (below CC_CURRENT, so the clamp is
  load-bearing at the start of the CC phase) and replacing the
  voltage-timing mutant with a cleaner one (CV current never decays).
  Note (corrected after the blind pilot, see below): the clamp only
  actually binds for t=1-50, before derating engages at t=51 and
  already brings current to 25 (below the 45 clamp) for the rest of the
  CC phase -- "load-bearing on every CC-phase tick" was never literally
  true; the mutant's strength (320/320 ticks differ) comes from the 50
  ticks of extra delivered current creating a permanent SoC/temperature
  offset that then propagates through the rest of the simulation via
  the usual state-threading, not from the clamp binding throughout.
- Initial checkpoint-based rubric weights (5 checkpoints clustered in
  the first half of the trace, package/local/event weights set by
  precedent) still left three mutants over 33% (40–66%, then 37–55%
  after a first reweight). Root-caused per mutant: the checkpoints
  simply didn't *land* after each mutant's divergence point — e.g. the
  TAPER-heat-rate bug's effect is numerically small and slow to build
  (first divergence at t=207, but checkpoints capped at t=250 then
  showed only a few degrees' difference, not enough to fail hash-sized
  scrutiny). Extending the simulation from 260 to 320 ticks revealed why
  that specific mutant needed more room: the accumulated heat error
  eventually pushes the mutant trajectory into a **second, spurious
  fault-latch cycle** (t=268–299) that the canonical trace never enters
  — a strong, late-arriving discriminator the shorter window couldn't
  capture. Final weights: checkpoints dropped the two earliest (always-
  matching, non-discriminating) ticks in favor of two later ones, event
  weight reduced (mode/fault-transition *timing* turned out insensitive
  to 2 of the 5 mutants), local-rule weight redistributed across 4
  dedicated rule criteria instead of 3 so every mutant's root rule has
  an owning criterion.

## Independent verifier verified end to end

`reference/bms_verify.py` — re-implements the ten per-tick update rules
from scratch, in its own code, never importing `bms_engine`. Replays
from t=1 to each of 5 checkpoint ticks independently and compares
against the primary's claimed state.

- **Accepts the true 320-tick trace in full** (all 5 checkpoints
  consistent, confirmed by execution).
- **Rejects both required adversarial mutations**: a claimed fault
  release after 2 consecutive cool ticks instead of 4, and a claimed
  delivered current above the overcurrent clamp as if never applied.

## Deliverables

- `reference/bms_engine.py` — primary engine, S01-S03, with 5 mutant
  hooks for the score-topology audit.
- `reference/bms_verify.py` — independent verifier (S04), re-coded from
  scratch, verified to accept the true trace and reject both required
  adversarial mutations.
- `reference/score_counterfactual.py` — score-topology audit, all 5
  mutants verified under 33% (14.5%-31.6%).
- `design/architecture-attack.md` (with the STATIC10→CELLGUARD-10 pivot
  addendum), `design/semantic-contract-cellguard.md`.
- `platform/rubric.md` — 29 criteria, positive total 117, two negatives
  (-4 independence, -8 trap), audited against the full
  `03-RUBRIC-AND-LINTER-GUIDE.md` checklist from the first draft (every
  checkpoint/event criterion states its own expected values explicitly,
  all three memo topics from the prompt have an owning criterion, no
  mechanism+value bundling, 4-bucket score-topology ceiling computed
  explicitly at ~41%).
- `platform/prompt.md` — 443 words, zero internal hyphens (mistake #64).
- `platform/ideal-flow.md` — Analyze/Execute & Generate/Synthesize.
- `artifact/cellguard10_v1.pdf` — 5 pages (3 rasterized figures:
  constants table, per-tick rules, certificate-format worked example
  with fake data; 2 text spec pages). Verified byte-level: empty
  metadata (Info dict and XMP both blank), zero vector drawing objects
  on every page, one raster image per figure page and zero on text
  pages, no leaked computed values (no checkpoint state, no event tick,
  no hash) anywhere in extracted text, no tool/path signatures in the
  raw bytes.

## Local blind pilot (Phase 8.5) — ran, found two real bugs, both fixed

A cold subagent, given only the frozen `prompt.md` and `cellguard10_v1.pdf`
in an isolated directory with zero access to `reference/`, `design/`, or
`platform/rubric.md`, solved the task genuinely blind. Result: a model-
quality, well-engineered solution (from-scratch independent verifier
using a deliberately different implementation style — class-based replay
with Decimal/round-half-up arithmetic vs. the primary's float arithmetic
— both required adversarial tests correctly rejected, clean reproduction
verified, all ambiguities honestly flagged rather than silently guessed
past) that still diverged from canonical, for a real, fixable reason.

**Bug 1 — hash mismatch despite every checkpoint value matching exactly.**
All 9 reported state records (8 checkpoints + final) matched canonical
byte-for-byte on every field, yet the certificate hash differed
(`3e2d011d887d98d6` vs. the old canonical `f3bf4a132dfb66b5`). Root
cause: the reference engine's `serialize()` used a bare `round(x, 2)`
followed by Python's default float-to-string conversion, which drops
trailing zeros (`25.0`, not `25.00`) — while S03's text ("rounded to
exactly 2 decimal places") is genuinely ambiguous between that and
fixed-width display. The blind pilot's reading (fixed 2-decimal width)
is the more natural one and is what a real pilot would plausibly also
do. Same failure class as mistake #66 (LEDGER-8's hash-serialization
ambiguity), this time in a decimal-formatting rule rather than a
field-order rule. Fixed: `serialize()` now uses `:.2f` formatting; new
canonical hash `3e2d011d887d98d6` — confirmed by independently
recomputing it after the fix and finding it matches the blind pilot's
own hash exactly. All value strings in `rubric.md` and the artifact's
Figure 3 updated to match; S03 states the fixed-width rule explicitly
now.

**Bug 2 — a factually false claim in the packet's own prose.** SPEC_TEXT,
prompt.md, ideal-flow.md, and rubric criterion 28 all asserted the
overcurrent clamp "binds on every CC-phase tick... by a fixed, constant
margin independent of temperature." The blind pilot traced its own
engine's incoming-temperature values and found this is false: derating
engages at t=51 (temperature reaches 450), reducing current to 25
*before* the clamp step runs — since 25 < 45, the clamp executes
(structurally, every tick, as the rules require) but only *binds*
(changes the value) for t=1-50; it's a no-op for the remaining 110 of
160 CC-phase ticks. The pilot reported this as "a genuine tension...
worth flagging to whoever owns the spec" rather than quietly bending
its explanation to match the false premise — exactly the honest
behavior this phase is meant to surface. Fixed: the overclaiming prose
rewritten everywhere (SPEC_TEXT section 3, prompt.md, ideal-flow.md)
to state the true, more interesting story; rubric criterion 28 rewritten
to ask for the accurate explanation (which ticks it binds on, and why
it stops) instead of asking the model to justify a false premise.

**Four smaller judgment calls**, all resolved the same way the reference
engine actually behaves (so none caused this run's divergence, but each
was a real gap a different, equally defensible guess could exploit on a
future run): whether the CV regulation current is available the same
tick the CC→CV transition fires (yes); whether the CV→TAPER check and
taper-down both read the pre-decay value (yes, same "previous value"
convention as voltage); whether internal state carries full precision
between ticks or rounds every tick (full precision; rounding is
display-only); whether the hysteresis counter resets to zero at the
instant of release (yes). All four now stated explicitly in S03a of the
semantic contract and in SPEC_TEXT.

Artifact rebuilt as `cellguard10_v2.pdf` (Playbook mistake #46: always
rename on a content revision). Re-ran the full S08 gate after all fixes
— see the table above, unchanged (the fixes only affect display
formatting and prose accuracy, not the underlying per-tick computation
the mutants exercise).

## Second local blind pilot (Phase 8.5, round 2) — clean solve, bugs confirmed closed

A fresh cold subagent, same isolation (zero access to reference/design/
rubric), given only `prompt.md` and `cellguard10_v3.pdf`. Result: exact
match to canonical on everything. Hash `3e2d011d887d98d6` — identical.
All 8 checkpoints and the final state matched field-for-field, including
the 2-decimal format (`25.00`, not `25.0`). All 4 event ticks matched.
Verifier correctly accepted the true trace and rejected both required
adversarial mutations. The rewritten memo criterion (overcurrent-clamp
explanation) was answered correctly and precisely: independently
confirmed via its own code that the clamp binds on exactly t=1-50
("contiguous, count=50") and is a structural no-op for the rest of the
CC phase — exactly the corrected story, not the old false premise.

One more honest judgment call surfaced, again causing no divergence
(this pilot resolved it the same way the reference engine does) but
real and worth closing: the CV regulation-current taper-down (rule 3)
is unconditional for CV-mode ticks, not gated by the fault latch — so
the CV-to-TAPER mode transition can fire, and does fire in this model
at t=196, while the fault is still latched (release isn't until t=206).
Closed explicitly in S03b of the semantic contract and in SPEC_TEXT
section 2. Artifact rebuilt as `cellguard10_v3.pdf`; gate re-verified
unchanged.

**Honest caveat, not just good news**: two cold blind pilots in a row
have now fully solved CELLGUARD-10 once the packaging bugs were fixed —
correctly implementing all five interacting rules with zero computation
errors. That is real validation the packet is finally clean, but it is
*not* evidence the content difficulty will hold against a real target-
model pilot; it is the same shape of signal (a careful solver reading
an unambiguous spec and just getting it right) that preceded
TYPECHAIN-9's 99%/100%. Phase 8.5's local blind pilots are a packaging
and spec-ambiguity check, not a difficulty predictor — Phase 10/11's
real pilot is still the only evidence that actually settles this.

## Hardening: cell balancing added as a sixth interacting rule

User chose to harden content rather than proceed to a real pilot after
two clean blind-pilot solves. Rebuilt around a genuinely new dimension,
not just more volume: the pack is now **two series-connected cells (A,
B)** with different capacities (`CAPACITY_A=5700`, `CAPACITY_B=6300`),
each with its own independently-tracked state of charge and voltage.
Mode, temperature, and fault remain pack-level and shared. A new rule
(S02.6): every tick, whichever cell currently leads in state of charge
has 8 units bled from its delivered current (a passive balancing
resistor); the lagging cell gets the full shared base current.
Re-evaluated from scratch every tick — because the two capacities
differ, which cell leads is not fixed for the whole run (confirmed:
balancing is active 63 of 320 ticks, toggling on/off 122 times, not a
one-time correction that then sits idle).

This is qualitatively different from the five existing rules, which all
operate on one shared pack-level state: a model that handled those five
correctly could still get the balance direction backwards, apply it to
the wrong cell, forget to re-decay the comparison each tick, or
silently collapse back to treating both cells identically.

Prototyped numerically first (per mistake #68's lesson — confirm the
dynamics before writing the real engine): an initial design (fixed
initial SoC offset, equal capacities) only exercised balancing for 4
ticks total, then the gap froze and never moved again — too weak a
test. Switched to differing capacities with equal starting SoC, which
produces sustained, oscillating divergence throughout the run instead.

Score-topology re-verified with all six mutants (five original plus
drop-balancing): 14.8% / 23.8% / 16.4% / 18.0% / 30.3% / 13.9% — all
clear 33%. The balancing-drop mutant alone corrupts 300/320 ticks
(first divergence at t=21), the strongest single-rule divergence after
the overcurrent clamp, confirming the new rule is genuinely
load-bearing. Independent verifier rewritten with a new required
adversarial test (claimed state with both cells receiving identical
current, as if balancing were never applied) in place of the old
clamp-bypass test, which no longer fit the two-cell state shape.

Rubric rebuilt (32 criteria, positive total 122) applying the same
discipline as every prior audit this session: all 9 checkpoint/event/
final-state facts re-verified byte-for-byte against a fresh execution,
all bodies ≤301 chars, the new balancing local-rule and memo criteria
checked for atomicity/self-containment. Platform prompt rewritten for
the two-cell model and trimmed to stay under the 500-word cap (454
words, zero hyphens). Artifact rebuilt as `cellguard10_v4.pdf`
(6 pages now: 3 figures, 3 text pages), re-verified byte-level clean.

## Round 3: third local blind pilot against the hardened two-cell packet

Ran a fresh, cold subagent (zero access to `design/`, `reference/`, or
`platform/`, only the frozen `prompt.md` and `cellguard10_v4.pdf`) per
Phase 8.5. Result: a clean solve. Its reported hash, all 8 checkpoint
records, all 4 event ticks, the final-tick state, and both verifier
adversarial-rejection results matched a fresh execution of the
reference engine exactly, byte-for-byte. Its memo correctly reconciled
TAPER heat, fault-release hysteresis, the overcurrent clamp's narrow
active window, and cell balancing's repeated activation/deactivation —
the same four stories required by criteria 27-30.

This is the **third consecutive clean local-blind-pilot solve** of this
content (round 1 after its two packaging-bug fixes, round 2, and now
round 3). Recorded honestly, not as pure reassurance: this is the same
signal shape — repeated clean solves on sequential hardening passes —
that preceded TYPECHAIN-9's eventual 99%/100% real-pilot failure
(mistake #67). A local blind pilot is not a difficulty predictor; it
only catches packaging/spec bugs, and it has now done that three times
running. It is not evidence that a real pilot will also fail to solve
this content — only evidence that the packet is no longer obviously
broken.

**New finding (packet-correctness bug, not a solving-skill gap):** the
pilot's own findings report noted, as an honest observation rather than
a complaint, that in its executed trace cell A (the smaller-capacity
cell) was the only cell ever bled across the full run — it never saw
the lead flip to cell B, despite the packet's own prose (S03c item 8,
and the matching `make_packet.py` SPEC_TEXT section 4) explicitly
telling solvers not to assume a fixed leader and that "which cell is
ahead is not fixed for the whole run."

Verified this independently by direct execution before trusting the
pilot's framing (same discipline as every other finding this project):
computed `leaders = {r['t']: 'A' if ... else 'B' ...}` across all 320
ticks where `current_a != current_b` (63 active ticks) — every single
one shows cell A, never cell B. Then ran 5 retuning experiments varying
`CAPACITY_A`/`CAPACITY_B`, `BALANCE_THRESHOLD`, and `BALANCE_BLEED`
across different combinations to check whether this was just an
unlucky constant choice fixable by retuning — all 5 still showed
`leaders: {'A'}` with zero flips. Concluded this is a **structural,
not incidental, property of the rule**: with a constant shared current,
the smaller-capacity cell always gains state-of-charge percentage
faster than the larger one (same numerator, smaller denominator), so
once an imbalance opens it structurally becomes, and stays, the
leading cell — balancing only ever narrows the gap back toward the
threshold, it can never reverse which cell is ahead. No retuning of
these three constants changes that direction; it would need either
equal capacities (which collapses the rule to the single-cell case) or
a capacity relationship that changes mid-run (which this packet's
fixed-constant model doesn't have).

This is the same category of bug as mistake #69 (a packet's own prose
overclaiming a consequence of its stated rules, discovered only by an
independently-reasoning solver executing far enough to check the
claim) — not a hand-typed wrong number, but an assumption about
runtime behavior nobody traced before asserting it. Fixed by rewriting
the claim everywhere it appeared: `design/semantic-contract-cellguard.md`
S03c item 8, and `artifact/make_packet.py` SPEC_TEXT section 4. Both now
state the true story — the leading cell is *derived* from which
capacity is smaller, must still be computed fresh every tick rather
than hardcoded, but for this packet's fixed constants the lead does not
flip across the run. Checked `platform/rubric.md`, `platform/prompt.md`,
and `platform/ideal-flow.md` via targeted grep for the same false
claim: none of the three contained it — they only state the separate,
confirmed-true claim that balancing itself toggles on and off
repeatedly (122 transitions), which is unaffected and needed no change.
Criterion 9 and criterion 30 in `platform/rubric.md` were specifically
re-examined against this finding and judged still accurate as written,
since both describe the *mechanism* (recompute fresh every tick, don't
hardcode a cell) without asserting an observed flip.

No engine, constant, or computed value changed — this was a
prose-only fix. Re-ran `bms_verify.py` and `score_counterfactual.py`
after the fix to confirm: canonical hash, all 8 checkpoints, all 4
events, and all 6 mutant scores (14.8% / 23.8% / 16.4% / 18.0% / 30.3%
/ 13.9%) are byte-identical to the pre-fix run, as expected. Artifact
rebuilt as `cellguard10_v5.pdf` (per mistake #46 — always rename on any
content revision) and re-verified byte-level clean: empty Info dict,
zero XMP bytes, zero vector drawings, exactly one raster image on each
of the 3 figure pages, no filesystem paths or tool signatures in the
raw bytes, and none of the solution's computed values (hash, final
state, any checkpoint) present anywhere in the extracted text.
`platform/prompt.md` filename reference updated to match
(`cellguard10_v5.pdf`), word count re-confirmed at 454 (still under the
500 cap) and hyphen count still 0.

## Remaining

- This is the third round of fixes driven by local blind pilots, each
  one catching a real, confirmed bug rather than a false alarm. Decide
  next: proceed to a real platform pilot now, run a fourth local blind
  pilot, or harden further. Given three consecutive clean content
  solves, a fourth local pilot is unlikely to teach much more than
  "still not obviously broken" — the open question a local pilot
  structurally cannot answer is whether the six-rule interaction is
  hard enough for Opus-tier solving, only a real pilot can.
- Real pilot run(s), whichever path is chosen.

---

# STATIC10 (shelved before any rubric/platform work)

**SHELVED at the S08 gate**, before writing any rubric or platform text —
the cheapest possible point to catch this. Reference engine
(`reference/sta_engine.py`), independent verifier
(`reference/sta_verify.py`), and a 14-arc fixed circuit
(`reference/circuit.py`) were built and verified correct (engine output
matches an independent hand computation exactly; verifier correctly
accepts the true program and rejects both required adversarial
mutations). The score-topology audit then failed outright: all five
required single-bug mutants scored 40-66% against every reweighting
attempted, all far above the 33% target.

## Why this isn't a reweighting problem

Static timing analysis is, structurally, an **independent-facts** domain:
each register-to-register arc's classification and delay is a function of
that specific arc's own data (its gates, its constraint-file entry) and
nothing else. Synchronous digital design is deliberately built this way —
registers exist specifically to break combinational dependency chains
into independent per-stage analyses, so a wrong regime classification on
one arc has no natural channel to corrupt any other arc's value.

The certificate hash does detect every one of the five mutants
(`hash_match=False` in all cases) — the problem isn't sensitivity, it's
that a hash is capped at +10 like any other criterion (the platform's
own per-criterion limit, honored throughout this project), and no fair
reweighting can make +10 outweigh the 70-90 points of content a narrow,
single-regime bug honestly leaves untouched (13 of 14 arcs, both
aggregate selections, unrelated local-rule and memo criteria, two of
three verifier checks). Worked the algebra explicitly: clearing 33% for
the narrowest mutant (drop FALSE-path exclusion, corrupting exactly one
arc) would require either violating the ±10 cap or assigning that one
arc 15-20x the weight of every other arc — not a defensible rubric,
just hidden difficulty-manufacturing. Confirmed this is the same root
cause as LEDGER-8's original failure (independent facts), now caught at
the design stage instead of after a real pilot.

## What's being kept

`design/architecture-attack.md`, `design/semantic-contract.md`,
`reference/circuit.py`, `reference/sta_engine.py`,
`reference/sta_verify.py`, `reference/score_counterfactual.py` — all
correct and fully verified, kept as the historical record. Do not reuse
the "many independently-classified items, no state threading" shape for
a future task without first confirming genuine cross-item dependency
exists in the domain, the same check this file itself is evidence for.

## Replacement

Needs genuine temporal/state-threading cascading (QUORUM-7's proven
property), via a mechanism and domain that doesn't reskin QUORUM-7's
protocol/consensus shape. See the updated `design/architecture-attack.md`
addendum for the new direction.
