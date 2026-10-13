"""MV-20: Bramhall Colliery underground ventilation network. Single source of truth for solver, drawing and data sheet."""
RHO = 1.20                 # kg/m^3 air density (taken constant)
CC = 0.65                  # regulator contraction coefficient
# roadway profiles: (description, area m^2, perimeter m, Atkinson friction factor k kg/m^3)
PROF = {"P1": ("arched main, steel arches, 5.2 m span", 16.0, 15.2, 0.0090),
        "P2": ("rectangular, roof bolted, 4.8 x 3.0 m", 14.4, 15.6, 0.0110),
        "P3": ("rectangular, roof bolted, 4.4 x 2.6 m", 11.4, 14.0, 0.0130),
        "P4": ("panel gate, yielding arches, 3.8 x 2.5 m", 9.5, 12.6, 0.0170),
        "P5": ("return, rectangular, 4.6 x 2.6 m", 12.0, 14.4, 0.0150)}
R_DS, R_US = 0.0042, 0.0048            # shaft resistances N s^2/m^8 (downcast, upcast incl. fan drift)
# fan curves: fan static pressure p = a - b1 Q - b2 Q^2 (Pa, Q in m^3/s)
FAN = {"main 0": (3300.0, 2.0, 0.044), "main +5": (3550.0, 2.0, 0.042), "main -5": (3050.0, 2.0, 0.047),
       "standby": (3050.0, 1.2, 0.049)}
# routes: (id, from node, to node, [(profile, length m), ...]) in drawing order
ROUTES = [
    ("I1", "PB", "J1", [("P1", 620), ("P1", 480)]),
    ("I2", "J1", "J2", [("P1", 540), ("P2", 380)]),
    ("I3", "J2", "J3", [("P2", 450), ("P2", 330)]),
    ("I4", "J3", "J10", [("P2", 520), ("P3", 410)]),
    ("W1", "J1", "J7", [("P2", 300), ("P3", 380)]),
    ("W2", "J7", "J4", [("P4", 260), ("P5", 420)]),
    ("C1", "J2", "J8", [("P2", 360), ("P3", 290)]),
    ("C2", "J8", "J5", [("P4", 310), ("P5", 350)]),
    ("E1", "J3", "J9", [("P3", 330), ("P4", 280)]),
    ("E2", "J9", "J6", [("P4", 240), ("P5", 390)]),
    ("X1", "J7", "J8", [("P3", 470), ("P3", 310)]),
    ("X2", "J8", "J9", [("P4", 300), ("P4", 360)]),
    ("T1", "J10", "UB", [("P3", 520), ("P5", 470)]),
    ("R1", "J4", "J5", [("P5", 540), ("P5", 300)]),
    ("R2", "J5", "J6", [("P5", 440), ("P1", 460)]),
    ("R3", "J6", "UB", [("P1", 520), ("P1", 380)]),
]
REG = {"W2": "REG-W", "C2": "REG-C", "E2": "REG-E", "T1": "REG-T"}    # regulator in route
REG_AREA = {"REG-W": 2.4, "REG-C": 1.8, "REG-E": 2.8, "REG-T": 1.5}  # normal openings m^2
R_BRATTICE = 3.5           # temporary brattice in place of a stopping, N s^2/m^8 (in series with the crosscut)
FACE = {"W": "W2", "C": "C2", "E": "E2"}   # panel face airflow = flow in this route
FACE_MIN = 30.0            # m^3/s required at every working face
