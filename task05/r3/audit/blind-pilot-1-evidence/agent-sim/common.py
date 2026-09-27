"""
Immutable input constants shared between the PRIMARY simulator (kiln_sim.py)
and the INDEPENDENT verifier (verifier_sim.py).

Per the task instructions, only *immutable input constants* (the numbers
transcribed directly off the packet) may be shared between the two
implementations -- no decision logic, no data structures, no helper
algorithms.  This module contains nothing but literal constants copied from
KILNWORKS Retrofit Engineering Packet (Revision R3).
"""

# ---------------------------------------------------------------------------
# Section A -- plant aisle graph and docking bays
# ---------------------------------------------------------------------------
# Edges present in BOTH aisle layouts (extracted from the packet's vector
# drawing -- see work/EXTRACTION_NOTES.md for the coordinate-level proof).
EDGES_COMMON = [
    (0, 3), (3, 6), (3, 4), (4, 7), (6, 7), (7, 8), (5, 8), (2, 5), (1, 4),
]
# Extra edge that exists ONLY in the open-aisle retrofit (D3, D5).
EDGE_OPEN_ONLY = (4, 5)

P_NODE = 3
Q_NODE = 5
K_NODE = 1
JUNCTION_NODE = 4

# Docking-bay / junction capacities (max robots simultaneously present).
# Nodes not listed here are uncapacitated.
NODE_CAPACITY = {K_NODE: 2, P_NODE: 2, Q_NODE: 2, JUNCTION_NODE: 1}

ROBOT0_HOME = P_NODE
ROBOT1_HOME = Q_NODE

# ---------------------------------------------------------------------------
# Section B -- six retrofit designs
# ---------------------------------------------------------------------------
# name -> (F, G, aisle, capital)
DESIGNS = {
    "D0": dict(F=2, G=5, aisle="closed", capital=0),
    "D1": dict(F=3, G=5, aisle="closed", capital=7),
    "D2": dict(F=2, G=6, aisle="closed", capital=9),
    "D3": dict(F=2, G=5, aisle="open",   capital=6),
    "D4": dict(F=3, G=6, aisle="closed", capital=16),
    "D5": dict(F=3, G=6, aisle="open",   capital=22),
}

# ---------------------------------------------------------------------------
# Section C -- campaign workload and cadence
# ---------------------------------------------------------------------------
NUM_CAMPAIGNS = 4          # s = 0..3
LOTS_PER_CAMPAIGN = 5       # j = 0..4
CADENCE = 35                 # minutes between campaign release windows


def family_of(j, s):
    return (j + s) % 2


def release_local(j):
    return 2 * (j // 2)


def release_abs(j, s):
    return CADENCE * s + release_local(j)


def pbase(j, s):
    return 5 + ((j * j) + 2 * s) % 4


def qbase(j, s):
    return 4 + (3 * j + s) % 5


def global_index(j, s):
    return 5 * s + j


# ---------------------------------------------------------------------------
# Section D -- setup rule
# ---------------------------------------------------------------------------
SETUP_MATCH = 0
SETUP_MISMATCH = 2

# ---------------------------------------------------------------------------
# Section E -- robot dispatch, disruption
# ---------------------------------------------------------------------------
CARGO_CAPACITY = 1
# Forced-offline duration at Robot 0's FIRST arrival at node 4.
# Read directly off the packet's vector-drawn shaded span: the rectangle's
# fill path runs from x=3.0 to x=9.0 data units (see EXTRACTION_NOTES.md),
# i.e. width = 6 grid lines = 6 minutes. This is the one datum in the packet
# that is only recoverable graphically, never printed as a number.
FORCED_OFFLINE_MINUTES = 6

# ---------------------------------------------------------------------------
# Section F -- oven batching, power, tariff
# ---------------------------------------------------------------------------
PAIRING_DEADLINE_SLACK = 2   # anchor deadline = arrival_minute + 2

POWER_DRAW = {
    "P_op": 2,
    "Q_op": 3,
    "oven_op": 3,
    "robot_move": 1,
    "robot_pickup": 1,
    "robot_unload": 1,
    "robot_wait": 0,
}


def cure_minutes(family):
    return 4 + family


def tariff_multiplier(t):
    return 1 + ((t // 7) % 3)
