"""TASK 13 v2 answer key. Relay B's inputs are reconstructed exactly as a solver must: bus B voltages from the
L2-21 Sub B record, L1 current at B = -(L1 current at A) (two-terminal line, no charging), scaled to relay B's
secondary by the CT ratio actually in service."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import case2 as cs, relay  # noqa: E402

c = cs.build(); rec = c["rec"]
first = cs.first


def recon(ratio_b):
    IB = [[-x * 240.0 / ratio_b for x in ch] for ch in rec["A"]["I"]]
    return {"V": rec["L2B"]["V"], "I": IB}


def replayB(ratio_b):
    dA, dB, PA, PB = relay.replay(rec["A"], recon(ratio_b), cs.SET_A, cs.SET_B)
    return dA, dB, PB


ser = {"RX": first(c["dB"], "RX"), "ECHO": first(c["dB"], "ECHO"), "Z3R": None, "Z2": None, "Z1": None}
out = {"opens": c["opens"], "A_first": {k: first(c["dA"], k) for k in ("Z1", "Z2", "KEY", "RX", "TRIP")},
       "B_SER_first": ser, "L2B_first": {k: first(c["d2b"], k) for k in ("Z1", "Z2", "KEY", "RX", "TRIP")},
       "L2C_first": {k: first(c["d2c"], k) for k in ("Z1", "Z2", "KEY", "RX", "TRIP")}}
dA, dB, PB = replayB(240.0)
out["B_recon_at_240"] = {k: first(dB, k) for k in ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY")}
out["A_with_B_recon_240_trip"] = first(dA, "TRIP")
dA, dB, PB = replayB(400.0)
out["B_recon_at_400"] = {k: first(dB, k) for k in ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY")}
out["A_with_B_recon_400_trip"] = first(dA, "TRIP")
z = dB[400]["Z"]["BC"]; out["B_recon400_BC_sec_k400"] = [round(z.real, 3), round(z.imag, 3)]
dA0, dB0, PB0 = replayB(240.0); z0 = dB0[400]["Z"]["BC"]; out["B_recon240_BC_sec_k400"] = [round(z0.real, 3), round(z0.imag, 3)]
# which in-service ratios reproduce the SER (no Z1/Z2/Z3R, RX and ECHO times)?
ok = []
for r in range(240, 801, 5):
    _, d, _ = replayB(float(r))
    got = {k: first(d, k) for k in ("Z1", "Z2", "Z3R", "RX", "ECHO")}
    ok.append((r, got == ser))
lo = min(r for r, g in ok if g); out["ratios_reproducing_SER"] = [lo, max(r for r, g in ok if g)]
out["ratio_scan_all_ok_from_lo"] = all(g for r, g in ok if r >= lo)
zA = c["dA"][400]["Z"]["BC"]; out["A_BC_sec_k400"] = [round(zA.real, 3), round(zA.imag, 3)]
out["IB_L1_at_B_pri_k400"] = round(abs(c["PA"]["I"][1][400]) * 240)
out["corrective_if_core_stays_2000_5"] = {"CTR": 400, "Z1P": 6.18, "Z2P": 9.65, "Z3P": 2.9, "50PP": 0.3}
json.dump(out, open(os.path.join(HERE, "out", "answer_key2.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
