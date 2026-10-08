"""TASK 13 answer key, computed from the exact recorded (quantized) samples in the bundle."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import waves, relay, build_case as bc  # noqa: E402

q, rec, dA, dB, PA, PB, trip = bc.build()
first = lambda d, key: next((k for k, x in enumerate(d) if x[key]), None)
K = 400
zA = dA[K]["Z"]["BC"]; zB = dB[K]["Z"]["BC"]
ibB = PB["I"][1][K]
key = {
    "fault_type": "BC (phase-to-phase, no ground)", "fault_start_sample": waves.K_FAULT,
    "A_first": {e: first(dA, e) for e in ("Z1", "Z2", "KEY", "RX", "TRIP")},
    "B_first": {e: first(dB, e) for e in ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP")},
    "A_open_sample": trip + waves.BKR_A,
    "zA_sec": [round(zA.real, 3), round(zA.imag, 3)], "zA_pri": [round(zA.real * 2000 / 240, 2), round(zA.imag * 2000 / 240, 2)],
    "zB_sec": [round(zB.real, 3), round(zB.imag, 3)],
    "zB_pri_true_2000_5": [round(zB.real * 5, 2), round(zB.imag * 5, 2)],
    "zB_pri_if_1200_5": [round(zB.real * 2000 / 240, 2), round(zB.imag * 2000 / 240, 2)],
    "IB_at_B_sec": round(abs(ibB), 3), "IB_at_B_pri_true": round(abs(ibB) * 400), "IB_at_B_pri_if_1200_5": round(abs(ibB) * 240),
    "IB_at_A_pri": round(abs(PA["I"][1][K]) * 240),
}
# prefault current comparison (phase A, sample 300)
key["prefault_IA_A_pri"] = round(abs(PA["I"][0][300]) * 240, 1)
key["prefault_IA_B_sec"] = round(abs(PB["I"][0][300]), 4)
key["prefault_IA_B_pri_true"] = round(abs(PB["I"][0][300]) * 400, 1)
# counterfactual: B's currents as a 1200:5 core would have delivered them (x 400/240)
recB2 = {"V": rec["B"]["V"], "I": [[x * 400 / 240 for x in ch] for ch in rec["B"]["I"]]}
dA2, dB2, _, _ = relay.replay(rec["A"], recB2, bc.SET_A, bc.SET_B)
key["counterfactual_1200_5"] = {"B_Z3R_first": first(dB2, "Z3R"), "B_ECHO_first": first(dB2, "ECHO"),
                                "A_TRIP_first": first(dA2, "TRIP"), "A_Z2_first": first(dA2, "Z2")}
key["corrective_settings_if_core_stays_2000_5"] = {"CTR": 400, "Z1P": round(3.71 * 400 / 240, 2), "Z2P": round(5.79 * 400 / 240, 2),
                                                    "Z3P": round(1.74 * 400 / 240, 2), "50PP": round(0.5 * 240 / 400, 2)}
key["B_Z3R_actual_primary_reach"] = round(1.74 * 2000 / 400, 2)
json.dump(key, open(os.path.join(HERE, "out", "answer_key.json"), "w"), indent=1)
print(json.dumps(key, indent=1))
