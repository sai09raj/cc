#!/usr/bin/env python3
"""
Produces the causal-explanation diagnostics used in MEMO.md: per design,
how often the fixture ceiling F is the binding constraint, how many robot
actions get refused and for which reason (power / node capacity / edge
capacity), and how the oven pairing timer's batch sizes come out.

Writes certification/design_diagnostics.json.
"""
import json

import common as C
from kiln_sim import Simulator

ORIG = Simulator.apply_robot_action


def make_wrapper(counts_dict):
    def wrapped(self, robot, intent, t, remaining_budget, edges_used, other_final_pos):
        kind, draw, detail = ORIG(self, robot, intent, t, remaining_budget, edges_used, other_final_pos)
        r = detail.get("refused")
        if r:
            counts_dict[r] = counts_dict.get(r, 0) + 1
        return kind, draw, detail
    return wrapped


def main():
    report = {}
    for name in C.DESIGNS:
        counts = {"power": 0, "node_capacity": 0, "edge_capacity": 0}
        Simulator.apply_robot_action = make_wrapper(counts)
        sim = Simulator(name)
        summary = sim.run()
        Simulator.apply_robot_action = ORIG  # reset before next design, no layering

        binding_minutes = sum(1 for r in sim.minute_rows if r["fixture_held"] >= sim.F)
        oven_starts = [e for e in sim.trace if e["event"] == "oven_start"]
        batch_sizes = [len(e["lots"]) for e in oven_starts]

        report[name] = {
            "makespan": summary["makespan"], "bill": summary["bill"],
            "fixture_binding_minutes": binding_minutes,
            "total_minutes": len(sim.minute_rows),
            "fixture_binding_pct": round(100 * binding_minutes / len(sim.minute_rows), 1),
            "robot_action_refusals": dict(counts),
            "n_oven_batches": len(oven_starts),
            "n_paired_batches": sum(1 for s in batch_sizes if s == 2),
            "n_solo_batches": sum(1 for s in batch_sizes if s == 1),
        }

    print(json.dumps(report, indent=2))
    with open("/tmp/kilnworks-blind-test/work/certification/design_diagnostics.json", "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
