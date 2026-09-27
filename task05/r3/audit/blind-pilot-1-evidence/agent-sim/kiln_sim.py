#!/usr/bin/env python3
"""
KILNWORKS retrofit PRIMARY simulator.

Event-by-event (minute-by-minute), deterministic, single continuous clock
covering all four campaigns (20 lots) back to back for one retrofit design.

This is the "primary" implementation. An independently-coded verifier lives
in verifier_sim.py and shares only the literal constants in common.py.

Usage:
    python3 kiln_sim.py D0 [--trace-csv out.csv] [--summary-json out.json]
"""
import argparse
import csv
import json
import sys
from collections import deque, namedtuple

import common as C


# ---------------------------------------------------------------------------
# Graph helpers
# ---------------------------------------------------------------------------
def build_graph(aisle):
    edges = list(C.EDGES_COMMON)
    if aisle == "open":
        edges.append(C.EDGE_OPEN_ONLY)
    adj = {}
    for u, v in edges:
        adj.setdefault(u, set()).add(v)
        adj.setdefault(v, set()).add(u)
    return adj


def bfs_dist_from(adj, root):
    """Return {node: distance from root} via BFS."""
    dist = {root: 0}
    q = deque([root])
    while q:
        u = q.popleft()
        for v in sorted(adj.get(u, ())):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def next_hop_toward(adj, dist_to_target, current):
    """Lowest-id neighbor of `current` that lies one step closer to target."""
    if dist_to_target.get(current, None) == 0:
        return None  # already there
    best = None
    for n in sorted(adj.get(current, ())):
        if dist_to_target.get(n, 10**9) == dist_to_target[current] - 1:
            best = n
            break
    return best


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
class Lot:
    __slots__ = (
        "j", "s", "gidx", "family", "release", "pbase", "qbase",
        "status", "assigned_machine", "setup_used", "prepared_at",
        "picked_up_at", "delivered_at", "cure_start", "cure_end",
        "batch_id",
    )

    def __init__(self, j, s):
        self.j = j
        self.s = s
        self.gidx = C.global_index(j, s)
        self.family = C.family_of(j, s)
        self.release = C.release_abs(j, s)
        self.pbase = C.pbase(j, s)
        self.qbase = C.qbase(j, s)
        self.status = "unreleased"      # -> released -> processing -> prepared
        # -> in_transit -> waiting_at_K -> curing -> done
        self.assigned_machine = None
        self.setup_used = None
        self.prepared_at = None
        self.picked_up_at = None
        self.delivered_at = None
        self.cure_start = None
        self.cure_end = None
        self.batch_id = None


class Machine:
    def __init__(self, name, node, draw, duration_fn):
        self.name = name
        self.node = node
        self.draw = draw
        self.duration_fn = duration_fn
        self.busy_until = None      # None => idle
        self.remembered_family = None
        self.current_lot = None

    def is_busy(self, t):
        return self.busy_until is not None and t < self.busy_until


class Robot:
    def __init__(self, rid, home):
        self.rid = rid
        self.pos = home
        self.home = home
        self.cargo = None           # lot object or None
        self.offline_triggered = False
        self.offline_until = None   # exclusive


class Oven:
    def __init__(self):
        self.busy_until = None
        self.batch = []             # list of lot objects currently curing
        self.pending_anchor = None  # lot object
        self.anchor_deadline = None
        self.next_batch_id = 0

    def is_busy(self, t):
        return self.busy_until is not None and t < self.busy_until


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------
class Simulator:
    def __init__(self, design_name):
        self.name = design_name
        cfg = C.DESIGNS[design_name]
        self.F = cfg["F"]
        self.G = cfg["G"]
        self.aisle = cfg["aisle"]
        self.capital = cfg["capital"]

        self.adj = build_graph(self.aisle)
        self.dist_to_K = bfs_dist_from(self.adj, C.K_NODE)
        self.dist_to_P = bfs_dist_from(self.adj, C.P_NODE)
        self.dist_to_Q = bfs_dist_from(self.adj, C.Q_NODE)

        self.lots = [Lot(j, s) for s in range(C.NUM_CAMPAIGNS) for j in range(C.LOTS_PER_CAMPAIGN)]
        self.lots.sort(key=lambda l: l.gidx)
        self.by_gidx = {l.gidx: l for l in self.lots}

        self.P = Machine("P", C.P_NODE, C.POWER_DRAW["P_op"], lambda l, setup: setup + l.pbase)
        self.Q = Machine("Q", C.Q_NODE, C.POWER_DRAW["Q_op"], lambda l, setup: setup + l.qbase)

        self.robots = [Robot(0, C.ROBOT0_HOME), Robot(1, C.ROBOT1_HOME)]

        self.oven = Oven()

        self.wait_P = []   # list of lots waiting (prepared, uncollected) at node P
        self.wait_Q = []
        self.wait_K = []   # list of lots delivered to K, uncured

        self.fixture_held = 0

        self.trace = []    # per-minute log rows
        self.bill = 0
        self.total_power_minutes = 0

        self.n_lots_total = len(self.lots)
        self.n_done = 0
        self.makespan = None

    # -- helpers -------------------------------------------------------
    def eligible_pool(self, t):
        return [l for l in self.lots
                if l.status == "released" and l.release <= t]

    def try_start_machine(self, machine, other_wait_list, t, remaining_budget):
        """Attempt to start a new job on `machine`. Returns (started, draw)."""
        if machine.is_busy(t):
            return False, 0
        pool = [l for l in self.eligible_pool(t) if self.fixture_held < self.F]
        if not pool:
            return False, 0
        # cost = setup + processing duration on this machine
        def cost(l):
            fam = l.family
            setup = C.SETUP_MATCH if (machine.remembered_family is None or machine.remembered_family == fam) else C.SETUP_MISMATCH
            dur = l.pbase if machine is self.P else l.qbase
            return (setup + dur, l.gidx)
        pool.sort(key=cost)
        chosen = pool[0]
        setup = C.SETUP_MATCH if (machine.remembered_family is None or machine.remembered_family == chosen.family) else C.SETUP_MISMATCH
        draw = machine.draw
        if draw > remaining_budget:
            return False, 0
        dur = setup + (chosen.pbase if machine is self.P else chosen.qbase)
        machine.busy_until = t + dur
        machine.remembered_family = chosen.family
        machine.current_lot = chosen
        chosen.status = "processing"
        chosen.assigned_machine = machine.name
        chosen.setup_used = setup
        self.fixture_held += 1
        self.trace_event(t, "machine_start", machine=machine.name, lot=chosen.gidx,
                          family=chosen.family, setup=setup, dur=dur,
                          busy_until=machine.busy_until)
        return True, draw

    def finish_machines(self, t):
        for m, wait_list in ((self.P, self.wait_P), (self.Q, self.wait_Q)):
            if m.busy_until == t:
                lot = m.current_lot
                lot.status = "prepared"
                lot.prepared_at = t
                wait_list.append(lot)
                self.trace_event(t, "machine_finish", machine=m.name, lot=lot.gidx)
                m.current_lot = None

    def finish_oven(self, t):
        if self.oven.busy_until == t:
            for lot in self.oven.batch:
                lot.status = "done"
                lot.cure_end = t
                self.fixture_held -= 1
                self.n_done += 1
            self.trace_event(t, "oven_finish", batch=[l.gidx for l in self.oven.batch],
                              batch_id=self.oven.batch[0].batch_id if self.oven.batch else None)
            self.oven.batch = []
            self.oven.busy_until = None

    def release_lots(self, t):
        for l in self.lots:
            if l.status == "unreleased" and l.release <= t:
                l.status = "released"

    # -- robot decision -------------------------------------------------
    def decide_robot_action(self, robot, t):
        """Returns a dict describing the *intended* action (before power/capacity
        admission). Structure: {'kind': 'offline'|'wait'|'move'|'pickup'|'unload',
        'target': node-or-None, 'lot': lot-or-None}
        """
        # Rule 1: forced-offline window (Robot 0 only, first arrival at node 4)
        if robot.rid == 0:
            if not robot.offline_triggered and robot.pos == C.JUNCTION_NODE:
                robot.offline_triggered = True
                robot.offline_until = t + C.FORCED_OFFLINE_MINUTES
            if robot.offline_triggered and t < robot.offline_until:
                return {"kind": "offline"}

        # Rule 2: carrying cargo and at K -> unload
        if robot.cargo is not None and robot.pos == C.K_NODE:
            return {"kind": "unload", "lot": robot.cargo}

        # Rule 3: empty at a node with a waiting prepared lot -> pick up
        if robot.cargo is None:
            here_list = None
            if robot.pos == C.P_NODE and self.wait_P:
                here_list = self.wait_P
            elif robot.pos == C.Q_NODE and self.wait_Q:
                here_list = self.wait_Q
            if here_list:
                # earliest-prepared, tie-break lowest global index
                chosen = min(here_list, key=lambda l: (l.prepared_at, l.gidx))
                return {"kind": "pickup", "lot": chosen}

        # Rule 4: carrying cargo, not at K -> move toward K
        if robot.cargo is not None:
            nh = next_hop_toward(self.adj, self.dist_to_K, robot.pos)
            if nh is None:
                # already at K -- shouldn't reach here since rule 2 covers it
                return {"kind": "wait"}
            return {"kind": "move", "target": nh}

        # Rule 5: empty, no lot here -> move toward nearest node with a waiting lot
        candidates = []
        if self.wait_P:
            candidates.append((C.P_NODE, self.dist_to_P.get(robot.pos, 10**9)))
        if self.wait_Q:
            candidates.append((C.Q_NODE, self.dist_to_Q.get(robot.pos, 10**9)))
        if candidates:
            candidates.sort(key=lambda x: (x[1], x[0]))
            target_node, _ = candidates[0]
            dist_map = self.dist_to_P if target_node == C.P_NODE else self.dist_to_Q
            nh = next_hop_toward(self.adj, dist_map, robot.pos)
            if nh is None:
                return {"kind": "wait"}  # already there but list empty check above prevents this normally
            return {"kind": "move", "target": nh}

        # Rule 6: empty, no lot anywhere -> move toward home dock
        if robot.pos == robot.home:
            return {"kind": "wait"}
        dist_map = self.dist_to_P if robot.home == C.P_NODE else self.dist_to_Q
        nh = next_hop_toward(self.adj, dist_map, robot.pos)
        if nh is None:
            return {"kind": "wait"}
        return {"kind": "move", "target": nh}

    def apply_robot_action(self, robot, intent, t, remaining_budget, edges_used, other_final_pos):
        """Attempt to execute `intent` given remaining power budget and this-minute
        collision state. `other_final_pos` is the node the OTHER robot occupies
        as of this point in the minute's resolution (its pre-minute position if
        it has not been resolved yet, its just-decided position if it has).
        Returns (actual_kind, draw_used, detail_dict)."""
        kind = intent["kind"]
        if kind == "offline":
            return "offline", 0, {}
        if kind == "wait":
            return "wait", 0, {}

        if kind == "pickup":
            lot = intent["lot"]
            draw = C.POWER_DRAW["robot_pickup"]
            if draw > remaining_budget:
                return "wait", 0, {"refused": "power", "would_pickup": lot.gidx}
            # execute
            if robot.pos == C.P_NODE:
                self.wait_P.remove(lot)
            else:
                self.wait_Q.remove(lot)
            robot.cargo = lot
            lot.status = "in_transit"
            lot.picked_up_at = t
            return "pickup", draw, {"lot": lot.gidx}

        if kind == "unload":
            lot = intent["lot"]
            draw = C.POWER_DRAW["robot_unload"]
            if draw > remaining_budget:
                return "wait", 0, {"refused": "power", "would_unload": lot.gidx}
            robot.cargo = None
            lot.status = "waiting_at_K"
            lot.delivered_at = t
            self.wait_K.append(lot)
            return "unload", draw, {"lot": lot.gidx}

        if kind == "move":
            target = intent["target"]
            edge = frozenset((robot.pos, target))
            draw = C.POWER_DRAW["robot_move"]
            cap = C.NODE_CAPACITY.get(target, float("inf"))
            landing_count = (1 if other_final_pos == target else 0) + 1  # self always lands there
            blocked = False
            reason = None
            if edge in edges_used:
                blocked, reason = True, "edge_capacity"
            elif landing_count > cap:
                blocked, reason = True, "node_capacity"
            elif draw > remaining_budget:
                blocked, reason = True, "power"
            if blocked:
                return "wait", 0, {"refused": reason, "would_move_to": target}
            # execute
            edges_used.add(edge)
            robot.pos = target
            return "move", draw, {"to": target}

        raise AssertionError("unreachable")

    # -- oven pairing -----------------------------------------------------
    def oven_pairing_step(self, t, remaining_budget):
        if self.oven.is_busy(t):
            return 0, {}
        if self.oven.pending_anchor is None:
            if self.wait_K:
                anchor = min(self.wait_K, key=lambda l: (l.delivered_at, l.gidx))
                self.oven.pending_anchor = anchor
                self.oven.anchor_deadline = anchor.delivered_at + C.PAIRING_DEADLINE_SLACK
                self.trace_event(t, "oven_anchor_set", lot=anchor.gidx, deadline=self.oven.anchor_deadline)
            else:
                return 0, {}

        anchor = self.oven.pending_anchor
        partners = [l for l in self.wait_K if l is not anchor and l.family == anchor.family]
        if partners:
            partner = min(partners, key=lambda l: l.gidx)
            batch = [anchor, partner]
        elif t > self.oven.anchor_deadline:
            batch = [anchor]
        else:
            return 0, {}

        draw = C.POWER_DRAW["oven_op"]
        if draw > remaining_budget:
            return 0, {"refused": "power"}

        for l in batch:
            self.wait_K.remove(l)
            l.status = "curing"
            l.cure_start = t
            l.batch_id = self.oven.next_batch_id
        dur = C.cure_minutes(anchor.family)
        self.oven.busy_until = t + dur
        self.oven.batch = batch
        self.trace_event(t, "oven_start", lots=[l.gidx for l in batch], family=anchor.family,
                          dur=dur, busy_until=self.oven.busy_until, batch_id=self.oven.next_batch_id)
        self.oven.next_batch_id += 1
        self.oven.pending_anchor = None
        self.oven.anchor_deadline = None
        return draw, {"batch": [l.gidx for l in batch]}

    # -- tracing ------------------------------------------------------
    def trace_event(self, t, kind, **kwargs):
        row = {"t": t, "event": kind}
        row.update(kwargs)
        self.trace.append(row)

    # -- main loop ------------------------------------------------------
    def run(self, max_minutes=100000):
        t = 0
        minute_rows = []
        while self.n_done < self.n_lots_total and t < max_minutes:
            self.release_lots(t)
            self.finish_machines(t)
            self.finish_oven(t)

            if self.n_done >= self.n_lots_total:
                # All curing completed exactly as of the top of minute t (i.e.
                # finish_oven just closed out the last batch). No further
                # decision-making happens: production consumed minutes
                # [0, t), so the makespan is t itself.
                self.makespan = t
                break

            remaining = self.G
            mandatory = 0
            if self.P.is_busy(t):
                mandatory += self.P.draw
            if self.Q.is_busy(t):
                mandatory += self.Q.draw
            if self.oven.is_busy(t):
                mandatory += C.POWER_DRAW["oven_op"]
            remaining -= mandatory

            draws_this_minute = {"P_mandatory": self.P.draw if self.P.is_busy(t) else 0,
                                  "Q_mandatory": self.Q.draw if self.Q.is_busy(t) else 0,
                                  "oven_mandatory": C.POWER_DRAW["oven_op"] if self.oven.is_busy(t) else 0}

            # ordered admission pass: P start, Q start, R0, R1, oven start
            started_p, draw_p = self.try_start_machine(self.P, self.wait_P, t, remaining)
            remaining -= draw_p
            started_q, draw_q = self.try_start_machine(self.Q, self.wait_Q, t, remaining)
            remaining -= draw_q

            edges_used = set()
            # final_pos[i] tracks robot i's position as known at this point in
            # the minute's sequential resolution: pre-minute position until
            # that robot is itself resolved, then its resolved position.
            final_pos = [self.robots[0].pos, self.robots[1].pos]

            robot_draws = []
            robot_details = []
            for idx, r in enumerate(self.robots):
                other_idx = 1 - idx
                intent = self.decide_robot_action(r, t)
                before_pos = r.pos
                actual_kind, draw, detail = self.apply_robot_action(
                    r, intent, t, remaining, edges_used, final_pos[other_idx]
                )
                remaining -= draw
                robot_draws.append(draw)
                robot_details.append((r.rid, before_pos, actual_kind, draw, detail))
                final_pos[idx] = r.pos

            oven_draw, oven_detail = self.oven_pairing_step(t, remaining)
            remaining -= oven_draw

            total_power = mandatory + draw_p + draw_q + sum(robot_draws) + oven_draw
            mult = C.tariff_multiplier(t)
            self.bill += total_power * mult

            minute_rows.append({
                "t": t,
                "P_busy": self.P.is_busy(t) or started_p,
                "Q_busy": self.Q.is_busy(t) or started_q,
                "oven_busy": self.oven.is_busy(t) or bool(oven_detail.get("batch")),
                "R0_action": robot_details[0][2], "R0_pos": self.robots[0].pos, "R0_cargo": self.robots[0].cargo.gidx if self.robots[0].cargo else None,
                "R1_action": robot_details[1][2], "R1_pos": self.robots[1].pos, "R1_cargo": self.robots[1].cargo.gidx if self.robots[1].cargo else None,
                "power_total": total_power, "tariff_mult": mult, "bill_delta": total_power * mult,
                "fixture_held": self.fixture_held,
            })

            t += 1
        else:
            if t >= max_minutes:
                raise RuntimeError(f"{self.name}: simulation did not terminate within {max_minutes} minutes")

        self.minute_rows = minute_rows
        return {
            "design": self.name,
            "F": self.F, "G": self.G, "aisle": self.aisle, "capital": self.capital,
            "makespan": self.makespan,
            "bill": self.bill,
        }

    # -- output helpers ---------------------------------------------------
    def lot_log(self):
        rows = []
        for l in self.lots:
            rows.append({
                "gidx": l.gidx, "j": l.j, "s": l.s, "family": l.family,
                "release": l.release, "pbase": l.pbase, "qbase": l.qbase,
                "assigned_machine": l.assigned_machine, "setup_used": l.setup_used,
                "prepared_at": l.prepared_at, "picked_up_at": l.picked_up_at,
                "delivered_at": l.delivered_at, "cure_start": l.cure_start,
                "cure_end": l.cure_end, "batch_id": l.batch_id, "status": l.status,
            })
        return rows

    def write_outputs(self, outdir):
        import os
        os.makedirs(outdir, exist_ok=True)
        base = self.name

        with open(os.path.join(outdir, f"{base}_minute_trace.csv"), "w", newline="") as f:
            if self.minute_rows:
                w = csv.DictWriter(f, fieldnames=list(self.minute_rows[0].keys()))
                w.writeheader()
                w.writerows(self.minute_rows)

        with open(os.path.join(outdir, f"{base}_events.jsonl"), "w") as f:
            for e in self.trace:
                f.write(json.dumps(e) + "\n")

        with open(os.path.join(outdir, f"{base}_lot_log.csv"), "w", newline="") as f:
            rows = self.lot_log()
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)


def run_design(name, outdir=None):
    sim = Simulator(name)
    summary = sim.run()
    if outdir:
        sim.write_outputs(outdir)
    return sim, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("design", choices=list(C.DESIGNS.keys()) + ["ALL"])
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--summary-json", default=None)
    args = ap.parse_args()

    names = list(C.DESIGNS.keys()) if args.design == "ALL" else [args.design]
    summaries = []
    for name in names:
        sim, summary = run_design(name, outdir=args.outdir)
        summaries.append(summary)
        print(json.dumps(summary))

    if args.summary_json:
        with open(args.summary_json, "w") as f:
            json.dump(summaries, f, indent=2)


if __name__ == "__main__":
    main()
