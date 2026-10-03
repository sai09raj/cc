"""CELLGUARD-10 independent verifier — S04/S05.

Re-implements S02's per-tick update rules from scratch, in its own code,
never importing or calling bms_engine. Replays from t=1 to each of five
checkpoint ticks and compares its own computed state against the
primary's claimed state at that tick.
"""
CAPACITY = 6000.0
CC_CURRENT = 50.0
CV_VOLTAGE_THRESHOLD = 4150.0
CV_DECAY_STEP = 1.2
TAPER_CURRENT_THRESHOLD = 8.0
TAPER_CURRENT = 3.0
IR_DROP_PER_UNIT = 2.0
BASE_VOLTAGE = 3700.0
VOLT_PER_SOC_PCT = 6.0

AMBIENT = 250
HEAT_FULL = 6
HEAT_DERATED = 3
HEAT_TAPER = 1
COOL_PER_TICK = 2
DERATE_TEMP = 450
DERATE_FACTOR = 0.5
FAULT_TEMP_HIGH = 575
FAULT_TEMP_LOW = 520
FAULT_RELEASE_TICKS = 4
OVERCURRENT_MAX = 45.0

CHECKPOINTS = [50, 100, 161, 175, 206]  # ordinary, ordinary, CC->CV, fault-engage, fault-release


def independently_simulate_to(target_tick, bug=None):
    """bug: optional string naming a deliberate error, for S05's adversarial tests."""
    soc = 0.0
    temp = AMBIENT
    mode = "CC"
    cv_current = None
    fault_latched = False
    cool_counter = 0
    voltage_prev = BASE_VOLTAGE
    voltage_cur = BASE_VOLTAGE
    state = None

    for t in range(1, target_tick + 1):
        if mode == "CC" and voltage_prev >= CV_VOLTAGE_THRESHOLD:
            mode = "CV"
            cv_current = CC_CURRENT
        if mode == "CV" and cv_current <= TAPER_CURRENT_THRESHOLD:
            mode = "TAPER"

        if mode == "CC":
            mode_current = CC_CURRENT
        elif mode == "CV":
            mode_current = cv_current
            cv_current = max(0.0, cv_current - CV_DECAY_STEP)
        else:
            mode_current = TAPER_CURRENT

        if fault_latched:
            actual_current = 0.0
        elif temp >= DERATE_TEMP:
            actual_current = mode_current * DERATE_FACTOR
        else:
            actual_current = mode_current

        actual_current = min(actual_current, OVERCURRENT_MAX)

        soc = min(100.0, soc + actual_current / CAPACITY * 100.0)

        if actual_current <= 0:
            heat = 0
        elif mode == "TAPER":
            heat = HEAT_TAPER
        elif temp >= DERATE_TEMP:
            heat = HEAT_DERATED
        else:
            heat = HEAT_FULL
        temp = temp + heat - COOL_PER_TICK

        if not fault_latched and temp >= FAULT_TEMP_HIGH:
            fault_latched = True
            cool_counter = 0
        elif fault_latched:
            release_threshold = 2 if bug == "early_release" else FAULT_RELEASE_TICKS
            if temp <= FAULT_TEMP_LOW:
                cool_counter += 1
                if cool_counter >= release_threshold:
                    fault_latched = False
                    cool_counter = 0
            else:
                cool_counter = 0

        voltage_cur = BASE_VOLTAGE + soc * VOLT_PER_SOC_PCT - actual_current * IR_DROP_PER_UNIT
        if bug == "no_clamp" and t == target_tick:
            # re-derive what current/voltage WOULD be without the clamp, for the adversarial test
            pre_clamp = mode_current * (DERATE_FACTOR if (not fault_latched and temp >= DERATE_TEMP) else 1.0)
            actual_current = pre_clamp
            voltage_cur = BASE_VOLTAGE + soc * VOLT_PER_SOC_PCT - actual_current * IR_DROP_PER_UNIT
        voltage_prev = voltage_cur

        state = {
            "t": t, "mode": mode, "soc": round(soc, 2), "temp": temp,
            "current": round(actual_current, 2), "voltage": round(voltage_cur, 2),
            "fault": fault_latched,
        }
    return state


def check_checkpoint(claimed_row, checkpoint_tick):
    independent = independently_simulate_to(checkpoint_tick)
    mismatches = []
    for key in ("mode", "soc", "temp", "current", "voltage", "fault"):
        if claimed_row.get(key) != independent[key]:
            mismatches.append((key, claimed_row.get(key), independent[key]))
    return (len(mismatches) == 0), mismatches


def check_all_checkpoints(claimed_rows_by_tick):
    for cp in CHECKPOINTS:
        claimed = claimed_rows_by_tick.get(cp)
        if claimed is None:
            return False, f"no claimed row for checkpoint t={cp}"
        ok, mismatches = check_checkpoint(claimed, cp)
        if not ok:
            return False, f"t={cp} mismatches: {mismatches}"
    return True, "all checkpoints consistent"


def accepts_true_program():
    import bms_engine as E
    for k in E.MUTANT:
        E.MUTANT[k] = False
    rows = E.run()
    by_tick = {r["t"]: {k: v for k, v in r.items() if k in
                         ("mode", "soc", "temp", "current", "voltage", "fault")} for r in rows}
    return check_all_checkpoints(by_tick)


def adversarial_mutation_early_release():
    """A claimed row at the fault-release checkpoint (t=206) that reports the
    fault released after only 2 consecutive cool ticks, not 4. Verifier must reject."""
    bugged = independently_simulate_to(206, bug="early_release")
    claimed_row = dict(bugged)
    ok, mismatches = check_checkpoint(claimed_row, 206)
    return (not ok), mismatches


def adversarial_mutation_no_clamp():
    """A claimed row at a CC-phase checkpoint (t=50) that reports delivered
    current/voltage as if the overcurrent clamp were never applied. Verifier
    must reject."""
    bugged = independently_simulate_to(50, bug="no_clamp")
    claimed_row = dict(bugged)
    ok, mismatches = check_checkpoint(claimed_row, 50)
    return (not ok), mismatches


if __name__ == "__main__":
    ok, reason = accepts_true_program()
    print("accepts true program:", ok, "-", reason)
    rejA, reasonA = adversarial_mutation_early_release()
    print("rejects mutation A (early fault release):", rejA, "-", reasonA)
    rejB, reasonB = adversarial_mutation_no_clamp()
    print("rejects mutation B (overcurrent clamp skipped):", rejB, "-", reasonB)
