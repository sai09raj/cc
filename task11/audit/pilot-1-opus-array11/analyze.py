#!/usr/bin/env python3
"""Summarise layouts and optimizer results into results_table.md and
analysis.txt (figures quoted in the memo). Standard library only."""
import json
import os
import math

HERE = os.path.dirname(os.path.abspath(__file__))
SC = ["S1", "S2", "S3", "S4", "S5"]


def load(p):
    with open(os.path.join(HERE, p)) as f:
        return json.load(f)


def stats(lay):
    by_type = {}
    for c in lay["cables"]:
        d = by_type.setdefault(c["type"], [0, 0, 0])
        d[0] += 1
        d[1] += c["length_m"]
        d[2] += c["cost"]
    feeders = [c for c in lay["cables"] if c["to"] == "PLATFORM"]
    return by_type, feeders


def main():
    raw = load("results_raw.json")
    lines = ["| Scenario | Platform | B | Cost | Feeders used | Lower bound | Gap (abs) | Gap (%) | Proven optimal |",
             "|---|---|---|---|---|---|---|---|---|"]
    out = []
    # a restricted scenario's optimum is >= its relaxation's optimum, so the
    # S1 bound also bounds S2 and the S4 bound also bounds S5
    for small, big in (("S2", "S1"), ("S5", "S4")):
        if raw[big]["lb"] > raw[small]["lb"]:
            raw[small]["lb_own"] = raw[small]["lb"]
            raw[small]["lb"] = raw[big]["lb"]
            raw[small]["lb_from"] = big
            raw[small]["gap"] = raw[small]["cost"] - raw[small]["lb"]
            raw[small]["gap_pct"] = 100.0 * raw[small]["gap"] / raw[small]["cost"]
    for sc in SC:
        r = raw[sc]
        lay = load("layout_%s.json" % sc)
        lines.append("| %s | %s | %d | %d | %d | %d | %d | %.2f%% | %s |" % (
            sc, lay["platform"], lay["feeder_bays_B"], r["cost"], r["feeders"], r["lb"], r["gap"],
            r["gap_pct"], "yes" if r["gap"] == 0 else "no"))
        if "lb_from" in r:
            out.append("   (%s bound taken from %s's bound %d; own Lagrangian bound %d)" % (sc, r["lb_from"], r["lb"], r["lb_own"]))
        by_type, feeders = stats(lay)
        out.append("== %s  cost %d  feeders %d  LB %d  gap %d (%.2f%%)" % (
            sc, r["cost"], r["feeders"], r["lb"], r["gap"], r["gap_pct"]))
        for t in sorted(by_type):
            n, L, c = by_type[t]
            out.append("   %s: %2d cables, %6d m, cost %8d" % (t, n, L, c))
        tl = sum(c["length_m"] for c in lay["cables"])
        out.append("   total length %d m; feeder loads %s; feeder lengths %s (sum %d m)" % (
            tl, sorted(c["load"] for c in feeders), sorted(c["length_m"] for c in feeders),
            sum(c["length_m"] for c in feeders)))
        out.append("   load-weighted length sum(load*len) = %d" % sum(c["load"] * c["length_m"] for c in lay["cables"]))
        out.append("   SA restarts (stage 1): %s" % sorted(r["sa_costs"], key=lambda x: (x is None, x)))
        out.append("   Esau-Williams greedy: %s" % r["ew_cost"])
        out.append("   time: heuristic %.0f s, lower bound %.0f s" % (r["t_heur"], r["t_lb"]))
    # platform geometry
    import optimizer as O
    for nm, p in O.PLATFORMS.items():
        ds = [math.hypot(x - p[0], y - p[1]) for x, y in O.TURBINES]
        out.append("platform %s %s: sum of straight-line turbine distances %.0f m, mean %.0f m, max %.0f m" % (
            nm, p, sum(ds), sum(ds) / len(ds), max(ds)))
    with open(os.path.join(HERE, "results_table.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(HERE, "analysis.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(lines))
    print("\n".join(out))


if __name__ == "__main__":
    main()
