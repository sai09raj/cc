#!/bin/sh
# Regenerate the broken layouts from layout_S1.json and run the checker on all eight layouts.
cd "$(dirname "$0")"
python3 make_broken.py
python3 checker.py layout_S1.json layout_S2.json layout_S3.json layout_S4.json layout_S5.json \
    broken_crossing.json broken_capacity.json broken_length.json greedy_EW_S1.json > checker_output.txt
echo "checker exit status: $? (1 expected because the three broken layouts are rejected)" >> checker_output.txt
cat checker_output.txt
