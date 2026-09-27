#!/usr/bin/env python3
"""
Experiment: "what if the four campaigns were run as four independent resets
instead of one continuous run?"

For each campaign s, this builds a Simulator whose lot universe is restricted
to that campaign's 5 lots alone, with release times rebased to a *local*
clock starting at 0 (release_local(j) instead of 35*s + release_local(j)),
and with machine memory / fixtures / robot positions / oven state all reset
to their t=0 initial condition -- i.e. exactly what "four independent
resets" would mean operationally.

It then compares:
  (a) sum of the four campaigns' own local makespans / bills computed this way
  (b) the actual continuous single-clock run's makespan / bill

against each other, and reports the concrete divergence + WHY (setup-memory
reuse across campaign boundaries, tail overlap, shared fixture/robot
contention) for each of the 6 designs.
"""
import json
import sys

import common as C
from kiln_sim import Simulator


def build_isolated_campaign_sim(design_name, s):
    sim = Simulator(design_name)
    # restrict to this campaign's lots only, rebased to a local clock
    keep = [l for l in sim.lots if l.s == s]
    for l in keep:
        l.release = C.release_local(l.j)  # strip the 35*s cadence offset
    sim.lots = keep
    sim.by_gidx = {l.gidx: l for l in keep}
    sim.n_lots_total = len(keep)
    # machine memory / fixtures / robots / oven are already at their fresh
    # t=0 initial state from Simulator.__init__, which is exactly the
    # "independent reset" semantics we want to test.
    return sim


def run_independent_resets(design_name):
    per_campaign = []
    for s in range(C.NUM_CAMPAIGNS):
        sim = build_isolated_campaign_sim(design_name, s)
        summary = sim.run()
        per_campaign.append({
            "campaign": s,
            "local_makespan": summary["makespan"],
            "local_bill": summary["bill"],
        })
    total_makespan_if_serial = sum(c["local_makespan"] for c in per_campaign)
    total_makespan_if_parallel_clock = max(c["local_makespan"] for c in per_campaign)  # naive alt reading
    total_bill_independent = sum(c["local_bill"] for c in per_campaign)
    return per_campaign, total_makespan_if_serial, total_bill_independent


def main():
    designs = sys.argv[1:] if len(sys.argv) > 1 else list(C.DESIGNS.keys())
    report = {}
    for name in designs:
        per_campaign, total_makespan_serial, total_bill_independent = run_independent_resets(name)

        continuous_sim = Simulator(name)
        continuous_summary = continuous_sim.run()

        report[name] = {
            "per_campaign_isolated": per_campaign,
            "independent_resets_sum_of_local_makespans": total_makespan_serial,
            "independent_resets_sum_of_local_bills": total_bill_independent,
            "continuous_run_makespan": continuous_summary["makespan"],
            "continuous_run_bill": continuous_summary["bill"],
            "makespan_delta_continuous_minus_independentsum": (
                continuous_summary["makespan"] - total_makespan_serial
            ),
            "bill_delta_continuous_minus_independentsum": (
                continuous_summary["bill"] - total_bill_independent
            ),
        }
        print(f"{name}: continuous=(makespan={continuous_summary['makespan']}, bill={continuous_summary['bill']})"
              f"  independent-resets-sum=(makespan={total_makespan_serial}, bill={total_bill_independent})")

    with open("/tmp/kilnworks-blind-test/work/certification/campaign_reset_experiment.json", "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
