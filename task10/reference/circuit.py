"""STATIC10 fixed circuit definition — the packet's own stated input.

All delays/periods/margins in picoseconds (ps). This module is the single
source of truth; the artifact's rendered circuit description is generated
from this, never retyped.
"""

CLOCKS = {
    "CLK_A": {"period": 5000, "uncertainty": 120},
    "CLK_B": {"period": 8000, "uncertainty": 150},
}

# name -> (clock, Tcq, Tsu, Th)
FLIP_FLOPS = {
    "A0": ("CLK_A", 180, 90, 70),
    "A1": ("CLK_A", 180, 90, 70),
    "A2": ("CLK_A", 180, 90, 70),
    "B0": ("CLK_A", 180, 90, 70),
    "B1": ("CLK_A", 180, 90, 70),
    "B2": ("CLK_A", 180, 90, 70),
    "C0": ("CLK_A", 180, 90, 70),
    "C1": ("CLK_A", 180, 90, 70),
    "F0": ("CLK_A", 180, 90, 70),
    "D0": ("CLK_B", 220, 110, 85),
    "D1": ("CLK_B", 220, 110, 85),
    "E0": ("CLK_B", 220, 110, 85),
    "E1": ("CLK_B", 220, 110, 85),
}

# name -> (inputs: list of "FF.Q" or gate name, delay, drives: "FF.D" or gate name)
GATES = {
    "g1":  (["A0.Q"],         300, "B0.D"),
    "g2":  (["A0.Q", "A1.Q"], 450, "g5"),
    "g3":  (["A1.Q", "A2.Q"], 380, "g5"),
    "g5":  (["g2", "g3"],     120, "B1.D"),
    "g4":  (["A2.Q"],         250, "B2.D"),
    "g6":  (["B0.Q"],         600, "C0.D"),
    "g7":  (["B1.Q", "B2.Q"], 350, "C1.D"),
    "g11": (["C0.Q"],         320, "D0.D"),
    "g12": (["C1.Q"],         280, "D1.D"),
    "g13": (["C0.Q"],         400, "g15"),
    "g14": (["C1.Q"],        1500, "g15"),
    "g15": (["g13", "g14"],    50, "F0.D"),
    "g16": (["D0.Q"],         500, "E0.D"),
    "g17": (["D1.Q"],         600, "E1.D"),
}

# (launch, capture) -> regime data. Missing pair with real connectivity = DEFAULT.
# regime in {"MULTICYCLE", "FALSE", "CDC"}; extra fields per regime.
CONSTRAINTS = {
    ("B0", "C0"): {"regime": "MULTICYCLE", "N": 2},
    ("B2", "C1"): {"regime": "MULTICYCLE", "N": 3},
    ("C1", "F0"): {"regime": "FALSE"},
    ("C0", "D0"): {"regime": "CDC", "synchronizer_depth": 3},
    ("C1", "D1"): {"regime": "CDC", "synchronizer_depth": 2},
}

CDC_SYNC_THRESHOLD = 3
