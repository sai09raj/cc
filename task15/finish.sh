#!/bin/bash
# FIRE-15: collect the 196 answer-key parts from the worker branches, aggregate, and write rubric.md + ideal-flow.md.
# Usage (repo root): bash task15/finish.sh
set -u
mkdir -p task15/gt
for s in $(seq 1 14); do for q in 0 1 2 3; do
  b=claude/fire15-gt-s${s}q${q}
  git fetch -q origin $b 2>/dev/null || { echo "missing branch $b"; continue; }
  for f in $(git ls-tree --name-only FETCH_HEAD task15/gt/ 2>/dev/null); do git show FETCH_HEAD:$f > $f; done
done; done
echo "part files: $(ls task15/gt/chunk_*.json 2>/dev/null | wc -l) of 196"
python3 task15/proto/aggregate.py task15/gt > /dev/null && cp task15/gt/aggregate.json task15/reference/aggregate.json
python3 -c "import json;a=json.load(open('task15/reference/aggregate.json'));print('missing',a['missing'],a.get('missing_list',''))"
python3 task15/platform/fill_package.py task15/reference/aggregate.json && echo "rubric.md and ideal-flow.md written"
