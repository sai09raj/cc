#!/usr/bin/env python3
"""
Diffs the PRIMARY simulator's per-minute trace and per-lot log against the
INDEPENDENT verifier's, for all six designs, and writes a plain-text report.
Exits nonzero if any mismatch is found.
"""
import csv
import os
import sys

import common as C

PRIMARY = "/tmp/kilnworks-blind-test/work/traces"
VERIFIER = "/tmp/kilnworks-blind-test/work/traces_v2"
OUT = "/tmp/kilnworks-blind-test/work/certification/trace_diff_report.txt"

LOT_FIELDS = ["gidx", "j", "s", "family", "release", "pbase", "qbase",
              "assigned_machine", "setup_used", "prepared_at", "picked_up_at",
              "delivered_at", "cure_start", "cure_end"]
MINUTE_FIELDS = ["t", "P_busy", "Q_busy", "oven_busy", "R0_action", "R0_pos",
                  "R0_cargo", "R1_action", "R1_pos", "R1_cargo", "power_total",
                  "tariff_mult", "bill_delta", "fixture_held"]


def main():
    lines = []
    all_ok = True
    for d in C.DESIGNS:
        a = list(csv.DictReader(open(f"{PRIMARY}/{d}_minute_trace.csv")))
        b = list(csv.DictReader(open(f"{VERIFIER}/{d}_minute_trace.csv")))
        mism = 0
        if len(a) != len(b):
            mism += 1
            lines.append(f"{d}: MINUTE-COUNT MISMATCH primary={len(a)} verifier={len(b)}")
        for ra, rb in zip(a, b):
            for f in MINUTE_FIELDS:
                if ra[f] != rb[f]:
                    mism += 1
                    lines.append(f"{d}: t={ra['t']} field={f} primary={ra[f]!r} verifier={rb[f]!r}")

        la = list(csv.DictReader(open(f"{PRIMARY}/{d}_lot_log.csv")))
        lb = list(csv.DictReader(open(f"{VERIFIER}/{d}_lot_log.csv")))
        for ra, rb in zip(la, lb):
            for f in LOT_FIELDS:
                if ra[f] != rb[f]:
                    mism += 1
                    lines.append(f"{d}: lot={ra['gidx']} field={f} primary={ra[f]!r} verifier={rb[f]!r}")

        status = "IDENTICAL" if mism == 0 else f"{mism} MISMATCHES"
        lines.append(f"{d}: minute_trace rows={len(a)}, lots={len(la)} -> {status}")
        if mism:
            all_ok = False

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print()
    print("ALL SIX DESIGNS BIT-IDENTICAL PRIMARY vs VERIFIER:" if all_ok
          else "MISMATCHES FOUND -- see report", all_ok)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
