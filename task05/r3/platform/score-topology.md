# R3 score topology and plausible-wrong survival audit

Positive total **61** across 38 binary criteria; one **-8** negative trap. This is
the second revision of this document. The first draft (positive 57, per-design
criteria at +1 each) let counterfactual B2 in at 46.9% but counterfactual B1 at
51.0% — failing the requirement that *both* named counterfactuals stay under 50%
(`Playbook/03-RUBRIC-AND-LINTER-GUIDE.md`, score-topology section). Three criteria
(30, 33, 34, 36) were reweighted down and criterion 26 was tightened in the first
revision; that alone fixed B2 but not B1. The fix applied here is different in kind:
criteria 14-25 (the twelve per-design value/reconciliation checks, which **no**
counterfactual below ever earns) were raised from +1 to +2 each, growing the
denominator without growing either counterfactual's numerator. No pilot has been
run; this is a pre-launch audit.

| Positive category | Criteria | Weight | Can a wrong integrated engine earn it? |
|---|---|---:|---|
| Package/presentation | 1-4 | 4 | Mostly yes — this is intentional; content is checked elsewhere |
| Local semantics/rules/scaffolding | 5-13 | 11 | Partially — rules a mutant's own code path still executes correctly pass; rules it structurally violates (continuous-run scope, persistent memory, single-fire fault) fail |
| Integrated production execution — per-design values | 14-25 | 24 | No — every counterfactual below fails all twelve; this is the single largest bucket by design |
| Integrated production execution — witnesses/verification/feasibility | 26-32 | 16 | Mostly no for a genuinely wrong engine |
| Decision/causal reconciliation | 33-38 | 6 | Partially — kept deliberately low-weight since selection arithmetic on wrong-but-self-consistent numbers is fair to grant generously |
| **Total** | | **61** | |

## Counterfactual A — empty/superficial package

No simulator executed, no values reported. Earns 0/49 (criteria 1-2 require an
executed command and accessible products with content; an empty submission has
neither).

## Counterfactual B1 — perfect local semantics, incomplete/wrong global execution

Grant every local-rule criterion (5-13) and every package criterion (1-4), but deny
every per-design value (14-25) and every temporal-composition witness (26-28); grant
the criteria that survive under a generous "don't recharge an already-counted error"
reading (29, 31, 32, 33, 34, 35, 36, 37, 38): `4 + 11 + (29:2+31:1+32:1) +
(33:1+34:1+35:1+36:1+37:1+38:1) = 4+11+4+6 = 25/61 = 41.0%`.

This is a hypothetical grant of "perfect local semantics" that a real wrong
implementation is unlikely to fully achieve simultaneously with wrong global
execution; B2 below is the executed, evidence-backed instance.

## Counterfactual B2 — actual runnable, locally-plausible, globally-wrong engine

`reference/mutant_per_campaign_reset.py` treats the four campaigns as four
independent per-campaign resets (R2's old architecture) instead of one continuous,
overlapping, state-persisting run. It is a real, executed, plausible mistake — not
an invented worst case.

Counted against the frozen rubric:

| Bucket | Earned | Of | Notes |
|---|---:|---:|---|
| Package (1-4) | 3 | 4 | Fails criterion 3 (not a continuous per-design trace) |
| Local (5-13) | 6 | 11 | Fails 6 (release resets per campaign), 8 (setup memory resets), 9 (no single continuous run to bound), 13 (fault fires up to 4x, not once) |
| Per-design values (14-25) | 0 | 24 | All six `(makespan, bill)` pairs wrong, at double weight |
| Witnesses/verify/feasibility (26-32) | 7 | 16 | Fails 26 (fault witness must come from the required continuous trace), 27 (no interleaving possible), 28 (no mixed-campaign batch possible); passes 29 (+2, separately-coded verifier exists) and 30 (+3, a self-consistent same-bug verifier still agrees with the primary -- this is why 30 is capped at 3, not the 6 a naive reading would suggest), and 31/32 (+1 each, structural mutation rejection still works) |
| Decision (33-38) | 4 | 6 | Passes 33/34/35 (its own selection arithmetic is internally consistent, generously graded per the "don't recharge upstream error" rule) and 37 (generic distance-relaxation explanation); fails 36 under a reading tightened to require the specific fault/fixture-ceiling interaction actually present in *this* mutant's own (wrong) trace, and fails 38 (a solver that actually believes per-campaign reset is correct would not write the required explanation of why it is wrong) |
| **Total** | **20** | **61** | **32.8%** |

`20/61 = 32.8%`, comfortably below the 50% threshold. This is the binding, executed
counterfactual.

Note: this mutant happens to recover the correct headline design **IDs** (`D5`
unrestricted, `D1` under `capital<=9`) while its own selection keys are wrong
(`D5` at `(177,1291,22,D5)` vs the true `(142,1356,22,D5)`; `D1` at
`(194,1191,7,D1)` vs the true `(165,1315,7,D1)`) — exactly the Task 04 Revision E
trap. Criteria 33/34 were deliberately kept at low weight (+1 each, not +3) so this
coincidence cannot materially inflate the score; the per-design value criteria
14-25, which this mutant fails completely, carry far more weight than the ID-only
selection criteria.

## Counterfactual C — correct engine, different valid organization

A solver producing the exact reference trace values but with different file layout,
variable names, formula notation, or physically-valid tie-broken routes earns 61/61
(no criterion here enforces exact code structure, filenames, or one specific route
among equally valid ones).

## Other tested mutants (not separately scored)

`mutant_disable_fault`, `mutant_oven_no_timer`, and `mutant_tiebreak_high`
(`audit/mutation-results.md`) each change all 6 designs' `(makespan, bill)` pairs
and additionally fail criterion 13 (fault) or 11 (oven timer) or introduce further
witness failures beyond what B2 fails. None was hand-scored line-by-line, but none
plausibly exceeds B2's 32.8% ceiling: each fails the same 24-point per-design bucket
B2 fails, while failing at least as many local/witness criteria as B2 (each corrupts
a *different* single mechanism rather than reverting the whole architecture, so none
retains B2's partial credit on the mechanisms it leaves untouched).

## Conclusion

The frozen rubric's plausible-wrong survival ceiling is below 50% for every executed
counterfactual. This clears the pre-pilot gate; it is not itself evidence of
frontier-model difficulty (see `design/architecture-attack.md`'s perfect-semantics
ablation and the caveat in `audit/independent-reconstruction.md`).
