"""TASK 13 v2 network: three-terminal line L1 (A - tee T - B, tap T - W wind farm), line L2 (B - C).

Buses: A, T, W, B, F (fault point on L2), C.  Sources behind A, W, B, C.
Positive = negative sequence impedances; no charging, no mutual coupling. BC fault at F through Rf.
"""
import cmath, math
import numpy as np

a = cmath.exp(2j * math.pi / 3)
KM = complex(0.05, 0.48)
VPH = 230e3 / math.sqrt(3)
LEN = dict(AT=35.0, TB=45.0, TW=8.0, L2=50.0)
BUS = ["A", "T", "W", "B", "F", "C"]
IDX = {b: i for i, b in enumerate(BUS)}


def branches(m, open_set=()):
    br = [("A", "T", KM * LEN["AT"], "L1_AT"), ("T", "B", KM * LEN["TB"], "L1_TB"), ("T", "W", KM * LEN["TW"], "L1_TW"),
          ("B", "F", KM * LEN["L2"] * m, "L2_BF"), ("F", "C", KM * LEN["L2"] * (1 - m), "L2_FC")]
    return [b for b in br if b[3] not in open_set]


def solve(zs, emf, m, rf, open_set=(), fault=True):
    n = len(BUS)
    Y = np.zeros((n, n), complex)
    br = branches(m, open_set)
    for i, j, z, _ in br:
        y = 1 / z; I, J = IDX[i], IDX[j]
        Y[I, I] += y; Y[J, J] += y; Y[I, J] -= y; Y[J, I] -= y
    inj = np.zeros(n, complex)
    for s in zs:
        Y[IDX[s], IDX[s]] += 1 / zs[s]; inj[IDX[s]] = emf[s] / zs[s]
    for k in range(n):
        if abs(Y[k, k]) < 1e-12:
            Y[k, k] = 1e-9
    V1pre = np.linalg.solve(Y, inj)
    f = IDX["F"]
    if fault and "L2_BF" not in open_set:
        Z = np.linalg.inv(Y)
        I1 = V1pre[f] / (2 * Z[f, f] + rf)
        V1 = V1pre - Z[:, f] * I1
        V2 = Z[:, f] * I1          # I2 = -I1 injected: V2 = -Z[:,f]*I2
    else:
        V1, V2 = V1pre, np.zeros(n, complex)

    def cur(i, j, name):
        for bi, bj, z, nm in br:
            if nm == name:
                s = 1 if (bi, bj) == (i, j) else -1
                return s * (V1[IDX[bi]] - V1[IDX[bj]]) / z, s * (V2[IDX[bi]] - V2[IDX[bj]]) / z
        return 0j, 0j

    def ph(x1, x2):
        return np.array([x1 + x2, a * a * x1 + a * x2, a * x1 + a * a * x2])
    out = {}
    # relay measuring points: (name, bus for voltage, current from bus into branch)
    for nm, bus, frm, to, brn in (("A", "A", "A", "T", "L1_AT"), ("B", "B", "B", "T", "L1_TB"), ("W", "W", "W", "T", "L1_TW"),
                                  ("L2B", "B", "B", "F", "L2_BF"), ("L2C", "C", "C", "F", "L2_FC")):
        i1, i2 = cur(frm, to, brn)
        out[nm] = dict(V=ph(V1[IDX[bus]], V2[IDX[bus]]), I=ph(i1, i2))
    return out


def loopZ(r):
    return (r["V"][1] - r["V"][2]) / (r["I"][1] - r["I"][2])


def mho_margin(z, D, ang=84.0, rev=False):
    c = cmath.rect(D / 2, math.radians(ang))
    return D / 2 - (abs(z + c) if rev else abs(z - c))
