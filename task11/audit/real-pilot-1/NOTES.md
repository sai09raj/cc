# ARRAY-11 real pilot round 1 (array11_v2.pdf + array-prompt.md)

Six real runs: one completed (98%), five timed out. The timed-out
trajectory file contains no events (`[]`), so nothing can be graded or
diagnosed from it.

## Completed run (`run-98.json`)

- Wall time 1 h 44 min (20:12 to 21:56 UTC), 180 turns, 140 Bash calls.
- Optimizer, Lagrangian bound and parallel branch and bound in
  JavaScript (Node.js v20.20.2, built-in modules only); checker in
  Python 3.11.17, standard library only. No third-party solver.
- All five certified minimums found AND proven (bound = cost, gap 0):
  5,878,715 / 5,921,875 / 8,075,675 / 7,480,955 / 7,516,700.
  Root Lagrangian bound 0.29% to 1.43% below optimum; branch and bound
  closed each in 7 to 86 s (189 to ~107,000 nodes). Cross-checked against
  brute force on 92 small instances and a second branching rule.
- All four differences exact (43,160 / 35,745 / 2,196,960 / 1,602,240)
  with correct causes; greedy 6,177,435; figure values exact.

## Reading

This is a genuine, clean solve of the full task, including the
optimality proofs the author needed CP-SAT for. The optimization
difficulty does not hold against the real target when it finishes.
Five timeouts are a time-limit effect, not evidence of difficulty.
