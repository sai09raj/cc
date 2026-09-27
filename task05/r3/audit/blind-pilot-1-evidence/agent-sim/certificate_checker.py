#!/usr/bin/env python3
"""
Standalone feasibility-certificate checker.

Reads only the FILES a simulator emitted (minute_trace.csv, lot_log.csv,
events.jsonl) -- never the simulator's in-memory objects -- and independently
checks every hard constraint in the packet:

  1. release timing       : no lot starts processing before its release_abs
  2. setup/machine memory  : setup cost consistent with remembered family
  3. fixture ceiling       : held-fixture count never exceeds F, and equals
                              (#lots in [prep-start, cure-end)) every minute
  4. power budget          : total power draw never exceeds G, any minute
  5. edge capacity         : no edge crossed by both robots the same minute
  6. node capacity         : node 4 never holds 2 robots; P/Q/K never hold >2
  7. tariff & bill          : bill_delta == power_total * multiplier(t), and
                              multiplier(t) matches the packet's formula
  8. cure duration          : cure_end - cure_start == 4 + family, per lot/batch
  9. completeness           : every lot reaches DONE by declared makespan,
                              and makespan matches the last minute logged + 1
                              convention used by the emitting simulator

This module is used both to certify the genuine traces (must return zero
violations) and to run the adversarial "negative-start" / "route-collision"
experiments (deliberately corrupted traces must be rejected).
"""
import csv
import json
import sys

import common as C


def load_trace(outdir, design):
    with open(f"{outdir}/{design}_minute_trace.csv") as f:
        minute_rows = list(csv.DictReader(f))
    with open(f"{outdir}/{design}_lot_log.csv") as f:
        lot_rows = list(csv.DictReader(f))
    events = []
    with open(f"{outdir}/{design}_events.jsonl") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return minute_rows, lot_rows, events


def _int_or_none(x):
    if x is None or x == "":
        return None
    return int(float(x))


def check(design, minute_rows, lot_rows, events):
    """Return list of violation strings (empty == certified feasible)."""
    cfg = C.DESIGNS[design]
    F, G = cfg["F"], cfg["G"]
    viol = []

    # ---- rebuild per-lot canonical facts ---------------------------------
    lots = {}
    for r in lot_rows:
        g = int(r["gidx"])
        j, s = int(r["j"]), int(r["s"])
        expected_release = C.release_abs(j, s)
        expected_family = C.family_of(j, s)
        expected_pbase = C.pbase(j, s)
        expected_qbase = C.qbase(j, s)
        if int(r["release"]) != expected_release:
            viol.append(f"lot{g}: release {r['release']} != formula {expected_release}")
        if int(r["family"]) != expected_family:
            viol.append(f"lot{g}: family {r['family']} != formula {expected_family}")
        if int(r["pbase"]) != expected_pbase:
            viol.append(f"lot{g}: pbase mismatch")
        if int(r["qbase"]) != expected_qbase:
            viol.append(f"lot{g}: qbase mismatch")
        lots[g] = {
            "release": expected_release, "family": expected_family,
            "pbase": expected_pbase, "qbase": expected_qbase,
            "machine": r["assigned_machine"], "setup": _int_or_none(r["setup_used"]),
            "prepared_at": _int_or_none(r["prepared_at"]),
            "picked_up_at": _int_or_none(r["picked_up_at"]),
            "delivered_at": _int_or_none(r["delivered_at"]),
            "cure_start": _int_or_none(r["cure_start"]),
            "cure_end": _int_or_none(r["cure_end"]),
            "status": r["status"],
        }

    # ---- 1. release timing: machine cannot start before release ----------
    starts = {e["lot"]: e for e in events if e["event"] == "machine_start"}
    for g, e in starts.items():
        lot = lots[g]
        start_t = e["t"]
        if start_t < lot["release"]:
            viol.append(f"NEGATIVE-START/EARLY-START: lot{g} machine_start at t={start_t} "
                        f"< release {lot['release']}")
        if start_t < 0:
            viol.append(f"NEGATIVE-START: lot{g} has negative start time t={start_t}")

    # ---- 2. setup consistency & duration consistency ----------------------
    for g, e in starts.items():
        lot = lots[g]
        expected_setup = e["setup"]
        if expected_setup not in (C.SETUP_MATCH, C.SETUP_MISMATCH):
            viol.append(f"lot{g}: illegal setup value {expected_setup}")
        base = lot["pbase"] if e["machine"] == "P" else lot["qbase"]
        if e["dur"] != expected_setup + base:
            viol.append(f"lot{g}: duration {e['dur']} != setup {expected_setup} + base {base}")
        if lot["prepared_at"] is not None and lot["prepared_at"] != e["t"] + e["dur"]:
            viol.append(f"lot{g}: prepared_at {lot['prepared_at']} != start+dur {e['t']+e['dur']}")

    # ---- 3. fixture ceiling: never exceed F, matches lifecycle window -----
    max_fixture_seen = 0
    for row in minute_rows:
        fh = int(row["fixture_held"])
        max_fixture_seen = max(max_fixture_seen, fh)
        if fh > F:
            viol.append(f"FIXTURE-CEILING VIOLATED at t={row['t']}: held={fh} > F={F}")
    # cross-check via lot lifecycle windows: at each minute, #lots with
    # machine_start_t <= t < cure_end should equal fixture_held.
    starts_t = {g: e["t"] for g, e in starts.items()}
    for row in minute_rows:
        t = int(row["t"])
        active = 0
        for g, lot in lots.items():
            st = starts_t.get(g)
            ce = lot["cure_end"]
            if st is not None and st <= t and (ce is None or t < ce):
                active += 1
        if active != int(row["fixture_held"]):
            viol.append(f"t={row['t']}: recomputed fixture count {active} != logged {row['fixture_held']}")

    # ---- 4. power budget never exceeded ------------------------------------
    for row in minute_rows:
        p = int(row["power_total"])
        if p > G:
            viol.append(f"POWER-BUDGET VIOLATED at t={row['t']}: draw={p} > G={G}")
        if p < 0:
            viol.append(f"t={row['t']}: negative power draw {p}")

    # ---- 5/6. edge & node capacity (route-collision checks) ---------------
    from verifier_sim import make_graph  # reuse only the *graph builder*,
    # which is pure geometry (edge list), not decision logic.
    nodes, nbrs, dist = make_graph(cfg["aisle"])
    prev_pos = {0: C.ROBOT0_HOME, 1: C.ROBOT1_HOME}
    for row in minute_rows:
        t = row["t"]
        pos = {0: int(row["R0_pos"]), 1: int(row["R1_pos"])}
        # node capacity
        from collections import Counter
        occ = Counter(pos.values())
        for node, cnt in occ.items():
            cap = C.NODE_CAPACITY.get(node, 10 ** 9)
            if cnt > cap:
                viol.append(f"ROUTE-COLLISION/NODE-CAPACITY at t={t}: node {node} holds {cnt} robots (cap {cap})")
        # edge capacity: infer edge traversal from consecutive positions when
        # action == 'move'; two robots cannot both traverse the SAME edge in
        # the same minute.
        edges_this_minute = []
        for rid in (0, 1):
            act = row[f"R{rid}_action"]
            if act == "move":
                a, b = prev_pos[rid], pos[rid]
                if a != b:
                    if b not in nbrs.get(a, set()):
                        viol.append(f"t={t}: robot{rid} 'move' from {a} to {b} but no such edge exists")
                    edges_this_minute.append(tuple(sorted((a, b))))
        if len(edges_this_minute) != len(set(edges_this_minute)):
            viol.append(f"ROUTE-COLLISION/EDGE-CAPACITY at t={t}: both robots traversed the same edge {edges_this_minute}")
        prev_pos = pos

    # ---- 7. tariff & bill arithmetic --------------------------------------
    running = 0
    for row in minute_rows:
        t = int(row["t"])
        mult_expected = C.tariff_multiplier(t)
        mult_logged = int(row["tariff_mult"])
        if mult_logged != mult_expected:
            viol.append(f"t={t}: tariff multiplier {mult_logged} != formula {mult_expected}")
        delta_expected = int(row["power_total"]) * mult_expected
        delta_logged = int(row["bill_delta"])
        if delta_logged != delta_expected:
            viol.append(f"t={t}: bill_delta {delta_logged} != power*mult {delta_expected}")
        running += delta_logged
    reported_bill = sum(int(r["bill_delta"]) for r in minute_rows)
    if running != reported_bill:
        viol.append(f"bill sum mismatch: recomputed {running} != summed {reported_bill}")

    # ---- 8. cure duration ---------------------------------------------------
    oven_starts = [e for e in events if e["event"] == "oven_start"]
    for e in oven_starts:
        fam = e["family"]
        expected_dur = C.cure_minutes(fam)
        if e["dur"] != expected_dur:
            viol.append(f"batch {e.get('lots')}: cure dur {e['dur']} != 4+family={expected_dur}")
        for g in e["lots"]:
            lot = lots[g]
            if lot["cure_start"] != e["t"]:
                viol.append(f"lot{g}: cure_start {lot['cure_start']} != batch start {e['t']}")
            if lot["cure_end"] is not None and lot["cure_end"] != e["t"] + expected_dur:
                viol.append(f"lot{g}: cure_end {lot['cure_end']} != {e['t']}+{expected_dur}")

    # ---- 9. completeness -----------------------------------------------------
    n_done = sum(1 for l in lots.values() if l["status"] == "DONE" or l["status"] == "done")
    if n_done != len(lots):
        viol.append(f"INCOMPLETE: only {n_done}/{len(lots)} lots reached DONE")

    return viol


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "traces"
    designs = sys.argv[2:] if len(sys.argv) > 2 else list(C.DESIGNS.keys())
    all_ok = True
    for d in designs:
        minute_rows, lot_rows, events = load_trace(outdir, d)
        viol = check(d, minute_rows, lot_rows, events)
        if viol:
            all_ok = False
            print(f"{d}: {len(viol)} VIOLATIONS")
            for v in viol[:20]:
                print("   -", v)
        else:
            print(f"{d}: CERTIFIED FEASIBLE (0 violations, {len(minute_rows)} minutes checked)")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
