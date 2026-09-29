#!/usr/bin/env python3
"""Programmatic score-topology counterfactual scorer for ATRIUM-9's rubric.
Criterion numbering matches platform/rubric.md exactly (<=50 criteria,
every weight capped at 10 -- the platform's per-criterion maximum).

Consolidated from a 61-criterion draft: criterion 22 was a literal
duplicate of criterion 3 (both test "144 unique legal rows") and several
same-mechanism pairs (package 1+2, boarding+alighting, timeout-trigger +
reassign-cost-compare, the two power-admission-order rules, the two
verifier-mutation checks, and several decision/reconciliation pairs) were
merged into single AND-criteria that still require the same facts. Every
merge either preserves the combined weight exactly or, where it touches a
criterion all three tested mutants pass "for free" (package/local/sweep
scaffolding unrelated to the specific bug), deliberately SHRINKS that
weight -- removing weight a mutant earns for free lowers its percentage
without weakening real coverage. Numbering:
  1-2    package (merged)
  3-12   local semantics (further merged: zoning+active-cars, eligibility+tie-break)
  13-19  integrated sweep (selections, agree-disclosure, samples -- reconciliation dropped)
  20-32  whole-sweep aggregate totals (3 grand totals + 10 partial sums) --
         each wrong under ALL THREE tested mutants; the main discriminator.
  33-41  baseline-trace witnesses + hash
  42     independent verification (merged: delivered, accepts baseline, rejects both mutations)
  43-44  decision/causal reconciliation (43 merged from 4 explanation facts -- now
         universal-fail, since each mutant fails a different piece of it)
  45-49  negative criteria for prohibitions the platform linter required dedicated
         negatives for (verifier independence; reassigned-away non-reuse; per-tick
         search instead of the fixed policy; equal-cost bouncing; shortened/sampled runs)
  50     negative trap (embedding precomputed values)
"""
import itertools
import hashlib
import atrium_sim as SIM
import atrium_verify as VER

ACTIVE = [2, 3, 4]
ZONING = ["SPLIT", "GROUND", "TOP"]
TIMEOUT = [50, 75, 100, 125]
POWER = [6, 8, 10, 12]

PACKAGE_WEIGHT = [2]  # criterion 1 (merged reproducibility+deliverables); criterion 2 below
PACKAGE2_WEIGHT = 1   # criterion 2 (144 unique rows -- was both 3 and 22, deduped)

# local semantics, criteria 3-12 (10 items; further merged from 12 to free
# 3 slots for negative criteria the linter required -- see bottom of file)
LOCAL_WEIGHT = {
    3: 2,   # call-generation formulas
    4: 2,   # zoning table + active-car count (merged, was 4+5)
    5: 3,   # eligibility rule + tie-break (merged, was 6+7)
    6: 2,   # per-direction commitment separation
    7: 1,   # re-derive next action
    8: 1,   # door-cycle timing constants
    9: 2,   # boarding+alighting (merged, was 12+13)
    10: 10, # power admission order + DWELL-to-CLOSING gating (merged, was 14+15)
    11: 1,  # energy formula
    12: 3,  # timeout trigger + reassign cost-compare (merged, was 17+18)
}

SWEEP_SELECTION_WEIGHT = 2    # criteria 13-15
SWEEP_AGREE_WEIGHT = 1        # criterion 16
SWEEP_SAMPLE_WEIGHT = 4       # criteria 17-19
# (the reconciliation criterion was dropped entirely -- criteria 13-15
# already grade the selection VALUE directly against a known-correct
# reference, so a separate "does it hold its own claimed extremum" check
# was largely tautological for this packet; dropping it also removes free
# weight every tested mutant earned, which helps margins)

SWEEP_REASSIGN_TOTAL_WEIGHT = 10   # criterion 20
REF_REASSIGN_TOTAL = 43
SWEEP_ENERGY_TOTAL_WEIGHT = 10     # criterion 21
REF_ENERGY_TOTAL = 547080
SWEEP_WAIT_TOTAL_WEIGHT = 10       # criterion 22
REF_WAIT_TOTAL = 2739.8125

# criteria 28-35: (label, filter-on-config-tuple, ref avg_wait, ref net_energy)
PARTIAL_SUMS = [
    ("active_cars==4", lambda k: k[0] == 4, 595.6625, 222024),
    ("zoning==GROUND", lambda k: k[1] == "GROUND", 884.4875, 180000),
    ("zoning==TOP", lambda k: k[1] == "TOP", 1071.15, 183072),
    ("wait_timeout==50", lambda k: k[2] == 50, 693.65, 136440),
    ("wait_timeout==75", lambda k: k[2] == 75, 682.25, 136464),
    ("power_budget==6", lambda k: k[3] == 6, 687.8875, 134664),
    ("active_cars==4 & zoning==GROUND", lambda k: k[0] == 4 and k[1] == "GROUND", 191.7875, 73248),
    ("active_cars==4 & zoning==TOP", lambda k: k[0] == 4 and k[1] == "TOP", 229.05, 75648),
    ("zoning==TOP & power_budget==6", lambda k: k[1] == "TOP" and k[3] == 6, 272.2875, 45552),
    ("zoning==TOP & wait_timeout==50", lambda k: k[1] == "TOP" and k[2] == 50, 286.9375, 45672),
]
PARTIAL_SUM_WEIGHT = 10  # each, criteria 23-32

W1_WEIGHT = 9    # criterion 33
W23_WEIGHT = 10  # criterion 34: merged W2(gidx=15)+W3a(gidx=5) -- both T-only, capped (was 9+10=19)
W3B_WEIGHT = 10  # criterion 35
W4_WEIGHT = 10   # criterion 36
W5_WEIGHT = 10   # criterion 37: gidx=26 board_tick
W6_WEIGHT = 10   # criterion 38: gidx=27 board_tick
PW1_CFG = dict(active_cars=4, zoning="SPLIT", wait_timeout=50, capacity=6, power_budget=6)
PW2_CFG = dict(active_cars=4, zoning="TOP", wait_timeout=50, capacity=6, power_budget=6)
PW1_WEIGHT = 10  # criterion 39
PW2_WEIGHT = 10  # criterion 40
HASH_WEIGHT = 10  # criterion 41

VERIFY_WEIGHT = 3   # criterion 42: merged -- independent verifier delivered, accepts baseline,
                     # and rejects both required adversarial mutations

DECISION_MAIN_WEIGHT = 8   # criterion 43: merged wait/energy-divergence + budget-tradeoff +
                           # power-delay-witness + door-closing-automatic explanation --
                           # this merge makes it fail under ALL THREE mutants (each fails a
                           # different piece of the combined explanation), so it moved from
                           # two AlwaysPass-ish decision criteria to one universal discriminator
DECISION_REASSIGN_WEIGHT = 2  # criterion 44: reassignment-non-reuse explanation

# criteria 45-49: negative criteria. 45-46 were added for the linter's first
# "prohibition must have a dedicated negative" finding; 47-49 for its second
# pass (three more positive-only prohibitions in the prompt text). None of
# these five trigger for canonical or the three scored mutants below -- they
# test failure modes distinct from the three mechanism bugs this script
# scores, so they cost 0 for all four and exist purely for required coverage.
NEG_VERIFIER_WRAP_WEIGHT = 4     # criterion 45
NEG_REASSIGN_REUSE_WEIGHT = 4    # criterion 46
NEG_PER_TICK_SEARCH_WEIGHT = 4   # criterion 47
NEG_EQUAL_COST_BOUNCE_WEIGHT = 3  # criterion 48
NEG_SHORTENED_RUN_WEIGHT = 5     # criterion 49

TOTAL = (sum(PACKAGE_WEIGHT) + PACKAGE2_WEIGHT + sum(LOCAL_WEIGHT.values())
         + SWEEP_SELECTION_WEIGHT * 3 + SWEEP_AGREE_WEIGHT
         + SWEEP_SAMPLE_WEIGHT * 3
         + SWEEP_REASSIGN_TOTAL_WEIGHT + SWEEP_ENERGY_TOTAL_WEIGHT + SWEEP_WAIT_TOTAL_WEIGHT
         + PARTIAL_SUM_WEIGHT * len(PARTIAL_SUMS)
         + W1_WEIGHT + W23_WEIGHT + W3B_WEIGHT + W4_WEIGHT
         + W5_WEIGHT + W6_WEIGHT + PW1_WEIGHT + PW2_WEIGHT + HASH_WEIGHT
         + VERIFY_WEIGHT
         + DECISION_MAIN_WEIGHT + DECISION_REASSIGN_WEIGHT)
NEGATIVE_TOTAL = 8 + NEG_VERIFIER_WRAP_WEIGHT + NEG_REASSIGN_REUSE_WEIGHT

BASELINE_CFG = dict(active_cars=3, zoning="TOP", wait_timeout=50, capacity=6, power_budget=8)
POWER_WITNESS_CFG = dict(active_cars=4, zoning="GROUND", wait_timeout=50, capacity=6, power_budget=6)

REF_HASH16 = "f544b2d2a1d0fb30"


def run_sweep(**mutant_kwargs):
    out = {}
    for ac, z, wt, pw in itertools.product(ACTIVE, ZONING, TIMEOUT, POWER):
        cfg = dict(active_cars=ac, zoning=z, wait_timeout=wt, capacity=6, power_budget=pw)
        r = SIM.simulate(cfg, trace_limit=300000, **mutant_kwargs)
        out[(ac, z, wt, pw)] = r
    return out


def selections(sweep):
    def w(k): return sweep[k]["avg_wait"]
    def e(k): return sweep[k]["net_energy"]
    wait_opt = min(sweep, key=lambda k: (round(w(k), 6), e(k), k))
    energy_opt = min(sweep, key=lambda k: (e(k), round(w(k), 6), k))
    under = [k for k in sweep if e(k) <= 3800]
    budget_opt = min(under, key=lambda k: (round(w(k), 6), e(k), k)) if under else None
    return wait_opt, energy_opt, budget_opt


def score(name, sweep_kwargs=None, local_fail=(), decision_fail=(), verify_fail=(),
          hash_ok=True):
    sweep_kwargs = sweep_kwargs or {}
    sweep = run_sweep(**sweep_kwargs)

    earned = 0

    earned += sum(PACKAGE_WEIGHT)
    earned += PACKAGE2_WEIGHT

    for cid, wgt in LOCAL_WEIGHT.items():
        if cid not in local_fail:
            earned += wgt

    wait_opt, energy_opt, budget_opt = selections(sweep)
    correct_wait = wait_opt == (4, "SPLIT", 50, 6)
    correct_energy = energy_opt == (2, "TOP", 50, 6)
    correct_budget = budget_opt == (2, "SPLIT", 50, 6)
    for ok in (correct_wait, correct_energy, correct_budget):
        if ok:
            earned += SWEEP_SELECTION_WEIGHT

    earned += SWEEP_AGREE_WEIGHT

    samples = [
        ((2, "TOP", 50, 6), 34.2875, 2676),
        ((4, "GROUND", 75, 8), 11.9625, 4428),
        ((4, "GROUND", 75, 6), 12.4000, 4380),
    ]
    for key, ref_w, ref_e in samples:
        r = sweep[key]
        if abs(r["avg_wait"] - ref_w) <= 0.01 and r["net_energy"] == ref_e:
            earned += SWEEP_SAMPLE_WEIGHT

    total_reassign = sum(sweep[k]["reassign_count"] for k in sweep)
    if total_reassign == REF_REASSIGN_TOTAL:
        earned += SWEEP_REASSIGN_TOTAL_WEIGHT

    total_energy = sum(sweep[k]["net_energy"] for k in sweep)
    if total_energy == REF_ENERGY_TOTAL:
        earned += SWEEP_ENERGY_TOTAL_WEIGHT

    total_wait = sum(sweep[k]["avg_wait"] for k in sweep)
    if abs(total_wait - REF_WAIT_TOTAL) <= 0.05:
        earned += SWEEP_WAIT_TOTAL_WEIGHT

    partial_ok = []
    for label, filt, ref_w, ref_e in PARTIAL_SUMS:
        pw_sum = sum(sweep[k]["avg_wait"] for k in sweep if filt(k))
        pe_sum = sum(sweep[k]["net_energy"] for k in sweep if filt(k))
        ok = abs(pw_sum - ref_w) <= 0.05 and pe_sum == ref_e
        partial_ok.append(ok)
        if ok:
            earned += PARTIAL_SUM_WEIGHT

    rb = SIM.simulate(BASELINE_CFG, trace_limit=300000, **sweep_kwargs)
    calls = {c.gidx: c for c in rb["calls"]}
    w1 = False
    for row in rb["trace"][:40]:
        dirs = [c["dir"] for c in row["cars"] if c["dir"]]
        if len(set(dirs)) >= 2:
            w1 = True
            break
    w2 = 15 in calls and calls[15].board_tick == 169 and calls[15].alight_tick == 200
    w3a = 5 in calls and calls[5].attempt == 2 and calls[5].assigned_car == 2 and calls[5].board_tick == 94
    w23 = w2 and w3a
    w3b = 19 in calls and calls[19].attempt == 1 and calls[19].assigned_car == 0 and calls[19].board_tick == 248
    w5 = 26 in calls and calls[26].board_tick == 278 and calls[26].assigned_car == 1
    w6 = 27 in calls and calls[27].board_tick == 302 and calls[27].assigned_car == 2
    rp = SIM.simulate(POWER_WITNESS_CFG, trace_limit=300000, **sweep_kwargs)
    w4 = (any(row["power"] == 6 for row in rp["trace"][24:60])
          and all(row["power"] <= 6 for row in rp["trace"]))
    rpw1 = SIM.simulate(PW1_CFG, trace_limit=300000, **sweep_kwargs)
    pw1 = all(row["power"] <= 6 for row in rpw1["trace"])
    rpw2 = SIM.simulate(PW2_CFG, trace_limit=300000, **sweep_kwargs)
    pw2 = all(row["power"] <= 6 for row in rpw2["trace"])

    for ok, cid, wgt in [(w1, 36, W1_WEIGHT), (w23, 37, W23_WEIGHT),
                          (w3b, 38, W3B_WEIGHT), (w4, 39, W4_WEIGHT),
                          (w5, 40, W5_WEIGHT), (w6, 41, W6_WEIGHT),
                          (pw1, 42, PW1_WEIGHT), (pw2, 43, PW2_WEIGHT)]:
        if ok:
            earned += wgt

    h = hashlib.sha256(SIM.canonical_trace_serialization(rb).encode()).hexdigest()[:16]
    if hash_ok and h == REF_HASH16:
        earned += HASH_WEIGHT

    if 42 not in verify_fail:
        earned += VERIFY_WEIGHT

    if 43 not in decision_fail:
        earned += DECISION_MAIN_WEIGHT
    if 44 not in decision_fail:
        earned += DECISION_REASSIGN_WEIGHT

    # criteria 45-49 (negative): none of the tested mutants actually violates
    # any of these five prohibitions (verifier independence, reassigned-away
    # non-reuse, per-tick search instead of the fixed policy, equal-cost
    # bouncing, shortened/sampled runs) -- each tests a failure mode distinct
    # from the three mechanism bugs scored here, so they cost 0 for all of
    # canonical/T/C/Pw. They exist for coverage the linter required, not as
    # discriminators.

    pct = 100 * earned / TOTAL
    print(f"{name}: {earned}/{TOTAL} = {pct:.1f}%  hash_match={h == REF_HASH16}  "
          f"sel_ok={correct_wait,correct_energy,correct_budget}  "
          f"w1={w1} w23={w23} w3b={w3b} w4={w4} w5={w5} w6={w6} pw1={pw1} pw2={pw2} "
          f"reassign_total={total_reassign} partial_sums_ok={sum(partial_ok)}/{len(partial_ok)}")
    return earned, pct


if __name__ == "__main__":
    print(f"Rubric total positive weight: {TOTAL}\n")

    score("canonical (sanity, must be 100%)")

    score("timeout reassignment disabled",
          sweep_kwargs=dict(mutant_no_timeout=True),
          local_fail={12}, hash_ok=False, decision_fail={43})

    score("reassignment never compares cost (always switches)",
          sweep_kwargs=dict(mutant_no_cost_compare=True),
          local_fail={12}, hash_ok=False, decision_fail={43})

    score("power admission disabled",
          sweep_kwargs=dict(mutant_power_disabled=True),
          local_fail={10}, hash_ok=False, decision_fail={43})
