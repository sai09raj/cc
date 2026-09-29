#!/usr/bin/env python3
"""Programmatic score-topology counterfactual scorer for ATRIUM-9's rubric.
Criterion numbering matches platform/rubric.md exactly (61 criteria, every
weight capped at 10 -- the platform's per-criterion maximum):
  1-3    package
  4-18   local semantics
  19-30  integrated sweep (selections, samples, reconciliation)
  31-41  whole-sweep aggregate totals (3 grand totals + 8 partial sums) --
         each of these eleven is wrong under ALL THREE tested mutants, so
         together they are the rubric's main discriminating bloc, since no
         single criterion can carry outsized weight under the 10-point cap.
  42-51  baseline-trace witnesses + hash
  52-55  independent verification
  56-60  decision/causal reconciliation
  61     negative trap
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

SWEEP_REASSIGN_TOTAL_WEIGHT = 10   # criterion 31
REF_REASSIGN_TOTAL = 43
SWEEP_ENERGY_TOTAL_WEIGHT = 10     # criterion 32
REF_ENERGY_TOTAL = 547080
SWEEP_WAIT_TOTAL_WEIGHT = 10       # criterion 33
REF_WAIT_TOTAL = 2739.8125

# criteria 34-41: (label, filter-on-config-tuple, ref avg_wait, ref net_energy)
PARTIAL_SUMS = [
    ("active_cars==4", lambda k: k[0] == 4, 595.6625, 222024),
    ("zoning==GROUND", lambda k: k[1] == "GROUND", 884.4875, 180000),
    ("zoning==TOP", lambda k: k[1] == "TOP", 1071.15, 183072),
    ("wait_timeout==50", lambda k: k[2] == 50, 693.65, 136440),
    ("wait_timeout==75", lambda k: k[2] == 75, 682.25, 136464),
    ("power_budget==6", lambda k: k[3] == 6, 687.8875, 134664),
    ("active_cars==4 & zoning==GROUND", lambda k: k[0] == 4 and k[1] == "GROUND", 191.7875, 73248),
    ("active_cars==4 & zoning==TOP", lambda k: k[0] == 4 and k[1] == "TOP", 229.05, 75648),
]
PARTIAL_SUM_WEIGHT = 10  # each, criteria 34-41

W1_WEIGHT = 9    # criterion 42
W2_WEIGHT = 9    # criterion 43
W3A_WEIGHT = 10  # criterion 44
W3B_WEIGHT = 10  # criterion 45
W4_WEIGHT = 10   # criterion 46
W5_WEIGHT = 10   # criterion 47: gidx=26 board_tick
W6_WEIGHT = 10   # criterion 48: gidx=27 board_tick
PW1_CFG = dict(active_cars=4, zoning="SPLIT", wait_timeout=50, capacity=6, power_budget=6)
PW2_CFG = dict(active_cars=4, zoning="TOP", wait_timeout=50, capacity=6, power_budget=6)
PW1_WEIGHT = 10  # criterion 49
PW2_WEIGHT = 10  # criterion 50
HASH_WEIGHT = 10  # criterion 51

VERIFY_WEIGHT = 1             # criteria 52-55
DECISION_WEIGHT = 2           # criteria 56-60

TOTAL = (sum(PACKAGE_WEIGHT) + sum(LOCAL_WEIGHT.values())
         + SWEEP_SELECTION_WEIGHT * 3 + SWEEP_ROWCOUNT_WEIGHT + SWEEP_AGREE_WEIGHT
         + SWEEP_SAMPLE_WEIGHT * 4 + SWEEP_RECON_WEIGHT * 3
         + SWEEP_REASSIGN_TOTAL_WEIGHT + SWEEP_ENERGY_TOTAL_WEIGHT + SWEEP_WAIT_TOTAL_WEIGHT
         + PARTIAL_SUM_WEIGHT * len(PARTIAL_SUMS)
         + W1_WEIGHT + W2_WEIGHT + W3A_WEIGHT + W3B_WEIGHT + W4_WEIGHT
         + W5_WEIGHT + W6_WEIGHT + PW1_WEIGHT + PW2_WEIGHT + HASH_WEIGHT
         + VERIFY_WEIGHT * 4 + DECISION_WEIGHT * 5)

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
          package_fail=(), witness_fail=(), hash_ok=True):
    sweep_kwargs = sweep_kwargs or {}
    sweep = run_sweep(**sweep_kwargs)

    earned = 0

    for i, wgt in enumerate(PACKAGE_WEIGHT, start=1):
        if i not in package_fail:
            earned += wgt

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

    earned += SWEEP_ROWCOUNT_WEIGHT
    earned += SWEEP_AGREE_WEIGHT

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

    def w(k): return sweep[k]["avg_wait"]
    def e(k): return sweep[k]["net_energy"]
    if correct_wait and all(round(w(k), 6) >= round(w(wait_opt), 6) for k in sweep):
        earned += SWEEP_RECON_WEIGHT
    if correct_energy and all(e(k) >= e(energy_opt) for k in sweep):
        earned += SWEEP_RECON_WEIGHT
    if correct_budget and all(e(k) > 3800 or round(w(k), 6) >= round(w(budget_opt), 6)
                               for k in sweep if k != budget_opt):
        earned += SWEEP_RECON_WEIGHT

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

    for ok, cid, wgt in [(w1, 42, W1_WEIGHT), (w2, 43, W2_WEIGHT), (w3a, 44, W3A_WEIGHT),
                          (w3b, 45, W3B_WEIGHT), (w4, 46, W4_WEIGHT),
                          (w5, 47, W5_WEIGHT), (w6, 48, W6_WEIGHT),
                          (pw1, 49, PW1_WEIGHT), (pw2, 50, PW2_WEIGHT)]:
        if ok and cid not in witness_fail:
            earned += wgt

    h = hashlib.sha256(SIM.canonical_trace_serialization(rb).encode()).hexdigest()[:16]
    if hash_ok and h == REF_HASH16:
        earned += HASH_WEIGHT

    for cid in (52, 53, 54, 55):
        if cid not in verify_fail:
            earned += VERIFY_WEIGHT

    for cid in (56, 57, 58, 59, 60):
        if cid not in decision_fail:
            earned += DECISION_WEIGHT

    pct = 100 * earned / TOTAL
    print(f"{name}: {earned}/{TOTAL} = {pct:.1f}%  hash_match={h == REF_HASH16}  "
          f"sel_ok={correct_wait,correct_energy,correct_budget}  "
          f"w1={w1} w2={w2} w3a={w3a} w3b={w3b} w4={w4} w5={w5} w6={w6} pw1={pw1} pw2={pw2} "
          f"reassign_total={total_reassign} partial_sums_ok={sum(partial_ok)}/{len(partial_ok)}")
    return earned, pct


if __name__ == "__main__":
    print(f"Rubric total positive weight: {TOTAL}\n")

    score("canonical (sanity, must be 100%)")

    score("timeout reassignment disabled",
          sweep_kwargs=dict(mutant_no_timeout=True),
          local_fail={17, 18}, hash_ok=False, decision_fail={57})

    score("reassignment never compares cost (always switches)",
          sweep_kwargs=dict(mutant_no_cost_compare=True),
          local_fail={18}, hash_ok=False, decision_fail={57})

    score("power admission disabled",
          sweep_kwargs=dict(mutant_power_disabled=True),
          local_fail={14, 15}, hash_ok=False, decision_fail={56})

    print()
    print("Two additional real bugs found during authoring (door-close treated")
    print("as automatic instead of power-gated; up/down commitments merged into")
    print("one set) both caused the simulator to LIVELOCK -- never completing a")
    print("single legal configuration, let alone the 144-row sweep or the")
    print("baseline trace. Both are qualitatively worse than the three scored")
    print("mutants above, not merely equally bad, because they cannot even")
    print("produce gradable output.")
