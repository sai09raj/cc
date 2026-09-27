"""
KILNWORKS R3 -- PRIMARY simulator.

Deterministic, event-by-event (minute-stepped) simulator for one design,
covering all four campaigns (20 lots) back-to-back on one shared clock and
one shared resource pool, per the full packet (sections A-H).

Architecture: a single object-oriented class KWSim holding all plant state,
stepped one simulated minute at a time.  Every minute we:

  0. Apply updates that become visible exactly at this minute (robot
     positions/cargo resolved last minute, K-queue arrivals from unloads
     decided last minute, forced-offline window activation).
  1. Detect machine completions effective at this minute (P and/or Q free
     immediately at the boundary minute); push newly prepared lots into the
     relevant dock buffer; update Q_cumulative / trigger the Section-H freeze.
  2. Power admission pass, IN ORDER: mandatory (already-ongoing) draws first,
     then new-starts in the packet's stated order: P start, Q start,
     Robot 0's action, Robot 1's action, new oven start.
  3. Record the full per-minute trace row.
  4. Advance the clock; stop when all 20 lots have finished curing.

This file is the PRIMARY implementation used to report the six designs'
(makespan, bill).  kw_verifier_sim.py is a second, independently written
implementation used only to check this one.
"""

import kw_constants as C


class Lot:
    __slots__ = (
        "s", "j", "family", "release", "pbase", "qbase", "gidx",
        "assigned_machine", "start_time", "setup", "proc_dur", "ready_time",
        "picked_up_time", "carrying_robot", "delivered_decision_minute",
        "arrival_minute", "batched", "cure_start", "cure_end", "oven_size",
    )

    def __init__(self, d):
        self.s, self.j, self.family = d["s"], d["j"], d["family"]
        self.release, self.pbase, self.qbase = d["release"], d["pbase"], d["qbase"]
        self.gidx = d["gidx"]
        self.assigned_machine = None
        self.start_time = None
        self.setup = None
        self.proc_dur = None
        self.ready_time = None          # minute machine frees / lot enters dock buffer
        self.picked_up_time = None
        self.carrying_robot = None
        self.delivered_decision_minute = None  # minute robot DECIDED the unload
        self.arrival_minute = None             # decision_minute + 1 (K-queue visible)
        self.batched = False
        self.cure_start = None
        self.cure_end = None
        self.oven_size = None


class Robot:
    __slots__ = ("rid", "pos", "cargo", "home",
                 "offline_from", "offline_until", "disruption_fired")

    def __init__(self, rid):
        self.rid = rid
        self.pos = C.START_POS[rid]
        self.cargo = None  # Lot or None
        self.home = C.HOME[rid]
        self.offline_from = None
        self.offline_until = None
        self.disruption_fired = False

    def is_offline(self, t):
        return (self.offline_from is not None
                and self.offline_from <= t <= self.offline_until)


class KWSim:
    def __init__(self, design_id, record_trace=True, safety_cap=3000):
        cfg = C.DESIGNS[design_id]
        self.design_id = design_id
        self.F = cfg["F"]
        self.G = cfg["G"]
        self.aisle_open = cfg["aisle_open"]
        self.capital = cfg["capital"]
        self.safety_cap = safety_cap

        self.adj, self.edge_set = C.build_graph(self.aisle_open)
        self.dist_to_K = C.bfs_dist_to(self.adj, C.K)
        self.dist_to_P = C.bfs_dist_to(self.adj, C.P_NODE)
        self.dist_to_Q = C.bfs_dist_to(self.adj, C.Q_NODE)
        self.dist_to_home = {0: self.dist_to_P, 1: self.dist_to_Q}

        lots_raw = C.gen_lots()
        self.lots = [Lot(d) for d in lots_raw]
        self.by_gidx = {L.gidx: L for L in self.lots}

        self.P_busy_until = None   # None == free
        self.P_job_start = None
        self.P_family_memory = None
        self.P_lot = None

        self.Q_busy_until = None
        self.Q_job_start = None
        self.Q_family_memory = None
        self.Q_lot = None
        self.Q_cumulative = 0
        self.Q_freeze_from = None
        self.Q_freeze_until = None
        self.Q_freeze_fired = False

        self.held_fixtures = 0

        self.P_buffer = []  # list of Lot, prepared & waiting for pickup at node 3
        self.Q_buffer = []  # ... at node 5

        self.K_queue = []   # list of Lot, delivered & waiting for oven (uncured)
        self.pending_kqueue = {}  # minute -> [Lot,...]

        self.oven_busy_until = None
        self.oven_start = None
        self.oven_batch = None
        self.anchor = None
        self.anchor_deadline = None

        self.robots = {0: Robot(0), 1: Robot(1)}

        self.record_trace = record_trace
        self.trace = []  # list of per-minute dict rows

        self.t = 0
        self.done = False
        self.makespan = None
        self.bill = 0

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def all_batched(self):
        return all(L.cure_end is not None for L in self.lots)

    def released_unassigned_pool(self, t):
        return [L for L in self.lots
                if L.assigned_machine is None and L.release <= t]

    # ------------------------------------------------------------------
    # main loop
    # ------------------------------------------------------------------
    def run(self):
        while True:
            if self.all_batched():
                final_makespan = max(L.cure_end for L in self.lots)
                if self.t >= final_makespan:
                    self.makespan = final_makespan
                    break
            if self.t > self.safety_cap:
                raise RuntimeError(f"{self.design_id}: safety cap exceeded at t={self.t}")
            self.step_minute()
            self.t += 1
        return self.makespan, self.bill

    def step_minute(self):
        t = self.t
        row = dict(t=t)

        # -- 0. visibility: K-queue arrivals scheduled for exactly this minute
        for L in self.pending_kqueue.pop(t, []):
            self.K_queue.append(L)

        # -- 1. machine completions effective at this (boundary) minute
        p_completed = False
        if self.P_busy_until is not None and self.P_busy_until == t:
            L = self.P_lot
            L.ready_time = t
            self.P_buffer.append(L)
            self.P_busy_until = None
            self.P_job_start = None
            self.P_lot = None
            p_completed = True

        # oven completion effective at this boundary minute -- fixtures held by
        # the batch's members release only NOW (curing end), never at cure start
        if self.oven_busy_until is not None and self.oven_busy_until == t:
            for gidx in self.oven_batch:
                self.held_fixtures -= 1
            self.oven_busy_until = None
            self.oven_start = None
            self.oven_batch = None

        q_completed = False
        if self.Q_busy_until is not None and self.Q_busy_until == t:
            L = self.Q_lot
            L.ready_time = t
            self.Q_buffer.append(L)
            # Q_cumulative tracks PROCESSING portion only, never setup
            prior = self.Q_cumulative
            self.Q_cumulative += L.qbase
            if (not self.Q_freeze_fired) and prior < C.Q_CUM_TRIGGER <= self.Q_cumulative:
                self.Q_freeze_fired = True
                self.Q_freeze_from = t + 1
                self.Q_freeze_until = t + C.Q_FREEZE_MINUTES
            self.Q_busy_until = None
            self.Q_job_start = None
            self.Q_lot = None
            q_completed = True

        # -- 2. power admission: mandatory continuing draws first
        remaining = self.G
        mand_p = mand_q = mand_oven = 0
        if self.P_busy_until is not None and self.P_job_start is not None and self.P_job_start < t:
            mand_p = C.DRAW["P"]
        if self.Q_busy_until is not None and self.Q_job_start is not None and self.Q_job_start < t:
            mand_q = C.DRAW["Q"]
        if self.oven_busy_until is not None and self.oven_batch is not None and self.oven_start < t:
            mand_oven = C.DRAW["oven"]
        remaining -= (mand_p + mand_q + mand_oven)

        draws = dict(P=mand_p, Q=mand_q, oven=mand_oven, R0=0, R1=0)
        events = dict(P_start=None, Q_start=None, R0=None, R1=None, oven_start=None)

        # -- 2a. P start attempt
        if self.P_busy_until is None:
            cand = self._pick_candidate(t, "P")
            if cand is not None:
                if remaining >= C.DRAW["P"]:
                    self._start_machine("P", cand, t)
                    remaining -= C.DRAW["P"]
                    draws["P"] += C.DRAW["P"]
                    events["P_start"] = cand.gidx

        # -- 2b. Q start attempt (unless frozen)
        q_frozen = (self.Q_freeze_from is not None and self.Q_freeze_from <= t <= self.Q_freeze_until)
        if self.Q_busy_until is None and not q_frozen:
            cand = self._pick_candidate(t, "Q")
            if cand is not None:
                if remaining >= C.DRAW["Q"]:
                    self._start_machine("Q", cand, t)
                    remaining -= C.DRAW["Q"]
                    draws["Q"] += C.DRAW["Q"]
                    events["Q_start"] = cand.gidx

        # -- 2c. Robot 0 acts fully (decide + resolve) before Robot 1 is computed
        r0 = self.robots[0]
        r1 = self.robots[1]
        act0, remaining = self._robot_turn(r0, other_pos=r1.pos, other_new_pos=None,
                                            other_edge=None, t=t, remaining=remaining)
        draws["R0"] = act0["draw"]
        events["R0"] = act0["label"]

        # -- 2d. Robot 1 acts, aware of Robot 0's now-resolved outcome
        act1, remaining = self._robot_turn(r1, other_pos=r0.pos, other_new_pos=act0["new_pos"],
                                            other_edge=act0["edge"], t=t, remaining=remaining)
        draws["R1"] = act1["draw"]
        events["R1"] = act1["label"]

        # apply resolved robot updates (positions/cargo effective for t+1 decisions)
        self._apply_robot_result(r0, act0, t)
        self._apply_robot_result(r1, act1, t)

        # -- 2e. oven bounded-pairing-timer step (last in the order)
        oven_evt = self._oven_step(t, remaining)
        if oven_evt is not None:
            draws["oven"] += C.DRAW["oven"]
            events["oven_start"] = oven_evt

        total_power = sum(draws.values())
        if total_power > self.G:
            raise RuntimeError(f"POWER OVERFLOW at t={t}: {total_power} > G={self.G}")
        mult = C.tariff_multiplier(t)
        self.bill += total_power * mult

        if self.record_trace:
            row.update(draws=dict(draws), events=events, total_power=total_power,
                       mult=mult, held_fixtures=self.held_fixtures,
                       P_busy=self.P_busy_until, Q_busy=self.Q_busy_until,
                       oven_busy=self.oven_busy_until,
                       q_frozen=q_frozen,
                       r0_pos=r0.pos, r0_cargo=(r0.cargo.gidx if r0.cargo else None),
                       r1_pos=r1.pos, r1_cargo=(r1.cargo.gidx if r1.cargo else None),
                       P_buffer=[L.gidx for L in self.P_buffer],
                       Q_buffer=[L.gidx for L in self.Q_buffer],
                       K_queue=[L.gidx for L in self.K_queue],
                       anchor=(self.anchor.gidx if self.anchor else None),
                       anchor_deadline=self.anchor_deadline)
            self.trace.append(row)

    # ------------------------------------------------------------------
    # machine assignment (Section D)
    # ------------------------------------------------------------------
    def _pick_candidate(self, t, machine):
        if self.held_fixtures >= self.F:
            return None
        pool = self.released_unassigned_pool(t)
        if not pool:
            return None
        remembered = self.P_family_memory if machine == "P" else self.Q_family_memory
        best = None
        best_cost = None
        for L in pool:
            dur = L.pbase if machine == "P" else L.qbase
            cost = C.setup_cost(remembered, L.family) + dur
            if best is None or cost < best_cost or (cost == best_cost and L.gidx < best.gidx):
                best = L
                best_cost = cost
        return best

    def _start_machine(self, machine, lot, t):
        dur = lot.pbase if machine == "P" else lot.qbase
        if machine == "P":
            remembered = self.P_family_memory
        else:
            remembered = self.Q_family_memory
        setup = C.setup_cost(remembered, lot.family)
        lot.assigned_machine = machine
        lot.start_time = t
        lot.setup = setup
        lot.proc_dur = dur
        self.held_fixtures += 1
        if machine == "P":
            self.P_busy_until = t + setup + dur
            self.P_job_start = t
            self.P_family_memory = lot.family
            self.P_lot = lot
        else:
            self.Q_busy_until = t + setup + dur
            self.Q_job_start = t
            self.Q_family_memory = lot.family
            self.Q_lot = lot

    # ------------------------------------------------------------------
    # robot dispatch (Section E)
    # ------------------------------------------------------------------
    def _robot_turn(self, r, other_pos, other_new_pos, other_edge, t, remaining):
        """Decide + power/collision-resolve one robot's minute. Returns
        (result_dict, remaining_budget_after)."""
        result = dict(kind="wait", target=None, new_pos=r.pos, edge=None,
                      draw=0, label="wait", pickup_lot=None, unload=False)

        # priority 1: forced-offline
        if r.is_offline(t):
            result["kind"] = "offline"
            result["label"] = "offline"
            return result, remaining

        # priority 2: carrying cargo and at K -> unload
        if r.cargo is not None and r.pos == C.K:
            ok_power = remaining >= C.DRAW["robot_action"]
            if ok_power:
                result["kind"] = "unload"
                result["label"] = f"unload(lot{r.cargo.gidx})"
                result["draw"] = C.DRAW["robot_action"]
                result["unload"] = True
                return result, remaining - C.DRAW["robot_action"]
            else:
                result["label"] = "wait(power-refused-unload)"
                return result, remaining

        # priority 3: empty at a node with a waiting prepared lot -> pick up
        if r.cargo is None:
            here_buf = self._buffer_for_node(r.pos)
            if here_buf:
                lot = min(here_buf, key=lambda L: (L.ready_time, L.gidx))
                ok_power = remaining >= C.DRAW["robot_action"]
                if ok_power:
                    result["kind"] = "pickup"
                    result["label"] = f"pickup(lot{lot.gidx})"
                    result["draw"] = C.DRAW["robot_action"]
                    result["pickup_lot"] = lot
                    return result, remaining - C.DRAW["robot_action"]
                else:
                    result["label"] = "wait(power-refused-pickup)"
                    return result, remaining

        # priority 4: carrying cargo, not at K -> move toward K
        if r.cargo is not None and r.pos != C.K:
            nh = C.next_hop_toward(self.adj, self.dist_to_K, r.pos)
            return self._try_move(r, nh, "toK", other_pos, other_new_pos, other_edge, remaining)

        # priority 5: empty, no lot here -> move toward nearest node w/ waiting lot
        if r.cargo is None:
            target = self._nearest_lot_node(r.pos)
            if target is not None:
                dist_arr = self.dist_to_P if target == C.P_NODE else self.dist_to_Q
                nh = C.next_hop_toward(self.adj, dist_arr, r.pos)
                return self._try_move(r, nh, f"toward_lot@{target}", other_pos, other_new_pos, other_edge, remaining)

        # priority 6: empty, no lot anywhere -> move toward own home; wait if home
        if r.pos == r.home:
            result["label"] = "wait(home)"
            return result, remaining
        dist_arr = self.dist_to_home[r.rid]
        nh = C.next_hop_toward(self.adj, dist_arr, r.pos)
        return self._try_move(r, nh, "toward_home", other_pos, other_new_pos, other_edge, remaining)

    def _buffer_for_node(self, node):
        if node == C.P_NODE:
            return self.P_buffer
        if node == C.Q_NODE:
            return self.Q_buffer
        return []

    def _nearest_lot_node(self, pos):
        candidates = []
        if self.P_buffer:
            candidates.append((self.dist_to_P[pos], C.P_NODE))
        if self.Q_buffer:
            candidates.append((self.dist_to_Q[pos], C.Q_NODE))
        if not candidates:
            return None
        candidates.sort(key=lambda x: (x[0], x[1]))
        return candidates[0][1]

    def _try_move(self, r, next_hop, label, other_pos, other_new_pos, other_edge, remaining):
        result = dict(kind="wait", target=next_hop, new_pos=r.pos, edge=None,
                      draw=0, label=f"wait(blocked:{label})", pickup_lot=None, unload=False)
        if next_hop is None:
            result["label"] = f"wait(no-path:{label})"
            return result, remaining

        edge = frozenset((r.pos, next_hop))

        # edge-capacity: at most one traversal per edge per minute
        if other_edge is not None and other_edge == edge:
            return result, remaining

        # node-capacity check at target
        occ_from_other = 1 if (other_new_pos is not None and other_new_pos == next_hop) else \
                          (1 if (other_new_pos is None and other_pos == next_hop) else 0)
        if occ_from_other + 1 > C.capacity(next_hop):
            return result, remaining

        # power
        if remaining < C.DRAW["robot_action"]:
            result["label"] = f"wait(power-refused:{label})"
            return result, remaining

        result["kind"] = "move"
        result["label"] = f"move({r.pos}->{next_hop}):{label}"
        result["new_pos"] = next_hop
        result["edge"] = edge
        result["draw"] = C.DRAW["robot_action"]
        return result, remaining - C.DRAW["robot_action"]

    def _apply_robot_result(self, r, act, t):
        if act["kind"] == "move":
            old_pos = r.pos
            r.pos = act["new_pos"]
            if r.rid == 0 and r.pos == C.JUNCTION and not r.disruption_fired:
                r.disruption_fired = True
                r.offline_from = t + 1
                r.offline_until = t + C.NODE4_DISRUPTION_MINUTES  # inclusive of arrival minute (t+1)
        elif act["kind"] == "pickup":
            lot = act["pickup_lot"]
            buf = self._buffer_for_node(r.pos)
            buf.remove(lot)
            lot.picked_up_time = t
            lot.carrying_robot = r.rid
            r.cargo = lot
        elif act["kind"] == "unload":
            lot = r.cargo
            lot.delivered_decision_minute = t
            lot.arrival_minute = t + 1
            self.pending_kqueue.setdefault(t + 1, []).append(lot)
            r.cargo = None
        # wait / offline: nothing to apply

    # ------------------------------------------------------------------
    # oven batching (Section F)
    # ------------------------------------------------------------------
    def _oven_step(self, t, remaining):
        if self.oven_busy_until is not None:
            return None  # busy, no new start possible

        if self.anchor is None:
            waiting = [L for L in self.K_queue]
            if not waiting:
                return None
            anchor = min(waiting, key=lambda L: (L.arrival_minute, L.gidx))
            self.anchor = anchor
            self.anchor_deadline = anchor.arrival_minute + C.ANCHOR_DEADLINE_OFFSET

        anchor = self.anchor
        partners = [L for L in self.K_queue if L is not anchor and L.family == anchor.family]
        if partners:
            partner = min(partners, key=lambda L: L.gidx)
            size = 2
            members = [anchor, partner]
        elif t >= self.anchor_deadline:
            size = 1
            members = [anchor]
        else:
            return None  # wait

        if remaining < C.DRAW["oven"]:
            return None  # power refusal -- anchor & deadline persist, retry next minute

        dur = C.cure_duration(anchor.family)
        self.oven_start = t
        self.oven_busy_until = t + dur
        self.oven_batch = [L.gidx for L in members]
        for L in members:
            self.K_queue.remove(L)
            L.batched = True
            L.cure_start = t
            L.cure_end = t + dur
            L.oven_size = size
        self.anchor = None
        self.anchor_deadline = None
        return [L.gidx for L in members]


def run_design(design_id, record_trace=True):
    sim = KWSim(design_id, record_trace=record_trace)
    makespan, bill = sim.run()
    return sim, makespan, bill


if __name__ == "__main__":
    for d in C.DESIGN_ORDER:
        sim, ms, bill = run_design(d)
        print(d, "makespan=", ms, "bill=", bill, "capital=", sim.capital)
