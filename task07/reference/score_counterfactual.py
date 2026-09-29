#!/usr/bin/env python3
"""Programmatic score-topology counterfactual scorer for CISTERN-7's rubric.
Criterion numbering matches platform/rubric.md exactly (48 criteria,
<=10 weight, <=301 chars each). A fresh file for this task -- ATRIUM-9's
score_counterfactual.py was domain-specific (elevator config tuples, its
own mutant set) and was not reused, per the playbook's own guidance.

Numbering:
  1-2    package
  3-12   local semantics
  13-19  integrated sweep (3 selections + disclosure + 3 samples)
  20-32  whole-sweep aggregate totals (3 grand totals + 10 partial sums) --
         the main discriminating bloc, wrong under every mutant tested.
  33-37  baseline-trace witnesses + hash
  38-40  independent verification + decision/causal reconciliation
  41-47  negative criteria (rotation-advance, min-run, TOU, pump-curve,
         verifier-wrap, shortened-run, day-type-as-free-dimension)
  48     negative trap (embedding precomputed values)
"""
import cistern_sim as SIM

TOL_E = 0.5
TOL_P = 0.05
TOL_I = 0.05

PACKAGE_WEIGHT = 3  # criteria 1-2, always earned unless a mutant breaks execution

LOCAL_WEIGHT = {
    3: 2,   # hydrograph + storm formula
    4: 2,   # pump-curve interpolation
    5: 2,   # duty-roster exclusion
    6: 2,   # LAG1/LAG2 ascending-ID assignment
    7: 2,   # per-role start/stop elevations
    8: 2,   # MIN_RUN compliance (positive: continues running)
    9: 2,   # MIN_OFF compliance
    10: 2,  # rotation-policy SELECTION mechanism (not the advance-timing rule)
    11: 2,  # overflow/mass-balance accounting
    12: 3,  # TOU tariff costing formula
}

SWEEP_SELECTION_WEIGHT = 2   # criteria 13-15
SWEEP_AGREE_WEIGHT = 1       # criterion 16
SWEEP_SAMPLE_WEIGHT = 4      # criteria 17-19

GRAND_E_WEIGHT = 10    # criterion 20
GRAND_P_WEIGHT = 10    # criterion 21
GRAND_I_WEIGHT = 10    # criterion 22
PARTIAL_WEIGHT = 10    # criteria 23-32 (each)

W33_WEIGHT = 10  # rotation-sequence witness
W34_WEIGHT = 10  # MIN_RUN-override witness
W35_WEIGHT = 8   # peak-level witness
W36_WEIGHT = 10  # duty=1-always-infeasible witness
HASH_WEIGHT = 10  # criterion 37

VERIFY_WEIGHT = 3           # criterion 38
DECISION_MAIN_WEIGHT = 8    # criterion 39
DECISION_ROTATION_WEIGHT = 2  # criterion 40

NEG_ROTATION_WEIGHT = 4     # criterion 41
NEG_MIN_RUN_WEIGHT = 5      # criterion 42
NEG_TARIFF_WEIGHT = 4       # criterion 43
NEG_PUMP_CURVE_WEIGHT = 4   # criterion 44
NEG_VERIFIER_WRAP_WEIGHT = 4  # criterion 45
NEG_SHORTENED_RUN_WEIGHT = 5  # criterion 46
NEG_DAY_TYPE_FREE_WEIGHT = 4  # criterion 47
NEG_WEIGHT = {41: NEG_ROTATION_WEIGHT, 42: NEG_MIN_RUN_WEIGHT,
              43: NEG_TARIFF_WEIGHT, 44: NEG_PUMP_CURVE_WEIGHT,
              45: NEG_VERIFIER_WRAP_WEIGHT, 46: NEG_SHORTENED_RUN_WEIGHT,
              47: NEG_DAY_TYPE_FREE_WEIGHT}

TOTAL = (PACKAGE_WEIGHT + sum(LOCAL_WEIGHT.values())
         + SWEEP_SELECTION_WEIGHT * 3 + SWEEP_AGREE_WEIGHT
         + SWEEP_SAMPLE_WEIGHT * 3
         + GRAND_E_WEIGHT + GRAND_P_WEIGHT + GRAND_I_WEIGHT
         + PARTIAL_WEIGHT * 10
         + W33_WEIGHT + W34_WEIGHT + W35_WEIGHT + W36_WEIGHT + HASH_WEIGHT
         + VERIFY_WEIGHT + DECISION_MAIN_WEIGHT + DECISION_ROTATION_WEIGHT)

BASELINE_POLICY = {"duty_pump_count": 3, "rotation_policy": "STRICT_ALTERNATE",
                    "deadband": "TIGHT", "min_run_time": "LONG"}
REF_HASH16 = "6a880d5a0cb10b6c"

# reference values for the three selections and their own sample rows
REF_ENERGY_OPT = (2, "FIXED_LEAD", "WIDE", "LONG")
REF_RELIAB_OPT = (3, "FIXED_LEAD", "TIGHT", "LONG")
REF_WEAR_OPT = (2, "RUNTIME_BALANCED", "TIGHT", "SHORT")

REF_GRAND_E = 5024.80
REF_GRAND_P = 187.4774
REF_GRAND_I = 46.3073

REF_PARTIALS = [
    ("duty==1", lambda k: k[0] == 1, 1506.27, 75.60, "EP"),
    ("duty==3", lambda k: k[0] == 3, 1795.75, 54.891, "EP"),
    ("deadband==TIGHT", lambda k: k[2] == "TIGHT", 1706.81, 14.0612, "EI"),
    ("deadband==WIDE", lambda k: k[2] == "WIDE", 1658.70, 16.1731, "EI"),
    ("rotation==FIXED_LEAD", lambda k: k[1] == "FIXED_LEAD", 1651.735, 16.7808, "EI"),
    ("rotation==STRICT_ALTERNATE", lambda k: k[1] == "STRICT_ALTERNATE", 1684.445, 14.8384, "EI"),
    ("rotation==RUNTIME_BALANCED", lambda k: k[1] == "RUNTIME_BALANCED", 1688.62, 14.688, "EI"),
    ("min_run==SHORT", lambda k: k[3] == "SHORT", 2503.12, 93.7619, "EP"),
    ("duty==1 & deadband==WIDE", lambda k: k[0] == 1 and k[2] == "WIDE", 499.68, 0, "EF"),
    ("duty==3 & rotation==STRICT_ALTERNATE", lambda k: k[0] == 3 and k[1] == "STRICT_ALTERNATE", 608.095, 4.4443, "EI"),
]


def run_sweep(**mutant_kwargs):
    sweep = {}
    for pc in SIM.all_policy_configs():
        sweep[SIM.policy_key(pc)] = SIM.run_both_days(pc, **mutant_kwargs)
    return sweep


def score(name, mutant_kwargs=None, local_fail=(), decision_fail=(),
          negative_fail=(), verify_fail=False, hash_ok=True):
    mutant_kwargs = mutant_kwargs or {}
    sweep = run_sweep(**mutant_kwargs)
    earned = 0

    earned += PACKAGE_WEIGHT

    for cid, wgt in LOCAL_WEIGHT.items():
        if cid not in local_fail:
            earned += wgt

    energy_opt, reliab_opt, wear_opt = SIM.selections(sweep)
    correct_energy = energy_opt == REF_ENERGY_OPT
    correct_reliab = reliab_opt == REF_RELIAB_OPT
    correct_wear = wear_opt == REF_WEAR_OPT
    for ok in (correct_energy, correct_reliab, correct_wear):
        if ok:
            earned += SWEEP_SELECTION_WEIGHT

    earned += SWEEP_AGREE_WEIGHT  # disclosure itself is always reportable

    samples = [
        ((2, "FIXED_LEAD", "WIDE", "LONG"), "WET", 47.93, 0.0, 3.5474),
        ((3, "FIXED_LEAD", "TIGHT", "LONG"), "DRY", 48.22, 0.0, 1.8154),
        ((2, "RUNTIME_BALANCED", "TIGHT", "SHORT"), "WET", 49.46, 0.0, 2.8625),
    ]
    for key, day, ref_e, ref_ov, ref_p in samples:
        d, w = sweep[key]
        r = d if day == "DRY" else w
        ok = (abs(r["total_energy_cost"] - ref_e) <= TOL_E
              and r["overflow_volume"] == ref_ov
              and abs(r["peak_level"] - ref_p) <= TOL_P)
        if ok:
            earned += SWEEP_SAMPLE_WEIGHT

    grand_e = sum(SIM.combined_energy(*v) for v in sweep.values())
    grand_p = sum(SIM.worst_peak(*v) for v in sweep.values())
    grand_i = sum(SIM.worst_imbalance(*v) for v in sweep.values())
    if abs(grand_e - REF_GRAND_E) <= TOL_E:
        earned += GRAND_E_WEIGHT
    if abs(grand_p - REF_GRAND_P) <= TOL_P:
        earned += GRAND_P_WEIGHT
    if abs(grand_i - REF_GRAND_I) <= TOL_I:
        earned += GRAND_I_WEIGHT

    partial_ok = []
    for label, filt, ref_a, ref_b, kind in REF_PARTIALS:
        keys = [k for k in sweep if filt(k)]
        a = sum(SIM.combined_energy(*sweep[k]) for k in keys)
        if kind == "EP":
            b = sum(SIM.worst_peak(*sweep[k]) for k in keys)
            ok = abs(a - ref_a) <= TOL_E and abs(b - ref_b) <= TOL_P
        elif kind == "EI":
            b = sum(SIM.worst_imbalance(*sweep[k]) for k in keys)
            ok = abs(a - ref_a) <= TOL_E and abs(b - ref_b) <= TOL_I
        else:  # EF: energy + feasible count
            b = sum(1 for k in keys if SIM.is_feasible(*sweep[k]))
            ok = abs(a - ref_a) <= TOL_E and b == ref_b
        partial_ok.append(ok)
        if ok:
            earned += PARTIAL_WEIGHT

    rb = SIM.simulate(dict(BASELINE_POLICY, day_type="WET"), **mutant_kwargs)

    # w33: rotation sequence witness (two complete A,B,C cycles)
    ref_seq = [(25, 0), (123, 1), (211, 2), (248, 0), (280, 1), (308, 2)]
    prev_lead = None
    seq = []
    for row in rb["trace"]:
        if row["lead"] is not None and prev_lead is None:
            seq.append((row["t"], row["lead"]))
        prev_lead = row["lead"]
    w33 = seq[:6] == ref_seq
    if w33:
        earned += W33_WEIGHT

    # w34: MIN_RUN-override witness (pump A starts t=25, stops exactly t=40
    # -- check the specific event PAIR occurs anywhere in the trace, since
    # pump A starts/stops many times across the day).
    prev_on = set()
    open_start = {}
    w34 = False
    for row in rb["trace"]:
        on = set(row["running"])
        for p in on - prev_on:
            open_start[p] = row["t"]
        for p in prev_on - on:
            if p == 0 and open_start.get(0) == 25 and row["t"] == 40:
                w34 = True
        prev_on = on
    if w34:
        earned += W34_WEIGHT

    # w35: peak level witness
    peak_row = max(rb["trace"], key=lambda r: r["level"])
    w35 = peak_row["t"] == 358 and abs(peak_row["level"] - 2.4336) <= 0.005
    if w35:
        earned += W35_WEIGHT

    # w36: duty==1 always infeasible on WET; duty in {2,3} always feasible
    d1_bad = all(not SIM.is_feasible(*sweep[k]) for k in sweep if k[0] == 1)
    d23_good = all(SIM.is_feasible(*sweep[k]) for k in sweep if k[0] in (2, 3))
    w36 = d1_bad and d23_good
    if w36:
        earned += W36_WEIGHT

    h = SIM.canonical_trace_serialization(dict(BASELINE_POLICY, day_type="WET"), rb)
    import hashlib
    h16 = hashlib.sha256(h.encode()).hexdigest()[:16]
    if hash_ok and h16 == REF_HASH16:
        earned += HASH_WEIGHT

    if not verify_fail:
        earned += VERIFY_WEIGHT
    if 39 not in decision_fail:
        earned += DECISION_MAIN_WEIGHT
    if 40 not in decision_fail:
        earned += DECISION_ROTATION_WEIGHT

    for cid in negative_fail:
        earned -= NEG_WEIGHT[cid]

    pct = 100 * earned / TOTAL
    print(f"{name}: {earned}/{TOTAL} = {pct:.1f}%  hash_match={h16 == REF_HASH16}  "
          f"sel_ok={correct_energy, correct_reliab, correct_wear}  "
          f"w33={w33} w34={w34} w35={w35} w36={w36}  "
          f"partials_ok={sum(partial_ok)}/10  "
          f"grand_e={grand_e:.2f} grand_p={grand_p:.2f} grand_i={grand_i:.3f}")
    return earned, pct


if __name__ == "__main__":
    print(f"Rubric total positive weight: {TOTAL}\n")

    score("canonical (sanity, must be 100%)")

    score("rotation advances every tick instead of on genuine LEAD-START",
          mutant_kwargs=dict(mutant_rotation_every_tick=True),
          hash_ok=False, decision_fail={40}, negative_fail={41})

    score("minimum-run timer ignored",
          mutant_kwargs=dict(mutant_no_min_run=True),
          local_fail={8}, hash_ok=False, decision_fail={39},
          negative_fail={42})

    score("flat energy tariff (TOU ignored)",
          mutant_kwargs=dict(mutant_flat_tariff=True),
          local_fail={12}, hash_ok=True, decision_fail={39},
          negative_fail={43})

    score("flat pump curve (level-dependence ignored)",
          mutant_kwargs=dict(mutant_flat_pump_curve=True),
          local_fail={4}, hash_ok=False, decision_fail={39},
          negative_fail={44})
