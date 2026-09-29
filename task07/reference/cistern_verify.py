#!/usr/bin/env python3
"""CISTERN-7 independent verifier.

Deliberately structured differently from cistern_sim.py (a single running
state dict updated in one pass per tick, rather than a Pump-object model),
sharing only the immutable input constants (S01-S09). Provides both a
from-scratch re-simulation and a feasibility-certificate checker that can
be run against any delivered trace, including a corrupted one, without
re-simulating.
"""
import cistern_sim as REF  # immutable constants only: curves, bands, tariff

TOL = 1e-4


def _interp(anchors, x):
    if x <= anchors[0][0]:
        return anchors[0][1]
    if x >= anchors[-1][0]:
        return anchors[-1][1]
    lo, hi = 0, len(anchors) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if anchors[mid][0] <= x:
            lo = mid
        else:
            hi = mid
    x0, y0 = anchors[lo]
    x1, y1 = anchors[hi]
    if x1 == x0:
        return y0
    return y0 + (x - x0) / (x1 - x0) * (y1 - y0)


def inflow_independent(t, day_type):
    q = _interp(REF.DRY_ANCHORS, t)
    if day_type == "WET" and REF.STORM_START <= t <= REF.STORM_END:
        half = REF.STORM_PEAK - REF.STORM_START
        dist_from_peak = abs(t - REF.STORM_PEAK)
        q += max(0.0, REF.STORM_PEAK_Q * (1 - dist_from_peak / half))
    return q


def independent_simulate(policy_cfg, day_type):
    """From-scratch re-simulation: one state dict, updated per tick, rather
    than Pump objects. Used to cross-check cistern_sim.simulate's output."""
    duty_n = policy_cfg["duty_pump_count"]
    roster = list(range(duty_n))
    policy = policy_cfg["rotation_policy"]
    band = REF.DEADBANDS[policy_cfg["deadband"]]
    min_run = REF.MIN_RUN_SETTINGS[policy_cfg["min_run_time"]]

    running = {p: False for p in REF.PUMP_IDS}
    started_at = {p: None for p in REF.PUMP_IDS}
    stopped_at = {p: None for p in REF.PUMP_IDS}
    run_min = {p: 0 for p in REF.PUMP_IDS}
    starts = {p: 0 for p in REF.PUMP_IDS}
    lead = None
    rot_ctr = 0
    level = 1.0
    overflow_vol = 0.0
    overflow_ticks = 0
    energy = 0.0
    rows = []

    for t in range(REF.TICKS):
        if lead is None and roster and level >= band["LEAD"][0]:
            if policy == "FIXED_LEAD":
                lead = roster[0]
            elif policy == "STRICT_ALTERNATE":
                lead = roster[rot_ctr % duty_n]
            else:  # RUNTIME_BALANCED
                lead = sorted(roster, key=lambda p: (run_min[p], p))[0]

        others = sorted(p for p in roster if p != lead)
        roles = {}
        if lead is not None:
            roles[lead] = "LEAD"
        for i, p in enumerate(others[:2]):
            roles[p] = ["LAG1", "LAG2"][i]

        for p in roster:
            role = roles.get(p)
            if role is None:
                continue
            start, stop = band[role]
            if not running[p]:
                off_ok = stopped_at[p] is None or t - stopped_at[p] >= REF.MIN_OFF
                if level >= start and off_ok:
                    running[p] = True
                    started_at[p] = t
                    starts[p] += 1
                    if role == "LEAD" and policy == "STRICT_ALTERNATE":
                        rot_ctr += 1
            else:
                if level <= stop and (t - started_at[p]) >= min_run:
                    running[p] = False
                    stopped_at[p] = t
                    if role == "LEAD":
                        lead = None

        on = [p for p in roster if running[p]]
        q_out = sum(_interp(REF.PUMP_CURVE, level) * REF.PUMP_CAPACITY_SCALE[p] for p in on)
        for p in on:
            run_min[p] += 1
        q_in = inflow_independent(t, day_type)

        nxt = level + (q_in - q_out) * REF.DT / REF.A_WELL
        if nxt > REF.HIGH_HIGH:
            overflow_vol += (nxt - REF.HIGH_HIGH) * REF.A_WELL
            overflow_ticks += 1
            nxt = REF.HIGH_HIGH
        elif nxt < REF.LOW_CUTOFF:
            nxt = REF.LOW_CUTOFF

        rate = REF.tariff_rate(t)
        energy += len(on) * REF.PUMP_KW * (REF.DT / 60.0) * rate

        rows.append({"t": t, "level": round(level, 6), "q_in": round(q_in, 6),
                      "q_out": round(q_out, 6), "running": tuple(sorted(on)),
                      "lead": lead})
        level = nxt

    return {
        "trace": rows,
        "overflow_volume": round(overflow_vol, 6),
        "overflow_duration": overflow_ticks,
        "total_energy_cost": round(energy, 6),
        "peak_level": round(max(r["level"] for r in rows), 6),
        "starts": starts,
        "run_minutes": run_min,
    }


def feasibility_certificate(trace, policy_cfg, reported_overflow_volume,
                             reported_energy_cost):
    """Checks a delivered trace's physical consistency independent of how it
    was produced. Returns (ok, reason)."""
    min_run = REF.MIN_RUN_SETTINGS[policy_cfg["min_run_time"]]

    # (a) mass-balance closure, tick by tick, from the trace's own recorded
    # level/q_in/q_out (catches a level update inconsistent with q_in-q_out).
    computed_overflow = 0.0
    for i in range(len(trace) - 1):
        row, nxt = trace[i], trace[i + 1]
        predicted = row["level"] + (row["q_in"] - row["q_out"]) * REF.DT / REF.A_WELL
        if predicted > REF.HIGH_HIGH:
            computed_overflow += (predicted - REF.HIGH_HIGH) * REF.A_WELL
            predicted = REF.HIGH_HIGH
        elif predicted < REF.LOW_CUTOFF:
            predicted = REF.LOW_CUTOFF
        if abs(predicted - nxt["level"]) > TOL:
            return False, (f"mass-balance violation at t={row['t']}: "
                            f"predicted level {predicted:.6f} != recorded "
                            f"{nxt['level']:.6f}")
    if abs(computed_overflow - reported_overflow_volume) > 1e-3:
        return False, (f"reported overflow_volume {reported_overflow_volume} "
                        f"!= recomputed {computed_overflow:.6f}")

    # (b) level bounds
    for row in trace:
        if not (REF.LOW_CUTOFF - TOL <= row["level"] <= REF.HIGH_HIGH + TOL):
            return False, f"level {row['level']} out of bounds at t={row['t']}"

    # (c) per-pump minimum-run / minimum-off timer compliance, derived from
    # the trace's own running-set transitions.
    prev_on = set()
    last_start = {}
    last_stop = {}
    for row in trace:
        on = set(row["running"])
        started = on - prev_on
        stopped = prev_on - on
        for p in started:
            if p in last_stop and row["t"] - last_stop[p] < REF.MIN_OFF:
                return False, (f"pump {p} restarted at t={row['t']} before "
                                f"MIN_OFF ({REF.MIN_OFF}) elapsed")
            last_start[p] = row["t"]
        for p in stopped:
            if p in last_start and row["t"] - last_start[p] < min_run:
                return False, (f"pump {p} stopped at t={row['t']} before "
                                f"MIN_RUN ({min_run}) elapsed")
            last_stop[p] = row["t"]
        prev_on = on

    # (d) reported energy sanity: recompute independently from the running
    # sets and tariff bands.
    recomputed_energy = 0.0
    for row in trace:
        recomputed_energy += len(row["running"]) * REF.PUMP_KW * (REF.DT / 60.0) * REF.tariff_rate(row["t"])
    if abs(recomputed_energy - reported_energy_cost) > 1e-3:
        return False, (f"reported energy {reported_energy_cost} != "
                        f"recomputed {recomputed_energy:.6f}")

    return True, "ok"


def run_adversarial_mutations():
    """Confirms the verifier accepts a true baseline and rejects both
    required adversarial mutations."""
    # This is the packet's own baseline config (rubric.md witnesses 33-37):
    # TIGHT deadband's natural on/off cycle is short enough for min_run_time
    # to actually bind here (MEDIUM/WIDE cycles run long enough that
    # mutant_no_min_run would silently produce an identical trace to the
    # correct run for those deadbands).
    policy_cfg = {"duty_pump_count": 3, "rotation_policy": "STRICT_ALTERNATE",
                  "deadband": "TIGHT", "min_run_time": "LONG"}
    cfg = dict(policy_cfg, day_type="WET")

    true_result = REF.simulate(cfg)
    ok, reason = feasibility_certificate(
        true_result["trace"], policy_cfg, true_result["overflow_volume"],
        true_result["total_energy_cost"])
    print(f"[baseline]              accepted={ok}  ({reason})")
    assert ok, "verifier must accept the true baseline"

    # Mutation A: corrupt one tick's recorded level so it no longer matches
    # q_in - q_out (a mass-balance violation).
    corrupted = [dict(r) for r in true_result["trace"]]
    corrupted[500]["level"] = round(corrupted[500]["level"] + 0.5, 6)
    ok_a, reason_a = feasibility_certificate(
        corrupted, policy_cfg, true_result["overflow_volume"],
        true_result["total_energy_cost"])
    print(f"[mutation A: mass-bal]  accepted={ok_a}  ({reason_a})")
    assert not ok_a, "verifier must reject the mass-balance mutation"

    # Mutation B: a pump stops before its own MIN_RUN has elapsed (produced
    # by the primary's own mutant_no_min_run flag -- a genuine wrong run,
    # not a hand-edited trace).
    bad_result = REF.simulate(cfg, mutant_no_min_run=True)
    ok_b, reason_b = feasibility_certificate(
        bad_result["trace"], policy_cfg, bad_result["overflow_volume"],
        bad_result["total_energy_cost"])
    print(f"[mutation B: min-run]  accepted={ok_b}  ({reason_b})")
    assert not ok_b, "verifier must reject the minimum-run-time violation"

    print("\nAll three checks passed: baseline accepted, both required "
          "adversarial mutations rejected.")


def cross_check_independent_resimulation():
    policy_cfg = {"duty_pump_count": 3, "rotation_policy": "STRICT_ALTERNATE",
                  "deadband": "MEDIUM", "min_run_time": "SHORT"}
    cfg = dict(policy_cfg, day_type="WET")
    primary = REF.simulate(cfg)
    indep = independent_simulate(policy_cfg, "WET")
    agree = (primary["overflow_volume"] == indep["overflow_volume"] and
             primary["total_energy_cost"] == indep["total_energy_cost"] and
             primary["peak_level"] == indep["peak_level"] and
             primary["starts"] == indep["starts"] and
             primary["run_minutes"] == indep["run_minutes"])
    print(f"Independent re-simulation agrees with primary: {agree}")
    if not agree:
        print("  primary:", primary["overflow_volume"], primary["total_energy_cost"],
              primary["peak_level"], primary["starts"])
        print("  indep:  ", indep["overflow_volume"], indep["total_energy_cost"],
              indep["peak_level"], indep["starts"])
    assert agree, "independent re-simulation must match the primary exactly"


if __name__ == "__main__":
    cross_check_independent_resimulation()
    print()
    run_adversarial_mutations()
