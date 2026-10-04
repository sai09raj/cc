"""CELLGUARD-10 independent verifier — re-implements the eleven per-tick
update rules (including cell balancing) from scratch, in its own code,
never importing or calling bms_engine. Replays from t=1 to each of
several checkpoint ticks and compares its own computed state against
the primary's claimed state at that tick.
"""
CAPACITY_A = 5700.0
CAPACITY_B = 6300.0
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

BALANCE_THRESHOLD = 1.5
BALANCE_BLEED = 8.0

CHECKPOINTS = [50, 100, 163, 175, 198, 206]


def independently_simulate_to(target_tick, bug=None):
    """bug: optional string naming a deliberate error, for required adversarial tests."""
    soc_a, soc_b = 0.0, 0.0
    temp = AMBIENT
    mode = "CC"
    cv_current = None
    fault_latched = False
    cool_counter = 0
    va_prev, vb_prev = BASE_VOLTAGE, BASE_VOLTAGE
    state = None

    for t in range(1, target_tick + 1):
        ref_voltage = max(va_prev, vb_prev)
        if mode == "CC" and ref_voltage >= CV_VOLTAGE_THRESHOLD:
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
            base_current = 0.0
        elif temp >= DERATE_TEMP:
            base_current = mode_current * DERATE_FACTOR
        else:
            base_current = mode_current
        base_current = min(base_current, OVERCURRENT_MAX)

        cur_a, cur_b = base_current, base_current
        diff = soc_a - soc_b
        balance_threshold = 999.0 if bug == "no_balancing" else BALANCE_THRESHOLD
        if base_current > 0 and abs(diff) >= balance_threshold:
            if diff > 0:
                cur_a = max(0.0, base_current - BALANCE_BLEED)
            else:
                cur_b = max(0.0, base_current - BALANCE_BLEED)

        soc_a = min(100.0, soc_a + cur_a / CAPACITY_A * 100.0)
        soc_b = min(100.0, soc_b + cur_b / CAPACITY_B * 100.0)

        if base_current <= 0:
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

        va_cur = BASE_VOLTAGE + soc_a * VOLT_PER_SOC_PCT - cur_a * IR_DROP_PER_UNIT
        vb_cur = BASE_VOLTAGE + soc_b * VOLT_PER_SOC_PCT - cur_b * IR_DROP_PER_UNIT
        va_prev, vb_prev = va_cur, vb_cur

        state = {
            "t": t, "mode": mode,
            "soc_a": round(soc_a, 2), "soc_b": round(soc_b, 2), "temp": temp,
            "current_a": round(cur_a, 2), "current_b": round(cur_b, 2),
            "voltage_a": round(va_cur, 2), "voltage_b": round(vb_cur, 2),
            "fault": fault_latched,
        }
    return state


FIELDS = ("mode", "soc_a", "soc_b", "temp", "current_a", "current_b", "voltage_a", "voltage_b", "fault")


def check_checkpoint(claimed_row, checkpoint_tick):
    independent = independently_simulate_to(checkpoint_tick)
    mismatches = []
    for key in FIELDS:
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
    by_tick = {r["t"]: {k: v for k, v in r.items() if k in FIELDS} for r in rows}
    return check_all_checkpoints(by_tick)


def adversarial_mutation_early_release():
    """A claimed row at the fault-release checkpoint (t=206) that reports the
    fault released after only 2 consecutive cool ticks, not 4. Verifier must reject."""
    bugged = independently_simulate_to(206, bug="early_release")
    ok, mismatches = check_checkpoint(dict(bugged), 206)
    return (not ok), mismatches


def adversarial_mutation_no_balancing():
    """A claimed row at t=50 (a tick where balancing is genuinely active in the
    true trace) that reports both cells receiving identical current, as if
    balancing were never applied. Verifier must reject."""
    bugged = independently_simulate_to(50, bug="no_balancing")
    ok, mismatches = check_checkpoint(dict(bugged), 50)
    return (not ok), mismatches


if __name__ == "__main__":
    ok, reason = accepts_true_program()
    print("accepts true program:", ok, "-", reason)
    rejA, reasonA = adversarial_mutation_early_release()
    print("rejects mutation A (early fault release):", rejA, "-", reasonA)
    rejB, reasonB = adversarial_mutation_no_balancing()
    print("rejects mutation B (balancing skipped):", rejB, "-", reasonB)
