"""HOLLOWAY-18: 4-storey, 3-bay steel frame on grid line C. Single source of truth for solver, drawings and data sheet."""
E = 210e6          # kN/m^2 (210 GPa)
G_ACC = 9.81       # m/s^2, self-weight = mass x g
LINE_Y = {"B": 0.0, "C": 6.0, "D": 12.6}   # plan positions of frame lines B, C, D (m); frame C strip = half of B-C + half of C-D
SPACING = (LINE_Y["C"] - LINE_Y["B"]) / 2 + (LINE_Y["D"] - LINE_Y["C"]) / 2   # 6.3 m tributary width of frame C

# Section table: A (cm^2), I major axis (cm^4), mass (kg/m)
SEC = {
    "203x203x46 UC": (58.7, 4568, 46.1),
    "203x203x52 UC": (66.3, 5259, 52.0),
    "203x203x60 UC": (76.4, 6125, 60.0),
    "254x254x73 UC": (93.1, 11410, 73.1),
    "254x254x89 UC": (113.0, 14270, 88.9),
    "406x178x54 UB": (69.0, 18720, 54.1),
    "406x178x60 UB": (76.5, 21600, 60.1),
    "457x191x67 UB": (85.5, 29380, 67.1),
    "457x191x74 UB": (94.6, 33320, 74.3),
    "533x210x82 UB": (105.0, 47540, 82.2),
    "533x210x92 UB": (117.0, 55230, 92.1),
    "168.3x6.3 CHS": (32.1, 1053, 25.2),
    "139.7x6.3 CHS": (26.4, 589, 20.7),
    "254x146x31 UB": (39.7, 4413, 31.1),
}

GRID_X = {"1": 0.0, "2": 6.0, "3": 13.5, "4": 20.7}                 # bay widths 6.0 / 7.5 / 7.2
LEVEL_Y = {"G": 0.0, "L1": 4.20, "L2": 7.95, "L3": 11.55, "R": 15.15}  # storeys 4.20 / 3.75 / 3.60 / 3.60
SPLICE = {"1": ("L2", 0.60), "2": ("L1", 0.60), "3": ("L2", 0.60), "4": ("L2", 0.60)}   # per column line: (level, height above it) of the splice

# Column sections per grid line: (below splice, above splice)
COL = {"1": ("203x203x60 UC", "203x203x52 UC"),
       "2": ("254x254x89 UC", "254x254x73 UC"),
       "3": ("254x254x89 UC", "254x254x73 UC"),
       "4": ("203x203x60 UC", "203x203x52 UC")}
BASE = {"1": "pin", "2": "fixed", "3": "fixed", "4": "pin"}

# Beams per level and bay: section; end connections (left, right): "M" moment (rigid) or "S" simple (pinned)
BEAM = {
    ("L1", "1-2"): ("457x191x74 UB", "M", "M"), ("L1", "2-3"): ("533x210x92 UB", "M", "M"), ("L1", "3-4"): ("457x191x67 UB", "M", "M"),
    ("L2", "1-2"): ("457x191x67 UB", "M", "M"), ("L2", "2-3"): ("533x210x82 UB", "M", "M"), ("L2", "3-4"): ("457x191x74 UB", "M", "M"),
    ("L3", "1-2"): ("457x191x74 UB", "S", "M"), ("L3", "2-3"): ("533x210x92 UB", "M", "M"), ("L3", "3-4"): ("457x191x67 UB", "M", "M"),
    ("R",  "1-2"): ("406x178x54 UB", "M", "M"), ("R",  "2-3"): ("406x178x60 UB", "M", "M"), ("R",  "3-4"): ("406x178x54 UB", "M", "M"),
}
# Diagonal braces (pinned both ends, axial only): (id, from (grid, level), to (grid, level))
BRACE = [("BR1", ("3", "G"), ("2", "L1")), ("BR2", ("3", "L1"), ("2", "L2"))]
BRACE_SEC = "168.3x6.3 CHS"

# Floor area loads (kN/m^2, dead + imposed as one case, no factors) on every bay of the level
AREA = {"L1": 7.5, "L2": 7.5, "L3": 7.0, "R": 5.0}
# Storage zone (extra kN/m^2) on L2 bay 2-3 from a to b metres measured from grid 2
STORAGE = dict(level="L2", bay="2-3", q=4.0, a=1.5, b=4.5)
# Roof plant AHU-2: point load (kN) on roof bay 3-4; final position a metres from grid 3, temporary landing position a_temp
PLANT = dict(level="R", bay="3-4", P=45.0, a=4.8)
PLANT_TEMP_A = 1.8
# Wind: horizontal point loads (kN) at grid 1, acting towards grid 4
WIND = {"L1": 36.0, "L2": 34.0, "L3": 32.0, "R": 17.0}

# ---- neighbouring frame lines B and D (drawn on the plans and in the schedule; not analysed) ----
BEAM_B = {
    ("L1", "1-2"): "457x191x67 UB", ("L1", "2-3"): "533x210x82 UB", ("L1", "3-4"): "457x191x74 UB",
    ("L2", "1-2"): "457x191x74 UB", ("L2", "2-3"): "533x210x92 UB", ("L2", "3-4"): "457x191x67 UB",
    ("L3", "1-2"): "457x191x67 UB", ("L3", "2-3"): "533x210x82 UB", ("L3", "3-4"): "457x191x74 UB",
    ("R",  "1-2"): "406x178x60 UB", ("R",  "2-3"): "406x178x54 UB", ("R",  "3-4"): "406x178x60 UB"}
BEAM_D = {
    ("L1", "1-2"): "457x191x67 UB", ("L1", "2-3"): "533x210x92 UB", ("L1", "3-4"): "457x191x74 UB",
    ("L2", "1-2"): "457x191x74 UB", ("L2", "2-3"): "533x210x82 UB", ("L2", "3-4"): "457x191x67 UB",
    ("L3", "1-2"): "457x191x67 UB", ("L3", "2-3"): "533x210x82 UB", ("L3", "3-4"): "457x191x74 UB",
    ("R",  "1-2"): "406x178x54 UB", ("R",  "2-3"): "406x178x54 UB", ("R",  "3-4"): "406x178x60 UB"}
SIMPLE_B = [("L3", "1-2", "2"), ("L2", "2-3", "3")]      # (level, bay, grid end) simple connections drawn on line B
SIMPLE_D = [("L3", "3-4", "3"), ("L1", "1-2", "1")]
SIMPLE_C = [("L3", "1-2", "1")]                          # as drawn on line C (must match BEAM)
TIE = "254x146x31 UB"                                    # ties on grid lines 1-4 between frame lines (not analysed)
# column schedule rows (mark: below splice, splice level, splice height m, above splice, base)
COLSCHED = {
    "B/1": ("203x203x52 UC", "L2", 0.60, "203x203x46 UC", "pin"),   "B/2": ("254x254x89 UC", "L2", 0.60, "254x254x73 UC", "pin"),
    "B/3": ("254x254x73 UC", "L1", 0.60, "203x203x60 UC", "fixed"), "B/4": ("203x203x60 UC", "L1", 0.60, "203x203x52 UC", "pin"),
    "C/1": (COL["1"][0], SPLICE["1"][0], SPLICE["1"][1], COL["1"][1], BASE["1"]),
    "C/2": (COL["2"][0], SPLICE["2"][0], SPLICE["2"][1], COL["2"][1], BASE["2"]),
    "C/3": (COL["3"][0], SPLICE["3"][0], SPLICE["3"][1], COL["3"][1], BASE["3"]),
    "C/4": (COL["4"][0], SPLICE["4"][0], SPLICE["4"][1], COL["4"][1], BASE["4"]),
    "D/1": ("203x203x60 UC", "L1", 0.60, "203x203x52 UC", "fixed"), "D/2": ("254x254x73 UC", "L2", 0.60, "254x254x73 UC", "fixed"),
    "D/3": ("254x254x89 UC", "L1", 0.60, "254x254x73 UC", "pin"),   "D/4": ("203x203x52 UC", "L2", 0.60, "203x203x46 UC", "pin"),
}
BRACE_D = [("BR3", ("1", "G"), ("2", "L1")), ("BR4", ("2", "L1"), ("1", "L2"))]
BRACE_D_SEC = "139.7x6.3 CHS"
AHU1 = dict(line="D", bay="2-3", P=38.0, a=3.2)          # roof plant on line D (not frame C)
