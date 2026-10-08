"""TASK 13: synthesize the secondary waveforms recorded by the L1 relays at A and B.

Network states (from proto/net.py): prefault -> BC fault on L2 -> L2 cleared at both ends -> L1 opened at A.
The L1 CT at A is 1200:5 (ratio 240). The L1 CT at B is in service at 2000:5 (ratio 400), although relay B's
settings assume 1200:5 (240). Both VTs are 2000:1 (230 kV / 115 V).
"""
import cmath, math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "proto"))
from net import solve, VPH  # noqa: E402

F = 60.0
N = 32
FS = F * N
NS = 640
K_FAULT = 320
K_L2_CLEAR_DELAY = 140          # L2 opens at both ends 140 samples after inception (independent of L1 relays)
BKR_A = 96                      # breaker A opens 96 samples after relay A trips
TAU = 0.025                     # s, DC offset time constant
CTR_A, CTR_B_ACTUAL, CTR_B_SET, PTR = 240.0, 400.0, 240.0, 2000.0
THETA0 = math.radians(96.0)     # phase of the system reference at sample 0

ZS = dict(A=complex(1.2, 12.0), B=complex(4.0, 45.0), C=complex(2.0, 22.0))
EMF = dict(A=cmath.rect(1.03 * VPH, math.radians(8)), B=cmath.rect(1.0 * VPH, 0.0), C=cmath.rect(0.99 * VPH, math.radians(-6)))
M_FAULT, RF = 0.13, 3.0


def states():
    pre = solve(ZS, EMF, M_FAULT, RF, fault=False)
    flt = solve(ZS, EMF, M_FAULT, RF)
    l2o = solve(ZS, EMF, M_FAULT, RF, l2_closed=False, fault=False)
    l1o = solve(ZS, EMF, M_FAULT, RF, l2_closed=False, l1_closed=False, fault=False)
    return pre, flt, l2o, l1o


def inst(ph, k):
    t = k / FS
    return math.sqrt(2) * (ph * cmath.exp(1j * (2 * math.pi * F * t + THETA0))).real


def synth(k_tripA):
    """Return primary instantaneous VA,VB,VC,IA.. for relays A and B (lists of 3 lists), given A's trip sample."""
    pre, flt, l2o, l1o = states()
    k_l2 = K_FAULT + K_L2_CLEAR_DELAY
    k_open = k_tripA + BKR_A if k_tripA is not None else NS + 1
    bounds = sorted([(K_FAULT, flt), (k_l2, l2o), (k_open, l1o)], key=lambda x: x[0])

    def state_at(k):
        s = pre
        for kb, st in bounds:
            if k >= kb:
                s = st
        return s

    out = {}
    for end, vkey, ikey in (("A", "VA", "IA"), ("B", "VB", "IB")):
        V = [[0.0] * NS for _ in range(3)]
        I = [[0.0] * NS for _ in range(3)]
        dc = [0.0, 0.0, 0.0]; kdc = 0
        prev = pre
        for k in range(NS):
            s = state_at(k)
            if s is not prev:
                for p in range(3):  # current continuity through a decaying DC term
                    old = inst(prev[ikey][p], k) + dc[p] * math.exp(-(k - kdc) / FS / TAU)
                    new = inst(s[ikey][p], k)
                    dc[p] = 0.0 if abs(s[ikey][p]) < 1e-9 else old - new
                kdc = k
                prev = s
            for p in range(3):
                V[p][k] = inst(s[vkey][p], k)
                I[p][k] = inst(s[ikey][p], k) + dc[p] * math.exp(-(k - kdc) / FS / TAU)
        out[end] = {"V": V, "I": I}
    return out


def to_secondary(prim, seed):
    rnd = random.Random(seed)
    A = prim["A"]; B = prim["B"]
    sec = {}
    for end, rec, ctr in (("A", A, CTR_A), ("B", B, CTR_B_ACTUAL)):
        V = [[v / PTR + rnd.gauss(0, 0.03) for v in ch] for ch in rec["V"]]
        I = [[i / ctr + rnd.gauss(0, 0.002) for i in ch] for ch in rec["I"]]
        sec[end] = {"V": V, "I": I}
    return sec
