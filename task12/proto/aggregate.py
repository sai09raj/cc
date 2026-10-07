#!/usr/bin/env python3
"""Aggregate the exhaustive COHERE-12 v2 enumeration (448 files x 65,536 line maps).

Each file c_{d0}_{d1}_{Q}_{B}.bin holds, for line map h = 0..65535, uint16 makespan
and uint16 messages. Objective key: (makespan, messages, d0, d1, Q, B, h).
"""
import glob, json, os, struct, sys
from array import array

D = sys.argv[1]
files = sorted(glob.glob(os.path.join(D, "c_*.bin")))
assert len(files) == 448, len(files)
best = None
best_q = {}
best_b = {}
hist = {}
total = 0
top = []  # keep the 20 best overall
import heapq
for f in files:
    d0, d1, q, b = map(int, os.path.basename(f)[2:-4].split("_"))
    a = array("H"); a.frombytes(open(f, "rb").read())
    assert len(a) == 2 * 65536
    ms, msg = a[0::2], a[1::2]
    for h in range(65536):
        key = (ms[h], msg[h], d0, d1, q, b, h)
        total += 1
        if best is None or key < best:
            best = key
        if q not in best_q or key < best_q[q]:
            best_q[q] = key
        if b not in best_b or key < best_b[b]:
            best_b[b] = key
        if len(top) < 20:
            heapq.heappush(top, tuple(-x for x in key))
        elif key < tuple(-x for x in top[0]):
            heapq.heapreplace(top, tuple(-x for x in key))
top = sorted(tuple(-x for x in t) for t in top)
fmt = lambda k: dict(makespan=k[0], messages=k[1], d0=k[2], d1=k[3], Q=k[4], B=k[5], linemap=k[6])
out = dict(total=total, optimum=fmt(best), best_per_Q={q: fmt(v) for q, v in sorted(best_q.items())},
           best_per_B={b: fmt(v) for b, v in sorted(best_b.items())}, top20=[fmt(t) for t in top])
json.dump(out, open(os.path.join(D, "aggregate.json"), "w"), indent=1)
print(json.dumps(out, indent=1)[:4000])
