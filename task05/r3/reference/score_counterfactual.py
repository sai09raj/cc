#!/usr/bin/env python3
"""Full rubric scoring for a counterfactual/mutant result set, computed
programmatically to avoid hand-arithmetic transcription errors (see
Playbook/03-RUBRIC-AND-LINTER-GUIDE.md's numeric-entry-discipline warnings).

Criterion numbering matches platform/rubric.md (final, post-hardening, post
full rubric-guidelines atomicity pass -- see revision-delta.md):
  1-3 package (1-4 merged into one reproducibility criterion), 4-16 local
  (10=oven partner-matching, 11=oven deadline-timing -- split from the old
  bundled criterion 11; 14=maintenance trigger/tracking, 15=maintenance
  trigger-minute-unaffected, 16=maintenance 13-minute window -- split from
  the old bundled criterion 15), 17-28 per-design values+reconciliation (27
  is +7, not +10 -- see below), 29-33 named production witnesses (29 fault,
  30 interleave, 31 mixed-batch, 32 maintenance-freeze, 33 setup-memory/W3),
  34 verifier-exists, 35 verifier-agrees, 36-37 adversarial checks,
  38-43 per-design canonical trace-hash, 44-49 decision, 50 negative trap.

Weights below must be kept in sync with platform/rubric.md by hand; this file
does not parse the rubric. After any rubric weight change, re-check both.
"""
import hashlib
import kilnworks_sim as k
from mutant_per_campaign_reset import simulate_per_campaign_reset as reset_sim

PER_DESIGN_WEIGHT = 10          # criteria 17-22 (all) and 23-28 (D4/27 overridden below)
PER_DESIGN_RECON_WEIGHT = {"D4": 7}  # 27 lost 3 of its 10 to the standalone W3 criterion (33)
PER_DESIGN_HASH_WEIGHT = 10     # criteria 38-43, one per design
PACKAGE_WEIGHT = [2, 1, 1]                                                     # 1-3
LOCAL_WEIGHT = {4: 2, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 1, 14: 2, 15: 1, 16: 1}  # 4-16
W_FAULT, W_INTERLEAVE, W_MIXED, W_MAINT, W_SETUP_MEM = 3, 3, 3, 3, 3           # 29-33
W_VERIFIER_EXISTS, W_VERIFIER_AGREES, W_NEGSTART, W_COLLISION = 1, 1, 1, 1     # 34-37
DECISION_WEIGHT = {44: 1, 45: 1, 46: 1, 47: 1, 48: 1, 49: 1}

TOTAL = (sum(PACKAGE_WEIGHT) + sum(LOCAL_WEIGHT.values())
         + PER_DESIGN_WEIGHT * 6                                    # 17-22
         + (PER_DESIGN_WEIGHT * 5 + PER_DESIGN_RECON_WEIGHT["D4"])  # 23-28
         + PER_DESIGN_HASH_WEIGHT * 6
         + W_FAULT + W_INTERLEAVE + W_MIXED + W_MAINT + W_SETUP_MEM
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
            recon_weight = PER_DESIGN_RECON_WEIGHT.get(name, PER_DESIGN_WEIGHT)
            earned += PER_DESIGN_WEIGHT + recon_weight  # value criterion + reconciliation
        try:
            h = hashlib.sha256(k.canonical_trace_serialization(results[name]).encode()).hexdigest()
            if h == CANON_TRACE_HASH[name]:
                earned += PER_DESIGN_HASH_WEIGHT
        except Exception:
            pass
    return earned, detail


def witness_setup_memory(results, continuous):
    """W3: a Q or P job whose setup cost is 2, is the machine's first job of its
    own campaign, and the machine's most recent earlier job (if any) belongs to a
    strictly earlier campaign -- i.e. the setup cost is attributable only to family
    memory carried over from an earlier campaign, not to any same-campaign job."""
    if not continuous:
        return 0
    r = results.get("D4")
    if r is None:
        return 0
    events = sorted(r["prep_events"], key=lambda e: e["start_t"])
    last_by_machine = {}
    for e in events:
        gidx = e["lot"]
        s, j = divmod(gidx, k.LOTS_PER_CAMPAIGN)
        lot = k.Lot(dict(gidx=gidx, s=s, j=j, family=(j + s) % 2,
                          release_abs=e["release_abs"],
                          pbase=5 + (j * j + 2 * s) % 4, qbase=4 + (3 * j + s) % 5))
        setup = e["dur"] - k.duration_on(e["machine"], lot)
        prev = last_by_machine.get(e["machine"])
        same_campaign_earlier = prev is not None and prev["s"] == s and prev["start_t"] < e["start_t"]
        earlier_campaign_exists = prev is not None and prev["s"] < s
        if setup == 2 and not same_campaign_earlier and earlier_campaign_exists:
            return W_SETUP_MEM
        last_by_machine[e["machine"]] = dict(s=s, start_t=e["start_t"])
    return 0


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
    ws = witness_setup_memory(results, continuous)
    w_ver_exists, w_negstart, w_collision = W_VERIFIER_EXISTS, W_NEGSTART, W_COLLISION
    w_ver_agrees = W_VERIFIER_AGREES

    package_earned = sum(wt for i, wt in zip(range(1, 4), PACKAGE_WEIGHT) if i not in package_fail)
    local_earned = sum(wt for i, wt in LOCAL_WEIGHT.items() if i not in local_fail)
    decision_earned = sum(wt for i, wt in DECISION_WEIGHT.items() if i not in decision_fail)

    total_earned = (package_earned + local_earned + pd_earned
                    + wf + wi + wm + wmaint + ws
                    + w_ver_exists + w_ver_agrees + w_negstart + w_collision
                    + decision_earned)
    pct = 100 * total_earned / TOTAL
    print(f"{label}: {total_earned}/{TOTAL} = {pct:.1f}%   per-design ok:{pd_detail}")
    return pct


if __name__ == "__main__":
    print(f"Rubric total positive weight: {TOTAL}\n")

    score("canonical (sanity, must be 100%)", CANON, local_fail=(), package_fail=(), decision_fail=())

    r = {name: k.simulate(name, mutant_disable_fault=True) for name in k.DESIGNS}
    score("fault disabled", r, local_fail={13}, decision_fail={44}, w_fault_override=False)

    r = {name: k.simulate(name, mutant_oven_no_timer=True) for name in k.DESIGNS}
    score("oven no timer", r, local_fail={11}, decision_fail={44})

    r = {name: k.simulate(name, mutant_tiebreak_high=True) for name in k.DESIGNS}
    score("tiebreak high", r, local_fail={7, 9, 10}, decision_fail=())  # picks D4 correctly

    r = {name: k.simulate(name, mutant_disable_maintenance=True) for name in k.DESIGNS}
    score("maintenance disabled", r, local_fail={14, 15, 16}, w_maint_override=False, decision_fail={44})

    r = {name: k.simulate(name, mutant_maintenance_inclusive=True) for name in k.DESIGNS}
    score("maintenance inclusive (wrong boundary only)", r, local_fail={15, 16}, w_maint_override=False, decision_fail=())

    r = {name: reset_sim(name) for name in k.DESIGNS}
    score("per-campaign reset", r, local_fail={5, 7, 8, 13, 14, 15, 16}, package_fail={3},
          decision_fail={44, 49}, continuous=False)
