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

## Round 4: fourth local blind pilot, run on a different (stronger) model

User asked to run the next local blind pilot specifically on "Opus 4.8
Max," the real platform's target model. That exact model/deployment
name is not invocable from this environment — the `Agent` tool's model
override only accepts generic aliases (`sonnet`/`opus`/`haiku`/`fable`)
that resolve to whatever this harness currently defaults to, which does
not verifiably match the platform's Opus 4.8 Max. Surfaced this
mismatch explicitly rather than silently substituting and reporting it
as a match; user chose to run with the `opus` alias anyway, as the
closest available stand-in, understood as informative but not a
verified same-model comparison.

Result: another clean solve, and the strongest one yet. Hash, all
checkpoints, all events, final state, and all three verifier results
matched exactly. More notably, its independent verifier used **exact
rational arithmetic** (not floating point) specifically to rule out
rounding/threshold ambiguity, and it cross-checked that choice against
a floating-point implementation across all 320 ticks before trusting
either — a more rigorous validation approach than any of the three
Sonnet-tier pilots used. This is the **fourth consecutive clean
content solve** (three Sonnet, one Opus-alias) — the pattern is now a
clear yellow flag on its own terms regardless of model tier, though
still not proof a real Opus 4.8 Max pilot will also solve it cleanly.

**Findings — three new, confirmed packet-correctness bugs**, none
previously caught by any of the three Sonnet-tier pilots:

1. **Figure 2's own diagram image still had the stale, false claim**
   ("...which cell leads can change over the run") that round 3 had
   already corrected in the surrounding prose (S03c.8 and SPEC_TEXT
   section 4) but not in `make_packet.py`'s `diagram_rules()` function
   — a separate code path building the rendered image shown in Figure
   2. Root cause: my round-3 grep search found this file as a match (3
   files total) but I only viewed and fixed one specific line range
   inside it, rather than checking the whole file for every
   occurrence — an incomplete-fix process bug on my part, not a new
   content bug. Also removed a leftover draft artifact in the same
   diagram text, "(per cell, the new rule)," which has no business
   being in a frozen packet. Re-grepped the entire `task10/` tree
   afterward with broader patterns (`can change`, `leads can`,
   `lead can`, `no guarantee which cell`, `the new rule`) to confirm no
   further occurrences survive in any platform- or solver-facing file.
   Also corrected one occurrence in `design/semantic-contract-cellguard.md`'s
   S08 rationale section ("no guarantee which cell leads at any given
   point") that was similarly missed in round 3 because it wasn't
   literally the S03c.8 clarification text itself, just referencing it
   inaccurately.

2. **TAPER heat rule's "always" was genuinely ambiguous against the
   fault-latch zero-heat rule.** SPEC_TEXT section 5 stated the
   zero-current/zero-heat rule (fault latched → no heat) in one
   sentence, then a separate sentence claiming TAPER mode "always
   generates HEAT_TAPER, regardless of... DERATE_TEMP" — read as two
   independent facts rather than an explicit precedence order, a
   reader could reasonably conclude TAPER's "always" overrides even the
   zero-current case during a fault-latched TAPER tick. It doesn't:
   confirmed via the reference engine (`bms_engine.py` lines 98-101)
   that the zero-current check runs first, unconditionally, before the
   TAPER check. The pilot found this by testing the alternate reading
   explicitly and discovering it changes the hash entirely — a genuine,
   not hypothetical, scoring-affecting ambiguity (same risk class as
   mistake #69: a packet's own wording can be read two structurally
   different ways with no textual signal for which is intended).
   Figure 2's diagram text already had unambiguous explicit ordering
   ("0 if base=0. Else, in TAPER mode...") and needed no change; fixed
   SPEC_TEXT section 5 to make the same precedence explicit in prose,
   stating directly that the zero-current rule is evaluated first and
   takes priority over every mode-specific heat rule including TAPER's.

3. **CV-decay-on-the-transition-tick was only inferable, not stated.**
   Whether the regulation current decays on the very tick CC→CV fires
   (as opposed to starting decay only from the following tick) followed
   only from tracing Figure 2's step 2/step 3 ordering (mode is already
   CV by step 2, so step 3's "in CV mode, after step 2" decay applies
   that same tick) — confirmed correct against the reference engine
   (`bms_engine.py` lines 70-73), but the SPEC_TEXT prose never said so
   directly; the pilot got it right but flagged it as "only implied."
   Added one explicit sentence to SPEC_TEXT section 2 stating plainly
   that decay begins on the transition tick itself, with no grace tick.

**One additional hardening, not a correctness bug:** the pilot also
flagged that Figure 2's rendered diagram had two rules' text visually
overlapping (step 6's longer block running into step 7's text) — a
legibility defect from the original rendering code using a fixed
per-step vertical decrement (`y -= 0.088`) regardless of how many lines
each step's text actually occupied. Rewrote `diagram_rules()` to
measure each step's actual rendered height via matplotlib's renderer
and advance by exactly that height plus a fixed gap, which eliminates
overlap regardless of future text-length changes to any step. Rebuilt
Figure 2 and visually confirmed (rendered to PNG, read back) that all
11 steps are now fully legible with no overlap.

**Also strengthened, pre-emptively, two things the pilot raised as
risk** rather than confirmed bugs: (a) Figure 3's fake worked example
used numbers that quietly violate this packet's own formulas (an
impossible CC current of 50.00 under the 45 clamp, a voltage that
doesn't follow from its own stated SoC) — already labeled "fake," and
the pilot correctly treated it as format-only and was not actually
misled, but strengthened the disclaimer to state explicitly and
up-front that the fake numbers deliberately do not satisfy the
packet's formulas and must never be used to validate an
implementation's logic. (b) Figure 3's two-line visual wrap of each
certificate record (an artifact of fitting the figure to page width)
could be misread as part of the actual format; the existing "one line
per tick" rule already resolved this correctly for every pilot so far,
but added an explicit parenthetical stating the wrap is a display-only
artifact of the figure and the real certificate has no line break
there.

No engine, constant, or computed value changed in any of this — all
fixes are prose/diagram-rendering only. Re-ran `bms_verify.py` and
`score_counterfactual.py`: canonical hash, all 8 checkpoints, all 4
events, and all 6 mutant scores are byte-identical to every prior
round. Artifact rebuilt as `cellguard10_v6.pdf` and re-verified
byte-level clean (empty metadata, zero XMP, zero vector drawings, one
raster image per figure page, no path/tool signatures, no leaked
solution values — including checked specifically for the *alternate*
hashes the ambiguous readings above would have produced, to make sure
none of them leaked into the packet either). `platform/prompt.md`
filename reference updated to `cellguard10_v6.pdf`, word count
re-confirmed 454/500, hyphen count still 0.

## Round 5: user-run pilot, reported as the platform's actual Opus 4.8 Max

User ran the frozen `prompt.md` + `cellguard10_v6.pdf` packet themselves,
outside this session, against the model they identified as the
platform's actual target ("Opus 4.8 Max") — not the generic `opus`
alias this session can invoke. This closes the model-identity gap round
4 flagged: unlike every prior round, this one is reported to be the
real target model, not a stand-in.

Graded the full submitted deliverable bundle (uploaded as a zip:
engine source, independent verifier source, full certificate, full-
precision CSV, findings report, certification evidence doc, engineering
memo, README, and raw execution transcripts) against all 32 rubric
criteria with the same rigor as round 4 — not just the pasted summary
text initially shared. Verified independently, not taken on trust:

- Diffed the submitted `cellguard_certificate.txt` against a freshly
  generated canonical trace — byte-identical, all 320 lines.
- Read the submitted engine and verifier source in full. The engine's
  rule 7 (heat) comment explicitly states the zero-current-first,
  TAPER-ignores-temperature precedence — the exact ambiguity round 4's
  fix resolved, read and implemented correctly. The verifier is a
  genuinely from-scratch re-implementation (no import of the engine;
  confirmed by reading the full file), with both adversarial mutations
  built from the verifier's own independent replay logic, not reused
  from the engine's mutation hooks.
- Cross-checked the two adversarial-mutation divergence points (t=204
  for early fault release, t=21 for uniform current) against canonical
  — both exact.

**Score: 121/122 (99.2%)** — identical to round 4's opus-alias score,
and missing the exact same single criterion (package criterion 3, tool
version). Every local rule, all 8 checkpoints, all 4 events, final
state, hash, all 3 verifier criteria, and all 4 memo criteria confirmed
correct by direct inspection of the actual files, not just the
submitted summary.

**That both independently-run pilots missed the identical criterion
led to finding a real bug in this packet, not a solving gap**: grepped
`prompt.md`, `ideal-flow.md`, and the PDF's `SPEC_TEXT` for any mention
of recording a tool/runtime version or declaring an offline,
dependency-free environment, and found none. Criterion 3 ("Records the
language/runtime tool version used, in a declared offline,
dependency-free (stdlib-only) execution environment") was scoring
solvers down for something the packet never asked them to do — a
rubric/prompt mismatch, the same class of unfairness this project has
flagged before (the "Rubric Prohibition Criteria Check" pattern from
earlier tasks). Neither solver could plausibly have known to record
this. Fixed by adding an explicit instruction to both `prompt.md`
("record the exact language and runtime version you used, in a
declared offline, dependency free execution environment") and
`ideal-flow.md`'s Execute & Generate section, matching language.
`prompt.md` re-confirmed at 472/500 words, 0 hyphens. No PDF rebuild
needed (the artifact never discussed tool versioning; this was prompt-
only), no engine/value change, so no re-run of the S08 audit was
needed either.

**Net effect of this round**: with the packaging bug fixed, the
real-target-model pilot's result is effectively a clean, near-perfect
solve (121/122, and the 1-point miss was never a fair test to begin
with — correcting for it, this is functionally 122/122). Combined with
four prior clean local solves, this is the strongest and most direct
evidence yet that this content, as currently hardened, is not clearing
the real-pilot difficulty bar — not a proxy signal anymore, but
(reportedly) the actual target model solving it cleanly end to end,
including correctly resolving an ambiguity fix made only one round
earlier.

## Remaining

- **Recommendation: do not spend a real platform pilot slot on this
  content as currently hardened.** Five consecutive clean solves (four
  local, one reported as the real target model via an uploaded,
  independently-graded bundle) is no longer a yellow flag — if the
  model-identity claim is accurate, it's a direct result. Spending a
  real pilot now would very likely reproduce TYPECHAIN-9's 99%/100%
  outcome, for the same underlying reason mistake #67 and #68 already
  named: six genuinely-interacting rules is necessary but has not
  proven sufficient on its own against a model of this strength.
- Next real decision: harden substantially further (a seventh
  interacting rule, or a mechanism change deep enough to not just be
  "more of the same six"), or treat task10 as heading toward the same
  shelve-and-pivot outcome as STATIC10 and TYPECHAIN-9, documented
  honestly rather than forcing a pilot spend to confirm what five
  solves already indicate.
- If a real pilot is still run despite this, treat any score at or
  above ~50% as expected, not surprising, given this evidence — not as
  new information requiring a fresh root-cause investigation.

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
