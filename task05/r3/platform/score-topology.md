# R3 score topology and plausible-wrong survival audit (post-hardening)

Positive total **222** across 49 binary criteria; one **-8** negative trap. This is
the fifth revision of this document: after the Machine-Q maintenance freeze was
added (round 2), after a rubric-guidelines duplicate/consistency fix split witness
W3 out of criterion 26 into its own row (round 3), after a full atomicity pass
split the oven-timer and Q-maintenance-boundary criteria and merged two redundant
package criteria (round 4), and now (round 5, R3c) after three real target-model
(Opus 4.8 Max) pilot transcripts scored 72%, 73%, and 99% — see
`revision-delta.md`'s R3b->R3c section for the full forensic finding: the two
lower-scoring runs' delivered simulators were proven **bit-exact identical** to
`reference/kilnworks_sim.py` (independently recomputed trace hash match, with no
access to our serialization algorithm), meaning this was a genuine task-difficulty
gap, not a scoring artifact. Round 4's own closing paragraph flagged this exact
risk in advance ("if Opus 4.8 Max produces a response that is correct on almost
everything... it could plausibly score in the low 30s") — the actual pilots
outpaced even that warning, landing at 72-99%, because the model didn't even need
the one-narrow-mistake failure mode: it got the mechanism fully right. Round 5's
fix hardens S13 (Machine-Q maintenance) from a one-time event to a **recurring**
interval, the smallest change consistent with "harden the task, not the rubric."

## Method: programmatic scoring, not hand arithmetic

Earlier rounds of this audit were computed by hand and repeatedly needed
correction (a design's headline selection ID was assumed unchanged without
checking; generous grants were applied inconsistently). This revision was computed
by `reference/score_counterfactual.py`, which runs each mutant's actual simulation
output against explicit, code-defined per-criterion pass/fail logic for every
objectively-checkable row (per-design values, per-design trace hashes, the five
named production witnesses) and takes an explicit, documented, per-mutant list of
which judgment-based rows (package/local/decision) also fail. Reproduce with
`python3 reference/score_counterfactual.py`.

## Why per-design value/reconciliation (17-28) and per-design hash (38-43) are at
## the legal +10 ceiling

Two earlier weight configurations were tried and rejected before this one:

1. **+2 per per-design criterion (total positive 65).** A mutant that disabled the
   node-4 fault or the oven pairing timer outright scored 27-30%: acceptable, but a
   mutant that got only the *boundary convention* of the new maintenance mechanism
   wrong (everything else correct) scored 50.4% — worse than the original 50%
   threshold this whole exercise exists to beat.
2. **+10 per per-design *value* criterion only, no per-design hash (total positive
   137-168 across attempts).** This closed the 50%+ gap but several single-mechanism
   mutants still landed at 31-39%: comfortably better than before, but not the
   <30% margin requested given the target model (Opus 4.8 Max) is materially
   stronger than the Sonnet-tier agent used for local blind testing.

Adding a **second, independent per-design proof** — a full-trace SHA-256 hash,
sensitive to any single divergent minute anywhere in that design's run, not just
its final summary — at the same +10 ceiling was the fix that mattered, because it
grows the bucket that every tested wrong implementation fails on, without growing
any bucket that a wrong implementation can pass "for free."

## Positive weight by bucket

| Bucket | Criteria | Weight | Can a wrong integrated engine earn it? |
|---|---|---:|---|
| Package/presentation | 1-3 | 4 | Mostly yes — intentional; content is checked elsewhere |
| Local semantics/rules/scaffolding | 4-16 | 16 | Partially — rules a mutant's own code path still executes correctly pass; rules it structurally violates fail. (Criteria 10/11 split the old bundled oven-timer row; 14/15/16 split the old bundled Q-maintenance-trigger-and-boundary rows — see the atomicity note below.) |
| Integrated per-design values + reconciliation | 17-28 | 117 | No, for any design whose execution actually diverges — this is the dominant bucket by design. (D4's reconciliation, criterion 27, is +7 rather than +10 — the other 3 moved to the standalone witness criterion 33 below.) |
| Named production witnesses | 29-33 | 15 | Only for designs/mechanisms the mutant leaves genuinely intact. Each witness (including W3, criterion 33) is graded from the trace alone, independent of whether that design's overall numbers are also right — same as its four siblings. |
| Verifier independence + adversarial checks | 34-37 | 4 | Mostly yes — generous, structural; see explicit caveat on criterion 35 |
| Per-design trace-integrity hash | 38-43 | 60 | No, for any design whose full trace diverges anywhere — this is the second-largest bucket |
| Decision/causal reconciliation | 44-49 | 6 | Partially — kept deliberately low-weight; selection arithmetic on wrong-but-self-consistent numbers is fairly graded generously |
| **Total** | | **222** | |

## Executed counterfactuals (from `score_counterfactual.py`, current output)

| Mutant | What it gets wrong | Score |
|---|---|---:|
| Per-campaign reset (reverts to R2's architecture) | Everything about the continuous run | **8.1%** |
| Fault disabled | S07 only | **18.0%** |
| Oven pairing timer disabled | S06 only | **18.0%** |
| All tie-breaks reversed (highest index wins, not lowest) | S03/S05/S06 tie-break direction only | **18.9%** |
| Machine-Q maintenance disabled | S13 entirely | **30.2%** |
| Machine-Q maintenance single-shot (fires once, doesn't recur) | Exactly the "reverted to R3b's old behavior" regression — R3c's real target failure mode | **30.2%** |
| Machine-Q maintenance boundary convention only (copies S07's inclusive rule instead of S13's stated default) | One `>=` vs the wrong minute-alignment, nothing else | **31.5%** |

`MAINT_THRESHOLD` was lowered from 12 to 10 specifically to fix the single-shot
regression's score: at 12, three of six designs' recurrence was causally inert
(each happened to cross the threshold only on its very last Q job), so a mutant
that quietly reverted to one-time behavior still scored 57.2% — above the <50%
target and the whole reason this hardening round exists. At 10, five of six
designs genuinely exercise the recurrence and the same mutant drops to 30.2%,
in line with every other single-mechanism mutant.

## Honest limitation: the narrowest single-mechanism mutants still sit above 30%
## (30.2%, 30.2%, 31.5%)

This moved again — every round of atomicity fixes moves these three numbers up a
little, and this revision is no exception. The pattern is structural, not a bug to
keep chasing: **splitting a bundled criterion into atomic pieces, which the rubric
guidelines require, mechanically increases how much partial credit a narrow mutant
can recover**, because a mutant that breaks only one of several now-separate facts
loses only that fact's weight instead of the whole bundle's. This round split the
oven-timer criterion (old 11) into partner-matching (new 10) and deadline-timing
(new 11), and the Q-maintenance-boundary criterion (old 15) into
trigger-minute-unaffected (new 15) and the 13-minute-window fact (new 16) — both
real, required fixes (a response genuinely can get one half right and the other
wrong, which is exactly the guidelines' test for when a row must split). The
`tiebreak high` mutant, for example, no longer loses credit for oven
deadline-timing (new 11) at all, because that specific mutant's tie-break bug
never actually touches deadline arithmetic — the old bundled criterion 11 was
overcharging it before, not correctly scoring it.

This is disclosed rather than hidden or reverted by re-bundling (re-bundling to
chase a lower number would reintroduce the exact atomicity defects the guidelines
flagged, and was rejected for that reason in the prior round too). Mitigating
points, unchanged in substance from the prior revision:

1. **These are the narrowest, most adversarially-constructed single-bit mutants
   tested** — a real implementation attempt that gets exactly one boundary
   direction wrong while getting a dense 50-criterion specification's every other
   detail exactly right, including which of two conventions applies to which of two
   structurally-similar-looking mechanisms, is not the median failure mode. The
   local blind-pilot run that motivated the original hardening round
   (`audit/blind-pilot-1.md`) made exactly this *class* of mistake once, not zero
   times and not twice, and it was found by inspecting the agent's code directly,
   not by construction. The second blind pilot (`audit/blind-pilot-2.md`), run cold
   against the hardened packet, scored 17.6% (now 18.0% under the current weights)
   — nowhere near these adversarially-constructed margins.
2. **The realistic, broader failure modes remain far below both the 50% and the
   30% line** (8.1-18.0%), including reverting to R2's whole architecture and
   dropping either disruption mechanism entirely.
3. **Re-tuning weights specifically to force these three back under 30% was
   considered and rejected again**, for the same structural reason logged in prior
   rounds: any shared-criterion weight increase that helps one narrow mutant
   measurably hurts another (see the git history of `score_counterfactual.py`).
   Chasing a clean number by further reweighting, on top of an already-adversarial
   synthetic mutant, has diminishing honesty returns, and actively fights against
   the atomicity fix this revision exists to make — the real gate is the
   target-model pilot, not this local diagnostic.

**What actually happened when this went to a target-model pilot**: this section
previously predicted that a response correct on almost everything, wrong on
exactly one narrow boundary/tie-break rule, "could plausibly score in the low
30s." Three real Opus 4.8 Max pilots outpaced that warning entirely — two of them
were not "almost everything," they were **bit-exact correct**, proven by
independently recomputing the canonical trace hash from their own delivered code
and matching ours exactly, and scored 72-73%; the third scored 99%. The
speculative "one narrow mistake" scenario this document worried about did not
occur; the model simply solved the mechanism. That is the actual finding this
revision (R3c) responds to — see `revision-delta.md`. The remaining
30.2/30.2/31.5% single-mechanism-mutant scores above are a different, narrower,
still-honest concern (an adversarially-constructed one-bug mutant, not a real
pilot result) and are disclosed as such below, not conflated with the pilot
finding.

## Executed counterfactual C — correct engine, different valid organization

A solver producing the exact reference trace values, hashes, and witnesses but with
different file layout, variable names, formula notation, or physically-valid
tie-broken routes earns 222/222 (no criterion here enforces exact code structure,
filenames, or one specific route among equally valid ones).

## Conclusion

Round 4's atomicity pass brought the rubric into compliance with the official
rubric guidelines but, as its own closing paragraph anticipated, left real margin
for a target model that gets the mechanism substantively right. Three real Opus
4.8 Max pilots confirmed this directly: two delivered bit-exact-correct
simulators (72%, 73%), one scored 99%. Round 5 (R3c) responds with the smallest
change consistent with "harden the task, not the rubric": S13 (Machine-Q
maintenance) is now a recurring interval instead of a one-time event, with the
threshold tuned (12->10) so the recurrence is causally load-bearing in 5 of 6
designs rather than inert in half of them. This closes the exact regression this
round exists to catch (a "reverted to one-shot" implementation, previously scoring
57.2%, now scores 30.2% — in line with every other single-mechanism mutant) without
touching rubric weights, criterion count, goldens' overall shape, or any mechanism
outside S13. It does not, and cannot, guarantee the next target-model pilot scores
under 50% — that determination requires an actual fresh pilot against the
hardened `kw-r3c.pdf`, not another local proxy. The three narrow, hand-constructed
single-mechanism mutants sitting at 30.2-31.5% remain a disclosed, structural,
unresolved limitation (see above); they are a different, more adversarial question
than what the actual pilots exercised.
