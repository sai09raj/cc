"""WD-22: Fenwick Hill water supply zone, 24 h extended-period simulation. Single source of truth."""
# pipe section types (code on the plan): (description, internal diameter mm, Hazen-Williams C)
PIPE = {"DI300": ("ductile iron 300", 300.0, 130.0), "DI250": ("ductile iron 250", 250.0, 125.0), "DI200": ("ductile iron 200", 200.0, 120.0),
        "CI200": ("cast iron 200 (old, tuberculated)", 200.0, 90.0), "PVC150": ("PVC 150", 150.0, 140.0)}
H_RES = 40.0                      # reservoir water level (m)
PUMP = (68.0, 0.0042)             # each pump: head gain H = a - b q^2 (m, q in L/s per pump); identical pumps in parallel
ETA = 0.72                        # pump set efficiency (wire to water)
TANK = dict(node="T", base=96.0, diameter=12.0, init=3.20, max=6.0)
PRV = dict(up="J6", down="J10", setting=72.0)   # PRV holds the downstream head at 72.0 m when active
P_MIN = 20.0                      # minimum service pressure (m)
RESERVE = 1.00                    # tank reserve level (m)
DT_MIN = 15                       # hydraulic time step (min)
TARIFF = [0.08] * 7 + [0.21] * 16 + [0.08]    # cost per kWh by hour (night 00-07 and 23-24 cheap)
# demand pattern multipliers by hour (shown only as a bar chart on sheet 3)
PATTERN = [0.55, 0.50, 0.45, 0.45, 0.50, 0.65, 1.05, 1.55, 1.60, 1.35, 1.20, 1.15,
           1.20, 1.15, 1.05, 1.00, 1.05, 1.25, 1.45, 1.40, 1.20, 0.95, 0.75, 0.60]
# junctions: elevation (m), base demand (L/s)
NODE = {"J1": (34.0, 0.0), "J2": (41.0, 5.8), "J3": (46.0, 7.0), "J4": (44.0, 4.7), "J5": (49.0, 6.6), "J6": (52.0, 3.9),
        "J7": (55.0, 5.4), "J8": (77.0, 3.1), "J9": (47.0, 5.0), "J10": (30.0, 0.0), "J11": (24.0, 7.4), "J12": (21.0, 6.2)}
# pipes: (id, from, to, [(type, length m), ...]) in drawing order
PIPES = [
    ("A1", "J1", "J2", [("DI300", 420), ("DI300", 380)]),
    ("A2", "J2", "J3", [("DI250", 450), ("DI200", 360)]),
    ("A3", "J3", "J4", [("DI200", 400), ("DI200", 310)]),
    ("B1", "J1", "J5", [("DI250", 520), ("DI250", 410)]),
    ("B2", "J5", "J6", [("DI200", 380), ("CI200", 460)]),
    ("B3", "J2", "J5", [("DI200", 340), ("DI200", 490)]),
    ("C1", "J3", "J7", [("DI200", 460), ("DI200", 390)]),
    ("C2", "J7", "J8", [("DI250", 390), ("DI250", 300)]),
    ("C3", "J6", "J7", [("CI200", 350), ("DI200", 520)]),
    ("D1", "J4", "J9", [("PVC150", 450), ("DI200", 380)]),
    ("D2", "J9", "J6", [("DI200", 300), ("PVC150", 390)]),
    ("TK", "J8", "T", [("DI250", 260), ("DI300", 340)]),
    ("L1", "J10", "J11", [("DI200", 480), ("DI200", 370)]),
    ("L2", "J11", "J12", [("PVC150", 420), ("PVC150", 330)]),
]
# controls: pump on when tank level <= on, off when >= off (evaluated at the start of each step)
CTRL = {"P-1": (2.40, 4.20), "P-2": (1.90, 3.00)}
INIT_PUMPS = {"P-1": True, "P-2": False}
SETPOINTS = [2.00, 2.20, 2.40, 2.60, 2.80]     # candidate P-1 start levels for the decision
