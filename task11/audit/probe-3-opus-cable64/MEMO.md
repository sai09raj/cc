# Engineering memo: inter-array cable layout, scenarios S1-S4

## Bottom line
I found validated layouts for all four scenarios. **I did not prove any of them optimal.** The lower bounds from my own LP/branch-and-bound leave gaps of 1.5% to 7.5%. Each reported cost is the best feasible layout I found, and the independent checker confirms it is valid. It is not a certified minimum.

| Scen. | Best layout cost (UB) | Feeders used | Proven lower bound (LB) | Gap | Greedy baseline |
|---|---|---|---|---|---|
| S1 (primary, C1-C3, ≤6 bays) | **5,948,945** | 5 | 5,746,429 | 3.40% | 6,177,435 (Esau-Williams) |
| S2 (primary, C1-C3, ≤5 bays) | **5,948,945** | 5 | 5,756,599 | 3.24% | 6,483,945 (sweep; EW infeasible) |
| S3 (primary, C2-C3, ≤6 bays) | **8,105,915** | 6 | 7,985,015 | 1.49% | 8,268,705 (sweep; EW infeasible) |
| S4 (alternative, C1-C3, ≤6 bays) | **7,841,955** | 6 | 7,256,158 | 7.47% | 8,264,435 (sweep; EW and equal-sector sweep infeasible) |

Each LB is the safe dual bound of the best-first B&B frontier after 720 s of CPU, rounded up to an integer. Logs are in `evidence/bnb_S*.log`.

## Model and preprocessing
- Lengths: Euclidean distance, rounded half-up, computed with exact integer arithmetic. No pair of turbines lies between 1300 and 1300.5 m. T40-T50 is exactly 1300 m, so it is allowed.
- Candidate cables: 175 turbine pairs are at most 1300 m apart, plus 64 turbine-to-substation cables.
- Crossing conflicts (rule 5, including touching and collinear overlap): 377 pairs for the primary platform and 524 for the alternative. These are grouped into 358 and 483 cliques of mutually crossing cables.
- No turbine lies on another candidate cable.

## Method
1. **Upper bounds.**
   - Greedy constructions: Esau-Williams with crossing checks, and a sweep that splits the turbines into angular sectors around the substation and builds a Prim tree in each.
   - Simulated annealing on the parent array. A move re-hangs or re-roots a subtree onto a new neighbour. Moves that cross an existing cable are rejected; feeders above the limit are penalised.
   - Solutions were cross-seeded between scenarios: a layout feasible for S2 is also feasible for S1 and S3.
2. **Lower bounds (exact attempt).** I wrote a bounded dual simplex in C, with a dense basis inverse and periodic refactorisation. It solves a capacity-indexed formulation:
   - Variables x[a][q] are 1 when directed cable a carries load q. Cost is length × price of the cheapest admissible type for q.
   - Constraints:
     - one outgoing cable per turbine;
     - load conservation, Σq·x(out) − Σq·x(in) = 1;
     - feeder limit;
     - crossing-clique rows;
     - lazily separated load-monotonicity cuts (single child and pairs of children).
   - Branching is on directed arcs. Fixing an arc to 1 also fixes all conflicting arcs to 0.
   - Node bounds are recomputed from the dual vector by weak duality with box bounds. Pruning therefore does not depend on simplex round-off.
   - Root bounds: S1 5,718,453; S2 5,730,648; S3 7,958,922; S4 7,214,588.
3. **Validation.** `checker.py` was coded separately. It uses exact rational segment intersection and checks every rule: the tree reaches the substation, loads, cheapest admissible type, the 1300 m limit, crossings, feeders, and cost. All four reported layouts and all greedy layouts pass. Its geometry was also cross-tested against the optimizer's on 30k random cases.

## Why I could not prove optimality
The LP relaxation is weak for this cost structure. Prices step at loads 4, 8 and 14, and the LP mixes fractional loads at those breakpoints, for example half load-4 and half load-8 on an arc carrying 6. That convexifies the step costs and costs 3-8% of bound. Best-first B&B raised the bounds only about 0.3-0.5% in 12 CPU-minutes. Closing the gap would need a much stronger relaxation, such as branch-and-price over feeder subtrees, plus far more search. That is beyond this budget with home-made solvers.

## How the scenarios differ (based on the best layouts found)
- **S1 vs S2.** The best S1 layout I found uses only 5 feeders, with loads 12, 13, 13, 13 and 13, so restricting to 5 bays cost nothing. Any S2 layout is feasible for S1, so S1 ≤ S2. I could not prove that a 6-feeder layout is never cheaper for S1.
- **S3.** Without C1, the 53 lightly loaded cables (load at most 4) cost 160/m instead of 100/m, about +36% overall. The layout also shifts its structure: 60 C2 cables and 6 feeders carrying 7-14 turbines each, because there is no longer any reason to keep branches at 4 or fewer.
- **S4.** The alternative platform sits off the west edge, so eastern turbines need long, heavily loaded runs. Total cable length is 58.3 km against 50.6 km, and feeder length is 9.7 km against 3.3 km. The layout uses more C2 and C3, and the cost is about 32% above S1. My S4 bound is also the loosest, so this layout may be the furthest from optimal.

## Greedy comparison
- Plain Esau-Williams works only for S1 (6,177,435, +3.8% over the best found). In the other scenarios it gets stuck with more feeders than allowed.
- The sector-sweep greedy is feasible everywhere: S1 6,410,160 (+7.8%), S2 6,483,945 (+9.0%), S3 8,268,705 (+2.0%), S4 8,264,435 (+5.4%).
- Simulated annealing saved 0.23-0.54 M in cost relative to these.

## Interpretation choices
- The 1300 m limit is applied to the rounded length as the rules define it. This makes no difference for this data.
- A turbine lying inside another cable would count as a crossing, because its own cable shares that point. No such case occurs.
- The substation is a single point. Feeder cables may meet there at any angle but may not overlap collinearly.
- Rule 7's "always uses the cheapest type" is treated as determining the type from the load, and cost uses that type.
