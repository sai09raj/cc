"""ISO-16 draft: authored 3D cooling-water piping network (mm). Moves: (dir, length) with dir in E W N S U D."""
VEC = {"E": (1, 0, 0), "W": (-1, 0, 0), "N": (0, 1, 0), "S": (0, -1, 0), "U": (0, 0, 1), "D": (0, 0, -1)}
START = ("P1", (2000, 1500, 800))   # pump discharge nozzle (E, N, EL)
# Each line: (line id, DN, from node, [items]); item = (dir, length[, fitting-after]) or a node label string.
# fitting-after: 'GV' gate valve, 'CK' check valve, 'GL' globe valve, 'RED' reducer to next DN at that point
LINES = [
    ("CW-101", 150, "P1", [("U", 1200, "CK"), ("U", 600, "GV"), ("E", 1850), ("U", 3900), ("N", 4200), "T1",
                           ("N", 3600), "T2", ("N", 2750), ("E", 5400), "T3", ("E", 3300), "T4", ("E", 2150),
                           ("D", 900), ("E", 1600), "T5", ("E", 2800), ("U", 1200), ("E", 2000), ("D", 1200), "T6",
                           ("E", 2450), "END1"]),
    ("CW-102", 100, "T1", [("W", 1500, "GV"), ("W", 900), ("D", 4300), ("S", 700), "C1"]),
    ("CW-103", 100, "T2", [("E", 2200, "GV"), ("D", 2100), ("E", 1300), ("D", 1650), ("E", 650), "C2"]),
    ("CW-104", 80, "T3", [("N", 2500, "GV"), ("D", 5200), ("N", 600), "C3"]),
    ("CW-105", 80, "T4", [("S", 3100, "GV"), ("D", 1800), ("S", 750), ("D", 1500), ("S", 900), ("U", 1100), "C4"]),
    ("CW-106", 100, "T5", [("D", 2600, "RED"), ("N", 1900), ("D", 1100), ("E", 800), "C5"]),
    ("CW-107", 50, "T6", [("N", 1800, "GV"), ("U", 700), ("N", 1200), ("D", 4800), ("N", 450), "C6"]),
]
