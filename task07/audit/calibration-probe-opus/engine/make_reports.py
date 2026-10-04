#!/usr/bin/env python3
"""Assembles the decision file, certification evidence and a Markdown sweep table from the
engine outputs (sweep_table.json, decision_engine.json, baseline_certificate.json) and the
independent verifier's report (verifier_report.json).  Copies numbers; computes nothing new."""
import json, os, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
J = lambda f: json.load(open(os.path.join(OUT, f)))
rows, dec, cert, ver = J("sweep_table.json"), J("decision_engine.json"), J("baseline_certificate.json"), J("verifier_report.json")

agree_engine_verifier = (dec["recovery_optimal"] == ver["recovery_optimal"] and dec["overhead_optimal"] == ver["overhead_optimal"]
                         and all(dec["per_setting"][s]["crash_to_new_leader_ticks"] == ver["per_setting"][s]["crash_to_new_leader_ticks"]
                                 and dec["per_setting"][s]["total_msgs_5_scenarios"] == ver["per_setting"][s]["total_msgs_5_scenarios"] for s in dec["per_setting"]))
decision = {
    "feasibility": {s: {"engine_selfcheck": dec["per_setting"][s]["feasible_engine_selfcheck"],
                        "independent_verifier": ver["per_setting"][s]["feasible"]} for s in dec["per_setting"]},
    "criteria": {s: {"crash_to_new_leader_ticks(CRASH_RECOVER)": dec["per_setting"][s]["crash_to_new_leader_ticks"],
                     "total_msgs_sent_all_5_scenarios": dec["per_setting"][s]["total_msgs_5_scenarios"]} for s in dec["per_setting"]},
    "recovery_optimal": dec["recovery_optimal"],
    "overhead_optimal": dec["overhead_optimal"],
    "selections_agree": dec["selections_agree"],
    "disclosure": ("The two selections DIVERGE: recovery-optimal=%s, overhead-optimal=%s." % (dec["recovery_optimal"], dec["overhead_optimal"]))
                  if not dec["selections_agree"] else "The two selections AGREE.",
    "engine_and_verifier_agree_on_selections_and_criteria": agree_engine_verifier,
    "tie_break": "none needed (all criteria values distinct); rule would be setting order SHORT<MEDIUM<LONG",
}
json.dump(decision, open(os.path.join(OUT, "decision.json"), "w"), indent=2)

evidence = {
    "baseline": "election_timeout=MEDIUM, scenario=PARTITION",
    "trace_file": "baseline_trace_MEDIUM_PARTITION.txt (exact hashed bytes: header + 2400 tick lines, '\\n'-joined, no trailing newline)",
    "engine_sha256": cert["sha256"], "engine_certificate_first16": cert["certificate_first16"],
    "verifier_sha256": ver["baseline"]["sha256"], "verifier_certificate_first16": ver["baseline"]["certificate_first16"],
    "verifier_rederived_trace_byte_identical_to_engine_file": ver["baseline"]["engine_trace_file_byte_identical"],
    "verifier_accepts_original_engine_certificate": ver["mutations"]["original"]["accepted"],
    "mutation_M1_vote_to_lower_term_candidate": {k: ver["mutations"]["M1_vote_to_lower_term_candidate"][k] for k in ("injected", "accepted", "rule_checks", "reasons")},
    "mutation_M2_leader_overwrites_committed_entry": {k: ver["mutations"]["M2_leader_overwrites_committed_entry"][k] for k in ("injected", "accepted", "rule_checks", "reasons")},
    "all_15_engine_certificates_accepted": ver["all_engine_certificates_accepted"],
    "all_15_rederived_runs_safe": ver["all_runs_safe"],
    "sweep_table_crosscheck": ver.get("sweep_table_crosscheck"),
}
json.dump(evidence, open(os.path.join(OUT, "certification_evidence.json"), "w"), indent=2)

cols = ["setting", "scenario", "anchor_tick", "fault_window", "leaders_seq", "final_max_term", "prevote_rounds",
        "real_elections", "msgs_sent_total", "msgs_dropped", "cmds_appended", "commit_index_max_final",
        "crash_to_new_leader_ticks", "trace_sha256_16"]
vr = {(r["setting"], r["scenario"]): r for r in ver["runs"]}
with open(os.path.join(OUT, "sweep_table.md"), "w") as f:
    f.write("| " + " | ".join(cols + ["verifier ES/LM/LC"]) + " |\n|" + "---|" * (len(cols) + 1) + "\n")
    for r in rows:
        v = vr[(r["setting"], r["scenario"])]
        f.write("| " + " | ".join(str(r.get(c, "")) for c in cols) + " | " +
                "/".join("ok" if v[k] else "FAIL" for k in ("election_safety", "log_matching", "leader_completeness")) + " |\n")
print(json.dumps(decision, indent=2))
