#!/usr/bin/env python3
"""ATRIUM-9 canonical reference simulator.

A 4-car elevator bank dispatch simulator implementing the visible policy in
the engineering packet exactly. Stdlib only. Deterministic: there is no free
scheduling choice for a solver to search for at the per-tick dispatch level;
the search space is the CONFIGURATION sweep (active car count, zoning,
reassignment timeout, capacity, power budget), not the per-tick decisions.

Each car tracks its committed stops SEPARATELY per scan direction (the
standard up-queue/down-queue convention): a floor needed while the car is
scanning UP is a different commitment from the same floor needed while
scanning DOWN, because a hall call's direction and a car call's approach
direction are both fixed at assignment/boarding time and must not be
conflated with whichever way the car physically happens to be facing when
it later reaches that floor.
"""
import sys

FLOORS = 8                  # 0 (ground) .. 7 (top)
NUM_CARS = 4                 # A=0, B=1, C=2, D=3
CAR_NAMES = ["A", "B", "C", "D"]
CAMPAIGNS = 4
CALLS_PER_CAMPAIGN = 20
CAMPAIGN_CADENCE = 200
CALL_SPACING = 8

T_FLOOR = 4                  # ticks to traverse one floor while moving
T_DOOR_OPEN = 2
T_DWELL = 3
T_DOOR_CLOSE = 2

POWER = {"move": 2, "door": 1}    # per-car per-tick draw while active
ENERGY_BASE = 3
ENERGY_LOAD_FACTOR = 1       # moving up costs +factor*load; moving down regenerates factor*load

UP, DOWN = "UP", "DOWN"


def gen_calls():
    calls = []
    for c in range(CAMPAIGNS):
        for k in range(CALLS_PER_CAMPAIGN):
            group = k // 3   # 3 calls per group share a floor+direction, clustering arrivals
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
            calls.append(dict(gidx=gidx, c=c, k=k, origin=origin, direction=direction,
                               arrival=arrival, dest=dest))
    return calls


class Call:
    __slots__ = ("gidx", "origin", "direction", "arrival", "dest",
                 "state", "assigned_car", "assign_tick", "attempt", "board_tick", "alight_tick")

    def __init__(self, d):
        self.gidx = d["gidx"]; self.origin = d["origin"]; self.direction = d["direction"]
        self.arrival = d["arrival"]; self.dest = d["dest"]
        self.state = "pending"       # pending -> assigned -> boarded -> done
        self.assigned_car = None
        self.assign_tick = None
        self.attempt = 0
        self.board_tick = None
        self.alight_tick = None


class Car:
    __slots__ = ("cid", "pos", "direction", "door", "door_since",
                 "committed", "waiting", "load", "home", "active", "moving_until")

    def __init__(self, cid, home, active):
        self.cid = cid
        self.pos = home
        self.direction = None        # None = idle
        self.door = "CLOSED"         # CLOSED / OPENING / DWELL / CLOSING
        self.door_since = None
        self.committed = {UP: set(), DOWN: set()}   # floors needed per scan direction
        self.waiting = {UP: {}, DOWN: {}}            # direction -> floor -> set(call gidx)
        self.load = 0
        self.home = home
        self.active = active
        self.moving_until = None     # tick at which an in-progress floor-hop completes

    def has_commitments(self):
        return bool(self.committed[UP] or self.committed[DOWN])


def zoning_homes(policy):
    if policy == "SPLIT":
        return [0, 2, 5, 7]
    if policy == "GROUND":
        return [0, 0, 0, 0]
    if policy == "TOP":
        return [7, 7, 7, 7]
    raise ValueError(policy)


def eligible_cost(car, floor, direction, current_tick):
    """Cost in ticks for `car` to reach `floor` while scanning `direction`,
    or None if `car` cannot accept this assignment this tick.

    Idle (no commitments in either direction): eligible for anything, cost =
    travel distance. Moving/committed: eligible only while already scanning
    `direction` AND `floor` still lies ahead of the car's current position in
    that direction (a car already past a floor in one pass never backtracks
    for it; the call would need a fresh assignment on a later pass)."""
    if not car.active:
        return None
    if not car.has_commitments():
        return abs(car.pos - floor) * T_FLOOR
    if car.direction != direction:
        return None
    ahead = floor >= car.pos if direction == UP else floor <= car.pos
    if not ahead:
        return None
    lo, hi = (car.pos, floor) if direction == UP else (floor, car.pos)
    stops_between = sum(1 for f in car.committed[direction] if lo <= f <= hi)
    dist = abs(car.pos - floor) * T_FLOOR
    overhead = stops_between * (T_DOOR_OPEN + T_DWELL + T_DOOR_CLOSE)
    return dist + overhead


def do_assign(car, call, current_tick):
    call.assigned_car = car.cid
    call.assign_tick = current_tick
    call.attempt += 1
    call.state = "assigned"
    car.waiting[call.direction].setdefault(call.origin, set()).add(call.gidx)
    car.committed[call.direction].add(call.origin)


def assign_call(cars, call, current_tick, active_mask):
    best_car, best_cost = None, None
    for car in cars:
        if not active_mask[car.cid]:
            continue
        cost = eligible_cost(car, call.origin, call.direction, current_tick)
        if cost is None:
            continue
        if best_cost is None or cost < best_cost or (cost == best_cost and car.cid < best_car.cid):
            best_car, best_cost = car, cost
    if best_car is None:
        return False
    do_assign(best_car, call, current_tick)
    return True


def retract_call(cars, call):
    car = cars[call.assigned_car]
    d = call.direction
    s = car.waiting[d].get(call.origin)
    if s is not None:
        s.discard(call.gidx)
        if not s:
            del car.waiting[d][call.origin]
            # only drop the commitment if no car-call also needs this floor
            # in this same direction (checked by caller via has_car_call)
            car.committed[d].discard(call.origin)
    call.assigned_car = None
    call.state = "pending"


def simulate(config, trace_limit=400000, mutant_no_timeout=False,
             mutant_shared_direction=False, mutant_power_disabled=False,
             mutant_no_cost_compare=False):
    """config: dict with keys active_cars(int 2-4), zoning(str), wait_timeout(int),
    capacity(int), power_budget(int)."""
    active_n = config["active_cars"]
    zoning = config["zoning"]
    wait_timeout = config["wait_timeout"]
    capacity = config["capacity"]
    G = config["power_budget"]

    homes = zoning_homes(zoning)
    active_mask = [i < active_n for i in range(NUM_CARS)]
    cars = [Car(i, homes[i], active_mask[i]) for i in range(NUM_CARS)]

    calls = [Call(d) for d in gen_calls()]
    by_gidx = {c.gidx: c for c in calls}
    pending_by_tick = {}
    for c in calls:
        pending_by_tick.setdefault(c.arrival, []).append(c.gidx)

    # car_call destination bookkeeping: dest_owner[(car_id, direction, floor)] = count of
    # boarded-but-not-alighted passengers requiring that stop, so the commitment can be
    # safely dropped only when both the hall-call waiting set AND the car-call count are empty.
    dest_count = {}

    trace = []
    energy_total = 0
    wait_sum = 0
    done_count = 0
    reassign_count = 0

    def car_next_hop(car):
        """Direction car should move this tick, or None. Re-derived fresh
        every call: continue the current scan direction only while a
        commitment remains ahead in THAT direction's own set; otherwise
        switch to whichever direction has the nearest remaining commitment;
        otherwise head home."""
        if car.has_commitments():
            if car.direction is not None:
                d = car.direction
                ahead = [f for f in car.committed[d] if (f > car.pos if d == UP else f < car.pos)]
                if ahead:
                    return d
            candidates = [(f, UP) for f in car.committed[UP]] + [(f, DOWN) for f in car.committed[DOWN]]
            nearest = min(candidates, key=lambda fd: (abs(fd[0] - car.pos), fd[1]))
            f, _ = nearest
            if f > car.pos:
                return UP
            if f < car.pos:
                return DOWN
            # already at the nearest commitment's floor: prefer whichever
            # direction actually has a commitment here
            return UP if car.pos in car.committed[UP] else DOWN
        if car.pos == car.home:
            return None
        return UP if car.home > car.pos else DOWN

    for t in range(trace_limit):
        # ---- boundary: complete in-flight floor hops / door phases ----
        for car in cars:
            if car.moving_until == t:
                car.moving_until = None
                d = car.direction
                if d is not None and car.pos in car.committed[d]:
                    car.door = "OPENING"
                    car.door_since = t
            if car.door == "OPENING" and t == car.door_since + T_DOOR_OPEN:
                car.door = "DWELL"
                car.door_since = t
                # ---- atomic boarding + alighting, direction-scoped ----
                floor = car.pos
                d = car.direction
                waiting_here = car.waiting[d].get(floor, set())
                boardable = sorted(waiting_here)
                room = capacity - car.load
                boarded_now = []
                for g in boardable:
                    if room <= 0:
                        break
                    call = by_gidx[g]
                    call.state = "boarded"
                    call.board_tick = t
                    car.load += 1
                    key = (car.cid, d, call.dest)
                    dest_count[key] = dest_count.get(key, 0) + 1
                    car.committed[d].add(call.dest)
                    boarded_now.append(g)
                    room -= 1
                for g in boarded_now:
                    waiting_here.discard(g)
                if not waiting_here:
                    car.waiting[d].pop(floor, None)
                    car.committed[d].discard(floor)
                # alighting: any boarded call with this car/direction/dest==floor
                key = (car.cid, d, floor)
                n_alight = dest_count.pop(key, 0)
                if n_alight:
                    alit = 0
                    for call in calls:
                        if call.state == "boarded" and call.assigned_car == car.cid \
                           and call.direction == d and call.dest == floor and call.alight_tick is None:
                            call.alight_tick = t
                            call.state = "done"
                            wait_sum += (call.board_tick - call.arrival)
                            done_count += 1
                            alit += 1
                            if alit == n_alight:
                                break
                    car.load -= alit
                    if (car.cid, d, floor) not in dest_count and floor not in car.waiting[d]:
                        car.committed[d].discard(floor)
            if car.door == "CLOSING" and t == car.door_since + T_DOOR_CLOSE:
                car.door = "CLOSED"
                car.door_since = None
                if not car.has_commitments():
                    car.direction = None

        # ---- new call arrivals + retry of any still-pending call ----
        for gidx in pending_by_tick.get(t, []):
            call = by_gidx[gidx]
            assign_call(cars, call, t, active_mask)
        for call in calls:
            if call.state == "pending" and call.arrival <= t:
                assign_call(cars, call, t, active_mask)

        # ---- timeout reassignment: only switch if a strictly better car
        # exists, so a call already assigned to the best available car does
        # not cycle forever between equally-placed cars once it has waited
        # past the threshold. ----
        if not mutant_no_timeout:
            for call in calls:
                if call.state == "assigned" and t - call.assign_tick >= wait_timeout:
                    incumbent = cars[call.assigned_car]
                    incumbent_cost = eligible_cost(incumbent, call.origin, call.direction, t)
                    best_car, best_cost = None, None
                    for car in cars:
                        if car.cid == incumbent.cid or not active_mask[car.cid]:
                            continue
                        cost = eligible_cost(car, call.origin, call.direction, t)
                        if cost is None:
                            continue
                        if best_cost is None or cost < best_cost or (cost == best_cost and car.cid < best_car.cid):
                            best_car, best_cost = car, cost
                    switch = (best_car is not None and
                              (mutant_no_cost_compare or incumbent_cost is None or best_cost < incumbent_cost))
                    if switch:
                        retract_call(cars, call)
                        do_assign(best_car, call, t)
                        reassign_count += 1
                    else:
                        call.assign_tick = t

        # ---- power-gated admission: mandatory ongoing draws first, then new
        # operations in fixed priority order A,B,C,D ----
        remaining = G
        for car in cars:
            if car.moving_until is not None and car.moving_until > t:
                remaining -= POWER["move"]
            elif car.door in ("OPENING", "CLOSING"):
                remaining -= POWER["door"]
        if mutant_power_disabled:
            remaining = 10 ** 9
        for car in cars:
            if not car.active:
                continue
            if car.moving_until is not None:
                continue
            if car.door in ("OPENING", "CLOSING"):
                continue
            if car.door == "DWELL":
                if t >= car.door_since + T_DWELL:
                    if remaining < POWER["door"]:
                        continue
                    car.door = "CLOSING"
                    car.door_since = t
                    remaining -= POWER["door"]
                continue
            if car.door == "CLOSED":
                hop = car_next_hop(car)
                if hop is None:
                    car.direction = None
                    continue
                car.direction = hop
                if car.pos in car.committed[hop]:
                    if remaining < POWER["door"]:
                        continue
                    car.door = "OPENING"
                    car.door_since = t
                    remaining -= POWER["door"]
                    continue
                if remaining < POWER["move"]:
                    continue
                car.pos += 1 if hop == UP else -1
                car.moving_until = t + T_FLOOR
                remaining -= POWER["move"]

        # ---- energy accounting ----
        tick_power = 0
        tick_energy = 0
        for car in cars:
            if car.moving_until is not None and car.moving_until - T_FLOOR <= t < car.moving_until:
                tick_power += POWER["move"]
                sign = 1 if car.direction == UP else -1
                tick_energy += ENERGY_BASE + ENERGY_LOAD_FACTOR * car.load * sign
            elif car.door in ("OPENING", "CLOSING"):
                tick_power += POWER["door"]
        if tick_power > G and not mutant_power_disabled:
            raise AssertionError(f"t={t}: power {tick_power} > G {G}")
        energy_total += tick_energy

        trace.append(dict(t=t, power=tick_power, energy=tick_energy,
                           cars=[dict(pos=c.pos, dir=c.direction, door=c.door, load=c.load)
                                 for c in cars]))

        if done_count == len(calls) and all(c.moving_until is None and c.door == "CLOSED"
                                             and not c.has_commitments() for c in cars):
            makespan = t + 1
            break
    else:
        undone = [c.gidx for c in calls if c.state != "done"]
        car_state = [(c.cid, c.pos, c.direction, c.door,
                      sorted(c.committed[UP]), sorted(c.committed[DOWN]), c.load) for c in cars]
        raise RuntimeError(f"did not terminate; undone={undone[:20]} (n={len(undone)}); cars={car_state}")

    avg_wait = wait_sum / len(calls)
    return dict(config=config, makespan=makespan, avg_wait=avg_wait,
                net_energy=energy_total, reassign_count=reassign_count,
                trace=trace, calls=calls)


def canonical_trace_serialization(result):
    lines = [f"CONFIG:{result['config']}"]
    for row in result["trace"]:
        lines.append(f"{row['t']},{row['power']},{row['energy']}")
    return "\n".join(lines)


if __name__ == "__main__":
    cfg = dict(active_cars=4, zoning="SPLIT", wait_timeout=150, capacity=8, power_budget=10)
    r = simulate(cfg)
    print(f"makespan={r['makespan']} avg_wait={r['avg_wait']:.2f} net_energy={r['net_energy']} "
          f"reassigns={r['reassign_count']}")
