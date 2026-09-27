"""
KILNWORKS R3 -- INDEPENDENT VERIFIER.

A second, separately-written re-derivation of the full per-minute trace for
a design, sharing ONLY the immutable constants in kw_constants.py with the
primary implementation (kw_primary_sim.py).  It is deliberately built with
a different internal architecture:

  * structure-of-arrays (parallel dicts keyed by global index) instead of a
    Lot class;
  * plant state kept in one flat dict instead of instance attributes;
  * shortest-path tables built with a hand-rolled array-based BFS (no
    collections.deque) instead of the primary's deque-based BFS;
  * the per-minute step is one long function using local closures instead
    of a method-per-concern class design;
  * tie-breaks are expressed as explicit sorted() calls with tuple keys
    written independently from the primary's min()-with-key calls.

If this file and kw_primary_sim.py produce the same minute-by-minute
outcome for all six designs, that is strong evidence the packet's rules
were both read and implemented the same (and correct) way twice.
"""

import kw_constants as C


# ---------------------------------------------------------------------------
# graph helpers (independent array-based BFS, not the primary's deque BFS)
# ---------------------------------------------------------------------------
def build_adj(aisle_open):
    edges = list(C.BASE_EDGES)
    if aisle_open:
        edges.append(C.OPEN_EXTRA_EDGE)
    adj = {n: [] for n in C.NODES}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    for n in adj:
        adj[n] = sorted(set(adj[n]))
    return adj


def bfs_distances(adj, src):
    dist = {n: -1 for n in adj}
    dist[src] = 0
    frontier = [src]
    while frontier:
        nxt = []
        for u in frontier:
            for v in adj[u]:
                if dist[v] == -1:
                    dist[v] = dist[u] + 1
                    nxt.append(v)
        frontier = nxt
    return {n: (d if d >= 0 else None) for n, d in dist.items()}


def step_toward(adj, dist, cur):
    d = dist[cur]
    options = [v for v in adj[cur] if dist[v] is not None and dist[v] == d - 1]
    if not options:
        return None
    return sorted(options)[0]


# ---------------------------------------------------------------------------
# lot table (structure-of-arrays)
# ---------------------------------------------------------------------------
def build_lot_table():
    T = {}
    for s in range(C.N_CAMPAIGNS):
        for j in range(C.LOTS_PER_CAMPAIGN):
            g = 5 * s + j
            fam = (j + s) % 2
            rel_local = 2 * (j // 2)
            rel = C.CADENCE * s + rel_local
            pb = 5 + ((j * j) + 2 * s) % 4
            qb = 4 + (3 * j + s) % 5
            T[g] = dict(s=s, j=j, gidx=g, family=fam, release=rel, pbase=pb, qbase=qb,
                        machine=None, t_start=None, t_ready=None, t_pickup=None,
                        carrier=None, t_deliver_decided=None, t_arrive=None,
                        oven_batch_id=None, t_cure_start=None, t_cure_end=None)
    return T


def setup_of(remembered, fam):
    if remembered is None:
        return 0
    return 0 if remembered == fam else 2


# ---------------------------------------------------------------------------
# verifier simulation
# ---------------------------------------------------------------------------
def run_verifier(design_id, record_trace=True):
    cfg = C.DESIGNS[design_id]
    F, G, aisle_open, capital = cfg["F"], cfg["G"], cfg["aisle_open"], cfg["capital"]

    adj = build_adj(aisle_open)
    dK = bfs_distances(adj, C.K)
    dP = bfs_distances(adj, C.P_NODE)
    dQ = bfs_distances(adj, C.Q_NODE)
    dHome = {0: dP, 1: dQ}

    lots = build_lot_table()

    st = dict(
        t=0,
        P_busy_until=None, P_start=None, P_family=None,
        Q_busy_until=None, Q_start=None, Q_family=None,
        Q_cum=0, Q_freeze_from=None, Q_freeze_until=None, Q_freeze_fired=False,
        held=0,
        P_buf=[], Q_buf=[],           # lists of gidx
        Kq=[],                        # gidx waiting for oven, uncured
        pending_arrivals={},          # minute -> [gidx]
        oven_busy_until=None, oven_start=None, oven_members=None,
        anchor=None, anchor_deadline=None,
        r_pos={0: C.START_POS[0], 1: C.START_POS[1]},
        r_cargo={0: None, 1: None},
        r_off_from={0: None, 1: None}, r_off_until={0: None, 1: None},
        r_fired={0: False, 1: False},
        bill=0,
    )

    trace = []
    next_batch_id = [0]
    safety_cap = 3000

    def buf_of(node):
        if node == C.P_NODE:
            return st["P_buf"]
        if node == C.Q_NODE:
            return st["Q_buf"]
        return []

    def nearest_target(node):
        opts = []
        if st["P_buf"]:
            opts.append((dP[node], C.P_NODE))
        if st["Q_buf"]:
            opts.append((dQ[node], C.Q_NODE))
        if not opts:
            return None
        opts_sorted = sorted(opts, key=lambda pr: (pr[0], pr[1]))
        return opts_sorted[0][1]

    def pick_machine_candidate(machine, t):
        if st["held"] >= F:
            return None
        pool = [g for g, rec in lots.items() if rec["machine"] is None and rec["release"] <= t]
        if not pool:
            return None
        remembered = st["P_family"] if machine == "P" else st["Q_family"]
        scored = []
        for g in pool:
            rec = lots[g]
            dur = rec["pbase"] if machine == "P" else rec["qbase"]
            cost = setup_of(remembered, rec["family"]) + dur
            scored.append((cost, g))
        scored.sort(key=lambda pr: (pr[0], pr[1]))
        return scored[0][1]

    def start_machine(machine, g, t):
        rec = lots[g]
        dur = rec["pbase"] if machine == "P" else rec["qbase"]
        remembered = st["P_family"] if machine == "P" else st["Q_family"]
        su = setup_of(remembered, rec["family"])
        rec["machine"] = machine
        rec["t_start"] = t
        st["held"] += 1
        if machine == "P":
            st["P_busy_until"] = t + su + dur
            st["P_start"] = t
            st["P_family"] = rec["family"]
        else:
            st["Q_busy_until"] = t + su + dur
            st["Q_start"] = t
            st["Q_family"] = rec["family"]

    def robot_turn(rid, other_cur_pos, other_new_pos, other_edge, t, remaining):
        pos = st["r_pos"][rid]
        cargo = st["r_cargo"][rid]

        off_from, off_until = st["r_off_from"][rid], st["r_off_until"][rid]
        if off_from is not None and off_from <= t <= off_until:
            return dict(kind="offline", new_pos=pos, edge=None, draw=0,
                        label="offline", pickup=None, unload=False), remaining

        # priority 2 unload
        if cargo is not None and pos == C.K:
            if remaining >= C.DRAW["robot_action"]:
                return dict(kind="unload", new_pos=pos, edge=None,
                            draw=C.DRAW["robot_action"], label="unload",
                            pickup=None, unload=True), remaining - C.DRAW["robot_action"]
            return dict(kind="wait", new_pos=pos, edge=None, draw=0,
                        label="wait_pow_unload", pickup=None, unload=False), remaining

        # priority 3 pickup
        if cargo is None:
            here = buf_of(pos)
            if here:
                ordered = sorted(here, key=lambda g: (lots[g]["t_ready"], g))
                chosen = ordered[0]
                if remaining >= C.DRAW["robot_action"]:
                    return dict(kind="pickup", new_pos=pos, edge=None,
                                draw=C.DRAW["robot_action"], label="pickup",
                                pickup=chosen, unload=False), remaining - C.DRAW["robot_action"]
                return dict(kind="wait", new_pos=pos, edge=None, draw=0,
                            label="wait_pow_pickup", pickup=None, unload=False), remaining

        # priority 4 move to K
        if cargo is not None and pos != C.K:
            nh = step_toward(adj, dK, pos)
            return resolve_move(pos, nh, other_cur_pos, other_new_pos, other_edge, remaining)

        # priority 5 move to nearest waiting lot
        if cargo is None:
            tgt = nearest_target(pos)
            if tgt is not None:
                darr = dP if tgt == C.P_NODE else dQ
                nh = step_toward(adj, darr, pos)
                return resolve_move(pos, nh, other_cur_pos, other_new_pos, other_edge, remaining)

        # priority 6 move home
        home = C.HOME[rid]
        if pos == home:
            return dict(kind="wait", new_pos=pos, edge=None, draw=0,
                        label="wait_home", pickup=None, unload=False), remaining
        nh = step_toward(adj, dHome[rid], pos)
        return resolve_move(pos, nh, other_cur_pos, other_new_pos, other_edge, remaining)

    def resolve_move(pos, nh, other_cur_pos, other_new_pos, other_edge, remaining):
        if nh is None:
            return dict(kind="wait", new_pos=pos, edge=None, draw=0,
                        label="wait_nopath", pickup=None, unload=False), remaining
        e = frozenset((pos, nh))
        if other_edge is not None and other_edge == e:
            return dict(kind="wait", new_pos=pos, edge=None, draw=0,
                        label="wait_edge_collision", pickup=None, unload=False), remaining
        occ_other = 0
        if other_new_pos is not None:
            occ_other = 1 if other_new_pos == nh else 0
        else:
            occ_other = 1 if other_cur_pos == nh else 0
        if occ_other + 1 > C.capacity(nh):
            return dict(kind="wait", new_pos=pos, edge=None, draw=0,
                        label="wait_node_capacity", pickup=None, unload=False), remaining
        if remaining < C.DRAW["robot_action"]:
            return dict(kind="wait", new_pos=pos, edge=None, draw=0,
                        label="wait_pow_move", pickup=None, unload=False), remaining
        return dict(kind="move", new_pos=nh, edge=e, draw=C.DRAW["robot_action"],
                    label=f"move_{pos}_{nh}", pickup=None, unload=False), remaining - C.DRAW["robot_action"]

    def apply_robot(rid, res, t):
        if res["kind"] == "move":
            st["r_pos"][rid] = res["new_pos"]
            if rid == 0 and res["new_pos"] == C.JUNCTION and not st["r_fired"][0]:
                st["r_fired"][0] = True
                st["r_off_from"][0] = t + 1
                st["r_off_until"][0] = t + C.NODE4_DISRUPTION_MINUTES
        elif res["kind"] == "pickup":
            g = res["pickup"]
            pos = st["r_pos"][rid]
            buf_of(pos).remove(g)
            lots[g]["t_pickup"] = t
            lots[g]["carrier"] = rid
            st["r_cargo"][rid] = g
        elif res["kind"] == "unload":
            g = st["r_cargo"][rid]
            lots[g]["t_deliver_decided"] = t
            lots[g]["t_arrive"] = t + 1
            st["pending_arrivals"].setdefault(t + 1, []).append(g)
            st["r_cargo"][rid] = None

    def oven_step(t, remaining):
        if st["oven_busy_until"] is not None:
            return None
        if st["anchor"] is None:
            if not st["Kq"]:
                return None
            ordered = sorted(st["Kq"], key=lambda g: (lots[g]["t_arrive"], g))
            a = ordered[0]
            st["anchor"] = a
            st["anchor_deadline"] = lots[a]["t_arrive"] + C.ANCHOR_DEADLINE_OFFSET
        a = st["anchor"]
        fam = lots[a]["family"]
        partner_opts = sorted([g for g in st["Kq"] if g != a and lots[g]["family"] == fam])
        if partner_opts:
            members = [a, partner_opts[0]]
        elif t >= st["anchor_deadline"]:
            members = [a]
        else:
            return None
        if remaining < C.DRAW["oven"]:
            return None
        dur = C.cure_duration(fam)
        st["oven_start"] = t
        st["oven_busy_until"] = t + dur
        bid = next_batch_id[0]
        next_batch_id[0] += 1
        st["oven_members"] = members
        for g in members:
            st["Kq"].remove(g)
            lots[g]["oven_batch_id"] = bid
            lots[g]["t_cure_start"] = t
            lots[g]["t_cure_end"] = t + dur
        st["anchor"] = None
        st["anchor_deadline"] = None
        return list(members)

    final_makespan = None
    while True:
        if all(lots[g]["t_cure_end"] is not None for g in lots):
            fm = max(lots[g]["t_cure_end"] for g in lots)
            if st["t"] >= fm:
                final_makespan = fm
                break
        if st["t"] > safety_cap:
            raise RuntimeError(f"{design_id} verifier: safety cap exceeded")

        t = st["t"]
        for g in st["pending_arrivals"].pop(t, []):
            st["Kq"].append(g)

        if st["oven_busy_until"] is not None and st["oven_busy_until"] == t:
            for g in st["oven_members"]:
                st["held"] -= 1
            st["oven_busy_until"] = None
            st["oven_start"] = None
            st["oven_members"] = None

        if st["P_busy_until"] is not None and st["P_busy_until"] == t:
            g = [gg for gg, rec in lots.items() if rec["machine"] == "P" and rec["t_ready"] is None][0]
            lots[g]["t_ready"] = t
            st["P_buf"].append(g)
            st["P_busy_until"] = None
            st["P_start"] = None

        if st["Q_busy_until"] is not None and st["Q_busy_until"] == t:
            g = [gg for gg, rec in lots.items() if rec["machine"] == "Q" and rec["t_ready"] is None][0]
            lots[g]["t_ready"] = t
            st["Q_buf"].append(g)
            before = st["Q_cum"]
            st["Q_cum"] += lots[g]["qbase"]
            if (not st["Q_freeze_fired"]) and before < C.Q_CUM_TRIGGER <= st["Q_cum"]:
                st["Q_freeze_fired"] = True
                st["Q_freeze_from"] = t + 1
                st["Q_freeze_until"] = t + C.Q_FREEZE_MINUTES
            st["Q_busy_until"] = None
            st["Q_start"] = None

        remaining = G
        mand_p = C.DRAW["P"] if (st["P_busy_until"] is not None and st["P_start"] is not None and st["P_start"] < t) else 0
        mand_q = C.DRAW["Q"] if (st["Q_busy_until"] is not None and st["Q_start"] is not None and st["Q_start"] < t) else 0
        mand_oven = C.DRAW["oven"] if (st["oven_busy_until"] is not None and st["oven_start"] is not None and st["oven_start"] < t) else 0
        mand = mand_p + mand_q + mand_oven
        remaining -= mand

        draws = dict(P=mand_p, Q=mand_q, oven=mand_oven, R0=0, R1=0)
        events = dict(P_start=None, Q_start=None, R0=None, R1=None, oven_start=None)

        if st["P_busy_until"] is None:
            cand = pick_machine_candidate("P", t)
            if cand is not None and remaining >= C.DRAW["P"]:
                start_machine("P", cand, t)
                remaining -= C.DRAW["P"]
                draws["P"] += C.DRAW["P"]
                events["P_start"] = cand

        frozen = st["Q_freeze_from"] is not None and st["Q_freeze_from"] <= t <= st["Q_freeze_until"]
        if st["Q_busy_until"] is None and not frozen:
            cand = pick_machine_candidate("Q", t)
            if cand is not None and remaining >= C.DRAW["Q"]:
                start_machine("Q", cand, t)
                remaining -= C.DRAW["Q"]
                draws["Q"] += C.DRAW["Q"]
                events["Q_start"] = cand

        pos1_before = st["r_pos"][1]
        res0, remaining = robot_turn(0, other_cur_pos=pos1_before, other_new_pos=None,
                                      other_edge=None, t=t, remaining=remaining)
        draws["R0"] = res0["draw"]
        events["R0"] = res0["label"]

        pos0_before = st["r_pos"][0]
        res1, remaining = robot_turn(1, other_cur_pos=pos0_before, other_new_pos=res0["new_pos"],
                                      other_edge=res0["edge"], t=t, remaining=remaining)
        draws["R1"] = res1["draw"]
        events["R1"] = res1["label"]

        apply_robot(0, res0, t)
        apply_robot(1, res1, t)

        oe = oven_step(t, remaining)
        if oe is not None:
            draws["oven"] += C.DRAW["oven"]
            events["oven_start"] = oe

        total = sum(draws.values())
        if total > G:
            raise RuntimeError(f"{design_id} verifier: power overflow t={t} total={total} G={G}")
        mult = C.tariff_multiplier(t)
        st["bill"] += total * mult

        if record_trace:
            trace.append(dict(
                t=t, draws=dict(draws),
                events=events, total_power=total, mult=mult, held_fixtures=st["held"],
                P_busy=st["P_busy_until"], Q_busy=st["Q_busy_until"], oven_busy=st["oven_busy_until"],
                q_frozen=frozen,
                r0_pos=st["r_pos"][0], r0_cargo=st["r_cargo"][0],
                r1_pos=st["r_pos"][1], r1_cargo=st["r_cargo"][1],
                P_buffer=list(st["P_buf"]), Q_buffer=list(st["Q_buf"]), K_queue=list(st["Kq"]),
                anchor=st["anchor"], anchor_deadline=st["anchor_deadline"],
            ))

        st["t"] += 1

    return dict(design_id=design_id, makespan=final_makespan, bill=st["bill"],
                capital=capital, trace=trace, lots=lots)


if __name__ == "__main__":
    for d in C.DESIGN_ORDER:
        r = run_verifier(d)
        print(d, "makespan=", r["makespan"], "bill=", r["bill"], "capital=", r["capital"])
