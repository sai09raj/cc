"""DH-19: Ashgrove district heating network. Single source of truth for solver, drawings and data sheet."""
RHO, MU, CP = 965.0, 3.15e-4, 4.20          # kg/m3, Pa s, kJ/(kg K) - fixed for all water in the network
ROUGH = 0.05e-3                              # m, absolute roughness of every pipe
T_GROUND = 8.0                               # C
T_RET = 45.0                                 # C, primary return temperature leaving every substation
DP_MIN = 60.0                                # kPa, minimum differential pressure across every substation in service
# Pipe types: inner diameter (mm), supply-pipe heat loss coefficient U' (W per m length per K above ground temperature)
PIPE = {"DN200": (210.1, 0.42), "DN150": (160.3, 0.36), "DN125": (132.5, 0.33), "DN100": (107.1, 0.30), "DN80": (82.5, 0.27), "DN65": (70.3, 0.25)}
# Routes: (id, from node, to node, [(type, length m), ...]) sections in order from 'from' to 'to'; supply and return pipes are laid together, identical
ROUTES = [
    ("A1", "EC", "H1", [("DN200", 540), ("DN150", 330)]),
    ("A2", "H1", "H2", [("DN150", 420), ("DN125", 380)]),
    ("A3", "H2", "H3", [("DN125", 450), ("DN100", 260)]),
    ("A4", "H3", "H4", [("DN100", 330), ("DN80", 390)]),
    ("B1", "EC", "H5", [("DN200", 610), ("DN150", 280), ("DN150", 350)]),
    ("B2", "H5", "H6", [("DN125", 510), ("DN125", 470)]),
    ("B3", "H6", "H7", [("DN100", 380), ("DN80", 300)]),
    ("C1", "EC", "H8", [("DN150", 480), ("DN125", 520)]),
    ("C2", "H8", "H9", [("DN125", 400), ("DN100", 430)]),
    ("C3", "H9", "H10", [("DN100", 360), ("DN80", 290)]),
    ("D1", "EC", "H11", [("DN150", 700), ("DN125", 340)]),
    ("D2", "H11", "H12", [("DN100", 560), ("DN80", 250)]),
    ("L1", "H4", "H10", [("DN80", 640), ("DN100", 420)]),        # loop link, normally open-flow (valves open)
    ("L2", "H7", "H12", [("DN80", 520), ("DN80", 340)]),         # loop link, valves open
    ("X3", "H2", "H6", [("DN100", 460), ("DN100", 470)]),        # crossover, normally closed (valve XV3)
]
# Heat demand at 09:00 (kW) at each substation
LOAD = {"H1": 820, "H2": 640, "H3": 710, "H4": 530, "H5": 900, "H6": 760, "H7": 480, "H8": 860, "H9": 690, "H10": 560, "H11": 940, "H12": 620}
T_SUPPLY_NOMINAL = 90.0                      # C, EC supply setpoint at the start of the log
