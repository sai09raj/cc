#!/bin/bash
# GRID-14 answer-key worker for one (cycle C, plan index PL): 2 lags x 4^9 offsets = 524,288 configurations,
# run as 4 parallel parts (lag 0/1 x offset-index halves). Usage (repo root): bash task14/proto/gt_run.sh C PL
set -u
C=$1; PL=$2
ROOT=$(git rev-parse --show-toplevel); cd "$ROOT"
OUT=task14/gt; mkdir -p $OUT
gcc -O3 -march=native -o /tmp/cgrid_fast task14/proto/cgrid_fast.c || { echo "BUILD FAILED"; exit 1; }
CHECK=$(/tmp/cgrid_fast one 84 0 0,0,0,0,0,0,0,0,0 lead)
[ "${CHECK##*total }" = "4052648" ] || { echo "SELF-CHECK FAILED: $CHECK"; exit 1; }
echo "start C=$C plan=$PL $(nproc) cores $(date -u)"
for LAG in 0 1; do for H in 0 1; do
  F=$OUT/chunk_C${C}_P${PL}_L${LAG}_H${H}.json
  [ -f $F ] || /tmp/cgrid_fast chunk $C $PL $LAG $((H*131072)) $(((H+1)*131072)) 4052648 $F &
done; done
wait
n=$(ls $OUT/chunk_C${C}_P${PL}_*.json 2>/dev/null | wc -l)
echo "done $(date -u): $n of 4 part files"
git add $OUT/chunk_C${C}_P${PL}_*.json; git commit -q -m "task14 gt: C=$C plan=$PL ($n/4 parts)" || true
for i in 1 2 3 4; do git push -q -u origin HEAD && { echo "PUSHED"; break; }; sleep $((2**i)); done
