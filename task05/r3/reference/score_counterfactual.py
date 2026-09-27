#!/usr/bin/env python3
"""Full rubric scoring for a counterfactual/mutant result set, computed
programmatically to avoid hand-arithmetic transcription errors (see
Playbook/03-RUBRIC-AND-LINTER-GUIDE.md's numeric-entry-discipline warnings).

Criterion numbering matches platform/rubric.md (final, post-hardening):
  1-4 package, 5-15 local (14=maintenance trigger/tracking, 15=maintenance
  boundary convention -- split so a boundary-only bug doesn't also erase
  trigger-tracking credit), 16-27 per-design values+reconciliation,
  28-33 named production witnesses (28 fault, 29 interleave, 30 mixed-batch,
  31 maintenance-freeze), 32 verifier-exists, 33 verifier-agrees,
  34-35 adversarial checks, 36-41 per-design canonical trace-hash,
  42-47 decision, 48 negative trap.

Weights below must be kept in sync with platform/rubric.md by hand; this file
does not parse the rubric. After any rubric weight change, re-check both.
"""
import hashlib
import kilnworks_sim as k
from mutant_per_campaign_reset import simulate_per_campaign_reset as reset_sim

PER_DESIGN_WEIGHT = 10        # criteria 16-21 and 22-27
PER_DESIGN_HASH_WEIGHT = 10   # criteria 36-41, one per design
PACKAGE_WEIGHT = [1, 1, 1, 1]                                                  # 1-4
LOCAL_WEIGHT = {5: 2, 6: 2, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 1, 14: 2, 15: 2}  # 5-15
W_FAULT, W_INTERLEAVE, W_MIXED, W_MAINT = 3, 3, 3, 3                           # 28-31
W_VERIFIER_EXISTS, W_VERIFIER_AGREES, W_NEGSTART, W_COLLISION = 1, 1, 1, 1     # 32-35
DECISION_WEIGHT = {42: 1, 43: 1, 44: 1, 45: 1, 46: 1, 47: 1}

TOTAL = (sum(PACKAGE_WEIGHT) + sum(LOCAL_WEIGHT.values())
         + PER_DESIGN_WEIGHT * 12 + PER_DESIGN_HASH_WEIGHT * 6
         + W_FAULT + W_INTERLEAVE + W_MIXED + W_MAINT
         + W_VERIFIER_EXISTS + W_VERIFIER_AGREES + W_NEGSTART + W_COLLISION
         + sum(DECISION_WEIGHT.values()))

CANON = {name: k.simulate(name) for name in k.DESIGNS}
CANON_VALUES = {name: (r["makespan"], r["bill"]) for name, r in CANON.items()}
CANON_TRACE_HASH = {name: hashlib.sha256(k.canonical_trace_serialization(r).encode()).hexdigest()
                     for name, r in CANON.items()}


def per_design(results):
    earned, detail = 0, {}
    for name in k.DESIGNS:
        ok = (results[name]["makespan"], results[name]["bill"]) == CANON_VALUES[name]
        detail[name] = ok
        if ok:
            earned += PER_DESIGN_WEIGHT * 2  # value criterion + reconciliation twin
        try:
            h = hashlib.sha256(k.canonical_trace_serialization(results[name]).encode()).hexdigest()
            if h == CANON_TRACE_HASH[name]:
                earned += PER_DESIGN_HASH_WEIGHT
        except Exception:
            pass
    return earned, detail


def witness_fault(results, continuous):
    if not continuous:
        return 0
    return W_FAULT if any(results[n]["fault_triggered"] for n in k.DESIGNS) else 0


def witness_maintenance(results, continuous):
    if not continuous:
        return 0
    for name in ("D1", "D2", "D3", "D4", "D5"):
        r = results[name]
        if r.get("q_maint_triggered") and r.get("q_maint_trigger_t") is not None:
            if r["q_freeze_until"] == r["q_maint_trigger_t"] + k.MAINT_WINDOW:
                return W_MAINT
    return 0


def witness_mixed_batch(results, continuous):
    if not continuous:
        return 0
    for name in ("D1", "D4", "D5"):
        for b in results[name]["batch_log"]:
            if len(b["members"]) > 1 and len(b["campaigns"]) > 1:
                return W_MIXED
    return 0


def score(label, results, local_fail, package_fail=(), decision_fail=(),
          continuous=True, w_fault_override=None, w_maint_override=None):
    pd_earned, pd_detail = per_design(results)

    wf = (W_FAULT if w_fault_override is True else
          (0 if w_fault_override is False else witness_fault(results, continuous)))
    wi = W_INTERLEAVE if continuous else 0
    wm = witness_mixed_batch(results, continuous)
    wmaint = (W_MAINT if w_maint_override is True else
              (0 if w_maint_override is False else witness_maintenance(results, continuous)))
    w_ver_exists, w_negstart, w_collision = W_VERIFIER_EXISTS, W_NEGSTART, W_COLLISION
    w_ver_agrees = W_VERIFIER_AGREES

    package_earned = sum(wt for i, wt in zip(range(1, 5), PACKAGE_WEIGHT) if i not in package_fail)
    local_earned = sum(wt for i, wt in LOCAL_WEIGHT.items() if i not in local_fail)
    decision_earned = sum(wt for i, wt in DECISION_WEIGHT.items() if i not in decision_fail)

    total_earned = (package_earned + local_earned + pd_earned
                    + wf + wi + wm + wmaint
                    + w_ver_exists + w_ver_agrees + w_negstart + w_collision
                    + decision_earned)
    pct = 100 * total_earned / TOTAL
    print(f"{label}: {total_earned}/{TOTAL} = {pct:.1f}%   per-design ok:{pd_detail}")
    return pct


if __name__ == "__main__":
    print(f"Rubric total positive weight: {TOTAL}\n")

    score("canonical (sanity, must be 100%)", CANON, local_fail=(), package_fail=(), decision_fail=())

    r = {name: k.simulate(name, mutant_disable_fault=True) for name in k.DESIGNS}
    score("fault disabled", r, local_fail={13}, decision_fail={42}, w_fault_override=False)

    r = {name: k.simulate(name, mutant_oven_no_timer=True) for name in k.DESIGNS}
    score("oven no timer", r, local_fail={11}, decision_fail={42})

    r = {name: k.simulate(name, mutant_tiebreak_high=True) for name in k.DESIGNS}
    score("tiebreak high", r, local_fail={8, 10, 11}, decision_fail=())  # picks D4 correctly

    r = {name: k.simulate(name, mutant_disable_maintenance=True) for name in k.DESIGNS}
    score("maintenance disabled", r, local_fail={14, 15}, w_maint_override=False, decision_fail={42})

    r = {name: k.simulate(name, mutant_maintenance_inclusive=True) for name in k.DESIGNS}
    score("maintenance inclusive (wrong boundary only)", r, local_fail={15}, w_maint_override=False, decision_fail=())

    r = {name: reset_sim(name) for name in k.DESIGNS}
    score("per-campaign reset", r, local_fail={6, 8, 9, 13, 14, 15}, package_fail={3},
          decision_fail={42, 47}, continuous=False)
