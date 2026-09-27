#!/usr/bin/env python3
"""
Adversarial verifier experiments.

Takes a genuine, certified-feasible trace (D0's, by default) and deliberately
injects two classes of corruption to prove the certificate checker actually
*detects* infeasibility rather than rubber-stamping any input:

  1. NEGATIVE-START: force a lot's machine_start event to a time before its
     release_abs (and, separately, to a literally negative minute). The
     checker must flag a release-timing violation.

  2. ROUTE-COLLISION: force both robots onto node 4 (capacity 1) in the same
     minute, and separately force both robots to traverse the same edge in
     the same minute. The checker must flag node/edge-capacity violations.

Each experiment writes its corrupted trace files to a scratch directory,
runs certificate_checker.check() against them, and asserts the expected
violation category was raised. Results are written to
evidence/adversarial_results.json.
"""
import copy
import csv
import json
import os
import shutil
import sys

import common as C
import certificate_checker as CK


def _copy_trace_dir(src, dst, design):
    os.makedirs(dst, exist_ok=True)
    for suffix in ("minute_trace.csv", "lot_log.csv", "events.jsonl"):
        shutil.copyfile(f"{src}/{design}_{suffix}", f"{dst}/{design}_{suffix}")


def experiment_negative_start(src_dir, scratch_dir, design="D0"):
    dst = f"{scratch_dir}/neg_start_{design}"
    _copy_trace_dir(src_dir, dst, design)
    minute_rows, lot_rows, events = CK.load_trace(dst, design)

    # Pick a lot whose machine_start we can legally tamper with: any
    # machine_start event whose lot has release_abs > 5, so we can push its
    # start back by 3 minutes and still land at a non-negative time that is
    # genuinely before release (this is what makes case (a) distinct from
    # the literally-negative case (b) below).
    starts = [e for e in events if e["event"] == "machine_start"]
    starts.sort(key=lambda e: e["t"])
    lot_row_by_gidx = {int(r["gidx"]): r for r in lot_rows}
    target = next(e for e in starts if int(lot_row_by_gidx[e["lot"]]["release"]) > 5)
    g = target["lot"]

    results = {}

    # (a) start before release, but still non-negative
    release = int(lot_row_by_gidx[g]["release"])
    early_t = max(release - 3, 1)  # guaranteed < release, still >= 1 (non-negative)
    corrupted_events = copy.deepcopy(events)
    for e in corrupted_events:
        if e.get("event") == "machine_start" and e["lot"] == g and e["t"] == target["t"]:
            e["t"] = early_t
    with open(f"{dst}/{design}_events.jsonl", "w") as f:
        for e in corrupted_events:
            f.write(json.dumps(e) + "\n")
    _, _, ev2 = CK.load_trace(dst, design)
    viol = CK.check(design, minute_rows, lot_rows, ev2)
    caught = any("NEGATIVE-START" in v or "EARLY-START" in v for v in viol)
    results["early_start_before_release"] = {
        "injected_start_t": early_t, "true_release": release,
        "violations_found": len(viol), "caught": caught,
        "sample_violations": [v for v in viol if "START" in v][:3],
    }

    # (b) literally negative start time
    corrupted_events2 = copy.deepcopy(events)
    for e in corrupted_events2:
        if e.get("event") == "machine_start" and e["lot"] == g and e["t"] == target["t"]:
            e["t"] = -5
    with open(f"{dst}/{design}_events.jsonl", "w") as f:
        for e in corrupted_events2:
            f.write(json.dumps(e) + "\n")
    _, _, ev3 = CK.load_trace(dst, design)
    viol2 = CK.check(design, minute_rows, lot_rows, ev3)
    caught2 = any("NEGATIVE-START" in v for v in viol2)
    results["literally_negative_start"] = {
        "injected_start_t": -5, "violations_found": len(viol2), "caught": caught2,
        "sample_violations": [v for v in viol2 if "NEGATIVE" in v][:3],
    }

    # restore genuine events.jsonl in scratch dir for cleanliness (not required)
    with open(f"{dst}/{design}_events.jsonl", "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")

    return results


def experiment_route_collision(src_dir, scratch_dir, design="D0"):
    dst = f"{scratch_dir}/route_collision_{design}"
    _copy_trace_dir(src_dir, dst, design)
    minute_rows, lot_rows, events = CK.load_trace(dst, design)

    results = {}

    # (a) force both robots onto node 4 (capacity 1) in some interior minute
    corrupted = copy.deepcopy(minute_rows)
    pick_idx = len(corrupted) // 2
    corrupted[pick_idx]["R0_pos"] = "4"
    corrupted[pick_idx]["R1_pos"] = "4"
    _write_minute_csv(dst, design, corrupted)
    mr2, _, _ = CK.load_trace(dst, design)
    viol = CK.check(design, mr2, lot_rows, events)
    caught = any("NODE-CAPACITY" in v for v in viol)
    results["both_robots_on_junction_node4"] = {
        "minute_index": pick_idx, "t": corrupted[pick_idx]["t"],
        "violations_found": len(viol), "caught": caught,
        "sample_violations": [v for v in viol if "NODE-CAPACITY" in v][:3],
    }

    # (b) force both robots to traverse the SAME edge in the same minute
    corrupted2 = copy.deepcopy(minute_rows)
    idx = len(corrupted2) // 3
    prev_idx = idx - 1
    # set previous-minute positions to a common node 'a', and this-minute
    # positions to a common neighbor 'b', with both actions marked 'move'
    a, b = 3, 4  # edge (3,4) exists in both aisle layouts
    corrupted2[prev_idx]["R0_pos"] = str(a)
    corrupted2[prev_idx]["R1_pos"] = str(a)
    corrupted2[idx]["R0_pos"] = str(b)
    corrupted2[idx]["R1_pos"] = str(b)
    corrupted2[idx]["R0_action"] = "move"
    corrupted2[idx]["R1_action"] = "move"
    _write_minute_csv(dst, design, corrupted2)
    mr3, _, _ = CK.load_trace(dst, design)
    viol2 = CK.check(design, mr3, lot_rows, events)
    caught2 = any("EDGE-CAPACITY" in v or "NODE-CAPACITY" in v for v in viol2)
    results["both_robots_same_edge_same_minute"] = {
        "minute_index": idx, "t": corrupted2[idx]["t"], "edge": [a, b],
        "violations_found": len(viol2), "caught": caught2,
        "sample_violations": [v for v in viol2 if ("EDGE-CAPACITY" in v or "NODE-CAPACITY" in v)][:3],
    }

    # restore genuine minute_trace.csv
    _write_minute_csv(dst, design, minute_rows)

    return results


def _write_minute_csv(outdir, design, rows):
    with open(f"{outdir}/{design}_minute_trace.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    src_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/kilnworks-blind-test/work/traces"
    scratch_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/kilnworks-blind-test/work/certification/adversarial_scratch"
    design = sys.argv[3] if len(sys.argv) > 3 else "D0"

    os.makedirs(scratch_dir, exist_ok=True)

    neg = experiment_negative_start(src_dir, scratch_dir, design)
    coll = experiment_route_collision(src_dir, scratch_dir, design)

    all_results = {"design_used": design, "negative_start": neg, "route_collision": coll}
    out_path = "/tmp/kilnworks-blind-test/work/certification/adversarial_results.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)

    print(json.dumps(all_results, indent=2))

    all_caught = all(
        v["caught"] for group in (neg, coll) for v in group.values()
    )
    print("\nALL ADVERSARIAL INJECTIONS CAUGHT:" , all_caught)
    sys.exit(0 if all_caught else 1)


if __name__ == "__main__":
    main()
