# ARRAY-11 semantic contract (v1)

Offshore wind-farm inter-array cable layout. Every rule the reference
(`opt-prototype/solve_ci.py`, `opt-prototype/check.py`) uses is listed here
with the packet location that carries it. Nothing may exist only in code.

## A01 — Data

| Item | Value | Packet source |
|---|---|---|
| Turbines | 64, T01–T64, integer (x, y) metres | coordinate table (text page) |
| Primary platform | (3200, 3000) | **measured**: site plan, against 500 m gridlines and 100 m ticks |
| Alternative platform | (−700, 2700) | **measured**: site plan |
| Cable C1 | capacity 4 turbines, 100 per metre | **measured**: cable catalogue step chart |
| Cable C2 | capacity 8, 160 per metre | **measured**: catalogue chart |
| Cable C3 | capacity 14, 245 per metre | **measured**: catalogue chart |
| Turbine-to-turbine span limit | 1300 m | prose |

Coordinates in the table are exact; the turbine dots on the site plan are
for orientation only and the prose says so.

## A02 — Layout rules (prose)

1. Each turbine has exactly one outgoing cable, to another turbine or to
   the scenario's platform; following outgoing cables from any turbine
   reaches the platform (trees rooted at the platform).
2. Load of a cable = number of turbines whose power flows through it (the
   turbine it leaves plus all upstream turbines).
3. Cables are straight segments; length = Euclidean distance rounded to the
   nearest metre, exact halves up.
4. A turbine-to-turbine cable is at most 1300 m (rounded length; no pair
   lies in (1300, 1300.5), and T40–T50 is exactly 1300 m, so both readings
   agree). Turbine-to-platform cables have no length limit.
5. No two cables cross: segments may share only a common endpoint; a
   touching point or a collinear overlap counts as crossing.
6. At most `B` cables end at the platform (scenario's feeder bays).
7. Each cable uses the cheapest available type whose capacity is at least
   its load; cable cost = rounded length × that type's price per metre.
   Layout cost = sum of cable costs.

## A03 — Scenarios

| ID | Platform | Cable types | Bays `B` | Certified minimum cost |
|---|---|---|---|---|
| S1 | primary | C1, C2, C3 | 6 | 5,878,715 |
| S2 | primary | C1, C2, C3 | 5 | 5,921,875 |
| S3 | primary | C2, C3 | 6 | 8,075,675 |
| S4 | alternative | C1, C2, C3 | 6 | 7,480,955 |
| S5 | alternative | C1, C2, C3 | 5 | certification running |

Certification: capacity-indexed CP-SAT (OPTIMAL, bound = cost), cost
recomputed by the separate stdlib checker; second certification by
zero-gap SCIP running.

## A04 — What the solver must deliver (graded)

Per scenario: a valid layout; its cost; the best lower bound the solver
can establish and the remaining gap. Graded facts are the exact minimum
costs (unique by definition) and quantities derived from them. Layout
structure is not graded beyond validity, because optimal layouts need not
be unique.

## A05 — Fairness notes

- The minimum costs are found by search; a proof of optimality is not
  required for credit. The prompt asks for the best bound and gap, and the
  rubric rewards a valid bound and penalises claiming optimality for a cost
  above the minimum.
- Solvers are restricted to the standard library; this mirrors the
  offline, dependency-free requirement used on every prior task and is
  stated in the prompt.
