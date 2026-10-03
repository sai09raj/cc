#!/usr/bin/env python3
"""CELLGUARD-10 score-topology counterfactual scorer (S08 gate)."""
import bms_engine as E
import bms_verify as V

PACKAGE_WEIGHT = 3           # 3 atomic rows, +1 each
LOCAL_RULE_WEIGHT = 20       # 4 rule-statement criteria, +5 each
CHECKPOINT_WEIGHT = 5        # per checkpoint snapshot (unitary 6-field record), x7
EVENT_WEIGHT = 2             # per transition/event tick, x4
FINAL_STATE_WEIGHT = 6
HASH_WEIGHT = 10
VERIFY_ACCEPT_WEIGHT = 5
VERIFY_A_WEIGHT = 5
VERIFY_B_WEIGHT = 5
MEMO_WEIGHT_EACH = 5         # x3

CHECKPOINT_TICKS = [161, 175, 206, 230, 250, 280, 300, 315]
N_CHECKPOINTS = len(CHECKPOINT_TICKS)
N_EVENTS = 4

TOTAL = (PACKAGE_WEIGHT + LOCAL_RULE_WEIGHT + CHECKPOINT_WEIGHT * N_CHECKPOINTS
          + EVENT_WEIGHT * N_EVENTS + FINAL_STATE_WEIGHT + HASH_WEIGHT
          + VERIFY_ACCEPT_WEIGHT + VERIFY_A_WEIGHT + VERIFY_B_WEIGHT
          + MEMO_WEIGHT_EACH * 3)
FIELDS = ("mode", "soc", "temp", "current", "voltage", "fault")


def run_engine(**mutants):
    for k in E.MUTANT:
        E.MUTANT[k] = False
    E.MUTANT.update(mutants)
    rows = E.run()
    text = E.serialize(rows)
    h = E.certificate_hash(text)
    for k in E.MUTANT:
        E.MUTANT[k] = False
    return rows, h


CANON_ROWS, CANON_HASH = run_engine()
CANON_BY_TICK = {r["t"]: r for r in CANON_ROWS}


def find_events(rows):
    events = {}
    prev_mode = None
    prev_fault = False
    for r in rows:
        if r["mode"] != prev_mode:
            if prev_mode == "CC" and r["mode"] == "CV":
                events["cc_to_cv"] = r["t"]
            if prev_mode == "CV" and r["mode"] == "TAPER":
                events["cv_to_taper"] = r["t"]
            prev_mode = r["mode"]
        if r["fault"] != prev_fault:
            if r["fault"]:
                events["fault_engage"] = r["t"]
            else:
                events["fault_release"] = r["t"]
            prev_fault = r["fault"]
    return events


CANON_EVENTS = find_events(CANON_ROWS)


def score(name, mutant_kwargs=None, local_rule_fail=False,
          verify_accept_fail=False, verify_a_fail=False, verify_b_fail=False,
          memo_fail=False):
    mutant_kwargs = mutant_kwargs or {}
    rows, h = run_engine(**mutant_kwargs)
    by_tick = {r["t"]: r for r in rows}
    events = find_events(rows)

    earned = 0
    earned += PACKAGE_WEIGHT
    if not local_rule_fail:
        earned += LOCAL_RULE_WEIGHT

    correct_checkpoints = 0
    for cp in CHECKPOINT_TICKS:
        claimed = by_tick.get(cp, {})
        canon = CANON_BY_TICK[cp]
        if all(claimed.get(f) == canon[f] for f in FIELDS):
            correct_checkpoints += 1
            earned += CHECKPOINT_WEIGHT

    correct_events = 0
    for key in ("cc_to_cv", "cv_to_taper", "fault_engage", "fault_release"):
        if events.get(key) == CANON_EVENTS.get(key):
            correct_events += 1
            earned += EVENT_WEIGHT

    final_claimed = by_tick.get(E.N_TICKS, {})
    final_canon = CANON_BY_TICK[E.N_TICKS]
    final_match = all(final_claimed.get(f) == final_canon[f] for f in FIELDS)
    if final_match:
        earned += FINAL_STATE_WEIGHT

    if h == CANON_HASH:
        earned += HASH_WEIGHT

    if not verify_accept_fail:
        earned += VERIFY_ACCEPT_WEIGHT
    if not verify_a_fail:
        earned += VERIFY_A_WEIGHT
    if not verify_b_fail:
        earned += VERIFY_B_WEIGHT
    if not memo_fail:
        earned += MEMO_WEIGHT_EACH * 3

    pct = 100 * earned / TOTAL
    print(f"{name}: {earned}/{TOTAL} = {pct:.1f}%  checkpoints={correct_checkpoints}/{N_CHECKPOINTS}  "
          f"events={correct_events}/{N_EVENTS}  final_match={final_match}  hash_match={h==CANON_HASH}")
    return earned, pct


if __name__ == "__main__":
    print(f"Rubric total positive weight: {TOTAL}")
    print(f"Canonical hash: {CANON_HASH}")
    print(f"Canonical events: {CANON_EVENTS}\n")

    ok, r1 = V.accepts_true_program()
    rejA, r2 = V.adversarial_mutation_early_release()
    rejB, r3 = V.adversarial_mutation_no_clamp()
    print(f"verifier: accepts true={ok}  rejects A={rejA}  rejects B={rejB}\n")

    score("canonical (sanity, must be 100%)")

    score("drop thermal derating",
          mutant_kwargs=dict(no_derate=True),
          local_rule_fail=True, memo_fail=True)

    score("fault releases instantly, no hysteresis counter",
          mutant_kwargs=dict(fault_release_no_hysteresis=True),
          local_rule_fail=True, verify_a_fail=True, memo_fail=True)

    score("CV current never decays (TAPER never reached)",
          mutant_kwargs=dict(cv_no_decay=True),
          local_rule_fail=True, memo_fail=True)

    score("skip overcurrent clamp",
          mutant_kwargs=dict(no_overcurrent_clamp=True),
          local_rule_fail=True, verify_b_fail=True, memo_fail=True)

    score("TAPER uses full-heat rate, not TAPER-specific rate",
          mutant_kwargs=dict(taper_uses_full_heat=True),
          local_rule_fail=True, memo_fail=True)
