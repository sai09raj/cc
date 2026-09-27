#!/usr/bin/env python3
"""
Builds the six-design case matrix and both investment selections using the
lexicographic key (makespan, bill) -- ascending on makespan first, ties
broken by ascending bill -- applied to the primary simulator's results.

    unrestricted selection : argmin over all 6 designs
    capital<=9 selection    : argmin over designs with capital <= 9
"""
import csv
import json
import sys

import common as C
from kiln_sim import Simulator


def build_matrix():
    rows = []
    for name in C.DESIGNS:
        sim = Simulator(name)
        summary = sim.run()
        rows.append(summary)
    rows.sort(key=lambda r: r["design"])
    return rows


def select(rows, capital_cap=None):
    pool = rows if capital_cap is None else [r for r in rows if r["capital"] <= capital_cap]
    if not pool:
        return None
    best = min(pool, key=lambda r: (r["makespan"], r["bill"]))
    return best, pool


def main():
    rows = build_matrix()

    with open("/tmp/kilnworks-blind-test/work/case_matrix.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["design", "F", "G", "aisle", "capital", "makespan", "bill"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    best_unrestricted, pool_u = select(rows, None)
    best_restricted, pool_r = select(rows, 9)

    result = {
        "case_matrix": rows,
        "lexicographic_key": "(makespan asc, bill asc)",
        "unrestricted_selection": {
            "key": [best_unrestricted["makespan"], best_unrestricted["bill"]],
            "design": best_unrestricted["design"],
            "pool_considered": [r["design"] for r in pool_u],
            "full_ranking": sorted(pool_u, key=lambda r: (r["makespan"], r["bill"])),
        },
        "capital_le_9_selection": {
            "key": [best_restricted["makespan"], best_restricted["bill"]],
            "design": best_restricted["design"],
            "pool_considered": [r["design"] for r in pool_r],
            "full_ranking": sorted(pool_r, key=lambda r: (r["makespan"], r["bill"])),
        },
    }

    with open("/tmp/kilnworks-blind-test/work/case_matrix_and_selections.json", "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
