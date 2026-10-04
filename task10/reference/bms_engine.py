"""CELLGUARD-10 primary engine: discrete-tick battery pack charge/thermal
controller, TWO series-connected cells (A, B) with independent capacity,
state of charge, and voltage, sharing pack-level mode/temperature/fault
state. Every tick's state is computed from the previous tick's -- genuine
state-threading, not independent per-item facts.

Mutant hooks (S08 score-topology audit) in MUTANT dict below.
"""
import hashlib

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

N_TICKS = 320

MUTANT = {
    "no_derate": False,
    "fault_release_no_hysteresis": False,
    "cv_no_decay": False,
    "no_overcurrent_clamp": False,
    "taper_uses_full_heat": False,
    "no_balancing": False,          # mutant 6: never apply cell balancing
}


def run():
    soc_a, soc_b = 0.0, 0.0
    temp = AMBIENT
    mode = "CC"
    cv_current = None
    fault_latched = False
    cool_counter = 0
    va_prev, vb_prev = BASE_VOLTAGE, BASE_VOLTAGE
    va_cur, vb_cur = BASE_VOLTAGE, BASE_VOLTAGE

    rows = []
    for t in range(1, N_TICKS + 1):
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
            if not MUTANT["cv_no_decay"]:
                cv_current = max(0.0, cv_current - CV_DECAY_STEP)
        else:
            mode_current = TAPER_CURRENT

        if fault_latched:
            base_current = 0.0
        elif temp >= DERATE_TEMP and not MUTANT["no_derate"]:
            base_current = mode_current * DERATE_FACTOR
        else:
            base_current = mode_current

        if not MUTANT["no_overcurrent_clamp"]:
            base_current = min(base_current, OVERCURRENT_MAX)

        cur_a, cur_b = base_current, base_current
        diff = soc_a - soc_b
        if (not MUTANT["no_balancing"]) and base_current > 0 and abs(diff) >= BALANCE_THRESHOLD:
            if diff > 0:
                cur_a = max(0.0, base_current - BALANCE_BLEED)
            else:
                cur_b = max(0.0, base_current - BALANCE_BLEED)

        soc_a = min(100.0, soc_a + cur_a / CAPACITY_A * 100.0)
        soc_b = min(100.0, soc_b + cur_b / CAPACITY_B * 100.0)

        if base_current <= 0:
            heat = 0
        elif mode == "TAPER" and not MUTANT["taper_uses_full_heat"]:
            heat = HEAT_TAPER
        elif temp >= DERATE_TEMP and not MUTANT["no_derate"]:
            heat = HEAT_DERATED
        else:
            heat = HEAT_FULL
        temp = temp + heat - COOL_PER_TICK

        if not fault_latched and temp >= FAULT_TEMP_HIGH:
            fault_latched = True
            cool_counter = 0
        elif fault_latched:
            if MUTANT["fault_release_no_hysteresis"]:
                if temp <= FAULT_TEMP_LOW:
                    fault_latched = False
                    cool_counter = 0
            else:
                if temp <= FAULT_TEMP_LOW:
                    cool_counter += 1
                    if cool_counter >= FAULT_RELEASE_TICKS:
                        fault_latched = False
                        cool_counter = 0
                else:
                    cool_counter = 0

        va_cur = BASE_VOLTAGE + soc_a * VOLT_PER_SOC_PCT - cur_a * IR_DROP_PER_UNIT
        vb_cur = BASE_VOLTAGE + soc_b * VOLT_PER_SOC_PCT - cur_b * IR_DROP_PER_UNIT
        va_prev, vb_prev = va_cur, vb_cur

        rows.append({
            "t": t, "mode": mode,
            "soc_a": round(soc_a, 2), "soc_b": round(soc_b, 2),
            "temp": temp,
            "current_a": round(cur_a, 2), "current_b": round(cur_b, 2),
            "voltage_a": round(va_cur, 2), "voltage_b": round(vb_cur, 2),
            "fault": fault_latched,
            "cv_reg_current": round(cv_current, 2) if cv_current is not None else None,
            "fault_counter": cool_counter,
        })
    return rows


def serialize(rows):
    # All *_a/*_b numeric fields are fixed-width 2-decimal-place strings
    # (e.g. "25.00", never "25" or "25.0") -- see mistake #69.
    lines = ["CELLGUARD10-CERT-V2"]
    for r in rows:
        lines.append(
            f"t={r['t']};mode={r['mode']};soc_a={r['soc_a']:.2f};soc_b={r['soc_b']:.2f};"
            f"temp={r['temp']};current_a={r['current_a']:.2f};current_b={r['current_b']:.2f};"
            f"voltage_a={r['voltage_a']:.2f};voltage_b={r['voltage_b']:.2f};fault={r['fault']}"
        )
    return "\n".join(lines) + "\n"


def certificate_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


if __name__ == "__main__":
    for k in MUTANT:
        MUTANT[k] = False
    rows = run()
    text = serialize(rows)
    print(f"ticks: {len(rows)}")
    prev_mode = None
    for r in rows:
        if r["mode"] != prev_mode:
            print(f"  t={r['t']} MODE->{r['mode']} soc_a={r['soc_a']} soc_b={r['soc_b']} temp={r['temp']}")
            prev_mode = r["mode"]
    prev_fault = False
    for r in rows:
        if r["fault"] != prev_fault:
            print(f"  t={r['t']} FAULT->{r['fault']} temp={r['temp']}")
            prev_fault = r["fault"]
    balance_ticks = sum(1 for r in rows if abs(r["current_a"] - r["current_b"]) > 0.001)
    print("balance-active ticks:", balance_ticks)
    print("final:", rows[-1])
    print("HASH:", certificate_hash(text))
