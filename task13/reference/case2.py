"""TASK 13 v2: synthesize all records, replay every relay, iterate breaker timing to a consistent sequence.

Records shipped: relay A (L1 at A), relay L2B (L2 at B), relay L2C (L2 at C). Relay B (L1 at B) is synthesized and
replayed for the answer key, but its oscillography is NOT shipped (only its SER).
CTs: A 1200:5 (240); B L1 core 1 in service 2000:5 (400) while relay B is set CTR 240; L2B and L2C 1200:5 (240).
VTs: 2000:1 everywhere. Relays L1-21 B and L2-21 B use the same bus B VT.
"""
import cmath, math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "proto"))
import grid, relay  # noqa: E402

F, N = 60.0, 32
FS = F * N
NS = 640
K_FAULT = 320
BKR = 96
TAU = 0.025
THETA0 = math.radians(96.0)
M_FAULT, RF = 0.13, 3.0
PTR = 2000.0
CTR = dict(A=240.0, B=400.0, L2B=240.0, L2C=240.0)
QV, QI = 0.01, 0.001
SET_A = dict(Z1=3.71, Z2=5.79, ANG=84.0, Z3R=None)
SET_B = dict(Z1=3.71, Z2=5.79, ANG=84.0, Z3R=1.74)
SET_L2 = dict(Z1=2.32, Z2=3.62, ANG=84.0, Z3R=None)


def inst(ph, k):
    return math.sqrt(2) * (ph * cmath.exp(1j * (2 * math.pi * F * k / FS + THETA0))).real


def synth(opens, ctr_b=None):
    """opens: dict branch -> sample at which it opens ('L1' at A end, 'L2B', 'L2C')."""
    ctr = dict(CTR); ctr["B"] = ctr_b or CTR["B"]
    events = sorted(set([K_FAULT] + [k for k in opens.values() if k is not None]))
    cache = {}

    def state(k):
        key = (k >= K_FAULT,) + tuple(sorted(b for b, kb in opens.items() if kb is not None and k >= kb))
        if key not in cache:
            open_set = set(key[1:])
            if "L1" in open_set:
                open_set = open_set | {"L1"}
            cache[key] = grid.solve(M_FAULT, RF, open_set=open_set, fault=key[0])
        return cache[key], key
    recs = {}
    for nm in ("A", "B", "L2B", "L2C"):
        V = [[0.0] * NS for _ in range(3)]; I = [[0.0] * NS for _ in range(3)]
        dc = [0.0] * 3; kdc = 0; prev_key = None; prev = None
        for k in range(NS):
            s, key = state(k)
            if prev_key is not None and key != prev_key:
                for p in range(3):
                    old = inst(prev[nm]["I"][p], k) + dc[p] * math.exp(-(k - kdc) / FS / TAU)
                    new = inst(s[nm]["I"][p], k)
                    dc[p] = 0.0 if abs(s[nm]["I"][p]) < 1e-6 else old - new
                kdc = k
            prev_key, prev = key, s
            for p in range(3):
                V[p][k] = inst(s[nm]["V"][p], k)
                I[p][k] = inst(s[nm]["I"][p], k) + dc[p] * math.exp(-(k - kdc) / FS / TAU)
        recs[nm] = (V, I)
    rnd = random.Random(2713)
    q = {}
    for nm in ("A", "B", "L2B", "L2C"):
        V, I = recs[nm]
        q[nm] = {"V": [[round((v / PTR + rnd.gauss(0, 0.03)) / QV) for v in ch] for ch in V],
                 "I": [[round((i / ctr[nm] + rnd.gauss(0, 0.002)) / QI) for i in ch] for ch in I]}
    return q


def deq(q):
    return {nm: {"V": [[c * QV for c in ch] for ch in q[nm]["V"]], "I": [[c * QI for c in ch] for ch in q[nm]["I"]]} for nm in q}


def first(d, key):
    return next((k for k, x in enumerate(d) if x[key]), None)


def replay_single(rec, s):
    """Non-scheme relay (L2): Z1/Z2 and TRIP = Z1 (latched)."""
    P = {"V": [relay.phasors(c) for c in rec["V"]], "I": [relay.phasors(c) for c in rec["I"]]}
    out = []; trip = 0
    for k in range(len(rec["V"][0])):
        st, zs = relay.element_states(P["V"], P["I"], k, s)
        if st["Z1"]:
            trip = 1
        out.append(dict(Z1=int(st["Z1"]), Z2=int(st["Z2"]), TRIP=trip, Z=zs))
    return out, P


def build(ctr_b=None):
    opens = {"L1": None, "L2B": None, "L2C": None}
    for _ in range(8):
        q = synth(opens, ctr_b); rec = deq(q)
        d2b, d2c, _, _ = relay.replay(rec["L2B"], rec["L2C"], SET_L2, SET_L2, echo_b=False)
        dA, dB, PA, PB = relay.replay(rec["A"], rec["B"], SET_A, SET_B)
        tA, t2b, t2c = first(dA, "TRIP"), first(d2b, "TRIP"), first(d2c, "TRIP")
        new = {"L1": None if tA is None else tA + BKR, "L2B": None if t2b is None else t2b + BKR,
               "L2C": None if t2c is None else t2c + BKR}
        if new == opens:
            break
        opens = new
    return dict(q=q, rec=rec, dA=dA, dB=dB, PA=PA, PB=PB, d2b=d2b, d2c=d2c, opens=opens)


if __name__ == "__main__":
    c = build()
    print("opens", c["opens"])
    for nm, d, keys in (("A", c["dA"], ("Z1", "Z2", "KEY", "RX", "TRIP")), ("B", c["dB"], ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP")),
                        ("L2B", c["d2b"], ("Z1", "Z2", "KEY", "RX", "TRIP")), ("L2C", c["d2c"], ("Z1", "Z2", "KEY", "RX", "TRIP"))):
        print(nm, {k: first(d, k) for k in keys})
    cf = build(ctr_b=240.0)
    print("counterfactual 1200:5 at B:", {k: first(cf["dB"], k) for k in ("Z3R", "ECHO")}, "A trip", first(cf["dA"], "TRIP"), cf["opens"])
    for k in (360, 400):
        print(k, "B BC sec", c["dB"][k]["Z"].get("BC"), "A BC", c["dA"][k]["Z"].get("BC"))
