"""TASK 13: build the recorded case (quantized secondary samples) and replay both relays on it."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import waves, relay  # noqa: E402

SET_A = dict(Z1=3.71, Z2=5.79, ANG=84.0, Z3R=None)
SET_B = dict(Z1=3.71, Z2=5.79, ANG=84.0, Z3R=1.74)
QV, QI = 0.01, 0.001          # COMTRADE multipliers (V and A per count)


def quant(sec):
    q = {}
    for end in sec:
        q[end] = {"V": [[round(v / QV) for v in ch] for ch in sec[end]["V"]],
                  "I": [[round(i / QI) for i in ch] for ch in sec[end]["I"]]}
    return q


def deq(q):
    return {end: {"V": [[c * QV for c in ch] for ch in q[end]["V"]],
                  "I": [[c * QI for c in ch] for ch in q[end]["I"]]} for end in q}


def first(d, key):
    for k, x in enumerate(d):
        if x[key]:
            return k
    return None


def build():
    trip = None
    for _ in range(4):
        prim = waves.synth(trip)
        q = quant(waves.to_secondary(prim, seed=1313))
        rec = deq(q)
        dA, dB, PA, PB = relay.replay(rec["A"], rec["B"], SET_A, SET_B)
        t = first(dA, "TRIP")
        if t == trip:
            break
        trip = t
    return q, rec, dA, dB, PA, PB, trip


if __name__ == "__main__":
    q, rec, dA, dB, PA, PB, trip = build()
    for key in ("Z1", "Z2", "KEY", "RX", "TRIP"):
        print("A", key, first(dA, key))
    for key in ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP"):
        print("B", key, first(dB, key))
    print("max |I| counts A", max(abs(c) for ch in q["A"]["I"] for c in ch), "B", max(abs(c) for ch in q["B"]["I"] for c in ch))
    k = waves.K_FAULT + 40
    print("A BC Z at", k, dA[k]["Z"].get("BC"), " B BC Z", dB[k]["Z"].get("BC"))
    # B's reverse loop impedance over the fault and Z3R margin
    import cmath, math
    c = cmath.rect(SET_B["Z3R"] / 2, math.radians(84))
    for k in range(waves.K_FAULT, waves.K_FAULT + 140, 10):
        z = dB[k]["Z"].get("BC")
        za = dA[k]["Z"].get("BC")
        print(k, "B BC", None if z is None else f"{z.real:.3f}{z.imag:+.3f}j margin {abs(z + c) - SET_B['Z3R']/2:+.3f}",
              "| A BC", None if za is None else f"{za.real:.3f}{za.imag:+.3f}j", dA[k]["Z2"], dB[k]["ECHO"], dA[k]["TRIP"])
