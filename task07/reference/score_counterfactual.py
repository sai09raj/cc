#!/usr/bin/env python3
"""Programmatic score-topology counterfactual scorer for QUORUM-7's rubric.
Criterion numbering matches platform/rubric.md exactly (43 criteria,
<=10 weight, <=301 chars each). A fresh file for this task -- neither
ATRIUM-9's nor CISTERN-7's score_counterfactual.py is reused, per the
playbook's own guidance (each is domain-specific).

Numbering:
  1-2    package
  3-12   local semantics
  13-18  integrated sweep (2 selections + disclosure + 3 samples)
  19-28  whole-sweep aggregate totals (2 grand totals + 8 partial sums) --
         the main discriminating bloc, wrong under every mutant tested.
  29-33  baseline-trace witnesses + hash
  34-36  independent verification + decision/causal reconciliation
  37-42  negative criteria (no-prevote, wrong-quorum, commit-any-term,
         ignore-replication-tracking, verifier-wrap, shortened-run)
  43     negative trap (embedding precomputed values)
"""
import quorum_sim as SIM
import quorum_verify as VER
import scenarios as SC

TOL_MSG = 20
TOL_COMMIT = 1

PACKAGE_WEIGHT = 3  # criteria 1-2

LOCAL_WEIGHT = {
    3: 2,   # pre-vote gating before real election
    4: 2,   # election_elapsed reset rule (valid triggers only)
    5: 3,   # vote-granting: term/voted_for/log-completeness + tie-break
    6: 2,   # 3-of-5 quorum used consistently
    7: 4,   # per-follower next_index/match_index + bounded batch K=4
    8: 3,   # commit-advancement current-term-only rule
    9: 2,   # crash persistence semantics
    10: 2,  # partition/crash network-model semantics
    11: 2,  # client command broadcast + leader-only-append
    12: 2,  # heartbeat interval + immediate-send-on-new-entry
}

SEL_WEIGHT = 3        # criteria 13-14
AGREE_WEIGHT = 1      # criterion 15
SAMPLE_WEIGHT = 6     # criteria 16-18

GRAND_MSG_WEIGHT = 10   # criterion 19
GRAND_COMMIT_WEIGHT = 10  # criterion 20
PARTIAL_WEIGHT = 10     # criteria 21-28 (each)

W29_WEIGHT = 10  # crash-recovery latency witness
W30_WEIGHT = 8   # no-dual-leader witness
W31_WEIGHT = 10  # isolation term-unchanged witness
W32_WEIGHT = 2   # final logs identical witness
HASH_WEIGHT = 10  # criterion 33

VERIFY_WEIGHT = 3           # criterion 34
DECISION_MAIN_WEIGHT = 8    # criterion 35
DECISION_PREVOTE_WEIGHT = 2  # criterion 36

NEG_NO_PREVOTE_WEIGHT = 4       # criterion 37
NEG_WRONG_QUORUM_WEIGHT = 5     # criterion 38
NEG_COMMIT_ANY_TERM_WEIGHT = 4  # criterion 39
NEG_IGNORE_TRACKING_WEIGHT = 6  # criterion 40
NEG_VERIFIER_WRAP_WEIGHT = 4    # criterion 41
NEG_SHORTENED_RUN_WEIGHT = 5    # criterion 42
NEG_WEIGHT = {37: NEG_NO_PREVOTE_WEIGHT, 38: NEG_WRONG_QUORUM_WEIGHT,
              39: NEG_COMMIT_ANY_TERM_WEIGHT, 40: NEG_IGNORE_TRACKING_WEIGHT,
              41: NEG_VERIFIER_WRAP_WEIGHT, 42: NEG_SHORTENED_RUN_WEIGHT}

TOTAL = (PACKAGE_WEIGHT + sum(LOCAL_WEIGHT.values())
         + SEL_WEIGHT * 2 + AGREE_WEIGHT + SAMPLE_WEIGHT * 3
         + GRAND_MSG_WEIGHT + GRAND_COMMIT_WEIGHT + PARTIAL_WEIGHT * 8
         + W29_WEIGHT + W30_WEIGHT + W31_WEIGHT + W32_WEIGHT + HASH_WEIGHT
         + VERIFY_WEIGHT + DECISION_MAIN_WEIGHT + DECISION_PREVOTE_WEIGHT)

TIMEOUTS = ["SHORT", "MEDIUM", "LONG"]
SCENARIO_NAMES = ["CLEAN", "PARTITION", "CRASH_RECOVER", "MESSAGE_LOSS", "COMPETING_CANDIDATES"]

REF_HASH16 = "3243b745aaf9e7e2"
REF_RECOVERY_SETTING, REF_RECOVERY_TIME = "SHORT", 172
REF_OVERHEAD_SETTING, REF_OVERHEAD_MSGS = "LONG", 7355

REF_SAMPLES = [
    ("SHORT", "PARTITION", 1660, 5, 1),
    ("MEDIUM", "CLEAN", 1736, 5, 1),
    ("MEDIUM", "MESSAGE_LOSS", 1704, 5, 1),
]

REF_GRAND_MSG = 24027
REF_GRAND_COMMIT = 67

REF_PARTIALS = [
    ("timeout==SHORT", lambda t, s: t == "SHORT", 8573, 24),
    ("timeout==LONG", lambda t, s: t == "LONG", 7355, 19),
    ("timeout==MEDIUM", lambda t, s: t == "MEDIUM", 8099, 24),
    ("scenario==CLEAN", lambda t, s: s == "CLEAN", 5168, 14),
    ("scenario==PARTITION", lambda t, s: s == "PARTITION", 4692, 14),
    ("scenario==CRASH_RECOVER", lambda t, s: s == "CRASH_RECOVER", 4524, 11),
    ("scenario==MESSAGE_LOSS", lambda t, s: s == "MESSAGE_LOSS", 5063, 14),
    ("scenario==COMPETING_CANDIDATES", lambda t, s: s == "COMPETING_CANDIDATES", 4580, 14),
]

BASELINE_TIMEOUT, BASELINE_SCENARIO = "MEDIUM", "PARTITION"


def run_full_sweep(**mutant_kwargs):
    all_sc = SC.all_scenarios()
    sweep = {}
    for tname in TIMEOUTS:
        for sname in SCENARIO_NAMES:
            script, meta = all_sc[sname]
            r = SIM.run_scenario(tname, script, **mutant_kwargs)
            sweep[(tname, sname)] = (r, meta)
    return sweep, all_sc


def score(name, mutant_kwargs=None, local_fail=(), decision_fail=(),
          negative_fail=(), verify_fail=False, hash_ok=True):
    mutant_kwargs = mutant_kwargs or {}
    sweep, all_sc = run_full_sweep(**mutant_kwargs)
    earned = 0

    earned += PACKAGE_WEIGHT
    for cid, wgt in LOCAL_WEIGHT.items():
        if cid not in local_fail:
            earned += wgt

    def msgs(t, s):
        return sweep[(t, s)][0]["msg_count"]

    def max_commit(t, s):
        return max(f["commit_index"] for f in sweep[(t, s)][0]["final"].values())

    def max_term(t, s):
        return max(f["term"] for f in sweep[(t, s)][0]["final"].values())

    def leader(t, s):
        return [nid for nid, f in sweep[(t, s)][0]["final"].items() if f["role"] == "LEADER"]

    # selections
    recovery_times = {}
    for tname in TIMEOUTS:
        script, meta = all_sc["CRASH_RECOVER"]
        r, _ = sweep[(tname, "CRASH_RECOVER")]
        start = meta["start"]
        rt = None
        for row in r["trace"][start:]:
            for nid, info in row["nodes"].items():
                if info["role"] == "LEADER" and info["term"] > r["trace"][start]["nodes"][nid]["term"]:
                    rt = row["t"] - start
                    break
            if rt is not None:
                break
        recovery_times[tname] = rt if rt is not None else 10**9
    recovery_opt = min(TIMEOUTS, key=lambda t: recovery_times[t])
    correct_recovery = (recovery_opt == REF_RECOVERY_SETTING and
                         abs(recovery_times[recovery_opt] - REF_RECOVERY_TIME) <= 2)
    if correct_recovery:
        earned += SEL_WEIGHT

    total_msgs_by_setting = {t: sum(msgs(t, s) for s in SCENARIO_NAMES) for t in TIMEOUTS}
    overhead_opt = min(TIMEOUTS, key=lambda t: total_msgs_by_setting[t])
    correct_overhead = (overhead_opt == REF_OVERHEAD_SETTING and
                         abs(total_msgs_by_setting[overhead_opt] - REF_OVERHEAD_MSGS) <= TOL_MSG)
    if correct_overhead:
        earned += SEL_WEIGHT

    earned += AGREE_WEIGHT

    for tname, sname, ref_m, ref_c, ref_term in REF_SAMPLES:
        ok = (abs(msgs(tname, sname) - ref_m) <= 10 and max_commit(tname, sname) == ref_c
              and max_term(tname, sname) == ref_term)
        if ok:
            earned += SAMPLE_WEIGHT

    grand_msg = sum(msgs(t, s) for t in TIMEOUTS for s in SCENARIO_NAMES)
    grand_commit = sum(max_commit(t, s) for t in TIMEOUTS for s in SCENARIO_NAMES)
    if abs(grand_msg - REF_GRAND_MSG) <= 50:
        earned += GRAND_MSG_WEIGHT
    if abs(grand_commit - REF_GRAND_COMMIT) <= 1:
        earned += GRAND_COMMIT_WEIGHT

    partial_ok = []
    for label, filt, ref_m, ref_c in REF_PARTIALS:
        m = sum(msgs(t, s) for t in TIMEOUTS for s in SCENARIO_NAMES if filt(t, s))
        c = sum(max_commit(t, s) for t in TIMEOUTS for s in SCENARIO_NAMES if filt(t, s))
        ok = abs(m - ref_m) <= TOL_MSG and abs(c - ref_c) <= TOL_COMMIT
        partial_ok.append(ok)
        if ok:
            earned += PARTIAL_WEIGHT

    rb, rb_meta = sweep[(BASELINE_TIMEOUT, BASELINE_SCENARIO)]

    # w29: crash-recovery latency witness (its own named scenario, not the baseline)
    cr_r, cr_meta = sweep[(BASELINE_TIMEOUT, "CRASH_RECOVER")]
    start = cr_meta["start"]
    w29 = False
    base_terms = {nid: info["term"] for nid, info in cr_r["trace"][start]["nodes"].items()}
    for row in cr_r["trace"][start:]:
        for nid, info in row["nodes"].items():
            if info["role"] == "LEADER" and info["term"] > base_terms[nid]:
                w29 = (row["t"] - start == 272)
                break
        if w29 or row["t"] - start > 400:
            break
    if w29:
        earned += W29_WEIGHT

    # w30: no dual leader ever, same term
    ok30, _ = VER.check_election_safety(rb["trace"])
    if ok30:
        earned += W30_WEIGHT

    # w31: isolated pair term stays 1 throughout COMPETING_CANDIDATES at baseline timeout
    comp_r, comp_meta = sweep[(BASELINE_TIMEOUT, "COMPETING_CANDIDATES")]
    cs, ce = comp_meta["start"], comp_meta["end"]
    w31 = all(comp_r["trace"][t]["nodes"][2]["term"] == 1 and
              comp_r["trace"][t]["nodes"][3]["term"] == 1
              for t in range(cs, min(ce, len(comp_r["trace"]))))
    if w31:
        earned += W31_WEIGHT

    # w32: final logs identical across all 5 nodes, commit_index=5
    final = rb["final"]
    logs = [f["log"] for f in final.values()]
    w32 = all(l == logs[0] for l in logs) and final[0]["commit_index"] == 5
    if w32:
        earned += W32_WEIGHT

    ser = SIM.canonical_trace_serialization(BASELINE_TIMEOUT, BASELINE_SCENARIO, rb)
    import hashlib
    h16 = hashlib.sha256(ser.encode()).hexdigest()[:16]
    if hash_ok and h16 == REF_HASH16:
        earned += HASH_WEIGHT

    if not verify_fail:
        earned += VERIFY_WEIGHT
    if 35 not in decision_fail:
        earned += DECISION_MAIN_WEIGHT
    if 36 not in decision_fail:
        earned += DECISION_PREVOTE_WEIGHT

    for cid in negative_fail:
        earned -= NEG_WEIGHT[cid]

    pct = 100 * earned / TOTAL
    print(f"{name}: {earned}/{TOTAL} = {pct:.1f}%  hash_match={h16 == REF_HASH16}  "
          f"recovery_ok={correct_recovery}  overhead_ok={correct_overhead}  "
          f"w29={w29} w30={ok30} w31={w31} w32={w32}  partials_ok={sum(partial_ok)}/8  "
          f"grand_msg={grand_msg} grand_commit={grand_commit}")
    return earned, pct


if __name__ == "__main__":
    print(f"Rubric total positive weight: {TOTAL}\n")

    score("canonical (sanity, must be 100%)")

    score("no pre-vote phase (elections directly on timeout)",
          mutant_kwargs=dict(mutant_no_prevote=True),
          local_fail={3}, hash_ok=False, decision_fail={36},
          negative_fail={37})

    score("wrong quorum size (2-of-5 instead of 3-of-5)",
          mutant_kwargs=dict(mutant_wrong_quorum=True),
          local_fail={6}, hash_ok=False, decision_fail={35, 36},
          negative_fail={38})

    score("ignores per-follower replication tracking",
          mutant_kwargs=dict(mutant_ignore_replication_tracking=True),
          local_fail={7}, hash_ok=False, decision_fail={35},
          negative_fail={40})
