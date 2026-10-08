"""TASK 13 v2 network: A --L1-- B --L2(F)-- C, sources behind A, B, C; BC fault at F on L2 through Rf.

Positive = negative sequence impedances; no charging, no mutual coupling. Branches can be opened per end of L2
(opening the B end removes branch B-F, opening the C end removes F-C).
Measurement points (current from the named bus into the named branch):
  A   : bus A, L1 at A  (A -> B)       B   : bus B, L1 at B (B -> A)
  L2B : bus B, L2 at B  (B -> F)       L2C : bus C, L2 at C (C -> F)
"""
import cmath, math
import numpy as np

a = cmath.exp(2j * math.pi / 3)
KM = complex(0.05, 0.48)
VPH = 230e3 / math.sqrt(3)
BUS = ["A", "B", "F", "C"]
IDX = {b: i for i, b in enumerate(BUS)}
ZS = dict(A=complex(1.2, 12.0), B=complex(4.0, 45.0), C=complex(2.0, 22.0))
EMF = dict(A=cmath.rect(1.03 * VPH, math.radians(8)), B=cmath.rect(1.0 * VPH, 0.0), C=cmath.rect(0.99 * VPH, math.radians(-6)))


def solve(m, rf, open_set=(), fault=True):
    br = [("A", "B", KM * 80.0, "L1"), ("B", "F", KM * 50.0 * m, "L2B"), ("F", "C", KM * 50.0 * (1 - m), "L2C")]
    br = [b for b in br if b[3] not in open_set]
    n = len(BUS)
    Y = np.zeros((n, n), complex); inj = np.zeros(n, complex)
    for i, j, z, _ in br:
        y = 1 / z; I, J = IDX[i], IDX[j]
        Y[I, I] += y; Y[J, J] += y; Y[I, J] -= y; Y[J, I] -= y
    for s in ZS:
        Y[IDX[s], IDX[s]] += 1 / ZS[s]; inj[IDX[s]] = EMF[s] / ZS[s]
    for k in range(n):
        if abs(Y[k, k]) < 1e-12:
            Y[k, k] = 1e-9
    V1 = np.linalg.solve(Y, inj); V2 = np.zeros(n, complex)
    f = IDX["F"]
    fault_on = fault and ("L2B" not in open_set or "L2C" not in open_set)
    if fault_on:
        Z = np.linalg.inv(Y)
        I1 = V1[f] / (2 * Z[f, f] + rf)
        V1 = V1 - Z[:, f] * I1
        V2 = Z[:, f] * I1

    def cur(frm, name):
        for i, j, z, nm in br:
            if nm == name:
                s = 1 if i == frm else -1
                return s * (V1[IDX[i]] - V1[IDX[j]]) / z, s * (V2[IDX[i]] - V2[IDX[j]]) / z
        return 0j, 0j

    def ph(x1, x2):
        return np.array([x1 + x2, a * a * x1 + a * x2, a * x1 + a * a * x2])
    out = {}
    for nm, bus, brn in (("A", "A", "L1"), ("B", "B", "L1"), ("L2B", "B", "L2B"), ("L2C", "C", "L2C")):
        i1, i2 = cur(bus, brn)
        out[nm] = dict(V=ph(V1[IDX[bus]], V2[IDX[bus]]), I=ph(i1, i2))
    return out
