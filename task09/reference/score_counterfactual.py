#!/usr/bin/env python3
"""TYPECHAIN-9 score-topology counterfactual scorer (S08 gate).

Per-binding certificate correctness (27 bindings) carries most of the
weight, mirroring this project's established pattern, plus package/
memo/grand-total/adversarial-verification criteria. Scored against the
one confirmed real mutant (no_env_exclusion / S10 mutation B) by
actually running the buggy engine over the real program and the
independent checker over its (possibly-corrupted) output -- not
hand-estimated.
"""
import typecheck_engine as E
import checker as C

TEXT = open("program.ty").read()
BINDINGS = E.parse_program(TEXT)

PACKAGE_WEIGHT = 3
LOCAL_RULE_WEIGHT = 10   # S02's stated generalization rule, as a single mechanism criterion
GRAND_HASH_WEIGHT = 10
VERIFY_A_WEIGHT = 6      # independent checker rejects mutation A (occurs-check)
VERIFY_B_WEIGHT = 6      # independent checker rejects mutation B (over-generalization)
MEMO_WEIGHT = 6

# Per-binding weight: 27 bindings, each worth a flat 3 points (one
# binding -- RetainedEarnings-equivalent severity isn't meaningfully
# differentiable here the way LEDGER-8's dollar magnitudes were, so
# flat weight per fact is the honest choice, not reverse-engineered).
BINDING_WEIGHT = 3

TOTAL = (PACKAGE_WEIGHT + LOCAL_RULE_WEIGHT + GRAND_HASH_WEIGHT
         + VERIFY_A_WEIGHT + VERIFY_B_WEIGHT + MEMO_WEIGHT
         + BINDING_WEIGHT * len(BINDINGS))


def to_checker_type(t, varmap):
    if isinstance(t, E.TVar):
        if t.name not in varmap:
            varmap[t.name] = C.MVar()
        return varmap[t.name]
    if isinstance(t, E.TCon):
        return C.IINT if t.name == "Int" else C.IBOOL
    if isinstance(t, E.TArrow):
        return C.Arrow(to_checker_type(t.a, varmap), to_checker_type(t.b, varmap))
    if isinstance(t, E.TPair):
        return C.Pair(to_checker_type(t.a, varmap), to_checker_type(t.b, varmap))
    if isinstance(t, E.TList):
        return C.Lst(to_checker_type(t.a, varmap))
    raise TypeError(t)


def results_to_claimed(results):
    claimed = {}
    for name, quant, t, generalized in results:
        varmap = {}
        template = to_checker_type(t, varmap)
        quant_mvars = [varmap[v.name] for v in quant]
        claimed[name] = (quant_mvars, template)
    return claimed


def run_engine(**mutants):
    for k in E.MUTANT:
        E.MUTANT[k] = False
    E.MUTANT.update(mutants)
    results = E.infer_program(BINDINGS)
    for k in E.MUTANT:
        E.MUTANT[k] = False
    return results


CANONICAL_RESULTS = run_engine()
CANONICAL_LINES = dict(l.split("=", 1) for l in
                        E.canonical_serialization(CANONICAL_RESULTS).splitlines()[1:])
CANONICAL_HASH = E.certificate_hash(CANONICAL_RESULTS)


def score(name, mutant_kwargs=None, local_rule_fail=False, hash_ok=True,
          verify_a_fail=False, verify_b_fail=False, memo_fail=False):
    mutant_kwargs = mutant_kwargs or {}
    results = run_engine(**mutant_kwargs)
    lines = dict(l.split("=", 1) for l in
                 E.canonical_serialization(results).splitlines()[1:])
    h = E.certificate_hash(results)

    earned = 0
    earned += PACKAGE_WEIGHT
    if not local_rule_fail:
        earned += LOCAL_RULE_WEIGHT

    correct_bindings = 0
    for bname in CANONICAL_LINES:
        if lines.get(bname) == CANONICAL_LINES[bname]:
            correct_bindings += 1
            earned += BINDING_WEIGHT

    if hash_ok and h == CANONICAL_HASH:
        earned += GRAND_HASH_WEIGHT

    if not verify_a_fail:
        earned += VERIFY_A_WEIGHT
    if not verify_b_fail:
        earned += VERIFY_B_WEIGHT
    if not memo_fail:
        earned += MEMO_WEIGHT

    pct = 100 * earned / TOTAL
    print(f"{name}: {earned}/{TOTAL} = {pct:.1f}%  "
          f"correct_bindings={correct_bindings}/{len(CANONICAL_LINES)}  hash_match={h == CANONICAL_HASH}")
    return earned, pct


if __name__ == "__main__":
    print(f"Rubric total positive weight: {TOTAL}")
    print(f"Canonical hash: {CANONICAL_HASH}\n")

    score("canonical (sanity, must be 100%)")

    # S10 mutation B as a score-topology mutant: a plausible wrong
    # engine implementation (omits the generalization-exclusion rule
    # everywhere). hash_ok=False since the corrupted certificate can
    # never coincidentally match; verify_b_fail=True since a submission
    # that made this exact engine bug would almost certainly also fail
    # to implement the over-generalization check correctly in its own
    # checker (the same misunderstanding of S02 drives both).
    score("no generalization-exclusion (S02 rule dropped, S10 mutation B)",
          mutant_kwargs=dict(no_env_exclusion=True),
          local_rule_fail=True, hash_ok=False, verify_b_fail=True, memo_fail=True)

    # A second, independent plausible-wrong scenario: drops only the
    # alias-eligibility clause of S02 (the model implements the lambda
    # case right but misses the "bare alias of a polymorphic binding"
    # case). Weaker cascade on this specific program (confirmed via
    # execution, not assumed) but still a real, distinct rule violation.
    score("no alias-eligibility clause (S02 rule partially dropped)",
          mutant_kwargs=dict(no_alias_eligibility=True),
          local_rule_fail=True, hash_ok=False, memo_fail=True)
