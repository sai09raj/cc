#!/usr/bin/env python3
"""ATRIUM-9 primary simulator: deterministic tick-by-tick 4-car elevator bank.

Implements the packet (atrium9.pdf) sections 1-8.  Constants measured from the
figures are in atrium9_constants.py (shared, immutable, with the verifier).

Tick model (see memo for the full interpretation):
  start of tick t : finished phases roll over (TRAVEL->CLOSED at new floor,
                    OPENING->DWELL, CLOSING->CLOSED)
  dispatch        : timeout reassignment (gidx order), then assignment of
                    arrived-but-unassigned hall calls (gidx order)
  cars            : continuing phases keep their admitted power; then, in
                    fixed priority A,B,C,D, every car that wants a NEW
                    power-gated event (travel hop, door opening, dwell->close)
                    is admitted iff it fits in the remaining budget.  A car at
                    its first DWELL tick alights/boards (ascending gidx).
  accounting      : power = sum of draws this tick; energy = sum over cars
                    mid-travel of 3+load (up) / 3-load (down).
The run ends at the end of the tick in which the 80th call alights.
"""
import csv
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from atrium9_constants import (CAPACITY, N_FLOORS, TRAVEL_TICKS, OPEN_TICKS,
                               DWELL_TICKS, CLOSE_TICKS, P_TRAVEL, P_OPEN,
                               P_CLOSE, HOMES, CAR_NAMES, SWEEP,
                               BASELINE, ENERGY_CEILING)

UP, DOWN = 1, -1
DNAME = {UP: "UP", DOWN: "DOWN", None: "-"}


# --------------------------------------------------------------------------
# Section 1: workload
# --------------------------------------------------------------------------
class Call:
    __slots__ = ("gidx", "s", "k", "origin", "dir", "arrival", "dest",
                 "car", "assigned_at", "banned", "board_t", "alight_t",
                 "board_car", "history")

    def __init__(self, gidx, s, k, origin, d, arrival, dest):
        self.gidx, self.s, self.k = gidx, s, k
        self.origin, self.dir, self.arrival, self.dest = origin, d, arrival, dest
        self.car = None
        self.assigned_at = None
        self.banned = set()
        self.board_t = None
        self.alight_t = None
        self.board_car = None
        self.history = []


def generate_calls():
    calls = []
    for s in range(4):
        for k in range(20):
            group = k // 3
            origin = (3 * group + 2 * s) % 8
            if origin == 0:
                d = UP
            elif origin == 7:
                d = DOWN
            else:
                d = UP if (group + s) % 2 == 0 else DOWN
            arrival = 200 * s + 8 * k
            span = 1 + ((5 * k + 3 * s) % 7)
            if d == UP:
                dest = min(7, origin + span)
                if dest == origin:
                    dest = min(7, origin + 1)
            else:
                dest = max(0, origin - span)
                if dest == origin:
                    dest = max(0, origin - 1)
            calls.append(Call(20 * s + k, s, k, origin, d, arrival, dest))
    return calls


# --------------------------------------------------------------------------
# Cars
# --------------------------------------------------------------------------
class Car:
    def __init__(self, cid, home, active):
        self.cid = cid
        self.name = CAR_NAMES[cid]
        self.home = home
        self.active = active
        self.pos = home          # floor (departure floor while travelling)
        self.phase = "CLOSED"    # CLOSED | TRAVEL | OPENING | DWELL | CLOSING
        self.done = 0            # ticks already spent in current phase
        self.hop_dir = 0
        self.dir = None          # scan direction (None = no scan)
        self.passengers = []     # Call objects aboard

    # position measured in travel ticks (4 per floor)
    def pos_ticks(self):
        if self.phase == "TRAVEL":
            return TRAVEL_TICKS * self.pos + self.hop_dir * self.done
        return TRAVEL_TICKS * self.pos

    def cost_to(self, floor):
        """Distance in ticks from the car's current position to `floor`."""
        if self.phase == "TRAVEL":
            target = self.pos + self.hop_dir
            return (TRAVEL_TICKS - self.done) + TRAVEL_TICKS * abs(target - floor)
        return TRAVEL_TICKS * abs(self.pos - floor)

    def ahead(self, floor, d):
        pt = self.pos_ticks()
        return TRAVEL_TICKS * floor > pt if d == UP else TRAVEL_TICKS * floor < pt


class Sim:
    def __init__(self, active_cars, zoning, wait_timeout, power_budget,
                 record=False):
        self.cfg = dict(active_cars=active_cars, zoning=zoning,
                        wait_timeout=wait_timeout, capacity=CAPACITY,
                        power_budget=power_budget)
        self.timeout = wait_timeout
        self.budget = power_budget
        self.calls = generate_calls()
        homes = HOMES[zoning]
        self.cars = [Car(i, homes[i], i < active_cars) for i in range(4)]
        self.active = [c for c in self.cars if c.active]
        self.record = record
        self.trace = []      # (t, power, energy)
        self.events = []     # detailed per-tick records (baseline only)
        self.stats = dict(reassignments=0, capacity_leftbehind=0,
                          power_denials=0, close_denials=0, max_tick_power=0)

    # ---- commitments, derived fresh from call state --------------------
    def stops(self, car, d):
        s = {p.dest for p in car.passengers if p.dir == d}
        for c in self.calls:
            if c.car is car and c.board_t is None and c.dir == d:
                s.add(c.origin)
        return s

    def idle(self, car):
        return not self.stops(car, UP) and not self.stops(car, DOWN)

    def eligible(self, car, call):
        if not car.active or car.cid in call.banned:
            return False
        if self.idle(car):
            return True
        return car.dir == call.dir and car.ahead(call.origin, call.dir)

    def best_car(self, call, exclude=None):
        best = None
        for car in self.active:
            if car is exclude or not self.eligible(car, call):
                continue
            key = (car.cost_to(call.origin), car.cid)
            if best is None or key < best[0]:
                best = (key, car)
        return best

    # ---- per-car decision when stationary with doors closed ------------
    def decide(self, car):
        """Return ('open', d) | ('hop', d) | None; may update car.dir."""
        up, dn = self.stops(car, UP), self.stops(car, DOWN)
        p = car.pos
        if not up and not dn:
            car.dir = None
            if p != car.home:
                return ("hop", UP if car.home > p else DOWN)
            return None
        d = car.dir
        if d is not None:
            own = up if d == UP else dn
            if p in own:
                return ("open", d)
            if any((f > p) if d == UP else (f < p) for f in up | dn):
                return ("hop", d)
        # switch to the nearer remaining commitment
        cands = [(abs(f - p), f, 0, UP) for f in up] + \
                [(abs(f - p), f, 1, DOWN) for f in dn]
        cands.sort()
        dist, f, _, sd = cands[0]
        if f == p:
            car.dir = sd
            return ("open", sd)
        car.dir = UP if f > p else DOWN
        return ("hop", car.dir)

    # ---- one tick -------------------------------------------------------
    def step(self, t):
        rec = {"t": t, "events": []} if self.record else None
        # 1. phase roll-over
        for car in self.active:
            if car.phase == "TRAVEL" and car.done >= TRAVEL_TICKS:
                car.pos += car.hop_dir
                car.phase, car.done, car.hop_dir = "CLOSED", 0, 0
                if rec is not None:
                    rec["events"].append(f"{car.name} arrive L{car.pos}")
            elif car.phase == "OPENING" and car.done >= OPEN_TICKS:
                car.phase, car.done = "DWELL", 0
            elif car.phase == "CLOSING" and car.done >= CLOSE_TICKS:
                car.phase, car.done = "CLOSED", 0
        # 2. timeout reassignment
        for c in self.calls:
            if c.car is None or c.board_t is not None:
                continue
            if t - c.assigned_at > self.timeout:
                inc = c.car
                inc_cost = inc.cost_to(c.origin)
                best = self.best_car(c, exclude=inc)
                if best is not None and best[0][0] < inc_cost:
                    c.banned.add(inc.cid)
                    c.car = best[1]
                    c.assigned_at = t
                    c.history.append((t, best[1].name))
                    self.stats["reassignments"] += 1
                    if rec is not None:
                        rec["events"].append(
                            f"reassign call{c.gidx} {inc.name}->{best[1].name}"
                            f" (cost {inc_cost}->{best[0][0]})")
        # 3. new assignments
        for c in self.calls:
            if c.arrival > t or c.car is not None:
                continue
            best = self.best_car(c)
            if best is not None:
                c.car = best[1]
                c.assigned_at = t
                c.history.append((t, best[1].name))
                if rec is not None:
                    rec["events"].append(
                        f"assign call{c.gidx} L{c.origin}{DNAME[c.dir]} ->"
                        f" {best[1].name} (cost {best[0][0]})")
        # 4. cars: continuing power first
        power = 0
        draws = {}
        for car in self.active:
            dr = 0
            if car.phase == "TRAVEL":
                dr = P_TRAVEL
            elif car.phase in ("OPENING", "CLOSING"):
                dr = P_OPEN if car.phase == "OPENING" else P_CLOSE
            draws[car.cid] = dr
            power += dr
        # then new events in fixed priority A..D
        for car in self.active:
            if car.phase == "DWELL":
                if car.done == 0:
                    self.board_alight(car, t, rec)
                if car.done >= DWELL_TICKS:
                    if power + P_CLOSE <= self.budget:
                        power += P_CLOSE
                        draws[car.cid] = P_CLOSE
                        car.phase, car.done = "CLOSING", 0
                        if rec is not None:
                            rec["events"].append(f"{car.name} close@L{car.pos}")
                    else:
                        self.stats["close_denials"] += 1
            elif car.phase == "CLOSED":
                act = self.decide(car)
                if act is None:
                    continue
                kind, d = act
                need = P_OPEN if kind == "open" else P_TRAVEL
                if power + need <= self.budget:
                    power += need
                    draws[car.cid] = need
                    if kind == "open":
                        car.phase, car.done = "OPENING", 0
                        if rec is not None:
                            rec["events"].append(
                                f"{car.name} open@L{car.pos} dir {DNAME[d]}")
                    else:
                        car.phase, car.done, car.hop_dir = "TRAVEL", 0, d
                        if rec is not None:
                            rec["events"].append(
                                f"{car.name} hop L{car.pos}->L{car.pos + d}"
                                f" load {len(car.passengers)}")
                else:
                    self.stats["power_denials"] += 1
                    if rec is not None:
                        rec["events"].append(f"{car.name} {kind} DENIED (power)")
        # 5. energy
        energy = 0
        for car in self.active:
            if car.phase == "TRAVEL":
                load = len(car.passengers)
                energy += (3 + load) if car.hop_dir == UP else (3 - load)
        self.stats["max_tick_power"] = max(self.stats["max_tick_power"], power)
        self.trace.append((t, power, energy))
        if rec is not None:
            rec["power"], rec["energy"] = power, energy
            rec["cars"] = {car.name: dict(
                phase=car.phase, pos=car.pos, hop=car.hop_dir,
                dir=DNAME[car.dir], load=len(car.passengers),
                draw=draws[car.cid]) for car in self.active}
            self.events.append(rec)
        # 6. advance phase counters
        for car in self.active:
            if car.phase != "CLOSED":
                car.done += 1

    def board_alight(self, car, t, rec):
        p = car.pos
        stay = []
        for c in car.passengers:
            if c.dest == p:
                c.alight_t = t
                if rec is not None:
                    rec["events"].append(f"call{c.gidx} alight {car.name}@L{p}")
            else:
                stay.append(c)
        car.passengers = stay
        waiting = sorted((c for c in self.calls
                          if c.car is car and c.board_t is None
                          and c.origin == p and c.dir == car.dir
                          and c.arrival <= t), key=lambda c: c.gidx)
        for c in waiting:
            if len(car.passengers) >= CAPACITY:
                self.stats["capacity_leftbehind"] += 1
                continue
            c.board_t = t
            c.board_car = car.name
            car.passengers.append(c)
            if rec is not None:
                rec["events"].append(
                    f"call{c.gidx} board {car.name}@L{p} dest L{c.dest}")

    def run(self, max_t=200000):
        t = 0
        while True:
            self.step(t)
            if all(c.alight_t is not None for c in self.calls):
                break
            t += 1
            if t > max_t:
                raise RuntimeError(f"no completion by t={max_t}: {self.cfg}")
        waits = [c.board_t - c.arrival for c in self.calls]
        return dict(
            avg_wait=sum(waits) / len(waits),
            net_energy=sum(e for _, _, e in self.trace),
            max_wait=max(waits),
            total_wait=sum(waits),
            end_tick=self.trace[-1][0],
            **self.stats)

    def header(self):
        return "CONFIG:" + str(self.cfg)

    def serialize(self):
        lines = [self.header()] + [f"{t},{p},{e}" for t, p, e in self.trace]
        return "\n".join(lines)


# --------------------------------------------------------------------------
def sweep():
    rows = []
    for ac in SWEEP["active_cars"]:
        for zn in SWEEP["zoning"]:
            for wt in SWEEP["wait_timeout"]:
                for pb in SWEEP["power_budget"]:
                    sim = Sim(ac, zn, wt, pb)
                    r = sim.run()
                    h = hashlib.sha256(sim.serialize().encode("utf-8")).hexdigest()
                    rows.append(dict(active_cars=ac, zoning=zn, wait_timeout=wt,
                                     capacity=CAPACITY, power_budget=pb,
                                     trace_sha16=h[:16], **r))
    return rows


def select(rows):
    def cfg(r):
        return {k: r[k] for k in ("active_cars", "zoning", "wait_timeout",
                                  "capacity", "power_budget")}
    w = min(rows, key=lambda r: (r["avg_wait"], r["net_energy"]))
    e = min(rows, key=lambda r: (r["net_energy"], r["avg_wait"]))
    feas = [r for r in rows if r["net_energy"] <= ENERGY_CEILING]
    b = min(feas, key=lambda r: (r["avg_wait"], r["net_energy"])) if feas else None

    def tied(r, keyf):
        return [cfg(x) for x in rows if keyf(x) == keyf(r)]
    out = {}
    for name, r, keyf, desc in (
            ("wait_optimal", w, lambda r: (r["avg_wait"], r["net_energy"]),
             "min avg_wait, tie-break net_energy"),
            ("energy_optimal", e, lambda r: (r["net_energy"], r["avg_wait"]),
             "min net_energy, tie-break avg_wait"),
            ("budget_constrained", b, lambda r: (r["avg_wait"], r["net_energy"]),
             f"min avg_wait s.t. net_energy <= {ENERGY_CEILING}, tie-break net_energy")):
        if r is None:
            out[name] = None
            continue
        ties = tied(r, keyf) if name != "budget_constrained" else \
            [cfg(x) for x in feas if keyf(x) == keyf(r)]
        out[name] = dict(key=desc, config=cfg(r), avg_wait=r["avg_wait"],
                         net_energy=r["net_energy"], max_wait=r["max_wait"],
                         end_tick=r["end_tick"],
                         exact_key_ties=ties)
    out["feasible_count_under_ceiling"] = len(feas)
    out["energy_ceiling"] = ENERGY_CEILING
    out["tie_break_rule"] = (
        "The packet's two-level keys leave exact ties (wait_timeout and, below "
        "4 cars, power_budget never change the outcome). Residual ties are "
        "resolved by canonical sweep order: active_cars ascending, zoning in "
        "packet order SPLIT<GROUND<TOP, wait_timeout ascending, power_budget "
        "ascending (i.e. the least-investment member of the tie set). All tied "
        "configurations are listed in exact_key_ties.")
    return out


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    rows = sweep()
    fields = ["active_cars", "zoning", "wait_timeout", "capacity",
              "power_budget", "avg_wait", "net_energy", "total_wait",
              "max_wait", "end_tick", "reassignments", "power_denials",
              "close_denials", "capacity_leftbehind", "max_tick_power",
              "trace_sha16"]
    with open(os.path.join(outdir, "sweep_144.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        for r in rows:
            r2 = dict(r)
            r2["avg_wait"] = repr(r["avg_wait"])
            wr.writerow({k: r2[k] for k in fields})
    dec = select(rows)
    dec["sweep_totals"] = dict(
        rows=len(rows),
        sum_net_energy=sum(r["net_energy"] for r in rows),
        sum_total_wait=sum(r["total_wait"] for r in rows),
        total_reassignments=sum(r["reassignments"] for r in rows),
        total_power_denials=sum(r["power_denials"] + r["close_denials"] for r in rows),
        total_capacity_leftbehind=sum(r["capacity_leftbehind"] for r in rows))
    with open(os.path.join(outdir, "decision.json"), "w") as f:
        json.dump(dec, f, indent=2)

    # baseline certification
    sim = Sim(BASELINE["active_cars"], BASELINE["zoning"],
              BASELINE["wait_timeout"], BASELINE["power_budget"], record=True)
    res = sim.run()
    ser = sim.serialize()
    with open(os.path.join(outdir, "baseline_trace.txt"), "w", encoding="utf-8",
              newline="") as f:
        f.write(ser)
    digest = hashlib.sha256(ser.encode("utf-8")).hexdigest()
    with open(os.path.join(outdir, "baseline_events.jsonl"), "w") as f:
        for rec in sim.events:
            f.write(json.dumps(rec) + "\n")
    calls_out = [dict(gidx=c.gidx, s=c.s, k=c.k, origin=c.origin,
                      dir=DNAME[c.dir], arrival=c.arrival, dest=c.dest,
                      board_t=c.board_t, alight_t=c.alight_t,
                      board_car=c.board_car,
                      assignment_history=c.history,
                      banned=[CAR_NAMES[b] for b in sorted(c.banned)])
                 for c in sim.calls]
    with open(os.path.join(outdir, "baseline_calls.json"), "w") as f:
        json.dump(calls_out, f, indent=1)
    cert = dict(config_header=sim.header(), sha256=digest,
                certificate=digest[:16], ticks=len(sim.trace), result=res)
    with open(os.path.join(outdir, "baseline_certificate.json"), "w") as f:
        json.dump(cert, f, indent=2)
    print(json.dumps({k: dec[k] for k in ("wait_optimal", "energy_optimal",
                                         "budget_constrained")}, indent=1))
    print("sweep totals", dec["sweep_totals"])
    print("baseline", res)
    print("baseline certificate", digest[:16], digest)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out")
