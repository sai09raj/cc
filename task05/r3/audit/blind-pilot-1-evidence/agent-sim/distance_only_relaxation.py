#!/usr/bin/env python3
"""
Experiment: "what does a distance-only relaxation lose?"

Builds a deliberately optimistic lower-bound estimate of each design's
makespan that keeps ONLY the graph-distance geometry from Section A/E and
throws away every capacity/contention/timing rule that makes this a real
scheduling problem:

  - no fixture ceiling F (infinite concurrent in-flight lots)
  - no power ceiling G (every operation always admitted)
  - no docking-bay / junction node capacity (nodes hold unlimited robots)
  - no edge capacity (edges carry unlimited simultaneous traversals)
  - no robot contention at all -- every lot gets an idealized dedicated
    "virtual robot" that starts moving the instant the lot is prepared
  - no forced-offline disruption at node 4
  - no oven pairing-timer wait -- curing starts the instant a lot reaches K

Under this relaxation, each lot's earliest possible completion is:
    finish(lot) = release(lot)
                  + min(pbase(lot), qbase(lot))            # best machine, setup=0
                  + dist(best_machine_node -> K)             # free travel, 1 min/edge
                  + (4 + family(lot))                          # immediate solo cure

relaxed_makespan = max over lots of finish(lot)

Comparing this to the real simulator's makespan shows exactly how much
schedule length the capacity/contention machinery (fixtures, power, node/edge
capacity, the node-4 disruption, oven pairing) is responsible for -- i.e.
what a distance-only relaxation loses.
"""
import json
import sys

import common as C
from kiln_sim import build_graph, bfs_dist_from
from kiln_sim import Simulator


def relaxed_makespan(design_name):
    cfg = C.DESIGNS[design_name]
    adj = build_graph(cfg["aisle"])
    dist_to_K = bfs_dist_from(adj, C.K_NODE)
    dP = dist_to_K[C.P_NODE]
    dQ = dist_to_K[C.Q_NODE]

    worst = 0
    per_lot = []
    for s in range(C.NUM_CAMPAIGNS):
        for j in range(C.LOTS_PER_CAMPAIGN):
            fam = C.family_of(j, s)
            rel = C.release_abs(j, s)
            pb = C.pbase(j, s)
            qb = C.qbase(j, s)
            best_proc, travel = (pb, dP) if pb <= qb else (qb, dQ)
            # tie-break irrelevant here since we only need the minimum value
            finish = rel + best_proc + travel + C.cure_minutes(fam)
            per_lot.append({"j": j, "s": s, "finish": finish})
            worst = max(worst, finish)
    return worst, per_lot


def main():
    designs = sys.argv[1:] if len(sys.argv) > 1 else list(C.DESIGNS.keys())
    report = {}
    for name in designs:
        rel_ms, per_lot = relaxed_makespan(name)
        sim = Simulator(name)
        summary = sim.run()
        real_ms = summary["makespan"]
        report[name] = {
            "distance_only_relaxed_makespan_lower_bound": rel_ms,
            "actual_simulated_makespan": real_ms,
            "gap_minutes": real_ms - rel_ms,
            "gap_pct_of_actual": round(100.0 * (real_ms - rel_ms) / real_ms, 1),
        }
        print(f"{name}: relaxed_lower_bound={rel_ms}  actual={real_ms}  "
              f"gap={real_ms - rel_ms} min ({report[name]['gap_pct_of_actual']}% of actual)")

    with open("/tmp/kilnworks-blind-test/work/certification/distance_only_relaxation.json", "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
