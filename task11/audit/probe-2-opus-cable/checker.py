#!/usr/bin/env python3
"""Independent layout checker (Python 3 standard library only; shares no code with the optimizer).

Usage:  python3 checker.py <field.json> <S1|S2|S3|S4> <layout.json>

layout.json must contain {"layout": {"T01": {"to": "T07" | "OSS", "type": "C1"|"C2"|"C3"}, ...}}
(other keys are ignored except "total_cost", which, if present, is compared to the recomputed cost).
Validates every rule of the specification with exact integer arithmetic and prints the cost.
Exit status 0 = valid, 1 = invalid.
"""
import json
import math
import sys

CABLES = {"C1": (3, 100), "C2": (5, 145), "C3": (8, 210)}
SCENARIOS = {
    "S1": ("substation_primary", ("C1", "C2", "C3"), 7),
    "S2": ("substation_primary", ("C1", "C2", "C3"), 6),
    "S3": ("substation_primary", ("C1", "C2"), 11),
    "S4": ("substation_alternative", ("C1", "C2", "C3"), 7),
}
MAX_TT = 1300
OSS = "OSS"


def rounded_length(p, q):
    """Euclidean distance rounded to nearest integer, exact halves up (exact integer math)."""
    d2 = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
    r = math.isqrt(d2)                 # floor(sqrt(d2))
    # sqrt(d2) >= r + 1/2  <=>  4*d2 >= (2r+1)^2
    return r + 1 if 4 * d2 >= (2 * r + 1) ** 2 else r


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def on_closed_segment(p, a, b):
    return cross(a, b, p) == 0 and min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def segments_conflict(a, b, c, d):
    """True if closed segments ab and cd share a point other than a common endpoint,
    or are collinear and overlap along a stretch (even when sharing an endpoint)."""
    common = {a, b} & {c, d}
    o1, o2, o3, o4 = cross(a, b, c), cross(a, b, d), cross(c, d, a), cross(c, d, b)
    if o1 == 0 and o2 == 0:
        # collinear: compare the 1-D projections on the dominant axis
        ax = 0 if a[0] != b[0] else 1
        lo1, hi1 = sorted((a[ax], b[ax]))
        lo2, hi2 = sorted((c[ax], d[ax]))
        lo, hi = max(lo1, lo2), min(hi1, hi2)
        if lo > hi:
            return False                      # disjoint
        if lo < hi:
            return True                       # overlap along a stretch
        # touch in exactly one point: allowed only if it is a common endpoint
        pt = [p for p in (a, b, c, d) if p[ax] == lo][0]
        return pt not in common
    if common:
        # not collinear and sharing an endpoint: two distinct lines meet in one point only
        return False
    if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0) and o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0:
        return True                           # proper crossing
    # touching cases (an endpoint lying on the other segment)
    return (on_closed_segment(c, a, b) or on_closed_segment(d, a, b) or
            on_closed_segment(a, c, d) or on_closed_segment(b, c, d))


def check(field_path, scen, layout_path, verbose=True):
    field = json.load(open(field_path))
    sub_key, types, max_feeders = SCENARIOS[scen]
    pos = {k: tuple(v) for k, v in field["turbines"].items()}
    sub = tuple(field[sub_key])
    pos_all = dict(pos)
    pos_all[OSS] = sub
    doc = json.load(open(layout_path))
    lay = doc["layout"]
    errors = []

    # Rule 1: exactly one outgoing cable per turbine, to a turbine or the substation
    if set(lay) != set(pos):
        errors.append("layout turbines differ from field turbines: missing %s, extra %s"
                      % (sorted(set(pos) - set(lay)), sorted(set(lay) - set(pos))))
        return errors, None
    parent = {}
    for t, e in lay.items():
        to = e["to"]
        if to != OSS and to not in pos:
            errors.append("%s: unknown target %r" % (t, to))
        if to == t:
            errors.append("%s: cable to itself" % t)
        parent[t] = to
    if errors:
        return errors, None
    # every turbine must reach the substation
    for t in pos:
        seen, v = set(), t
        while v != OSS:
            if v in seen:
                errors.append("%s: following cables loops (cycle through %s)" % (t, v))
                break
            seen.add(v)
            v = parent[v]
    if errors:
        return errors, None

    # Rule 2: load = turbine itself + everything upstream
    load = {t: 0 for t in pos}
    for t in pos:
        v = t
        while v != OSS:
            load[v] += 1
            v = parent[v]

    # Rules 3/4/7: lengths, length limit, cable type and cost
    total = 0
    for t in sorted(pos):
        to = parent[t]
        L = rounded_length(pos[t], pos_all[to])
        if to != OSS and L > MAX_TT:
            errors.append("%s->%s: turbine-turbine cable %d m > %d m" % (t, to, L, MAX_TT))
        allowed = [c for c in types if CABLES[c][0] >= load[t]]
        if not allowed:
            errors.append("%s->%s: load %d exceeds every available cable" % (t, to, load[t]))
            continue
        cheapest = min(allowed, key=lambda c: CABLES[c][1])
        given = lay[t].get("type")
        if given is not None and given != cheapest:
            errors.append("%s->%s: type %s given but cheapest admissible type for load %d is %s"
                          % (t, to, given, load[t], cheapest))
        total += L * CABLES[cheapest][1]

    # Rule 5: no crossings (all pairs)
    cables = [(t, parent[t]) for t in sorted(pos)]
    for i in range(len(cables)):
        a, b = pos_all[cables[i][0]], pos_all[cables[i][1]]
        for j in range(i + 1, len(cables)):
            c, d = pos_all[cables[j][0]], pos_all[cables[j][1]]
            if segments_conflict(a, b, c, d):
                errors.append("cables %s-%s and %s-%s cross" % (cables[i] + cables[j]))

    # Rule 6: feeder bays
    feeders = sum(1 for t in pos if parent[t] == OSS)
    if feeders > max_feeders:
        errors.append("%d feeders > %d bays" % (feeders, max_feeders))

    if "total_cost" in doc and doc["total_cost"] != total:
        errors.append("reported total_cost %s != recomputed %d" % (doc["total_cost"], total))
    if verbose:
        print("%s: %s  feeders=%d  max load=%d  recomputed cost=%d" %
              (scen, layout_path, feeders, max(load.values()), total))
    return errors, total


def _self_test():
    # geometry corner cases for rule 5
    assert segments_conflict((0, 0), (4, 4), (0, 4), (4, 0))          # X crossing
    assert not segments_conflict((0, 0), (4, 4), (4, 4), (8, 0))      # shared endpoint only
    assert segments_conflict((0, 0), (4, 0), (2, 0), (6, 0))          # collinear overlap
    assert segments_conflict((0, 0), (4, 0), (0, 0), (2, 0))          # collinear overlap sharing endpoint
    assert not segments_conflict((0, 0), (4, 0), (4, 0), (6, 0))      # collinear, touch at common endpoint
    assert segments_conflict((0, 0), (4, 0), (2, 0), (2, 5))          # T-junction
    assert not segments_conflict((0, 0), (4, 0), (5, 0), (9, 0))      # collinear disjoint
    assert not segments_conflict((0, 0), (4, 0), (0, 1), (4, 1))      # parallel
    assert rounded_length((0, 0), (3, 4)) == 5
    assert rounded_length((0, 0), (1, 1)) == 1                        # 1.414 -> 1
    assert rounded_length((0, 0), (1, 2)) == 2                        # 2.236 -> 2
    assert rounded_length((0, 0), (2, 2)) == 3                        # 2.828 -> 3


if __name__ == "__main__":
    _self_test()
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    errs, cost = check(sys.argv[1], sys.argv[2], sys.argv[3])
    if errs:
        print("INVALID:")
        for e in errs:
            print("  " + e)
        sys.exit(1)
    print("VALID, total cost = %d" % cost)
