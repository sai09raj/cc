# R3 score topology and plausible-wrong survival audit (post-hardening)

Positive total **221** across 47 binary criteria; one **-8** negative trap. This is
the third revision of this document, after the Machine-Q maintenance freeze was
added to widen the boundary-timing attack surface beyond the single mechanism a
local blind-agent pilot found (`audit/blind-pilot-1.md`).

## Method: programmatic scoring, not hand arithmetic

Earlier rounds of this audit were computed by hand and repeatedly needed
correction (a design's headline selection ID was assumed unchanged without
checking; generous grants were applied inconsistently). This revision was computed
by `reference/score_counterfactual.py`, which runs each mutant's actual simulation
output against explicit, code-defined per-criterion pass/fail logic for every
objectively-checkable row (per-design values, per-design trace hashes, the four
named production witnesses) and takes an explicit, documented, per-mutant list of
which judgment-based rows (package/local/decision) also fail. Reproduce with
`python3 reference/score_counterfactual.py`.

## Why per-design value/reconciliation (16-27) and per-design hash (36-41) are at
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
| Package/presentation | 1-4 | 4 | Mostly yes — intentional; content is checked elsewhere |
| Local semantics/rules/scaffolding | 5-15 | 15 | Partially — rules a mutant's own code path still executes correctly pass; rules it structurally violates fail |
| Integrated per-design values + reconciliation | 16-27 | 117 | No, for any design whose execution actually diverges — this is the dominant bucket by design. (D4's reconciliation, criterion 26, is +7 rather than +10 — the other 3 moved to the standalone witness criterion 32 below, per the rubric-guidelines atomicity fix in `revision-delta.md`.) |
| Named production witnesses | 28-32 | 15 | Only for designs/mechanisms the mutant leaves genuinely intact. Each witness (including W3, criterion 32) is graded from the trace alone, independent of whether that design's overall numbers are also right — same as its four siblings always were. |
| Verifier independence + adversarial checks | 33-36 | 4 | Mostly yes — generous, structural; see explicit caveat on criterion 34 |
| Per-design trace-integrity hash | 37-42 | 60 | No, for any design whose full trace diverges anywhere — this is the second-largest bucket |
| Decision/causal reconciliation | 43-48 | 6 | Partially — kept deliberately low-weight; selection arithmetic on wrong-but-self-consistent numbers is fairly graded generously |
| **Total** | | **221** | |

## Executed counterfactuals (from `score_counterfactual.py`, current output)

| Mutant | What it gets wrong | Score |
|---|---|---:|
| Per-campaign reset (reverts to R2's architecture) | Everything about the continuous run | **7.7%** |
| Fault disabled | S07 only | **17.6%** |
| Oven pairing timer disabled | S06 only | **17.6%** |
| Machine-Q maintenance disabled | S13 entirely | **29.9%** |
| Machine-Q maintenance boundary convention only (copies S07's inclusive rule instead of S13's stated default) | One `>=` vs the wrong minute-alignment, nothing else | **31.2%** |
| All tie-breaks reversed (highest index wins, not lowest) | S03/S05/S06 tie-break direction only | **32.1%** |

## Honest limitation: three narrow single-mechanism mutants now sit at 29.9%,
## 31.2%, and 32.1% — two of them just above 30%

These numbers moved (from 28.5/29.9/30.8%) after a rubric-guidelines compliance
pass that split witness W3 out of criterion 26 into its own standalone criterion
32, matching how W1/W2/W4/W5 already worked (each graded from the trace alone,
not gated behind that design's overall correctness). That fix was required —
W3 had been bundled into D4's reconciliation criterion, which both violated the
atomicity rule (D4's bill and W3's presence are independently satisfiable/failable
facts) and, worse, duplicated W5's own dedicated criterion inside D1's
reconciliation row (the same fact charged twice). Both were real defects, not
stylistic ones, and fixing them was not optional. The side effect: a mutant that
still happens to produce *some* Q or P job with a cross-campaign setup-memory
signature — even while getting D4's own numbers wrong — now picks up 3 points for
witness 32 that used to be unreachable without D4 being exactly right. This moved
the tiebreak and maintenance-boundary mutants from just under 30% to just over it.

This is disclosed rather than hidden or reverted by re-bundling (re-bundling to
chase a target number would re-introduce the exact duplicate/atomicity defect the
guidelines flagged). Mitigating points:

1. **These are the narrowest, most adversarially-constructed single-bit mutants
   tested** — a real implementation attempt that gets exactly one boundary
   direction wrong while getting a dense 48-criterion specification's every other
   detail exactly right, including which of two conventions applies to which of two
   structurally-similar-looking mechanisms, is not the median failure mode. The
   local blind-pilot run that motivated this hardening round (`audit/blind-pilot-1.md`)
   made exactly this *class* of mistake once, not zero times and not twice, and it
   was found by inspecting the agent's code directly, not by construction. The
   second blind pilot (`audit/blind-pilot-2.md`), run cold against the hardened
   packet, scored 17.6% — nowhere near these adversarially-constructed margins.
2. **The realistic, broader failure modes remain far below both the 50% and the
   30% line** (7.7-17.6%), including reverting to R2's whole architecture and
   dropping either disruption mechanism entirely.
3. **Re-tuning weights specifically to force these two back under 30% was
   considered and rejected**, for the same reason logged in the prior round: any
   shared-criterion weight increase that helps one narrow mutant measurably hurts
   another (see the git history of `score_counterfactual.py`). Chasing a clean
   number by further reweighting, on top of an already-adversarial synthetic
   mutant, has diminishing honesty returns — the real gate is the target-model
   pilot, not this local diagnostic.

## Executed counterfactual C — correct engine, different valid organization

A solver producing the exact reference trace values, hashes, and witnesses but with
different file layout, variable names, formula notation, or physically-valid
tie-broken routes earns 221/221 (no criterion here enforces exact code structure,
filenames, or one specific route among equally valid ones).

## Conclusion

The hardening pass closed the gap the local blind pilot actually exploited
(criterion 15's boundary-convention requirement now exists and is worth real
weight) and drove every tested realistic wrong implementation below 20% —
confirmed for real by a second, independent local blind pilot at 17.6%
(`audit/blind-pilot-2.md`). Three narrow, hand-constructed single-mechanism
mutants remain in the 29.9-32.1% range, two of them just above the 30% target,
after a required rubric-guidelines compliance pass moved a witness criterion
that had been improperly bundled (see the limitation note above) into its own
standalone row. This is disclosed as a known limitation, not resolved by further
cosmetic reweighting — the next real signal is an actual Opus 4.8 Max platform
pilot.
