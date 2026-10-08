# Task 14 — GRID-14: signal coordination on a 3 x 3 urban grid (Civil Engineering, transportation)

Goal set by the user: stump in both ways.
1. Completed runs score below 50: most positive weight sits on exact whole-space aggregates
   (sums and counts over every configuration), which need every configuration simulated.
   A run that simulates part of the space and reports the rest scores low (COHERE-12 v2
   probe: 35.8 %).
2. Runs that try the full sweep time out: the full sweep needs several times the 9000 s CLI
   limit on the platform (17 threads, the real model's engine speed), measured with an
   engine written the way the real runs wrote theirs (mistake #77).

## System
- 9 signalized intersections, 12 boundary terminals, one lane per direction; link lengths
  in 7.5 m cells measured from the map (scale bar) - genuine visual measurement.
- Deterministic cellular automaton, 1 s steps: a vehicle moves one cell when the cell ahead
  was empty at the start of the step (single lane, so a waiting left-turner blocks the lane).
- Protected four-phase signals (NS through+right, NS left, EW through+right, EW left), 2 s
  all-red after each phase; green times from the timing table for each cycle and plan.
- Demand: Bernoulli arrivals per second from each terminal's LCG (rates read from the demand
  chart); turning decisions from each vehicle's own LCG, so routes are identical across all
  configurations and only timing changes.
- Run: 3600 s of arrivals, then until empty or the 7200 s cap.

## Configuration space
cycle C in {60, 72, 84, 96, 108, 120} x plan in {P1, P2, P3} x offset of each of the 9
intersections in {0, C/4, C/2, 3C/4} = 6 x 3 x 262,144 = 4,718,592 (resized after benchmark).

## Why no shortcut
Offsets interact through queues and spillback across a grid with loops; exact integer
counts and sums need every configuration; no time-shift symmetry (arrivals are not periodic).

## Answer key
C engine, verified against an independent Python reference and a JS engine; full sweep
split over cloud workers as for COHERE-12 v4.
