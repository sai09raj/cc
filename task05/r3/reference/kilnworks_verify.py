#!/usr/bin/env python3
"""KILNWORKS R3 feasibility checker and adversarial mutation harness.

Checks a delivered (design, prep_events, trace, edges) bundle for structural
feasibility: no negative/pre-release preparation start, no edge/node capacity
violation. Independent of *how* the schedule was produced -- it only looks at
the delivered records, mirroring what an examiner's separately-coded verifier
must do (S11/S12 in design/semantic-contract.md).

Run: python3 kilnworks_verify.py
"""
import copy
import kilnworks_sim as k


def check_prep_starts(prep_events):
    for ev in sorted(prep_events, key=lambda e: e["start_t"]):
        if ev["start_t"] < 0:
            return False, f"prep start {ev['start_t']} < 0 for lot {ev['lot']}", ev["start_t"]
        if ev["start_t"] < ev["release_abs"]:
            return False, (f"lot {ev['lot']} started prep at {ev['start_t']} before its "
                            f"release {ev['release_abs']}"), ev["start_t"]
    return True, None, None


def check_route_conflicts(trace, edges):
    """Reconstruct edge usage minute-by-minute from consecutive robot_pos
    snapshots and check both the no-swap/no-same-direction-sharing edge rule
    and node capacity."""
    for i in range(len(trace) - 1):
        row, nxt = trace[i], trace[i + 1]
        srcs = row["robot_pos"]
        dsts = nxt["robot_pos"]
        moves = {}
        for r in (0, 1):
            if srcs[r] != dsts[r]:
                moves[r] = (srcs[r], dsts[r])
        if len(moves) == 2:
            (s0, d0), (s1, d1) = moves[0], moves[1]
            if (s0, d0) == (d1, s1):
                return False, f"edge swap {s0}<->{d0} at t={row['t']}", row["t"]
            if {s0, d0} == {s1, d1}:
                return False, f"same edge used twice at t={row['t']}", row["t"]
        for r, node in dsts.items():
            occ = sum(1 for rr, n in dsts.items() if n == node)
            if occ > k.node_capacity(node):
                return False, f"node {node} capacity exceeded at t={nxt['t']}", nxt["t"]
    return True, None, None


def full_check(result):
    ok1, reason1, t1 = check_prep_starts(result["prep_events"])
    if not ok1:
        return False, reason1, t1
    ok2, reason2, t2 = check_route_conflicts(result["trace"], result["edges"])
    if not ok2:
        return False, reason2, t2
    return True, None, None


def negative_start_experiment(design_name):
    original = k.simulate(design_name)
    ok, reason, t = full_check(original)
    assert ok, f"original should be accepted, got: {reason} at t={t}"

    mutated = copy.deepcopy(original)
    earliest = min(mutated["prep_events"], key=lambda e: e["start_t"])
    earliest["start_t"] = -1
    ok2, reason2, t2 = full_check(mutated)
    assert not ok2, "mutated (negative start) schedule should be REJECTED but was accepted"
    return dict(original_accepted=ok, mutated_rejected=not ok2, mutated_reason=reason2)


def route_collision_experiment(design_name):
    original = k.simulate(design_name)
    ok, reason, t = full_check(original)
    assert ok, f"original should be accepted, got: {reason} at t={t}"

    mutated = copy.deepcopy(original)
    trace = mutated["trace"]
    # Force an artificial same-edge conflict: pick a minute with at least one
    # real move and force the other robot onto the exact same edge.
    injected_t = None
    for i in range(len(trace) - 1):
        srcs = trace[i]["robot_pos"]
        dsts = trace[i + 1]["robot_pos"]
        if srcs[0] != dsts[0]:
            trace[i + 1]["robot_pos"] = {0: dsts[0], 1: dsts[0]}
            injected_t = trace[i + 1]["t"]
            break
    assert injected_t is not None, "no move found to corrupt"
    ok2, reason2, t2 = full_check(mutated)
    assert not ok2, "mutated (route collision) schedule should be REJECTED but was accepted"
    return dict(original_accepted=ok, mutated_rejected=not ok2,
                mutated_reason=reason2, first_invalid_minute=t2)


if __name__ == "__main__":
    for name in k.DESIGNS:
        r = k.simulate(name)
        ok, reason, t = full_check(r)
        print(name, "feasibility:", "OK" if ok else f"FAIL: {reason} at t={t}")

    print()
    print("negative-start experiment (D0):", negative_start_experiment("D0"))
    print("route-collision experiment (D0):", route_collision_experiment("D0"))
