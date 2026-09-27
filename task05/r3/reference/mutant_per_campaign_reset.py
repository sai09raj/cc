#!/usr/bin/env python3
"""Realistic wrong-implementation mutant: treats the four campaigns as four
independent resets (R2's old semantics) instead of one continuous, overlapping,
state-persisting run (R3's S02/S03/S05 requirement). Used to prove the
continuous-chaining rule is load-bearing, not cosmetic, and to feed the
score-topology plausible-wrong survival audit.
"""
import kilnworks_sim as k


def simulate_per_campaign_reset(design_name):
    all_lots = k.gen_lots()
    total_makespan = 0
    total_bill = 0
    per_campaign = []
    for s in range(k.CAMPAIGNS):
        camp_lots = [dict(x) for x in all_lots if x["s"] == s]
        for x in camp_lots:
            x["release_abs"] = 2 * (x["j"] // 2)  # reset to campaign-local release, as if s=0
        r = k.simulate(design_name, lots_data=camp_lots)
        total_makespan += r["makespan"]
        total_bill += r["bill"]
        per_campaign.append((r["makespan"], r["bill"]))
    return dict(design=design_name, makespan=total_makespan, bill=total_bill,
                per_campaign=per_campaign, fault_triggered=None)


if __name__ == "__main__":
    canon = {name: k.simulate(name) for name in k.DESIGNS}
    for name in k.DESIGNS:
        r = simulate_per_campaign_reset(name)
        c = canon[name]
        print(name, "reset-mutant makespan/bill:", r["makespan"], r["bill"],
              " canonical:", c["makespan"], c["bill"],
              "CHANGED" if (r["makespan"], r["bill"]) != (c["makespan"], c["bill"]) else "same")
