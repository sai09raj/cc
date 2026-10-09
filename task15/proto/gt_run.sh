#!/bin/bash
# FIRE-15 answer-key worker: crew 1 at station S1, crew 2 at stations 4Q+1..4Q+4 (max 14), all 14^5 plans of crews 3-7
# for each, run as parallel parts. Usage (repo root): bash task15/proto/gt_run.sh S1 Q
set -u
S1=$1; Q=$2
ROOT=$(git rev-parse --show-toplevel); cd "$ROOT"
OUT=task15/gt; mkdir -p $OUT
gcc -O3 -march=native -o /tmp/ffast task15/proto/ffast.c || { echo "BUILD FAILED"; exit 1; }
CHECK=$(/tmp/ffast one 1,4,5,8,9,12,13)
[ "${CHECK##*total }" = "13766" ] || { echo "SELF-CHECK FAILED: $CHECK"; exit 1; }
echo "start S1=$S1 Q=$Q $(nproc) cores $(date -u)"
want=0
for S2 in $(seq $((4*Q+1)) $((4*Q+4))); do
  [ $S2 -le 14 ] || continue; want=$((want+1))
  F=$OUT/chunk_${S1}_${S2}.json
  [ -f $F ] || /tmp/ffast chunk $S1 $S2 1992,4240,3455,4079 $F &
done
wait
n=0; for S2 in $(seq $((4*Q+1)) $((4*Q+4))); do [ -f $OUT/chunk_${S1}_${S2}.json ] && n=$((n+1)); done
echo "done $(date -u): $n of $want part files"
git add $OUT/chunk_${S1}_*.json; git commit -q -m "task15 gt: S1=$S1 Q=$Q ($n/$want parts)" || true
for i in 1 2 3 4; do git push -q -u origin HEAD && { echo "PUSHED"; break; }; sleep $((2**i)); done
