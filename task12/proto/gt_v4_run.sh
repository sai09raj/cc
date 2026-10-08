#!/bin/bash
# COHERE-12 v4 answer-key worker: one directory placement (D0 node, D1 node), all 16 (Q,B) chunks.
# Usage: bash task12/proto/gt_v4_run.sh D0 D1      (run from the repository root)
set -u
D0=$1; D1=$2
ROOT=$(git rev-parse --show-toplevel); cd "$ROOT"
OUT=task12/gt_v4; mkdir -p $OUT
gcc -O3 -march=native -o /tmp/cohere_fast task12/proto/cohere_fast.c || { echo "BUILD FAILED"; exit 1; }
CHECK=$(/tmp/cohere_fast one 16 2400 0 7 2 2 19245)
[ "$CHECK" = "39980 38 58447 2181" ] || { echo "SELF-CHECK FAILED: $CHECK"; exit 1; }
run_chunk() {
  f=$OUT/chunk_${D0}_${D1}_$1_$2.json
  [ -f $f ] && return 0
  /tmp/cohere_fast chunk 16 2400 $D0 $D1 $1 $2 $f || echo "CHUNK FAILED $D0 $D1 $1 $2"
}
N=$(nproc); echo "placement N$D0/N$D1, $N cores, start $(date -u)"
for q in 1 2 3 4; do for b in 1 2 4 8; do
  run_chunk $q $b &
  while [ $(jobs -rp | wc -l) -ge $N ]; do sleep 5; done
done; done
wait
n=$(ls $OUT/chunk_${D0}_${D1}_*.json 2>/dev/null | wc -l)
echo "done $(date -u): $n of 16 chunk files"
git add $OUT/chunk_${D0}_${D1}_*.json
git commit -q -m "task12 gt_v4: placement N$D0/N$D1 ($n/16 chunks)" || true
for i in 1 2 3 4; do git push -q -u origin HEAD && { echo "PUSHED"; break; }; sleep $((2**i)); done
