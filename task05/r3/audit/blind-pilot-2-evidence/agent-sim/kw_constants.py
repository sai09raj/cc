"""
KILNWORKS R3 -- immutable input constants shared by the primary simulator
and the independent verifier.  Nothing here embeds any per-design ANSWER
(makespan/bill/etc.) -- only graph topology, lot-generation formulas, power
draws, and the tariff function, all taken directly from the packet
(kw-r3b.pdf), sections A-H.

Both kw_primary_sim.py and kw_verifier_sim.py import ONLY from this file
for their "physics"; the actual per-minute decision logic is written
independently (twice) in each of those two files.
"""

from collections import deque

# ---------------------------------------------------------------------------
# Section A -- plant aisle graph and docking bays
# ---------------------------------------------------------------------------
NODES = list(range(9))

# Edges present in BOTH aisle layouts (solid edges in the drawing).
BASE_EDGES = [
    (0, 3), (1, 4), (2, 5),
    (3, 4), (3, 6), (4, 7), (5, 8),
    (6, 7), (7, 8),
]
# Extra edge that exists only in the open-aisle retrofit (dashed edge 4-5).
OPEN_EXTRA_EDGE = (4, 5)

K, P_NODE, Q_NODE, JUNCTION = 1, 3, 5, 4

# Node capacities: docking bays P,Q,K hold up to 2 robots; the interior
# junction node 4 holds only 1; unlisted nodes are treated as unconstrained
# (never binding since the plant has only 2 robots total).
NODE_CAPACITY = {K: 2, P_NODE: 2, Q_NODE: 2, JUNCTION: 1}
DEFAULT_CAPACITY = 2  # any other node -- never binding with only 2 robots


def capacity(node):
    return NODE_CAPACITY.get(node, DEFAULT_CAPACITY)


def build_graph(aisle_open: bool):
    edges = list(BASE_EDGES)
    if aisle_open:
        edges.append(OPEN_EXTRA_EDGE)
    adj = {n: set() for n in NODES}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    return {n: sorted(nb) for n, nb in adj.items()}, set(frozenset(e) for e in edges)


def bfs_dist_to(adj, target):
    """Shortest-path distance from every node to `target` (unweighted BFS)."""
    dist = {n: None for n in adj}
    dist[target] = 0
    dq = deque([target])
    while dq:
        u = dq.popleft()
        for v in adj[u]:
            if dist[v] is None:
                dist[v] = dist[u] + 1
                dq.append(v)
    return dist


def next_hop_toward(adj, dist_to_target, current):
    """Lowest-id neighbor of `current` that lies on a shortest path to the
    target described by dist_to_target (dist_to_target[current] must be > 0).
    Returns None if current has no such neighbor (shouldn't happen on a
    connected graph)."""
    d = dist_to_target[current]
    best = None
    for v in adj[current]:
        if dist_to_target[v] is not None and dist_to_target[v] == d - 1:
            if best is None or v < best:
                best = v
    return best


# ---------------------------------------------------------------------------
# Section B -- six retrofit designs
# ---------------------------------------------------------------------------
# Design -> (F, G, aisle_open, capital)
DESIGNS = {
    "D0": dict(F=2, G=5, aisle_open=False, capital=0),
    "D1": dict(F=3, G=5, aisle_open=False, capital=7),
    "D2": dict(F=2, G=6, aisle_open=False, capital=9),
    "D3": dict(F=2, G=5, aisle_open=True,  capital=6),
    "D4": dict(F=3, G=6, aisle_open=False, capital=16),
    "D5": dict(F=3, G=6, aisle_open=True,  capital=22),
}
DESIGN_ORDER = ["D0", "D1", "D2", "D3", "D4", "D5"]

# ---------------------------------------------------------------------------
# Section C -- campaign workload and cadence
# ---------------------------------------------------------------------------
N_CAMPAIGNS = 4
LOTS_PER_CAMPAIGN = 5
CADENCE = 35


def gen_lots():
    """Returns list of dicts, one per lot (j,s), s=0..3, j=0..4."""
    lots = []
    for s in range(N_CAMPAIGNS):
        for j in range(LOTS_PER_CAMPAIGN):
            family = (j + s) % 2
            release_local = 2 * (j // 2)
            release_abs = CADENCE * s + release_local
            pbase = 5 + ((j * j) + 2 * s) % 4
            qbase = 4 + (3 * j + s) % 5
            gidx = 5 * s + j
            lots.append(dict(
                s=s, j=j, family=family, release=release_abs,
                pbase=pbase, qbase=qbase, gidx=gidx,
            ))
    lots.sort(key=lambda L: L["gidx"])
    return lots


# ---------------------------------------------------------------------------
# Section D -- setup rule
# ---------------------------------------------------------------------------
def setup_cost(remembered_family, job_family):
    if remembered_family is None:
        return 0
    return 0 if remembered_family == job_family else 2


# ---------------------------------------------------------------------------
# Section E -- robot dispatch constants
# ---------------------------------------------------------------------------
HOME = {0: P_NODE, 1: Q_NODE}       # robot id -> home dock node
START_POS = {0: P_NODE, 1: Q_NODE}  # robot id -> starting node at t=0

# Forced-offline window length at Robot 0's FIRST arrival at node 4, read
# directly off the Section E illustrative chart: shaded span from x=3 to
# x=9 -> width = 6 minutes, INCLUSIVE of the arrival minute itself.
NODE4_DISRUPTION_MINUTES = 6

# ---------------------------------------------------------------------------
# Section F -- oven batching / power / tariff
# ---------------------------------------------------------------------------
ANCHOR_DEADLINE_OFFSET = 2  # deadline = arrival_minute + 2

DRAW = dict(P=2, Q=3, oven=3, robot_action=1, robot_wait=0)


def cure_duration(family):
    return 4 + family


def tariff_multiplier(t):
    return 1 + ((t // 7) % 3)


# ---------------------------------------------------------------------------
# Section H -- Q maintenance freeze
# ---------------------------------------------------------------------------
Q_CUM_TRIGGER = 12
Q_FREEZE_MINUTES = 13  # trigger+1 .. trigger+13 inclusive

# ---------------------------------------------------------------------------
# Section G -- investment selection
# ---------------------------------------------------------------------------
def selection_key(design_id, makespan, bill, capital):
    return (makespan, bill + 3 * capital, capital, design_id)
