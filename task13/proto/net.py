"""TASK 13 prototype: 230 kV three-bus network, BC fault on line L2, phasors seen by L1 relays at A and B.

Positive- and negative-sequence networks (equal impedances, no line charging, no mutual coupling).
Buses: A(0), B(1), C(2), F(3) = fault point on L2 at fraction m from B.
Relay A: voltage at bus A, current in L1 flowing A -> B.
Relay B: voltage at bus B, current in L1 flowing B -> A (into the line from B).
"""
import cmath, math
import numpy as np

a = cmath.exp(2j * math.pi / 3)
KM_Z1 = complex(0.05, 0.48)         # ohm/km, both lines
L1_KM, L2_KM = 80.0, 50.0
VLL = 230e3
VPH = VLL / math.sqrt(3)


def solve(zs, emf, m, rf, l2_closed=True, l1_closed=True, fault=True):
    """zs, emf: dicts for sources at A, B, C (emf in volts phase, complex). Returns dict of phase phasors."""
    zl1 = KM_Z1 * L1_KM
    zbf = KM_Z1 * L2_KM * m
    zfc = KM_Z1 * L2_KM * (1 - m)
    n = 4
    Y = np.zeros((n, n), complex)

    def add(i, j, z):
        y = 1 / z
        Y[i, i] += y; Y[j, j] += y; Y[i, j] -= y; Y[j, i] -= y

    if l1_closed:
        add(0, 1, zl1)
    if l2_closed:
        add(1, 3, zbf); add(3, 2, zfc)
    for k, bus in (("A", 0), ("B", 1), ("C", 2)):
        Y[bus, bus] += 1 / zs[k]
    if not l2_closed:
        Y[3, 3] += 1e-9  # isolated fault node
    Ysrc = np.zeros(n, complex)
    for k, bus in (("A", 0), ("B", 1), ("C", 2)):
        Ysrc[bus] = emf[k] / zs[k]
    V1pre = np.linalg.solve(Y, Ysrc)
    if fault and l2_closed:
        Z = np.linalg.inv(Y)
        zth = Z[3, 3]
        I1 = V1pre[3] / (2 * zth + rf)      # BC fault: I1 = -I2 = Vf / (Z1 + Z2 + Rf)
        I2 = -I1
        V1 = V1pre - Z[:, 3] * I1
        V2 = -Z[:, 3] * I2
    else:
        V1 = V1pre; V2 = np.zeros(n, complex)

    def branch(i, j, z, closed):
        if not closed:
            return 0j, 0j
        return (V1[i] - V1[j]) / z, (V2[i] - V2[j]) / z

    iA1, iA2 = branch(0, 1, zl1, l1_closed)          # A -> B
    iB1, iB2 = -iA1, -iA2                            # B -> A (no charging)

    def ph(x1, x2):
        return np.array([x1 + x2, a * a * x1 + a * x2, a * x1 + a * a * x2])
    return dict(VA=ph(V1[0], V2[0]), IA=ph(iA1, iA2), VB=ph(V1[1], V2[1]), IB=ph(iB1, iB2),
                V1=V1, V2=V2)


def loopZ(v, i):  # BC loop
    return (v[1] - v[2]) / (i[1] - i[2])


def in_mho(z, reach, ang_deg):
    c = cmath.rect(reach / 2, math.radians(ang_deg))
    return abs(z - c) <= reach / 2


if __name__ == "__main__":
    zs = dict(A=complex(1.2, 12.0), B=complex(4.0, 45.0), C=complex(2.0, 22.0))
    emf = dict(A=cmath.rect(1.03 * VPH, math.radians(8)), B=cmath.rect(1.0 * VPH, math.radians(0)),
               C=cmath.rect(0.99 * VPH, math.radians(-6)))
    zl1 = KM_Z1 * L1_KM
    ang = math.degrees(cmath.phase(zl1))
    z1A, z2A = 0.8 * abs(zl1), 1.2 * abs(zl1)
    for m in (0.05, 0.1, 0.15, 0.2, 0.25):
        for rf in (0.5, 2, 5):
            pre = solve(zs, emf, m, rf, fault=False)
            f = solve(zs, emf, m, rf)
            zA = loopZ(f["VA"], f["IA"])
            zBrev = -loopZ(f["VB"], f["IB"])   # reverse-looking, flipped to forward plane
            w = zA - zl1
            print(f"m={m:.2f} rf={rf:4.1f} |IA|pre={abs(pre['IA'][0]):6.0f} P_A={3*(pre['VA'][0]*pre['IA'][0].conjugate()).real/1e6:6.1f}MW "
                  f"ZA={zA.real:6.2f}{zA.imag:+7.2f}j Z1?{in_mho(zA,z1A,ang)} Z2?{in_mho(zA,z2A,ang)} "
                  f"W={w.real:5.2f}{w.imag:+6.2f}j |W|={abs(w):5.2f} Wb={zBrev.real:5.2f}{zBrev.imag:+6.2f}j |IbF|={abs(f['IA'][1]):6.0f}")
