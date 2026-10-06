#!/bin/bash
# driver.sh K NMAX : worker K of 4 computes up to NMAX missing combos
K=$1; NMAX=$2; BIN=/home/user/cc/task12/proto/cohere_c; OUT=/tmp/claude-0/-home-user-cc/d4dced91-29da-5e32-939d-2f48108a4558/scratchpad/gt12
i=0; done_n=0
for a in 0 1 2 3 4 5 6; do for b in $(seq $((a+1)) 7); do for q in 1 2 3 4; do for bb in 1 2 4 8; do
  if [ $((i % 4)) -eq $K ]; then
    f=$OUT/c_${a}_${b}_${q}_${bb}.bin
    if [ ! -f $f ]; then
      [ $done_n -ge $NMAX ] && exit 0
      $BIN enum 16 400 $a $b $q $bb $f || { echo "FAIL $a $b $q $bb"; exit 1; }
      done_n=$((done_n+1))
    fi
  fi
  i=$((i+1))
done; done; done; done
echo "worker $K finished all"
