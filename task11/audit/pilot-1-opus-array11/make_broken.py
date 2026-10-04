#!/usr/bin/env python3
"""Derive three deliberately broken layouts from layout_S1.json.

broken_crossing.json : one turbine is re-attached so that two cables cross
broken_capacity.json : one cable is given a type whose capacity is below its load
broken_length.json   : one turbine is re-attached by a turbine-turbine cable > 1300 m

Each is searched so that, apart from the intended defect, the layout stays a
valid tree with correct cheapest cable types (types are recomputed after the
edit), so the checker's verdict isolates the intended rule. Uses the checker's
geometry only to search for candidates; the verdicts come from running
checker.py on the written files.
"""
import json
import os
import copy
import checker as C

HERE = os.path.dirname(os.path.abspath(__file__))
TYPES_S1 = sorted(C.CABLE_CATALOGUE.items(), key=lambda kv: kv[1][0])


def retype(lay):
    out = {c["from"]: c["to"] for c in lay["cables"]}
    load = {}
    for t in C.TURBINE_IDS:
        x = t
        while x != "PLATFORM":
            load[x] = load.get(x, 0) + 1
            x = out[x]
    for c in lay["cables"]:
        ld = load[c["from"]]
        fit = [k for k, (cap, pr) in TYPES_S1 if cap >= ld]
        if not fit:
            return None
        c["type"] = fit[0]
        c["load"] = ld
    for k in ("total_cost", "feeders_used"):
        lay.pop(k, None)
    for c in lay["cables"]:
        c.pop("cost", None)
        c.pop("length_m", None)
    return lay


def descendants(lay, t):
    ch = {}
    for c in lay["cables"]:
        ch.setdefault(c["to"], []).append(c["from"])
    st, seen = [t], set()
    while st:
        x = st.pop()
        seen.add(x)
        st.extend(ch.get(x, []))
    return seen


def reattach_search(base, want):
    leaves = set(C.TURBINE_IDS) - {c["to"] for c in base["cables"]}
    for a in sorted(leaves):
        desc = descendants(base, a)
        for b in C.TURBINE_IDS:
            if b in desc:
                continue
            lay = copy.deepcopy(base)
            for c in lay["cables"]:
                if c["from"] == a:
                    if c["to"] == b:
                        break
                    c["to"] = b
            else:
                if retype(lay) is None:
                    continue
                viol, _, _ = C.check(lay)
                if viol and all(v.startswith(want) for v in viol):
                    lay["defect"] = "%s re-attached to %s" % (a, b)
                    return lay
    raise SystemExit("no candidate found for " + want)


def main():
    base = json.load(open(os.path.join(HERE, "layout_S1.json")))
    assert not C.check(base)[0]
    # 1) crossing (exactly one crossing pair, nothing else wrong)
    lay = reattach_search(base, "CROSSING")
    json.dump(lay, open(os.path.join(HERE, "broken_crossing.json"), "w"), indent=1)
    # 2) capacity: a C2 cable relabelled C1 (capacity 4 < load)
    lay = copy.deepcopy(base)
    for c in lay["cables"]:
        if c["type"] == "C2":
            c["type"] = "C1"
            lay["defect"] = "cable %s-%s (load %d) relabelled C1" % (c["from"], c["to"], c["load"])
            break
    lay.pop("total_cost", None)
    json.dump(lay, open(os.path.join(HERE, "broken_capacity.json"), "w"), indent=1)
    # 3) turbine-turbine cable longer than 1300 m
    lay = reattach_search(base, "LENGTH")
    json.dump(lay, open(os.path.join(HERE, "broken_length.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
