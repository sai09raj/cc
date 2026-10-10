"""ISO-16 v4 draft: pumped cooling-water system with break tank, gravity consumers and outfall. SI units (m, m3/s)."""
import math
RHO, NU, G, PATM, PV, EPS = 998.2, 1.004e-6, 9.81, 101325.0, 2339.0, 0.045e-3
HV = (PV - PATM) / (RHO * G)            # gauge head at vapour pressure (m)
SUMP = 0.0
PUMPS = {"P-101A": (46.0, 2600.0), "P-101B": (44.0, 2300.0), "P-101C": (40.0, 2900.0)}   # H = H0 - k Q^2 (m, m3/s)
K_PUMP_DISCH = 4.0                       # check valve + discharge fittings, on DN150 velocity, per pump
D = {"DN200": 0.2027, "DN150": 0.1541, "DN100": 0.1023, "DN80": 0.0779}
# line: (dia, length m, K total excluding control valve and exchanger)
LINES = {
    "L1": ("DN200", 85.0, 3.2),     # pump header -> distribution node N2 (EL 4)
    "C1": ("DN100", 40.0, 2.4),     # N2 -> E-101 -> drain EL 6 (K incl. exit 1.0)
    "C2": ("DN100", 35.0, 2.1),     # N2 -> E-102 -> drain EL 5
    "R":  ("DN150", 60.0, 2.6),     # N2 -> riser -> TK-1 inlet, free discharge at EL 28 (incl. exit)
    "G":  ("DN150", 70.0, 1.9),     # TK-1 outlet -> gravity node N4 (EL 3) (incl. entrance)
    "C3": ("DN80", 30.0, 2.2),      # N4 -> E-103 -> drain EL 2
    "C4": ("DN80", 25.0, 2.0),      # N4 -> HV-204 -> E-104 -> drain EL 7
    "O_up": ("DN100", 48.0, 1.6),   # N4 -> outfall up-leg to crest EL 21.5 (incl. crest elbow)
    "O_dn": ("DN100", 42.0, 1.3),   # crest -> pond outlet EL -4 (incl. exit)
}
KHX = {"C1": 35.0, "C2": 28.0, "C3": 40.0, "C4": 32.0}
Z = dict(N2=4.0, C1=6.0, C2=5.0, R=28.0, N4=3.0, C3=2.0, C4=7.0, crest=21.5, pond=-4.0)
WEIR_Z, WEIR_L, CW = 26.0, 0.8, 1.84     # Q = CW * L * h^1.5
FV_K = {20: 410.0, 30: 160.0, 45: 52.0, 60: 21.0, 80: 8.5, 100: 4.2}   # FV-101 K vs % open (on DN100 velocity)
FC_SETPOINT = 0.018                      # FIC-101 setpoint (m3/s) when in AUTO

def vh(Q, dn): A = math.pi * D[dn] ** 2 / 4; return (Q / A) ** 2 / (2 * G)
def fric(Q, dn, L):
    if Q <= 0: return 0.0
    d = D[dn]; v = Q / (math.pi * d * d / 4); Re = v * d / NU
    f = 0.25 / math.log10(EPS / (3.7 * d) + 5.74 / Re ** 0.9) ** 2
    return f * L / d * v * v / (2 * G)
def loss(name, Q, k_extra=0.0):
    dn, L, K = LINES[name]; return fric(Q, dn, L) + (K + k_extra) * vh(Q, dn)
