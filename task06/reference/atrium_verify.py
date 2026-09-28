#!/usr/bin/env python3
"""ATRIUM-9 independent feasibility-certificate verifier.

Deliberately NOT a copy of atrium_sim.py's Sim/Car/Call classes or its
control flow: this script re-derives the immutable input constants
(building geometry, call table, timing/power constants) directly from the
same public formulas and checks a delivered trace + call ledger against a
closed set of feasibility invariants, without importing or reusing any of
atrium_sim's internal state machinery. It shares only the immutable input
constants with the primary implementation.
"""
import sys

FLOORS = 8
NUM_CARS = 4
CAMPAIGNS = 4
CALLS_PER_CAMPAIGN = 20
CAMPAIGN_CADENCE = 200
CALL_SPACING = 8
T_FLOOR = 4
T_DOOR_OPEN = 2
T_DWELL = 3
T_DOOR_CLOSE = 2
POWER_MOVE = 2
POWER_DOOR = 1
CAPACITY = 6
UP, DOWN = "UP", "DOWN"


def derive_call_table():
    """Recomputes the call table from the packet's formulas independently
    (no shared code path with atrium_sim.gen_calls)."""
    rows = []
    for c in range(CAMPAIGNS):
        for k in range(CALLS_PER_CAMPAIGN):
            group = k // 3
            origin = (group * 3 + c * 2) % FLOORS
            if origin == 0:
                direction = UP
            elif origin == FLOORS - 1:
                direction = DOWN
            else:
                direction = UP if (group + c) % 2 == 0 else DOWN
            arrival = c * CAMPAIGN_CADENCE + k * CALL_SPACING
            span = 1 + ((k * 5 + c * 3) % (FLOORS - 1))
            if direction == UP:
                dest = min(FLOORS - 1, origin + span)
                if dest == origin:
                    dest = min(FLOORS - 1, origin + 1)
            else:
                dest = max(0, origin - span)
                if dest == origin:
                    dest = max(0, origin - 1)
            gidx = c * CALLS_PER_CAMPAIGN + k
            rows.append(dict(gidx=gidx, origin=origin, direction=direction,
                              arrival=arrival, dest=dest))
    return rows


def verify(result, config):
    """result: the dict returned by atrium_sim.simulate(). Returns
    (ok: bool, violations: list[str])."""
    violations = []
    calls_ref = {r["gidx"]: r for r in derive_call_table()}
    calls = {c.gidx: c for c in result["calls"]}

    if set(calls.keys()) != set(calls_ref.keys()):
        violations.append("call gidx set mismatch")

    for gidx, ref in calls_ref.items():
        c = calls.get(gidx)
        if c is None:
            continue
        if c.origin != ref["origin"] or c.direction != ref["direction"] \
           or c.arrival != ref["arrival"] or c.dest != ref["dest"]:
            violations.append(f"call {gidx}: delivered fields diverge from independently-derived table")

    # Feasibility invariants over the trace
    G = config["power_budget"]
    prev_t = -1
    for row in result["trace"]:
        if row["t"] != prev_t + 1:
            violations.append(f"trace row ordering broken at t={row['t']}")
        prev_t = row["t"]
        if row["power"] > G:
            violations.append(f"t={row['t']}: power {row['power']} exceeds budget {G}")
        for ci, cstate in enumerate(row["cars"]):
            if not (0 <= cstate["pos"] <= FLOORS - 1):
                violations.append(f"t={row['t']} car{ci}: position {cstate['pos']} out of building bounds")
            if cstate["load"] > CAPACITY:
                violations.append(f"t={row['t']} car{ci}: load {cstate['load']} exceeds capacity {CAPACITY}")
            if cstate["load"] < 0:
                violations.append(f"t={row['t']} car{ci}: negative load")

    # Every call must complete exactly once, board before alight, and
    # alight strictly after board (no same-tick teleport).
    for gidx, c in calls.items():
        if c.state != "done":
            violations.append(f"call {gidx}: never reached done state (state={c.state})")
            continue
        if c.board_tick is None or c.alight_tick is None:
            violations.append(f"call {gidx}: done without both board_tick and alight_tick recorded")
            continue
        if c.board_tick < c.arrival:
            violations.append(f"call {gidx}: boarded before its own arrival tick")
        if c.alight_tick <= c.board_tick:
            violations.append(f"call {gidx}: alight_tick not strictly after board_tick")

    # Assignment count sanity: every call assigned at least once
    for gidx, c in calls.items():
        if c.attempt < 1:
            violations.append(f"call {gidx}: never assigned (attempt=0)")

    return (len(violations) == 0), violations


def negative_start_mutation(result):
    """Adversarial mutant: copy the delivered trace and set one call's
    board_tick to a value before its own arrival. Verifier must reject."""
    import copy
    mutated = copy.deepcopy(result)
    mutated["calls"][0].board_tick = mutated["calls"][0].arrival - 5
    mutated["calls"][0].alight_tick = mutated["calls"][0].board_tick + 1
    return mutated


def power_overrun_mutation(result, config):
    """Adversarial mutant: copy the delivered trace and inflate one row's
    power above the configured budget. Verifier must reject and identify
    the first invalid minute."""
    import copy
    mutated = copy.deepcopy(result)
    idx = min(10, len(mutated["trace"]) - 1)
    mutated["trace"][idx] = dict(mutated["trace"][idx])
    mutated["trace"][idx]["power"] = config["power_budget"] + 3
    return mutated


if __name__ == "__main__":
    sys.path.insert(0, ".")
    import atrium_sim as SIM

    cfg = dict(active_cars=4, zoning="TOP", wait_timeout=50, capacity=6, power_budget=8)
    r = SIM.simulate(cfg)
    ok, viol = verify(r, cfg)
    print("original accepted:", ok, "violations:" , viol[:5])

    mneg = negative_start_mutation(r)
    ok2, viol2 = verify(mneg, cfg)
    print("negative-start mutant rejected:", not ok2, "sample violation:", viol2[0] if viol2 else None)

    mpow = power_overrun_mutation(r, cfg)
    ok3, viol3 = verify(mpow, cfg)
    print("power-overrun mutant rejected:", not ok3, "sample violation:", viol3[0] if viol3 else None)
