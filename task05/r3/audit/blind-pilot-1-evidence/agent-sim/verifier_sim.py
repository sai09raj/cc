#!/usr/bin/env python3
"""
KILNWORKS retrofit INDEPENDENT VERIFIER.

This is a *separately coded* re-implementation of the same packet rules,
written from the specification text again (not derived from kiln_sim.py's
code). It intentionally uses different internal representations and control
flow so that agreement between the two implementations is meaningful:

  - state kept as a single flat dict-of-dicts ("W" for "world"), not classes
  - all-pairs shortest paths precomputed once via Floyd-Warshall + explicit
    next-hop table, instead of kiln_sim's per-call BFS
  - the five-step power-admission pass is expressed as one generic
    "spend(budget, amount)" closure walked over an explicit step list,
    instead of separate try_start_machine()/apply_robot_action() methods
  - robot dispatch priority is one linear cascade of independent local
    functions rather kiln_sim's single decide_robot_action() method

Only the literal constants in common.py (transcribed once, directly off the
packet) are shared with kiln_sim.py. All decision logic below was
transcribed independently from the packet text.

Usage:
    python3 verifier_sim.py D0 [--outdir traces_v2]
"""
import argparse
import csv
import json
import os
import sys

import common as C


# ---------------------------------------------------------------------------
# Graph: all-pairs shortest paths via Floyd-Warshall + explicit next-hop
# ---------------------------------------------------------------------------
def make_graph(aisle):
    nodes = list(range(9))
    edges = list(C.EDGES_COMMON)
    if aisle == "open":
        edges = edges + [C.EDGE_OPEN_ONLY]
    INF = 10 ** 9
    dist = {(a, b): (0 if a == b else INF) for a in nodes for b in nodes}
    nbrs = {a: set() for a in nodes}
    for (a, b) in edges:
        dist[(a, b)] = 1
        dist[(b, a)] = 1
        nbrs[a].add(b)
        nbrs[b].add(a)
    for k in nodes:
        for i in nodes:
            dik = dist[(i, k)]
            if dik == INF:
                continue
            for j in nodes:
                nd = dik + dist[(k, j)]
                if nd < dist[(i, j)]:
                    dist[(i, j)] = nd
    return nodes, nbrs, dist


def next_hop(nbrs, dist, src, dst):
    """Lowest-id neighbor of src minimizing distance to dst (must decrease by 1)."""
    if src == dst:
        return None
    target_d = dist[(src, dst)] - 1
    choices = [n for n in nbrs[src] if dist[(n, dst)] == target_d]
    if not choices:
        return None
    return min(choices)


# ---------------------------------------------------------------------------
# World-state construction
# ---------------------------------------------------------------------------
def new_world(design_name):
    cfg = C.DESIGNS[design_name]
    nodes, nbrs, dist = make_graph(cfg["aisle"])

    lots = {}
    for s in range(C.NUM_CAMPAIGNS):
        for j in range(C.LOTS_PER_CAMPAIGN):
            g = C.global_index(j, s)
            lots[g] = {
                "j": j, "s": s, "gidx": g,
                "family": C.family_of(j, s),
                "release": C.release_abs(j, s),
                "pbase": C.pbase(j, s),
                "qbase": C.qbase(j, s),
                "state": "PENDING",       # PENDING -> RELEASED -> ONMACH -> ATDOCK
                                            # -> CARRIED -> ATK -> CURING -> DONE
                "machine": None, "setup": None,
                "prep_done_t": None, "pickup_t": None, "dock_t": None,
                "cure_t0": None, "cure_t1": None, "batch": None,
            }

    W = {
        "design": design_name, "F": cfg["F"], "G": cfg["G"], "aisle": cfg["aisle"],
        "nbrs": nbrs, "dist": dist,
        "lots": lots,
        "mach": {
            "P": {"node": C.P_NODE, "draw": C.POWER_DRAW["P_op"], "free_t": 0, "fam": None, "lot": None},
            "Q": {"node": C.Q_NODE, "draw": C.POWER_DRAW["Q_op"], "free_t": 0, "fam": None, "lot": None},
        },
        "dockwait": {C.P_NODE: [], C.Q_NODE: []},   # lists of gidx, in arrival order
        "kwait": [],                                    # list of gidx at K uncured, in arrival order
        "oven": {"free_t": 0, "batch": None, "anchor": None, "deadline": None},
        "robots": {
            0: {"node": C.ROBOT0_HOME, "home": C.ROBOT0_HOME, "cargo": None,
                "off_seen4": False, "off_end": None},
            1: {"node": C.ROBOT1_HOME, "home": C.ROBOT1_HOME, "cargo": None},
        },
        "held_fixtures": 0,
        "bill": 0,
        "n_done": 0,
        "minute_log": [],
        "events": [],
    }
    return W


def log_event(W, t, kind, **kw):
    row = {"t": t, "event": kind}
    row.update(kw)
    W["events"].append(row)


# ---------------------------------------------------------------------------
# Per-minute phases
# ---------------------------------------------------------------------------
def phase_release(W, t):
    for lot in W["lots"].values():
        if lot["state"] == "PENDING" and lot["release"] <= t:
            lot["state"] = "RELEASED"


def phase_machine_completion(W, t):
    for mname, m in W["mach"].items():
        if m["lot"] is not None and m["free_t"] == t:
            g = m["lot"]
            lot = W["lots"][g]
            lot["state"] = "ATDOCK"
            lot["prep_done_t"] = t
            W["dockwait"][m["node"]].append(g)
            log_event(W, t, "machine_complete", machine=mname, lot=g)
            m["lot"] = None


def phase_oven_completion(W, t):
    ov = W["oven"]
    if ov["batch"] is not None and ov["free_t"] == t:
        for g in ov["batch"]:
            lot = W["lots"][g]
            lot["state"] = "DONE"
            lot["cure_t1"] = t
            W["held_fixtures"] -= 1
            W["n_done"] += 1
        log_event(W, t, "oven_complete", batch=list(ov["batch"]))
        ov["batch"] = None


def best_candidate(W, t, machine_name):
    m = W["mach"][machine_name]
    pool = [lot for lot in W["lots"].values()
            if lot["state"] == "RELEASED" and W["held_fixtures"] < W["F"]]
    if not pool:
        return None
    def key(lot):
        fam_ok = (m["fam"] is None) or (m["fam"] == lot["family"])
        setup = C.SETUP_MATCH if fam_ok else C.SETUP_MISMATCH
        base = lot["pbase"] if machine_name == "P" else lot["qbase"]
        return (setup + base, lot["gidx"])
    pool.sort(key=key)
    return pool[0]


def start_machine_if_possible(W, t, machine_name, budget_left):
    m = W["mach"][machine_name]
    if m["free_t"] > t:
        return 0  # busy
    cand = best_candidate(W, t, machine_name)
    if cand is None:
        return 0
    if m["draw"] > budget_left:
        return 0
    fam_ok = (m["fam"] is None) or (m["fam"] == cand["family"])
    setup = C.SETUP_MATCH if fam_ok else C.SETUP_MISMATCH
    base = cand["pbase"] if machine_name == "P" else cand["qbase"]
    dur = setup + base
    m["free_t"] = t + dur
    m["fam"] = cand["family"]
    m["lot"] = cand["gidx"]
    cand["state"] = "ONMACH"
    cand["machine"] = machine_name
    cand["setup"] = setup
    W["held_fixtures"] += 1
    log_event(W, t, "machine_start", machine=machine_name, lot=cand["gidx"],
              family=cand["family"], setup=setup, dur=dur, free_t=m["free_t"])
    return m["draw"]


# -- robot priority cascade (rules 1..6, transcribed independently) --------
def robot_intended_action(W, t, rid):
    r = W["robots"][rid]
    node = r["node"]

    # rule 1: Robot 0's one-time forced-offline window at first node-4 arrival
    if rid == 0:
        if (not r["off_seen4"]) and node == C.JUNCTION_NODE:
            r["off_seen4"] = True
            r["off_end"] = t + C.FORCED_OFFLINE_MINUTES
        if r["off_end"] is not None and t < r["off_end"]:
            return ("OFFLINE", None)

    # rule 2: carrying + at K -> unload
    if r["cargo"] is not None and node == C.K_NODE:
        return ("UNLOAD", r["cargo"])

    # rule 3: empty + waiting lot at this node -> pick up earliest-prepared
    if r["cargo"] is None and node in W["dockwait"] and W["dockwait"][node]:
        cand_gidxs = W["dockwait"][node]
        best = min(cand_gidxs, key=lambda g: (W["lots"][g]["prep_done_t"], g))
        return ("PICKUP", best)

    # rule 4: carrying, not at K -> step toward K
    if r["cargo"] is not None:
        nh = next_hop(W["nbrs"], W["dist"], node, C.K_NODE)
        if nh is None:
            return ("WAIT", None)
        return ("MOVE", nh)

    # rule 5: empty, nothing here -> step toward nearest node with a waiting lot
    opts = []
    for dock_node in (C.P_NODE, C.Q_NODE):
        if W["dockwait"][dock_node]:
            opts.append((W["dist"][(node, dock_node)], dock_node))
    if opts:
        opts.sort()
        _, target = opts[0]
        nh = next_hop(W["nbrs"], W["dist"], node, target)
        if nh is None:
            return ("WAIT", None)
        return ("MOVE", nh)

    # rule 6: empty, nothing anywhere -> step toward home
    if node == r["home"]:
        return ("WAIT", None)
    nh = next_hop(W["nbrs"], W["dist"], node, r["home"])
    if nh is None:
        return ("WAIT", None)
    return ("MOVE", nh)


def execute_robot_action(W, t, rid, action, budget_left, edge_locks, peer_node):
    r = W["robots"][rid]
    kind, arg = action

    if kind in ("OFFLINE", "WAIT"):
        return 0, kind

    if kind == "PICKUP":
        draw = C.POWER_DRAW["robot_pickup"]
        if draw > budget_left:
            return 0, "WAIT"
        g = arg
        W["dockwait"][r["node"]].remove(g)
        r["cargo"] = g
        W["lots"][g]["state"] = "CARRIED"
        W["lots"][g]["pickup_t"] = t
        return draw, "PICKUP"

    if kind == "UNLOAD":
        draw = C.POWER_DRAW["robot_unload"]
        if draw > budget_left:
            return 0, "WAIT"
        g = arg
        r["cargo"] = None
        W["lots"][g]["state"] = "ATK"
        W["lots"][g]["dock_t"] = t
        W["kwait"].append(g)
        return draw, "UNLOAD"

    if kind == "MOVE":
        target = arg
        draw = C.POWER_DRAW["robot_move"]
        edge_key = tuple(sorted((r["node"], target)))
        cap = C.NODE_CAPACITY.get(target, 10 ** 9)
        occupancy_if_moved = (1 if peer_node == target else 0) + 1
        if edge_key in edge_locks:
            return 0, "WAIT"
        if occupancy_if_moved > cap:
            return 0, "WAIT"
        if draw > budget_left:
            return 0, "WAIT"
        edge_locks.add(edge_key)
        r["node"] = target
        return draw, "MOVE"

    raise ValueError(kind)


def phase_robots(W, t, budget_left):
    order = [0, 1]
    edge_locks = set()
    node_now = {0: W["robots"][0]["node"], 1: W["robots"][1]["node"]}
    total = 0
    kinds = {}
    for rid in order:
        peer = 1 - rid
        action = robot_intended_action(W, t, rid)
        draw, kind = execute_robot_action(W, t, rid, action, budget_left, edge_locks, node_now[peer])
        budget_left -= draw
        total += draw
        kinds[rid] = kind
        node_now[rid] = W["robots"][rid]["node"]
    return total, budget_left, kinds


def phase_oven(W, t, budget_left):
    ov = W["oven"]
    if ov["batch"] is not None:
        return 0, budget_left  # already curing; mandatory draw handled by caller
    if ov["anchor"] is None:
        if W["kwait"]:
            g = min(W["kwait"], key=lambda x: (W["lots"][x]["dock_t"], x))
            ov["anchor"] = g
            ov["deadline"] = W["lots"][g]["dock_t"] + C.PAIRING_DEADLINE_SLACK
            log_event(W, t, "anchor_set", lot=g, deadline=ov["deadline"])
        else:
            return 0, budget_left

    a = ov["anchor"]
    afam = W["lots"][a]["family"]
    partners = [g for g in W["kwait"] if g != a and W["lots"][g]["family"] == afam]
    if partners:
        p = min(partners)
        batch = [a, p]
    elif t > ov["deadline"]:
        batch = [a]
    else:
        return 0, budget_left

    draw = C.POWER_DRAW["oven_op"]
    if draw > budget_left:
        return 0, budget_left  # refused; anchor/deadline persist

    for g in batch:
        W["kwait"].remove(g)
        W["lots"][g]["state"] = "CURING"
        W["lots"][g]["cure_t0"] = t
        W["lots"][g]["batch"] = tuple(batch)
    dur = C.cure_minutes(afam)
    ov["free_t"] = t + dur
    ov["batch"] = batch
    log_event(W, t, "oven_start", lots=list(batch), family=afam, dur=dur, free_t=ov["free_t"])
    ov["anchor"] = None
    ov["deadline"] = None
    return draw, budget_left - draw


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def run(design_name, max_minutes=100000):
    W = new_world(design_name)
    total_lots = len(W["lots"])
    t = 0
    while W["n_done"] < total_lots:
        if t > max_minutes:
            raise RuntimeError(f"{design_name}: exceeded {max_minutes} minutes without finishing")

        phase_release(W, t)
        phase_machine_completion(W, t)
        phase_oven_completion(W, t)

        if W["n_done"] >= total_lots:
            W["makespan"] = t
            break

        G = W["G"]
        mandatory = 0
        if W["mach"]["P"]["lot"] is not None:
            mandatory += W["mach"]["P"]["draw"]
        if W["mach"]["Q"]["lot"] is not None:
            mandatory += W["mach"]["Q"]["draw"]
        if W["oven"]["batch"] is not None:
            mandatory += C.POWER_DRAW["oven_op"]
        budget = G - mandatory

        draw_p = start_machine_if_possible(W, t, "P", budget)
        budget -= draw_p
        draw_q = start_machine_if_possible(W, t, "Q", budget)
        budget -= draw_q

        draw_r, budget, robot_kinds = phase_robots(W, t, budget)

        draw_ov, budget = phase_oven(W, t, budget)

        total_power = mandatory + draw_p + draw_q + draw_r + draw_ov
        mult = C.tariff_multiplier(t)
        W["bill"] += total_power * mult

        W["minute_log"].append({
            "t": t,
            "P_busy": W["mach"]["P"]["lot"] is not None,
            "Q_busy": W["mach"]["Q"]["lot"] is not None,
            "oven_busy": W["oven"]["batch"] is not None,
            "R0_action": robot_kinds[0].lower(), "R0_pos": W["robots"][0]["node"],
            "R0_cargo": W["robots"][0]["cargo"],
            "R1_action": robot_kinds[1].lower(), "R1_pos": W["robots"][1]["node"],
            "R1_cargo": W["robots"][1]["cargo"],
            "power_total": total_power, "tariff_mult": mult, "bill_delta": total_power * mult,
            "fixture_held": W["held_fixtures"],
        })
        t += 1

    summary = {
        "design": design_name, "F": W["F"], "G": W["G"], "aisle": W["aisle"],
        "capital": C.DESIGNS[design_name]["capital"],
        "makespan": W["makespan"], "bill": W["bill"],
    }
    return W, summary


def write_outputs(W, outdir):
    os.makedirs(outdir, exist_ok=True)
    base = W["design"]
    with open(os.path.join(outdir, f"{base}_minute_trace.csv"), "w", newline="") as f:
        rows = W["minute_log"]
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    with open(os.path.join(outdir, f"{base}_events.jsonl"), "w") as f:
        for e in W["events"]:
            f.write(json.dumps(e) + "\n")
    with open(os.path.join(outdir, f"{base}_lot_log.csv"), "w", newline="") as f:
        rows = []
        for g in sorted(W["lots"]):
            l = W["lots"][g]
            rows.append({
                "gidx": g, "j": l["j"], "s": l["s"], "family": l["family"],
                "release": l["release"], "pbase": l["pbase"], "qbase": l["qbase"],
                "assigned_machine": l["machine"], "setup_used": l["setup"],
                "prepared_at": l["prep_done_t"], "picked_up_at": l["pickup_t"],
                "delivered_at": l["dock_t"], "cure_start": l["cure_t0"],
                "cure_end": l["cure_t1"], "batch_id": l["batch"], "status": l["state"],
            })
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("design", choices=list(C.DESIGNS.keys()) + ["ALL"])
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--summary-json", default=None)
    args = ap.parse_args()

    names = list(C.DESIGNS.keys()) if args.design == "ALL" else [args.design]
    summaries = []
    for name in names:
        W, summary = run(name)
        if args.outdir:
            write_outputs(W, args.outdir)
        summaries.append(summary)
        print(json.dumps(summary))

    if args.summary_json:
        with open(args.summary_json, "w") as f:
            json.dump(summaries, f, indent=2)


if __name__ == "__main__":
    main()
