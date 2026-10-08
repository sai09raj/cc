"""TASK 13 reference: replay of the two L1 relays (A and B) from sampled secondary waveforms.

Semantics follow the relay manual excerpt in the bundle (manual.pdf):
- 32 samples per cycle; phasor at sample k from the most recent 32 samples (full-cycle DFT, fixed reference):
  X(k) = (sqrt(2)/32) * sum_{n=0..31} x[k-n] * exp(-j*2*pi*(k-n)/32); defined for k >= 31.
- Phase loops AB, BC, CA: V = Vx - Vy, I = Ix - Iy. A loop element is evaluated only when |I| >= 0.5 A.
- Forward mho of reach R at angle T: operates when |Z - (R/2)<T| <= R/2, Z = V / I.
- Reverse mho (Z3R): operates when |Z + (R/2)<T| <= R/2.
- An element is asserted when any of the three loops operates.
- Channel: a KEY asserted at sample k is received (RX) at the other end at sample k + 12.
- Echo (relay B): if RX is asserted and none of Z1, Z2, Z3R is asserted, and Z3R has not been asserted in the
  previous 64 samples, for 32 consecutive samples, ECHO asserts on that 32nd sample and stays asserted for 64 samples.
- KEY = Z2 or ECHO.  TRIP = Z1 or (Z2 and RX); TRIP latches.
"""
import cmath, math

N = 32


def phasors(x):
    """Full-cycle DFT phasor for every sample (None before sample 31)."""
    out = [None] * len(x)
    w = [cmath.exp(-2j * math.pi * k / N) for k in range(N)]
    for k in range(N - 1, len(x)):
        s = 0j
        for n in range(N):
            s += x[k - n] * w[(k - n) % N]
        out[k] = s * math.sqrt(2) / N
    return out


def mho(z, reach, ang, reverse=False):
    c = cmath.rect(reach / 2, math.radians(ang))
    return abs(z + c) <= reach / 2 if reverse else abs(z - c) <= reach / 2


LOOPS = (("AB", 0, 1), ("BC", 1, 2), ("CA", 2, 0))


def element_states(V, I, k, s):
    """V, I: lists of 3 phasor series. Returns dict element -> bool at sample k, plus loop impedances."""
    st = {"Z1": False, "Z2": False, "Z3R": False}
    zs = {}
    if V[0][k] is None:
        return st, zs
    for name, x, y in LOOPS:
        il = I[x][k] - I[y][k]
        vl = V[x][k] - V[y][k]
        if abs(il) < 0.5:
            continue
        z = vl / il
        zs[name] = z
        if mho(z, s["Z1"], s["ANG"]):
            st["Z1"] = True
        if mho(z, s["Z2"], s["ANG"]):
            st["Z2"] = True
        if s.get("Z3R") and mho(z, s["Z3R"], s["ANG"], reverse=True):
            st["Z3R"] = True
    return st, zs


def replay(recA, recB, setA, setB, chan=12, edpu=32, edur=64, eblk=64):
    """recX: dict with 'V' and 'I' as lists of 3 sample lists (secondary). Returns per-sample digital dicts."""
    n = len(recA["V"][0])
    PA = {"V": [phasors(c) for c in recA["V"]], "I": [phasors(c) for c in recA["I"]]}
    PB = {"V": [phasors(c) for c in recB["V"]], "I": [phasors(c) for c in recB["I"]]}
    keyA = [0] * n; keyB = [0] * n
    dA = []; dB = []
    tripA = tripB = 0
    echo_left = 0; cnt = 0; last_z3 = -10 ** 9
    for k in range(n):
        sA, zA = element_states(PA["V"], PA["I"], k, setA)
        sB, zB = element_states(PB["V"], PB["I"], k, setB)
        rxA = keyB[k - chan] if k >= chan else 0
        rxB = keyA[k - chan] if k >= chan else 0
        # relay A
        keyA[k] = 1 if sA["Z2"] else 0
        if sA["Z1"] or (sA["Z2"] and rxA):
            tripA = 1
        # relay B echo logic
        if sB["Z3R"]:
            last_z3 = k
        echo_now = 0
        if echo_left > 0:
            echo_left -= 1
            echo_now = 1
        else:
            cond = rxB and not (sB["Z1"] or sB["Z2"] or sB["Z3R"]) and (k - last_z3) > eblk
            cnt = cnt + 1 if cond else 0
            if cnt >= edpu:
                echo_now = 1
                echo_left = edur - 1
                cnt = 0
        keyB[k] = 1 if (sB["Z2"] or echo_now) else 0
        if sB["Z1"] or (sB["Z2"] and rxB):
            tripB = 1
        dA.append(dict(Z1=int(sA["Z1"]), Z2=int(sA["Z2"]), KEY=keyA[k], RX=rxA, TRIP=tripA, Z=zA))
        dB.append(dict(Z1=int(sB["Z1"]), Z2=int(sB["Z2"]), Z3R=int(sB["Z3R"]), RX=rxB, ECHO=echo_now,
                       KEY=keyB[k], TRIP=tripB, Z=zB))
    return dA, dB, PA, PB
