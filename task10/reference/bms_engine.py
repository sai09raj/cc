"""CELLGUARD-10 primary engine: discrete-tick battery charge/thermal
controller simulation. Every tick's state is computed from the PREVIOUS
tick's state (SoC, temperature, mode, fault-latch/counter, voltage) --
genuine state-threading, not independent per-item facts.

Mutant hooks (S08 score-topology audit) in MUTANT dict below.
"""
import hashlib

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

N_TICKS = 320

MUTANT = {
    "no_derate": False,              # mutant 1: never apply thermal derating
    "fault_release_no_hysteresis": False,  # mutant 2: release fault the instant temp<=LOW (no counter)
    "cv_no_decay": False,                  # mutant 3: CV current never tapers down, so TAPER mode is never reached
    "no_overcurrent_clamp": False,         # mutant 4: skip the final clamp to OVERCURRENT_MAX
    "taper_uses_full_heat": False,         # mutant 5: TAPER mode uses HEAT_FULL, not HEAT_TAPER
}


def run():
    soc = 0.0
    temp = AMBIENT
    mode = "CC"
    cv_current = None
    fault_latched = False
    cool_counter = 0
    voltage_prev = BASE_VOLTAGE
    voltage_cur = BASE_VOLTAGE

    rows = []
    for t in range(1, N_TICKS + 1):
        if mode == "CC" and voltage_prev >= CV_VOLTAGE_THRESHOLD:
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
            actual_current = 0.0
        elif temp >= DERATE_TEMP and not MUTANT["no_derate"]:
            actual_current = mode_current * DERATE_FACTOR
        else:
            actual_current = mode_current

        if not MUTANT["no_overcurrent_clamp"]:
            actual_current = min(actual_current, OVERCURRENT_MAX)

        soc = min(100.0, soc + actual_current / CAPACITY * 100.0)

        if actual_current <= 0:
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

        voltage_cur = BASE_VOLTAGE + soc * VOLT_PER_SOC_PCT - actual_current * IR_DROP_PER_UNIT
        voltage_prev = voltage_cur

        rows.append({
            "t": t, "mode": mode, "soc": round(soc, 2), "temp": temp,
            "current": round(actual_current, 2), "voltage": round(voltage_cur, 2),
            "fault": fault_latched,
            "cv_reg_current": round(cv_current, 2) if cv_current is not None else None,
            "fault_counter": cool_counter,
        })
    return rows


def serialize(rows):
    # soc/current/voltage are fixed-width 2-decimal-place strings (e.g. "25.00",
    # never "25" or "25.0") -- found genuinely ambiguous by the Phase 8.5 blind
    # pilot (a bare round(x,2) str() conversion drops trailing zeros); fixed
    # here and the ambiguity closed explicitly in the semantic contract.
    lines = ["CELLGUARD10-CERT-V1"]
    for r in rows:
        lines.append(
            f"t={r['t']};mode={r['mode']};soc={r['soc']:.2f};temp={r['temp']};"
            f"current={r['current']:.2f};voltage={r['voltage']:.2f};fault={r['fault']}"
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
            print(f"  t={r['t']} MODE->{r['mode']} soc={r['soc']} temp={r['temp']}")
            prev_mode = r["mode"]
    prev_fault = False
    for r in rows:
        if r["fault"] != prev_fault:
            print(f"  t={r['t']} FAULT->{r['fault']} temp={r['temp']}")
            prev_fault = r["fault"]
    print("final:", rows[-1])
    print("HASH:", certificate_hash(text))
