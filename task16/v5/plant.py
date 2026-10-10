"""CW-200 plant definition (geometry in mm, moves E W N S U D). Single source of truth for drawing, data sheet and solver."""
VEC = {"E": (1, 0, 0), "W": (-1, 0, 0), "N": (0, 1, 0), "S": (0, -1, 0), "U": (0, 0, 1), "D": (0, 0, -1)}
START = ("M", (0, 0, 1500))       # pump discharge manifold outlet
# (line id, DN, from node, items, to-node-or-None). Items: (dir, len[, 'GV'|'FV-xxx'|'HV-xxx'|'HX:E-xxx']) or node label.
LINES = [
    ("CW-201", 200, "M", [("U", 2500), ("E", 6000), "R1"]),
    ("CW-202", 200, "R1", [("N", 20000), "Ta", ("N", 30000), ("E", 40000), "Tb", ("E", 50000), ("S", 25000), "Tc",
                            ("S", 25000), ("W", 45000), "Td", ("W", 25000), "Te", ("W", 20000), "R1"]),
    ("CW-203", 100, "Ta", [("W", 4000, "FV-201"), ("D", 2000), ("W", 3000, "HX:E-201"), "D201"]),
    ("CW-204", 150, "Tb", [("N", 3000, "GV"), ("U", 28500), ("N", 5000), ("D", 1000), "TK1IN"]),
    ("CW-205", 100, "Tc", [("E", 5000, "GV"), ("D", 1500), ("E", 2500, "HX:E-202"), "D202"]),
    ("CW-206", 100, "Td", [("S", 3500, "FV-203"), ("D", 2500), ("S", 2000, "HX:E-203"), "D203"]),
    ("CW-207", 80, "Te", [("S", 4000, "HV-204"), ("U", 1000), ("S", 3000, "HX:E-204"), "D204"]),
    ("CW-208", 150, "TK1", [("D", 3000), ("W", 13000), ("D", 19000), ("N", 6000), "N5"]),
    ("CW-209", 80, "N5", [("E", 3000, "GV"), ("D", 1000), ("E", 2000, "HX:E-205"), "D205"]),
    ("CW-210", 80, "N5", [("N", 4000, "HV-206"), ("U", 3000), ("N", 2000, "HX:E-206"), "D206"]),
    ("CW-211", 80, "N5", [("W", 3000, "GV"), ("U", 18000), ("W", 9000), ("D", 30000), ("W", 4000), "POND"]),
]
TK1_OUTLET = (40000, 60000, 25000)   # TK-1 bottom outlet nozzle; tank open, weir crest EL +29000, free inlet above it
WEIR_CREST, WEIR_L, WEIR_C = 29.0, 0.8, 1.84
ID = {200: 0.2027, 150: 0.1541, 100: 0.1023, 80: 0.0779}
PUMPS = {"P-201A": (52.0, 1900.0), "P-201B": (50.0, 1750.0), "P-201C": (47.0, 2300.0), "P-201D": (50.0, 1800.0)}
K_PUMP = 4.0            # each pump's check valve + discharge fittings, on DN150 velocity
K = dict(ell=0.3, gv=0.15, hv_open=0.15, branch=1.0, ent=0.5, exit=1.0)
HX = {"E-201": 60.0, "E-202": 26.0, "E-203": 34.0, "E-204": 22.0, "E-205": 60.0, "E-206": 55.0}
FV_CHAR = {20: 420.0, 30: 170.0, 35: 115.0, 45: 55.0, 60: 22.0, 80: 9.0, 100: 4.5}   # K vs % open, on line velocity
RHO, NU, G, PATM, PV, EPS = 998.2, 1.004e-6, 9.81, 101325.0, 2339.0, 0.045e-3
PI_NODE = "R1"          # PI-100 on the ring at R1; auto-start of a standby pump when PI-100 < 2.0 bar g
AUTOSTART_BAR = 2.8
