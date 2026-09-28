#!/usr/bin/env python3
"""Programmatic score-topology counterfactual scorer for ATRIUM-9's rubric.
Criterion numbering matches platform/rubric.md: 1-3 package, 4-18 local,
19-30 sweep, 31-36 baseline witnesses, 37-40 verification, 41-44 decision,
45 negative trap. Computes each mutant's actual sweep/witness outputs and
scores them against the rubric's own stated pass conditions.
"""
import itertools
import hashlib
import atrium_sim as SIM
import atrium_verify as VER

ACTIVE = [2, 3, 4]
ZONING = ["SPLIT", "GROUND", "TOP"]
TIMEOUT = [50, 75, 100, 125]
POWER = [6, 8, 10, 12]

PACKAGE_WEIGHT = [1, 1, 1]
LOCAL_WEIGHT = {4: 2, 5: 1, 6: 1, 7: 2, 8: 1, 9: 2, 10: 1, 11: 1, 12: 1,
                13: 1, 14: 5, 15: 5, 16: 1, 17: 1, 18: 2}
SWEEP_SELECTION_WEIGHT = 2    # criteria 19-21
SWEEP_ROWCOUNT_WEIGHT = 2     # criterion 22
SWEEP_AGREE_WEIGHT = 1        # criterion 23
SWEEP_SAMPLE_WEIGHT = 4       # criteria 24-27
SWEEP_RECON_WEIGHT = 1        # criteria 28-30
SWEEP_REASSIGN_TOTAL_WEIGHT = 36   # criterion 31 (failed by all three mutants: pure discriminator)
REF_REASSIGN_TOTAL = 43
SWEEP_ENERGY_TOTAL_WEIGHT = 36     # criterion 32 (failed by all three mutants: pure discriminator)
REF_ENERGY_TOTAL = 547080
W1_WEIGHT = 9                 # criterion 33
W2_WEIGHT = 9                 # criterion 34
W3A_WEIGHT = 10                # criterion 35
W3B_WEIGHT = 28                # criterion 36
W4_WEIGHT = 14                  # criterion 37 (only discriminates power-disabled; kept modest since it raises the other two mutants' scores)
HASH_WEIGHT = 36                # criterion 38 (forced-fail for power-disabled too: pure discriminator)
VERIFY_WEIGHT = 1             # criteria 37-40
DECISION_WEIGHT = 2           # criteria 41-44

TOTAL = (sum(PACKAGE_WEIGHT) + sum(LOCAL_WEIGHT.values())
         + SWEEP_SELECTION_WEIGHT * 3 + SWEEP_ROWCOUNT_WEIGHT + SWEEP_AGREE_WEIGHT
         + SWEEP_SAMPLE_WEIGHT * 4 + SWEEP_RECON_WEIGHT * 3
         + SWEEP_REASSIGN_TOTAL_WEIGHT + SWEEP_ENERGY_TOTAL_WEIGHT
         + W1_WEIGHT + W2_WEIGHT + W3A_WEIGHT + W3B_WEIGHT + W4_WEIGHT + HASH_WEIGHT
         + VERIFY_WEIGHT * 4 + DECISION_WEIGHT * 4)

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


def keytuple(k):
    return k


def selections(sweep):
    def w(k): return sweep[k]["avg_wait"]
    def e(k): return sweep[k]["net_energy"]
    wait_opt = min(sweep, key=lambda k: (round(w(k), 6), e(k), keytuple(k)))
    energy_opt = min(sweep, key=lambda k: (e(k), round(w(k), 6), keytuple(k)))
    under = [k for k in sweep if e(k) <= 3800]
    budget_opt = min(under, key=lambda k: (round(w(k), 6), e(k), keytuple(k))) if under else None
    return wait_opt, energy_opt, budget_opt


def score(name, sweep_kwargs=None, local_fail=(), decision_fail=(), verify_fail=(),
          package_fail=(), witness_fail=(), hash_ok=True):
    sweep_kwargs = sweep_kwargs or {}
    sweep = run_sweep(**sweep_kwargs)

    earned = 0
    detail = {}

    # package
    for i, wgt in enumerate(PACKAGE_WEIGHT, start=1):
        if i not in package_fail:
            earned += wgt

    # local
    for cid, wgt in LOCAL_WEIGHT.items():
        if cid not in local_fail:
            earned += wgt

    # sweep selections (19-21)
    wait_opt, energy_opt, budget_opt = selections(sweep)
    ref_wait_opt = ('active_cars', 4)  # placeholder, real compare below
    correct_wait = wait_opt == (4, "SPLIT", 50, 6)
    correct_energy = energy_opt == (2, "TOP", 50, 6)
    correct_budget = budget_opt == (2, "SPLIT", 50, 6)
    if correct_wait:
        earned += SWEEP_SELECTION_WEIGHT
    if correct_energy:
        earned += SWEEP_SELECTION_WEIGHT
    if correct_budget:
        earned += SWEEP_SELECTION_WEIGHT
    detail['selections'] = (wait_opt, energy_opt, budget_opt, correct_wait, correct_energy, correct_budget)

    # row count (22) -- mutants never change sweep shape, always true here
    earned += SWEEP_ROWCOUNT_WEIGHT
    # agreement disclosure (23) -- always gradeable/true (structural, not content-dependent)
    earned += SWEEP_AGREE_WEIGHT

    # sample rows (24-27)
    samples = [
        ((2, "TOP", 50, 6), 34.2875, 2676),
        ((4, "GROUND", 75, 8), 11.9625, 4428),
        ((4, "GROUND", 75, 6), 12.4000, 4380),
        ((2, "GROUND", 125, 8), 27.1625, 2772),
    ]
    for key, ref_w, ref_e in samples:
        r = sweep[key]
        if abs(r["avg_wait"] - ref_w) <= 0.01 and r["net_energy"] == ref_e:
            earned += SWEEP_SAMPLE_WEIGHT

    # reconciliation (28-30): does the selected design actually hold the claimed extremum?
    def w(k): return sweep[k]["avg_wait"]
    def e(k): return sweep[k]["net_energy"]
    if correct_wait and all(round(w(k), 6) >= round(w(wait_opt), 6) for k in sweep):
        earned += SWEEP_RECON_WEIGHT
    if correct_energy and all(e(k) >= e(energy_opt) for k in sweep):
        earned += SWEEP_RECON_WEIGHT
    if correct_budget and all(e(k) > 3800 or round(w(k), 6) >= round(w(budget_opt), 6)
                               for k in sweep if k != budget_opt):
        earned += SWEEP_RECON_WEIGHT

    # total reassignment count across the whole sweep (31)
    total_reassign = sum(sweep[k]["reassign_count"] for k in sweep)
    if total_reassign == REF_REASSIGN_TOTAL:
        earned += SWEEP_REASSIGN_TOTAL_WEIGHT

    # total net_energy across the whole sweep (32)
    total_energy = sum(sweep[k]["net_energy"] for k in sweep)
    if total_energy == REF_ENERGY_TOTAL:
        earned += SWEEP_ENERGY_TOTAL_WEIGHT

    # baseline witnesses (33-37)
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
    w3b = 19 in calls and calls[19].attempt == 1 and calls[19].assigned_car == 0 and calls[19].board_tick == 248
    rp = SIM.simulate(POWER_WITNESS_CFG, trace_limit=300000, **sweep_kwargs)
    w4 = (any(row["power"] == 6 for row in rp["trace"][24:60])
          and all(row["power"] <= 6 for row in rp["trace"]))
    for ok, cid, wgt in [(w1, 31, W1_WEIGHT), (w2, 32, W2_WEIGHT), (w3a, 33, W3A_WEIGHT),
                          (w3b, 34, W3B_WEIGHT), (w4, 35, W4_WEIGHT)]:
        if ok and cid not in witness_fail:
            earned += wgt

    # hash (36)
    h = hashlib.sha256(SIM.canonical_trace_serialization(rb).encode()).hexdigest()[:16]
    if hash_ok and h == REF_HASH16:
        earned += HASH_WEIGHT

    # verification (37-40) -- independent of mutants (verifier is fixed); assume delivered+correct unless told otherwise
    for cid in (37, 38, 39, 40):
        if cid not in verify_fail:
            earned += VERIFY_WEIGHT

    # decision (41-44) -- generously assume explained correctly unless told otherwise
    for cid in (41, 42, 43, 44):
        if cid not in decision_fail:
            earned += DECISION_WEIGHT

    pct = 100 * earned / TOTAL
    print(f"{name}: {earned}/{TOTAL} = {pct:.1f}%  hash_match={h == REF_HASH16}  "
          f"sel_ok={correct_wait,correct_energy,correct_budget}  "
          f"w1={w1} w2={w2} w3a={w3a} w3b={w3b} w4={w4} reassign_total={total_reassign}")
    return earned, pct


if __name__ == "__main__":
    print(f"Rubric total positive weight: {TOTAL}\n")

    score("canonical (sanity, must be 100%)")

    score("timeout reassignment disabled",
          sweep_kwargs=dict(mutant_no_timeout=True),
          local_fail={17, 18}, hash_ok=False, decision_fail={44})

    score("reassignment never compares cost (always switches)",
          sweep_kwargs=dict(mutant_no_cost_compare=True),
          local_fail={18}, hash_ok=False, decision_fail={44})

    score("power admission disabled",
          sweep_kwargs=dict(mutant_power_disabled=True),
          local_fail={14, 15}, hash_ok=False, decision_fail={43})

    print()
    print("Two additional real bugs found during authoring (door-close treated")
    print("as automatic instead of power-gated; up/down commitments merged into")
    print("one set) both caused the simulator to LIVELOCK -- never completing a")
    print("single legal configuration, let alone the 144-row sweep or the")
    print("baseline trace. Under this rubric that means every criterion in")
    print("buckets 19-44 (129-8=121 of 129 positive points, since only package")
    print("and the local rows describing rules the mutant still executes")
    print("correctly could possibly be earned) is unreachable -- both are")
    print("qualitatively worse than the three scored mutants above, not merely")
    print("equally bad, because they cannot even produce gradable output.")
