#!/usr/bin/env python3
"""ARRAY-11 independent layout checker (Python 3 standard library only).

Written separately from optimizer.py and shares no code with it. Validates a
layout JSON file against every rule of the engineering packet and recomputes
its cost from scratch.

Usage:  python3 checker.py layout1.json [layout2.json ...]
Exit status 0 if every layout is valid, 1 otherwise.

Layout file: {"scenario": "S1", "cables": [{"from": "T05", "to": "T11",
"type": "C1"}, ...], "total_cost": ..., "feeders_used": ...}. Only scenario,
cables (from, to, type) are trusted; any claimed totals are compared against
the recomputation.
"""
import json
import sys
from fractions import Fraction
from math import isqrt

# --- packet section 4 (typed independently from the table) -------------------
COORDS = """
T01 4720 -80 T02 3040 -20 T03 1680 20 T04 80 40 T05 780 340 T06 5640 340
T07 2400 480 T08 3840 520 T09 0 660 T10 4700 700 T11 1700 820 T12 3260 940
T13 3920 1040 T14 700 1060 T15 2360 1080 T16 5520 1140 T17 1440 1540
T18 -140 1600 T19 3220 1680 T20 4680 1700 T21 2500 1860 T22 3920 1900
T23 840 1980 T24 5440 2140 T25 1520 2280 T26 80 2380 T27 3300 2400
T28 4920 2440 T29 3840 2640 T30 640 2680 T31 5540 2720 T32 2520 2880
T33 -120 3060 T34 1700 3080 T35 3100 3180 T36 4860 3320 T37 700 3520
T38 2560 3700 T39 3980 3700 T40 5700 3720 T41 4740 3960 T42 -120 4000
T43 1600 4080 T44 3220 4120 T45 3880 4360 T46 760 4380 T47 5440 4380
T48 2440 4480 T49 1580 4720 T50 4920 4760 T51 3100 4780 T52 -60 4940
T53 780 5080 T54 4080 5100 T55 2540 5240 T56 5740 5280 T57 1540 5520
T58 3360 5540 T59 60 5600 T60 4660 5760 T61 860 5840 T62 4100 5880
T63 5660 5960 T64 2320 6160
"""
_tok = COORDS.split()
POINTS = {_tok[k]: (int(_tok[k + 1]), int(_tok[k + 2])) for k in range(0, len(_tok), 3)}
TURBINE_IDS = sorted(POINTS)
assert len(TURBINE_IDS) == 64

# Figure 1 (site plan) and Figure 2 (cable catalogue), as read.
PLATFORM_POS = {"P": (3200, 3000), "A": (-700, 2700)}
CABLE_CATALOGUE = {"C1": (4, 100), "C2": (8, 160), "C3": (14, 245)}  # capacity, price/m

SCENARIO_DEF = {
    "S1": ("P", ("C1", "C2", "C3"), 6),
    "S2": ("P", ("C1", "C2", "C3"), 5),
    "S3": ("P", ("C2", "C3"), 6),
    "S4": ("A", ("C1", "C2", "C3"), 6),
    "S5": ("A", ("C1", "C2", "C3"), 5),
}
TT_LIMIT = 1300
PLATFORM_NAMES = ("PLATFORM", "P", "A")


def rounded_length(p, q):
    """nearest whole metre, exact halves up; exact integer arithmetic"""
    sq = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
    n = isqrt(sq)
    # sqrt(sq) >= n + 1/2  <=>  4*sq >= (2n+1)^2
    return n + 1 if 4 * sq >= (2 * n + 1) ** 2 else n


def _cr(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def common_points(A, B, C, D):
    """Return the intersection of closed segments AB and CD as either
    None, ('point', (x, y)) with Fraction coordinates, or ('overlap',)."""
    rx, ry = B[0] - A[0], B[1] - A[1]
    sx, sy = D[0] - C[0], D[1] - C[1]
    denom = rx * sy - ry * sx
    qx, qy = C[0] - A[0], C[1] - A[1]
    if denom != 0:
        t = Fraction(qx * sy - qy * sx, denom)
        u = Fraction(qx * ry - qy * rx, denom)
        if 0 <= t <= 1 and 0 <= u <= 1:
            return ("point", (A[0] + t * rx, A[1] + t * ry))
        return None
    if qx * ry - qy * rx != 0:
        return None  # parallel, distinct lines
    rr = rx * rx + ry * ry
    t0 = Fraction(qx * rx + qy * ry, rr)
    t1 = Fraction((D[0] - A[0]) * rx + (D[1] - A[1]) * ry, rr)
    lo, hi = max(Fraction(0), min(t0, t1)), min(Fraction(1), max(t0, t1))
    if lo > hi:
        return None
    if lo == hi:
        return ("point", (A[0] + lo * rx, A[1] + lo * ry))
    return ("overlap",)


def segments_cross(A, B, C, D):
    hit = common_points(A, B, C, D)
    if hit is None:
        return False
    if hit[0] == "overlap":
        return True
    X = hit[1]
    shared = {A, B} & {C, D}
    return not any(X[0] == s[0] and X[1] == s[1] for s in shared)


def check(layout):
    viol = []
    scen = layout.get("scenario")
    if scen not in SCENARIO_DEF:
        return ["SCENARIO: unknown scenario %r" % scen], None, None
    pname, allowed, B = SCENARIO_DEF[scen]
    pos = dict(POINTS)
    pos["PLATFORM"] = PLATFORM_POS[pname]

    def norm(name):
        return "PLATFORM" if name in PLATFORM_NAMES else name

    cables = []
    for c in layout.get("cables", []):
        a, b, ty = norm(c.get("from")), norm(c.get("to")), c.get("type")
        if a not in pos or b not in pos:
            viol.append("ENDPOINT: cable %s-%s has an unknown endpoint" % (a, b))
            continue
        cables.append((a, b, ty))

    # Rule: every turbine exactly one outgoing cable, platform none
    out = {}
    for a, b, ty in cables:
        if a == "PLATFORM":
            viol.append("TREE: cable leaves the platform (%s->%s)" % (a, b))
            continue
        if a == b:
            viol.append("TREE: self loop at %s" % a)
        if a in out:
            viol.append("TREE: turbine %s has more than one outgoing cable" % a)
        out[a] = b
    for t in TURBINE_IDS:
        if t not in out:
            viol.append("TREE: turbine %s has no outgoing cable" % t)

    # Rule: following outgoing cables always reaches the platform
    reaches = {}
    for t in TURBINE_IDS:
        seen = []
        x = t
        ok = False
        while True:
            if x == "PLATFORM":
                ok = True
                break
            if x in reaches:
                ok = reaches[x]
                break
            if x in seen or x not in out:
                ok = False
                break
            seen.append(x)
            x = out[x]
        for y in seen:
            reaches[y] = ok
        if not ok:
            viol.append("TREE: turbine %s does not reach the platform" % t)
    tree_ok = all(reaches.get(t) for t in TURBINE_IDS) and len(out) == 64

    # loads (only meaningful for a valid tree)
    load = {}
    if tree_ok:
        for t in TURBINE_IDS:
            x = t
            while x != "PLATFORM":
                load[x] = load.get(x, 0) + 1
                x = out[x]

    # lengths, length limit, types, costs
    total = 0
    for a, b, ty in cables:
        L = rounded_length(pos[a], pos[b])
        if a != "PLATFORM" and b != "PLATFORM" and L > TT_LIMIT:
            viol.append("LENGTH: turbine-to-turbine cable %s-%s is %d m > %d m" % (a, b, L, TT_LIMIT))
        if ty not in allowed:
            viol.append("TYPE: cable %s-%s uses type %r not available in %s" % (a, b, ty, scen))
            continue
        if tree_ok and a in load:
            ld = load[a]
            cap, pr = CABLE_CATALOGUE[ty]
            if cap < ld:
                viol.append("CAPACITY: cable %s-%s carries load %d but type %s has capacity %d"
                            % (a, b, ld, ty, cap))
            fitting = [(CABLE_CATALOGUE[k][1], k) for k in allowed if CABLE_CATALOGUE[k][0] >= ld]
            if not fitting:
                viol.append("CAPACITY: cable %s-%s load %d exceeds every available type" % (a, b, ld))
            elif cap >= ld and min(fitting)[1] != ty:
                viol.append("CHEAPEST: cable %s-%s (load %d) uses %s, cheapest adequate is %s"
                            % (a, b, ld, ty, min(fitting)[1]))
            total += L * pr

    # Rule: no crossings
    for i in range(len(cables)):
        a, b, _ = cables[i]
        for j in range(i + 1, len(cables)):
            c, d, _ = cables[j]
            if segments_cross(pos[a], pos[b], pos[c], pos[d]):
                viol.append("CROSSING: cable %s-%s crosses cable %s-%s" % (a, b, c, d))

    # Rule: feeder bays
    feeders = sum(1 for a, b, _ in cables if b == "PLATFORM" or a == "PLATFORM")
    if feeders > B:
        viol.append("FEEDERS: %d cables end at the platform, scenario allows %d" % (feeders, B))

    if len(cables) != 64:
        viol.append("TREE: layout has %d cables, a tree on 64 turbines needs 64" % len(cables))

    if not viol:
        if "total_cost" in layout and layout["total_cost"] != total:
            viol.append("COST: claimed total %s differs from recomputed %d" % (layout["total_cost"], total))
        if "feeders_used" in layout and layout["feeders_used"] != feeders:
            viol.append("COST: claimed feeders %s differs from recomputed %d" % (layout["feeders_used"], feeders))
    return viol, (total if tree_ok else None), feeders


def main(paths):
    all_ok = True
    for p in paths:
        with open(p) as f:
            lay = json.load(f)
        viol, cost, feeders = check(lay)
        status = "VALID" if not viol else "INVALID"
        all_ok &= not viol
        print("%s: %s  scenario=%s  recomputed_cost=%s  feeders=%s" % (p, status, lay.get("scenario"), cost, feeders))
        for v in viol:
            print("    violated rule -> " + v)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
