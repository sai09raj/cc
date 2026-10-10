"""ISO-16 v3 draft: gravity cooling-water network from head tank T-1 (mm). Same move format as proto/network.py."""
VEC = {"E": (1, 0, 0), "W": (-1, 0, 0), "N": (0, 1, 0), "S": (0, -1, 0), "U": (0, 0, 1), "D": (0, 0, -1)}
START = ("T-1", (0, 0, 20000))   # tank outlet nozzle; tank water level EL +25000
TANK_LEVEL = 25000
LINES = [
    ("CW-301", 150, "T-1", [("D", 6000), ("E", 4000), ("N", 3000), "T1", ("N", 8000), "T2", ("N", 6000), "T3",
                             ("N", 4000), ("U", 2000), "O4"]),
    ("CW-302", 80, "T1", [("E", 3000, "GV"), ("U", 1000), ("E", 1000), "O1"]),
    ("CW-303", 80, "T2", [("W", 2500, "GV"), ("U", 3000), ("W", 1500), "O2"]),
    ("CW-304", 80, "T3", [("E", 2000, "GV"), ("U", 17000), ("E", 6000), ("D", 31000), ("E", 1500), "O3"]),
]
ID = {150: 0.1541, 100: 0.1023, 80: 0.0779}    # inner diameter m (Sch 40)
K = dict(ent=0.5, ell=0.3, gv=0.15, tee_branch=1.0, tee_run=0.2, exit=1.0)
KHX = {1: 45.0, 2: 30.0, 4: 60.0}   # consumer exchanger K, on the line velocity at that outlet
RHO, NU, G, PATM, PV, EPS = 998.2, 1.004e-6, 9.81, 101325.0, 2339.0, 0.045e-3
