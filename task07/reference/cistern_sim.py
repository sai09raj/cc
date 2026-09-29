#!/usr/bin/env python3
"""CISTERN-7 canonical reference simulator.

Deterministic, tick-by-tick (1 minute, 1440 ticks/day) wet-well level
control simulator. Implements design/semantic-contract.md sections S01-S09
exactly. Offline, stdlib-only.
"""
import itertools
import hashlib

TICKS = 1440
DT = 1.0
A_WELL = 60.0
LOW_CUTOFF = 0.4
HIGH_HIGH = 4.2
MIN_OFF = 4

PUMP_IDS = [0, 1, 2]
PUMP_NAMES = {0: "A", 1: "B", 2: "C"}

# S01a -- DRY hydrograph anchors (minute, m^3/min), linearly interpolated.
DRY_ANCHORS = [
    (0, 0.5), (180, 0.5), (330, 2.5), (480, 6.0), (600, 3.5),
    (780, 3.0), (1080, 5.5), (1200, 4.0), (1320, 1.5), (1439, 0.5),
]
STORM_START, STORM_PEAK, STORM_END = 300, 360, 420
STORM_PEAK_Q = 8.0

# S03 -- pump curve breakpoints (level m, discharge m^3/min).
PUMP_CURVE = [(0.4, 3.0), (2.0, 4.0), (4.2, 5.0)]
# Pumps A and B are the station's matched primary units; pump C is the
# smaller reserve unit only ever brought into service at duty_pump_count=3
# (it is always excluded first -- S08), scaled to 85% of the shared curve.
PUMP_CAPACITY_SCALE = {0: 1.0, 1: 1.0, 2: 0.85}

# S03 -- deadband settings: role -> (start, stop) elevations (m).
DEADBANDS = {
    "TIGHT":  {"LEAD": (1.2, 0.8), "LAG1": (1.8, 1.4), "LAG2": (2.4, 2.0)},
    "MEDIUM": {"LEAD": (1.5, 0.7), "LAG1": (2.2, 1.2), "LAG2": (3.0, 1.8)},
    "WIDE":   {"LEAD": (2.0, 0.6), "LAG1": (3.0, 1.0), "LAG2": (3.8, 1.6)},
}

# S08 sweep domains
DUTY_PUMP_COUNTS = [1, 2, 3]
ROTATION_POLICIES = ["STRICT_ALTERNATE", "RUNTIME_BALANCED", "FIXED_LEAD"]
DEADBAND_SETTINGS = ["TIGHT", "MEDIUM", "WIDE"]
MIN_RUN_SETTINGS = {"SHORT": 8, "LONG": 15}
DAY_TYPES = ["DRY", "WET"]

# S07 -- TOU tariff bands: (start_minute_inclusive, end_minute_inclusive, $/kWh)
TARIFF_BANDS = [
    (0, 419, 0.08),      # off-peak continuation past midnight
    (420, 959, 0.14),    # mid-peak (07:00-15:59)
    (960, 1259, 0.22),   # on-peak (16:00-20:59)
    (1260, 1379, 0.14),  # mid-peak (21:00-22:59)
    (1380, 1439, 0.08),  # off-peak (23:00-23:59)
]
PUMP_KW = 15.0

WEAR_STARTS_CEILING = 15
ENERGY_FEASIBLE_OVERFLOW = 0.0


def interp(anchors, x):
    if x <= anchors[0][0]:
        return anchors[0][1]
    if x >= anchors[-1][0]:
        return anchors[-1][1]
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            frac = (x - x0) / (x1 - x0)
            return y0 + frac * (y1 - y0)
    raise AssertionError(x)


def inflow(t, day_type):
    q = interp(DRY_ANCHORS, t)
    if day_type == "WET":
        if STORM_START <= t <= STORM_PEAK:
            frac = (t - STORM_START) / (STORM_PEAK - STORM_START)
            q += frac * STORM_PEAK_Q
        elif STORM_PEAK < t <= STORM_END:
            frac = (STORM_END - t) / (STORM_END - STORM_PEAK)
            q += frac * STORM_PEAK_Q
    return q


def pump_discharge(level, pid=0):
    return interp(PUMP_CURVE, level) * PUMP_CAPACITY_SCALE[pid]


def tariff_rate(t):
    for lo, hi, rate in TARIFF_BANDS:
        if lo <= t <= hi:
            return rate
    raise AssertionError(t)


class Pump:
    __slots__ = ("pid", "running", "running_since", "last_stop_tick",
                 "total_run_minutes", "starts")

    def __init__(self, pid):
        self.pid = pid
        self.running = False
        self.running_since = None
        self.last_stop_tick = None
        self.total_run_minutes = 0
        self.starts = 0


def simulate(config, mutant_rotation_every_tick=False, mutant_no_min_run=False,
             mutant_flat_tariff=False, mutant_flat_pump_curve=False):
    """config: dict with duty_pump_count, rotation_policy, deadband,
    min_run_time (str key into MIN_RUN_SETTINGS), day_type."""
    duty_n = config["duty_pump_count"]
    roster = list(range(duty_n))
    policy = config["rotation_policy"]
    band = DEADBANDS[config["deadband"]]
    min_run = MIN_RUN_SETTINGS[config["min_run_time"]]
    day_type = config["day_type"]

    pumps = {pid: Pump(pid) for pid in PUMP_IDS}
    lead_id = None
    rotation_counter = 0

    level = 1.0  # fixed, stated initial level for every run (below every LEAD start)
    overflow_volume = 0.0
    overflow_duration = 0
    energy_cost = 0.0
    trace = []

    for t in range(TICKS):
        # ---- role assignment this tick (derived fresh, lead identity sticky) ----
        if lead_id is None and roster:
            candidate_level_ok = level >= band["LEAD"][0]
            if candidate_level_ok:
                if policy == "FIXED_LEAD":
                    lead_id = roster[0]
                elif policy == "STRICT_ALTERNATE":
                    lead_id = roster[rotation_counter % duty_n]
                elif policy == "RUNTIME_BALANCED":
                    lead_id = min(roster, key=lambda p: (pumps[p].total_run_minutes, p))
                else:
                    raise ValueError(policy)

        lag_pool = [p for p in roster if p != lead_id]
        role_of = {}
        if lead_id is not None:
            role_of[lead_id] = "LEAD"
        if len(lag_pool) >= 1:
            role_of[lag_pool[0]] = "LAG1"
        if len(lag_pool) >= 2:
            role_of[lag_pool[1]] = "LAG2"

        # ---- start/stop decisions using level(t) ----
        for pid in roster:
            pump = pumps[pid]
            role = role_of.get(pid)
            if role is None:
                continue
            start, stop = band[role]
            if not pump.running:
                off_ok = (pump.last_stop_tick is None or
                          t - pump.last_stop_tick >= MIN_OFF)
                if level >= start and off_ok:
                    pump.running = True
                    pump.running_since = t
                    pump.starts += 1
                    if role == "LEAD":
                        if policy in ("STRICT_ALTERNATE",) and not mutant_rotation_every_tick:
                            rotation_counter += 1
                        elif mutant_rotation_every_tick:
                            pass  # advanced unconditionally below instead
            else:
                if level <= stop:
                    run_elapsed = t - pump.running_since
                    if mutant_no_min_run or run_elapsed >= min_run:
                        pump.running = False
                        pump.last_stop_tick = t
                        if role == "LEAD":
                            lead_id = None

        if mutant_rotation_every_tick and policy == "STRICT_ALTERNATE":
            rotation_counter += 1

        # ---- outflow, energy, mass balance ----
        running_pumps = [pid for pid in roster if pumps[pid].running]
        if mutant_flat_pump_curve:
            q_out = sum(4.0 for _ in running_pumps)
        else:
            q_out = sum(pump_discharge(level, pid) for pid in running_pumps)
        for pid in running_pumps:
            pumps[pid].total_run_minutes += 1

        q_in = inflow(t, day_type)
        unclamped = level + (q_in - q_out) * DT / A_WELL

        if unclamped > HIGH_HIGH:
            overflow_volume += (unclamped - HIGH_HIGH) * A_WELL
            overflow_duration += 1
            next_level = HIGH_HIGH
        elif unclamped < LOW_CUTOFF:
            next_level = LOW_CUTOFF
        else:
            next_level = unclamped

        if mutant_flat_tariff:
            rate = 0.14
        else:
            rate = tariff_rate(t)
        energy_cost += len(running_pumps) * PUMP_KW * (DT / 60.0) * rate

        trace.append({
            "t": t, "level": round(level, 6), "q_in": round(q_in, 6),
            "q_out": round(q_out, 6),
            "running": tuple(sorted(running_pumps)),
            "lead": lead_id,
        })

        level = next_level

    peak_level = max(row["level"] for row in trace)
    starts = {pid: pumps[pid].starts for pid in PUMP_IDS}
    run_minutes = {pid: pumps[pid].total_run_minutes for pid in PUMP_IDS}
    max_starts = max((starts[pid] for pid in roster), default=0)

    return {
        "trace": trace,
        "overflow_volume": round(overflow_volume, 6),
        "overflow_duration": overflow_duration,
        "total_energy_cost": round(energy_cost, 6),
        "peak_level": round(peak_level, 6),
        "starts": starts,
        "run_minutes": run_minutes,
        "max_starts": max_starts,
        "final_level": round(level, 6),
        "initial_level": 1.0,
    }


def all_policy_configs():
    """The 54 legal control-setting configurations (S08) -- day_type is
    weather, not a control setting, so it is never part of this space."""
    for duty, policy, deadband, mr in itertools.product(
            DUTY_PUMP_COUNTS, ROTATION_POLICIES, DEADBAND_SETTINGS,
            MIN_RUN_SETTINGS.keys()):
        yield {
            "duty_pump_count": duty, "rotation_policy": policy,
            "deadband": deadband, "min_run_time": mr,
        }


def policy_key(cfg):
    return (cfg["duty_pump_count"], cfg["rotation_policy"], cfg["deadband"],
            cfg["min_run_time"])


def all_configs():
    """The 108 sweep rows (54 policy configs x 2 day-types)."""
    for base in all_policy_configs():
        for day in DAY_TYPES:
            yield dict(base, day_type=day)


def config_key(cfg):
    return policy_key(cfg) + (cfg["day_type"],)


def run_both_days(policy_cfg, **mutant_kwargs):
    """Run a policy config's DRY and WET rows; return (dry_result, wet_result)."""
    dry = simulate(dict(policy_cfg, day_type="DRY"), **mutant_kwargs)
    wet = simulate(dict(policy_cfg, day_type="WET"), **mutant_kwargs)
    return dry, wet


def combined_energy(dry, wet):
    return round(dry["total_energy_cost"] + wet["total_energy_cost"], 6)


def worst_peak(dry, wet):
    return round(max(dry["peak_level"], wet["peak_level"]), 6)


def worst_imbalance(dry, wet):
    worst = 0.0
    for r in (dry, wet):
        total = sum(r["run_minutes"].values())
        if total == 0:
            continue
        worst = max(worst, max(r["run_minutes"].values()) / total)
    return round(worst, 6)


def is_feasible(dry, wet):
    return dry["overflow_volume"] == 0.0 and wet["overflow_volume"] == 0.0


WEAR_IMBALANCE_CEILING = 0.80


def selections(sweep_by_policy):
    """sweep_by_policy: dict policy_key -> (dry_result, wet_result)."""
    feasible = [k for k, (d, w) in sweep_by_policy.items() if is_feasible(d, w)]

    def e(k):
        d, w = sweep_by_policy[k]
        return combined_energy(d, w)

    def p(k):
        d, w = sweep_by_policy[k]
        return worst_peak(d, w)

    def imb(k):
        d, w = sweep_by_policy[k]
        return worst_imbalance(d, w)

    energy_opt = min(feasible, key=lambda k: (e(k), k)) if feasible else None
    reliab_opt = min(sweep_by_policy, key=lambda k: (p(k), e(k), k))
    wear_pool = [k for k in feasible if imb(k) <= WEAR_IMBALANCE_CEILING]
    wear_opt = min(wear_pool, key=lambda k: (e(k), k)) if wear_pool else None
    return energy_opt, reliab_opt, wear_opt


def canonical_trace_serialization(cfg, result):
    """Deterministic serialization of one config's full trace for hashing."""
    parts = [f"CISTERN7|{config_key(cfg)}"]
    for row in result["trace"]:
        parts.append(f"{row['t']}|{row['level']:.6f}|{row['q_in']:.6f}|"
                      f"{row['q_out']:.6f}|{','.join(map(str, row['running']))}|"
                      f"{row['lead']}")
    return "\n".join(parts)


if __name__ == "__main__":
    policy_configs = list(all_policy_configs())
    print(f"Legal control-setting configurations: {len(policy_configs)} "
          f"({len(policy_configs) * 2} sweep rows)")

    sweep = {}
    for pc in policy_configs:
        sweep[policy_key(pc)] = run_both_days(pc)

    energy_opt, reliab_opt, wear_opt = selections(sweep)
    for name, k in [("energy_opt", energy_opt), ("reliab_opt", reliab_opt),
                     ("wear_opt", wear_opt)]:
        d, w = sweep[k]
        print(f"{name}: {k}")
        print(f"  E={combined_energy(d, w)}  worst_peak={worst_peak(d, w)}  "
              f"imbalance={worst_imbalance(d, w)}  "
              f"feasible={is_feasible(d, w)}")

    baseline_policy = {"duty_pump_count": 3, "rotation_policy": "STRICT_ALTERNATE",
                        "deadband": "TIGHT", "min_run_time": "LONG"}
    baseline = dict(baseline_policy, day_type="WET")
    r = simulate(baseline)
    print("\nBaseline", baseline)
    print(f"  overflow_volume={r['overflow_volume']}  overflow_duration={r['overflow_duration']}")
    print(f"  total_energy_cost={r['total_energy_cost']}  peak_level={r['peak_level']}")
    print(f"  starts={r['starts']}  run_minutes={r['run_minutes']}")
    h = hashlib.sha256(canonical_trace_serialization(baseline, r).encode()).hexdigest()[:16]
    print(f"  trace hash (16 hex) = {h}")
