#!/usr/bin/env python3
"""KILNWORKS R3 canonical reference simulator.

Implements design/semantic-contract.md sections S00-S10 exactly. Stdlib only.
Deterministic: there is no free optimization decision anywhere in this module.
Run: python3 kilnworks_sim.py
"""
from collections import deque
import json
import sys

CADENCE = 35
FAULT_ROBOT = 0
FAULT_WINDOW = 6
OVEN_WAIT_TICKS = 2
CAMPAIGNS = 4
LOTS_PER_CAMPAIGN = 5
MAINT_THRESHOLD = 10
MAINT_WINDOW = 13

DESIGNS = {
    "D0": dict(F=2, G=5, aisle="closed", capital=0),
    "D1": dict(F=3, G=5, aisle="closed", capital=7),
    "D2": dict(F=2, G=6, aisle="closed", capital=9),
    "D3": dict(F=2, G=5, aisle="open", capital=6),
    "D4": dict(F=3, G=6, aisle="closed", capital=16),
    "D5": dict(F=3, G=6, aisle="open", capital=22),
}

BASE_EDGES = [(0, 3), (3, 6), (3, 4), (4, 7), (6, 7), (7, 8), (5, 8), (2, 5), (1, 4)]
OPEN_EXTRA_EDGE = (4, 5)
DOCK_P, DOCK_Q, DOCK_K = 3, 5, 1
DOCK_CAPACITY = 2
INTERIOR_CAPACITY = 1
POWER = {"P": 2, "Q": 3, "oven": 3, "robot_action": 1}


def build_graph(aisle):
    edges = set()
    for a, b in BASE_EDGES:
        edges.add((a, b))
        edges.add((b, a))
    if aisle == "open":
        a, b = OPEN_EXTRA_EDGE
        edges.add((a, b))
        edges.add((b, a))
    adj = {}
    for a, b in edges:
        adj.setdefault(a, set()).add(b)
    return edges, adj


def node_capacity(node):
    return DOCK_CAPACITY if node in (DOCK_P, DOCK_Q, DOCK_K) else INTERIOR_CAPACITY


def bfs_distance_and_next_hop(adj, start, target):
    """Return (distance_in_edges, next_hop_node) for a shortest path from start
    to target, with the next-hop tie-break resolved by lowest node id at every
    step of the search frontier. distance is 0 and next_hop is None if
    start == target."""
    if start == target:
        return 0, None
    visited = {start}
    parent = {}
    dist = {start: 0}
    order = deque([start])
    while order:
        cur = order.popleft()
        for nxt in sorted(adj.get(cur, ())):
            if nxt not in visited:
                visited.add(nxt)
                parent[nxt] = cur
                dist[nxt] = dist[cur] + 1
                if nxt == target:
                    node = nxt
                    while parent[node] != start:
                        node = parent[node]
                    return dist[nxt], node
                order.append(nxt)
    return None, None


def bfs_next_hop(adj, start, target):
    """Return the next node on a shortest path from start to target,
    tie-broken by lowest node id at every step of the search frontier."""
    if start == target:
        return None
    visited = {start}
    parent = {}
    order = deque([start])
    while order:
        cur = order.popleft()
        for nxt in sorted(adj.get(cur, ())):
            if nxt not in visited:
                visited.add(nxt)
                parent[nxt] = cur
                if nxt == target:
                    node = nxt
                    while parent[node] != start:
                        node = parent[node]
                    return node
                order.append(nxt)
    return None


def gen_lots():
    lots = []
    for s in range(CAMPAIGNS):
        for j in range(LOTS_PER_CAMPAIGN):
            family = (j + s) % 2
            release_local = 2 * (j // 2)
            release_abs = s * CADENCE + release_local
            pbase = 5 + (j * j + 2 * s) % 4
            qbase = 4 + (3 * j + s) % 5
            lots.append(dict(
                gidx=s * LOTS_PER_CAMPAIGN + j, s=s, j=j, family=family,
                release_abs=release_abs, pbase=pbase, qbase=qbase,
            ))
    return lots


class Lot:
    __slots__ = (
        "gidx", "s", "j", "family", "release_abs", "pbase", "qbase",
        "state", "machine", "prep_end", "node", "cure_end", "arrival_time",
    )

    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)
        self.state = "pending"       # pending -> in_prep -> prepared -> in_transit -> waiting_cure -> curing -> done
        self.machine = None
        self.prep_end = None
        self.node = None
        self.cure_end = None
        self.arrival_time = None


def duration_on(machine, lot):
    return lot.pbase if machine == "P" else lot.qbase


def simulate(design_name, trace_limit=2000, debug=False,
             mutant_disable_fault=False, mutant_oven_no_timer=False,
             mutant_tiebreak_high=False, mutant_disable_maintenance=False,
             mutant_maintenance_inclusive=False, mutant_maintenance_single_shot=False,
             lots_data=None):
    d = DESIGNS[design_name]
    edges, adj = build_graph(d["aisle"])
    F, G = d["F"], d["G"]

    lots = [Lot(x) for x in (lots_data if lots_data is not None else gen_lots())]
    by_gidx = {lot.gidx: lot for lot in lots}
    tb = -1 if mutant_tiebreak_high else 1
    effective_oven_wait = 0 if mutant_oven_no_timer else OVEN_WAIT_TICKS

    machine_busy_until = {"P": None, "Q": None}
    machine_last_family = {"P": None, "Q": None}
    machine_current_lot = {"P": None, "Q": None}
    machine_current_proc_only = {"P": None, "Q": None}  # processing-only duration of the job in progress

    q_cumulative = 0
    q_maint_triggered = False
    q_maint_trigger_t = None
    q_maint_trigger_count = 0
    q_freeze_until = None

    fixture_held = 0

    robot_pos = {0: DOCK_P, 1: DOCK_Q}
    robot_cargo = {0: None, 1: None}
    robot_offline_until = {0: None, 1: None}
    robot_fault_arrival = {0: None, 1: None}
    fault_triggered = False

    oven_busy_until = None
    oven_members = []
    batch_log = []
    oven_anchor = None      # gidx of the pending anchor lot, or None
    oven_deadline = None    # minute by which the anchor must start alone

    # pending effects of actions chosen at t, applied at boundary t+1
    pending_robot_pos = {0: None, 1: None}
    pending_robot_cargo = {0: None, 1: None}
    pending_pickup_lot = {0: None, 1: None}   # gidx picked up at t, becomes cargo at t+1
    pending_unload_lot = {0: None, 1: None}   # gidx unloaded at t, becomes waiting_cure at t+1
    pending_fault_arm = {0: False, 1: False}  # robot arrived at node 4 at t -> offline window starts t+2

    trace = []
    bill = 0
    makespan = None
    lot_done_time = {}
    prep_events = []

    def tariff(t):
        return 1 + ((t // 7) % 3)

    for t in range(trace_limit):
        # ---- boundary t: apply completions and previous-minute effects ----
        for m in ("P", "Q"):
            if machine_busy_until[m] == t:
                lot = machine_current_lot[m]
                lot.state = "prepared"
                lot.node = DOCK_P if m == "P" else DOCK_Q
                machine_busy_until[m] = None
                machine_current_lot[m] = None
                if m == "Q" and not mutant_disable_maintenance:
                    q_cumulative += machine_current_proc_only[m]
                    machine_current_proc_only[m] = None
                    if q_cumulative >= MAINT_THRESHOLD and not (
                        mutant_maintenance_single_shot and q_maint_triggered
                    ):
                        # Recurring maintenance interval: re-arms every time the
                        # threshold is crossed, not just the first. q_cumulative
                        # resets to 0 so the next interval counts fresh processing
                        # only, matching a real periodic maintenance schedule.
                        q_maint_triggered = True
                        q_maint_trigger_t = t
                        q_maint_trigger_count += 1
                        if not mutant_maintenance_single_shot:
                            q_cumulative = 0
                        if mutant_maintenance_inclusive:
                            q_freeze_until = t + MAINT_WINDOW - 1  # wrong: copies S07's inclusive convention
                        else:
                            q_freeze_until = t + MAINT_WINDOW       # correct: default rule, starts t+1

        if oven_busy_until == t:
            for gidx in oven_members:
                by_gidx[gidx].state = "done"
                fixture_held -= 1
                lot_done_time[gidx] = t
            oven_members = []
            oven_busy_until = None

        for r in (0, 1):
            if pending_robot_pos[r] is not None:
                robot_pos[r] = pending_robot_pos[r]
                pending_robot_pos[r] = None
            if pending_pickup_lot[r] is not None:
                gidx = pending_pickup_lot[r]
                robot_cargo[r] = gidx
                by_gidx[gidx].state = "in_transit"
                pending_pickup_lot[r] = None
            if pending_robot_cargo[r] is not None:
                robot_cargo[r] = pending_robot_cargo[r]
                pending_robot_cargo[r] = None
            if pending_unload_lot[r] is not None:
                gidx = pending_unload_lot[r]
                by_gidx[gidx].state = "waiting_cure"
                by_gidx[gidx].node = DOCK_K
                by_gidx[gidx].arrival_time = t
                pending_unload_lot[r] = None
            if pending_fault_arm[r]:
                if not fault_triggered and r == FAULT_ROBOT:
                    fault_triggered = True
                    robot_fault_arrival[r] = t
                    # frozen at node 4 for FAULT_WINDOW minutes starting the arrival
                    # minute itself: t, t+1, ..., t+FAULT_WINDOW-1; resumes at t+FAULT_WINDOW.
                    robot_offline_until[r] = t + FAULT_WINDOW - 1
                pending_fault_arm[r] = False

        # ---- termination check ----
        all_done = all(lot.state == "done" for lot in lots)
        nothing_pending = (
            machine_busy_until["P"] is None and machine_busy_until["Q"] is None
            and oven_busy_until is None
            and robot_cargo[0] is None and robot_cargo[1] is None
        )
        if all_done and nothing_pending and makespan is None:
            makespan = t
            break

        # ---- S08 (part 1): power already locked in from ongoing operations
        # started in a strictly earlier minute; this power is mandatory and was
        # already admitted against G when it started. New admissions below draw
        # from what remains, in a fixed priority order: P start, Q start, robot 0
        # action, robot 1 action, oven start.
        locked_power = 0
        if machine_busy_until["P"] is not None:
            locked_power += POWER["P"]
        if machine_busy_until["Q"] is not None:
            locked_power += POWER["Q"]
        if oven_busy_until is not None:
            locked_power += POWER["oven"]
        remaining_budget = [G - locked_power]

        def q_frozen(t2):
            if q_maint_trigger_t is None:
                return False
            if mutant_maintenance_inclusive:
                return q_maint_trigger_t <= t2 <= q_freeze_until
            return q_maint_trigger_t < t2 <= q_freeze_until

        # ---- S03: machine assignment (P then Q), power-budget gated ----
        for m in ("P", "Q"):
            if machine_busy_until[m] is not None:
                continue
            if m == "Q" and q_frozen(t):
                continue
            pool = [
                lot for lot in lots
                if lot.state == "pending" and lot.release_abs <= t and fixture_held < F
            ]
            if not pool:
                continue
            if remaining_budget[0] < POWER[m]:
                continue  # deferred this minute purely by the power ceiling
            def cost(lot):
                setup = 0 if machine_last_family[m] in (None, lot.family) else 2
                return (setup + duration_on(m, lot), tb * lot.gidx)
            pool.sort(key=cost)
            chosen = pool[0]
            setup = 0 if machine_last_family[m] in (None, chosen.family) else 2
            dur = setup + duration_on(m, chosen)
            machine_busy_until[m] = t + dur
            machine_last_family[m] = chosen.family
            machine_current_lot[m] = chosen
            machine_current_proc_only[m] = duration_on(m, chosen)
            chosen.state = "in_prep"
            chosen.machine = m
            fixture_held += 1  # fixture held from prep start
            remaining_budget[0] -= POWER[m]
            prep_events.append(dict(machine=m, lot=chosen.gidx, start_t=t,
                                     dur=dur, release_abs=chosen.release_abs))

        # ---- S05: robot dispatch, robot 0 first then robot 1 ----
        reserved_edges = set()

        # Robot 0 decides first; at that point Robot 1 has not yet acted, so
        # Robot 0 conservatively assumes Robot 1 stays at its current position.
        # Robot 1 decides second, against Robot 0's now-FINALIZED destination
        # (not Robot 0's pre-minute position) -- a robot vacating a node this
        # same minute frees it for the other robot to enter (S05: "following
        # into a node vacated that same minute is legal").
        robot_final_pos = {0: robot_pos[0], 1: robot_pos[1]}

        def node_currently_occupied(node, exclude_robot=None):
            count = 0
            for r in (0, 1):
                if r == exclude_robot:
                    continue
                if robot_final_pos[r] == node:
                    count += 1
            return count

        def try_move(r, dest):
            if remaining_budget[0] < POWER["robot_action"]:
                return False
            src = robot_pos[r]
            edge = (src, dest)
            if edge in reserved_edges or (dest, src) in reserved_edges:
                return False
            occ = node_currently_occupied(dest, exclude_robot=r)
            if occ + 1 > node_capacity(dest):
                return False
            reserved_edges.add(edge)
            pending_robot_pos[r] = dest
            robot_final_pos[r] = dest
            remaining_budget[0] -= POWER["robot_action"]
            if dest == 4 and not fault_triggered and r == FAULT_ROBOT and not mutant_disable_fault:
                pending_fault_arm[r] = True
            return True

        actions = {}
        for r in (0, 1):
            if robot_offline_until[r] is not None and t <= robot_offline_until[r]:
                actions[r] = "wait(offline)"
                continue

            pos = robot_pos[r]
            cargo = robot_cargo[r]

            if cargo is not None and pos == DOCK_K:
                if remaining_budget[0] >= POWER["robot_action"]:
                    pending_unload_lot[r] = cargo
                    pending_robot_cargo[r] = None
                    robot_cargo[r] = None
                    actions[r] = "unload"
                    remaining_budget[0] -= POWER["robot_action"]
                else:
                    actions[r] = "wait(power)"
                continue

            if cargo is None:
                here = [
                    lot for lot in lots
                    if lot.state == "prepared" and lot.node == pos
                ]
                if here:
                    here.sort(key=lambda lot: (lot.prep_end or 0, tb * lot.gidx))
                    chosen = here[0]
                    if remaining_budget[0] >= POWER["robot_action"]:
                        chosen.state = "picked"
                        pending_pickup_lot[r] = chosen.gidx
                        actions[r] = f"pickup({chosen.gidx})"
                        remaining_budget[0] -= POWER["robot_action"]
                    else:
                        actions[r] = "wait(power)"
                    continue

            if cargo is not None:
                nxt = bfs_next_hop(adj, pos, DOCK_K)
                if nxt is not None and try_move(r, nxt):
                    actions[r] = f"move->{nxt}"
                else:
                    actions[r] = "wait(blocked)"
                continue

            targets = sorted(set(lot.node for lot in lots if lot.state == "prepared"))
            home = DOCK_P if r == 0 else DOCK_Q
            if not targets:
                if pos == home:
                    actions[r] = "wait(home)"
                else:
                    nxt = bfs_next_hop(adj, pos, home)
                    if nxt is not None and try_move(r, nxt):
                        actions[r] = f"move->{nxt}(home)"
                    else:
                        actions[r] = "wait(blocked-home)"
                continue
            # Move toward the NEAREST target (shortest edge-count distance);
            # tie-break by lowest target node id, then execute that target's
            # own next hop.
            best_target, best_dist, best_hop = None, None, None
            for target in targets:
                dist, nxt = bfs_distance_and_next_hop(adj, pos, target)
                if dist is None or nxt is None:
                    continue  # unreachable, or already at this target
                if best_dist is None or dist < best_dist:
                    best_target, best_dist, best_hop = target, dist, nxt
            if best_hop is not None and try_move(r, best_hop):
                actions[r] = f"move->{best_hop}(to {best_target})"
            else:
                actions[r] = "wait(no-target)"

        # ---- S06: oven start with bounded pairing timer, power-budget gated ----
        if oven_busy_until is None:
            arrived = [lot for lot in lots if lot.state == "waiting_cure"]
            if oven_anchor is None and arrived:
                arrived.sort(key=lambda lot: (lot.arrival_time, tb * lot.gidx))
                oven_anchor = arrived[0].gidx
                # Deadline is anchored to the lot's own arrival minute, not the
                # (possibly much later) minute it is picked up as anchor -- the
                # timer keeps running even while the oven was busy with an
                # earlier batch.
                oven_deadline = by_gidx[oven_anchor].arrival_time + effective_oven_wait
            if oven_anchor is not None:
                anchor = by_gidx[oven_anchor]
                candidates = sorted(
                    (lot for lot in arrived
                     if lot.gidx != anchor.gidx and lot.family == anchor.family),
                    key=lambda lot: tb * lot.gidx,
                )
                partner = candidates[0] if candidates else None
                should_start = partner is not None or t >= oven_deadline
                if should_start and remaining_budget[0] >= POWER["oven"]:
                    members = [anchor.gidx] + ([partner.gidx] if partner else [])
                    for gidx in members:
                        by_gidx[gidx].state = "curing"
                    oven_busy_until = t + 4 + anchor.family
                    oven_members = members
                    remaining_budget[0] -= POWER["oven"]
                    batch_log.append({"t": t, "members": list(members),
                                       "campaigns": sorted({by_gidx[g].s for g in members})})
                    oven_anchor = None
                    oven_deadline = None

        # ---- S08: power accounting ----
        minute_power = 0
        if machine_busy_until["P"] is not None and machine_current_lot["P"] is not None:
            minute_power += POWER["P"]
        if machine_busy_until["Q"] is not None and machine_current_lot["Q"] is not None:
            minute_power += POWER["Q"]
        if oven_busy_until is not None:
            minute_power += POWER["oven"]
        for r in (0, 1):
            if actions.get(r, "").startswith(("move", "pickup", "unload")):
                minute_power += POWER["robot_action"]
        if minute_power > G:
            raise AssertionError(f"{design_name} t={t}: power {minute_power} > G {G}")
        if fixture_held > F:
            raise AssertionError(f"{design_name} t={t}: fixture_held {fixture_held} > F {F}")
        bill += minute_power * tariff(t)

        trace.append({
            "t": t,
            "actions": actions,
            "robot_pos": dict(robot_pos),
            "robot_cargo": dict(robot_cargo),
            "fixture_held": fixture_held,
            "power": minute_power,
            "tariff": tariff(t),
            "cum_bill": bill,
            "oven_members": list(oven_members) if oven_busy_until is not None and oven_busy_until != t else [],
        })

        if debug and t % 5 == 0:
            states = {}
            for lot in lots:
                states.setdefault(lot.state, []).append(lot.gidx)
            print(t, "robots", robot_pos, robot_cargo, "fixture", fixture_held,
                  "oven_until", oven_busy_until, "P_until", machine_busy_until["P"],
                  "Q_until", machine_busy_until["Q"], "states", states)

        # freeze prep_end / node bookkeeping for newly assigned lots
        for m in ("P", "Q"):
            lot = machine_current_lot[m]
            if lot is not None and lot.prep_end is None:
                lot.prep_end = machine_busy_until[m]

    if makespan is None:
        raise RuntimeError(f"{design_name} did not terminate within {trace_limit} minutes")

    return dict(
        design=design_name,
        makespan=makespan,
        bill=bill,
        trace=trace,
        fault_triggered=fault_triggered,
        capital=d["capital"],
        lot_done_time=lot_done_time,
        batch_log=batch_log,
        prep_events=prep_events,
        edges=edges,
        q_maint_triggered=q_maint_triggered,
        q_maint_trigger_t=q_maint_trigger_t,
        q_maint_trigger_count=q_maint_trigger_count,
        q_freeze_until=q_freeze_until,
    )


def canonical_trace_serialization(result):
    """One line per minute: 't,power,cum_bill'. No header row per design other
    than a 'DESIGN:<name>' marker line. Used only for the trace-integrity hash
    (rubric criterion on canonical_hash); not a required output format."""
    lines = [f"DESIGN:{result['design']}"]
    for row in result["trace"]:
        lines.append(f"{row['t']},{row['power']},{row['cum_bill']}")
    return "\n".join(lines)


def canonical_hash(results_by_design):
    import hashlib
    blocks = [canonical_trace_serialization(results_by_design[name]) for name in DESIGNS]
    blob = "\n".join(blocks).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def lexicographic_key(result):
    d = DESIGNS[result["design"]]
    return (result["makespan"], result["bill"] + 3 * d["capital"], d["capital"], result["design"])


def main():
    results = {name: simulate(name) for name in DESIGNS}
    for name, r in results.items():
        print(f"{name}: makespan={r['makespan']} bill={r['bill']} fault_triggered={r['fault_triggered']}")

    unrestricted = min(results.values(), key=lexicographic_key)
    budget = min((r for r in results.values() if DESIGNS[r["design"]]["capital"] <= 9), key=lexicographic_key)
    print("unrestricted key:", lexicographic_key(unrestricted), unrestricted["design"])
    print("capital<=9 key:", lexicographic_key(budget), budget["design"])

    with open("reference_output.json", "w") as f:
        json.dump({
            name: {"makespan": r["makespan"], "bill": r["bill"], "fault_triggered": r["fault_triggered"]}
            for name, r in results.items()
        }, f, indent=2)


if __name__ == "__main__":
    sys.exit(main())
