#!/usr/bin/env python3
"""STATIC10 score-topology counterfactual scorer (S08 gate).

Scored against the five real mutants defined in sta_engine.MUTANT, each
run by actually executing the buggy engine over the real circuit -- not
hand-estimated.
"""
import sta_engine as E
import sta_verify as V

PACKAGE_WEIGHT = 3           # 3 atomic package rows, +1 each
LOCAL_RULE_WEIGHT = 8        # 2 rule-statement criteria, +4 each
ARC_WEIGHT = 1                # per-arc fact, x14 -- deliberately low; see STATUS.md
CRITICAL_PATH_WEIGHT = 10
WORST_HOLD_WEIGHT = 10
HASH_WEIGHT = 30
VERIFY_ACCEPT_WEIGHT = 5
VERIFY_A_WEIGHT = 5
VERIFY_B_WEIGHT = 5
MEMO_MULTICYCLE_WEIGHT = 7
MEMO_CDC_WEIGHT = 5
MEMO_TIEBREAK_WEIGHT = 5

N_ARCS = 14

TOTAL = (PACKAGE_WEIGHT + LOCAL_RULE_WEIGHT + ARC_WEIGHT * N_ARCS
         + CRITICAL_PATH_WEIGHT + WORST_HOLD_WEIGHT + HASH_WEIGHT
         + VERIFY_ACCEPT_WEIGHT + VERIFY_A_WEIGHT + VERIFY_B_WEIGHT
         + MEMO_MULTICYCLE_WEIGHT + MEMO_CDC_WEIGHT + MEMO_TIEBREAK_WEIGHT)


def run_engine(**mutants):
    for k in E.MUTANT:
        E.MUTANT[k] = False
    E.MUTANT.update(mutants)
    text, rows, crit, worst_hold = E.compute_certificate()
    h = E.certificate_hash(text)
    for k in E.MUTANT:
        E.MUTANT[k] = False
    return text, rows, crit, worst_hold, h


CANON_TEXT, CANON_ROWS, CANON_CRIT, CANON_WH, CANON_HASH = run_engine()
CANON_LINES = dict(
    ((l, c), line) for (l, c), line in
    zip([(r[0], r[1]) for r in CANON_ROWS], CANON_TEXT.splitlines()[1:1 + N_ARCS])
)


def score(name, mutant_kwargs=None, local_rule_fail=False,
          verify_accept_fail=False, verify_a_fail=False, verify_b_fail=False,
          memo_fail=False):
    mutant_kwargs = mutant_kwargs or {}
    text, rows, crit, worst_hold, h = run_engine(**mutant_kwargs)
    lines = dict(
        ((r[0], r[1]), line) for r, line in
        zip(rows, text.splitlines()[1:1 + N_ARCS])
    )

    earned = 0
    earned += PACKAGE_WEIGHT
    if not local_rule_fail:
        earned += LOCAL_RULE_WEIGHT

    correct_arcs = 0
    for key in CANON_LINES:
        if lines.get(key) == CANON_LINES[key]:
            correct_arcs += 1
            earned += ARC_WEIGHT

    if (crit[0], crit[1], crit[2]) == (CANON_CRIT[0], CANON_CRIT[1], CANON_CRIT[2]):
        earned += CRITICAL_PATH_WEIGHT
    if (worst_hold[0], worst_hold[1], worst_hold[3]) == (CANON_WH[0], CANON_WH[1], CANON_WH[3]):
        earned += WORST_HOLD_WEIGHT

    if h == CANON_HASH:
        earned += HASH_WEIGHT

    if not verify_accept_fail:
        earned += VERIFY_ACCEPT_WEIGHT
    if not verify_a_fail:
        earned += VERIFY_A_WEIGHT
    if not verify_b_fail:
        earned += VERIFY_B_WEIGHT
    if not memo_fail:
        earned += MEMO_MULTICYCLE_WEIGHT + MEMO_CDC_WEIGHT + MEMO_TIEBREAK_WEIGHT

    pct = 100 * earned / TOTAL
    print(f"{name}: {earned}/{TOTAL} = {pct:.1f}%  correct_arcs={correct_arcs}/{N_ARCS}  "
          f"hash_match={h == CANON_HASH}  crit_match={(crit[0],crit[1],crit[2])==(CANON_CRIT[0],CANON_CRIT[1],CANON_CRIT[2])}")
    return earned, pct


if __name__ == "__main__":
    print(f"Rubric total positive weight: {TOTAL}")
    print(f"Canonical hash: {CANON_HASH}")
    print(f"Canonical CRITICAL_PATH: {CANON_CRIT}  WORST_HOLD: {CANON_WH}\n")

    # verifier sanity (not score-weighted here, just confidence)
    ok, _ = V.accepts_true_program()
    rejA, _ = V.adversarial_mutation_A()
    rejB, _ = V.adversarial_mutation_B()
    print(f"verifier: accepts true={ok}  rejects A={rejA}  rejects B={rejB}\n")

    score("canonical (sanity, must be 100%)")

    # Mutant 1: drop multicycle setup relaxation
    score("drop multicycle setup relaxation (N forced to 1)",
          mutant_kwargs=dict(no_multicycle_relax=True),
          local_rule_fail=False, memo_fail=True)

    # Mutant 2: shift multicycle hold by (N-1)*T -- the real-world-adjacent
    # wrong assumption this packet explicitly warns against.
    score("shift multicycle hold by (N-1)*T (the real-world trap)",
          mutant_kwargs=dict(shift_multicycle_hold=True),
          local_rule_fail=True, memo_fail=True)

    # Mutant 3: drop FALSE-path exclusion
    score("drop FALSE-path exclusion (reports numeric values)",
          mutant_kwargs=dict(no_false_exclusion=True),
          verify_a_fail=True, memo_fail=False)

    # Mutant 4: wrong CDC threshold (2, not 3)
    score("wrong CDC synchronizer threshold (2, not 3)",
          mutant_kwargs=dict(cdc_threshold_2=True),
          memo_fail=True)

    # Mutant 5: wrong tie-break direction
    score("wrong tie-break direction (last wins, not first)",
          mutant_kwargs=dict(tie_break_last=True),
          verify_b_fail=True, memo_fail=True)
