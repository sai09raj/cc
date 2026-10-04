# Inter-array cable layout: engineering memo

## 1. Results

| Scenario | Platform | Types | Bays | **Optimal cost** | Feeders used (sizes) | Proven lower bound | Best greedy | Greedy overrun |
|---|---|---|---|---|---|---|---|---|
| S1 | primary | C1–C3 | 7 | **4,732,590** | 7 (5,5,7,7,8,8,8) | 4,732,590 | 5,236,860 | +10.7 % |
| S2 | primary | C1–C3 | 6 | **4,759,920** | 6 (8,8,8,8,8,8) | 4,759,920 | 5,295,080 | +11.2 % |
| S3 | primary | C1–C2 | 11 | **4,758,405** | 10 (4,4,5,5,5,5,5,5,5,5) | 4,758,405 | 4,854,950 | +2.0 % |
| S4 | alternative | C1–C3 | 7 | **6,667,570** | 7 (4,4,8,8,8,8,8) | 6,667,570 | 7,345,070 | +10.2 % |

All four costs are **proven optimal**: the solver's lower bound equals the cost of a feasible layout,
and the independent checker accepts every layout. Bound progression, per scenario:

| Scenario | Arc-formulation LP root bound | Set-partitioning LP bound | Root gap of SP bound | B&B nodes to close it |
|---|---|---|---|---|
| S1 | 4,614,367 | 4,699,826 | 0.69 % | 29 |
| S2 | 4,624,503 | 4,723,418 | 0.77 % | 15 |
| S3 | 4,681,740 | 4,734,897 | 0.49 % | 3 |
| S4 | 6,451,996 | 6,596,296 | 1.07 % | 37 |

Deliverables:
- `results/Sx_optimal.json` is the optimal layout. For each turbine it gives the cable endpoint (`to`), the cable type, the load, the rounded length and the cost.
- `results/Sx_evidence.json` is the proof record (§3). `results/Sx_log.txt` is the solver log.
- `results/Sx_greedy.json` is the best sweep + Prim greedy layout. In S3, `S3_costew_greedy.json` (cost-aware Esau-Williams, 4,854,950) is the best greedy and `S3_ew_greedy.json` is classic Esau-Williams; these two are feasible only in S3.

## 2. Method

**Model.** Every turbine has one outgoing cable, so a layout is a set of *feeder trees*. Each feeder tree is a turbine set S plus a tree hanging from one substation cable. A cable's load is the size of the subtree behind it, so its type and cost follow from the tree. Feeder trees are independent except for two couplings: the bay limit and the no-crossing rule.

1. **Upper bound.** Simulated annealing over parent arrays: 40 restarts of 2.5 M moves each. A move re-roots a subtree and re-hangs it elsewhere. The search respects the 1300 m limit, capacity and crossings, and penalises excess feeders.
2. **Feeder-set enumeration.** Every turbine set that could form one feeder is connected in the ≤1300 m graph and has at most Q turbines (Q = 8, or 5 in S3). ESU enumeration lists all of them: 409,517 sets for Q = 8 and 7,503 for Q = 5. A subset dynamic program gives w(S), the cheapest feeder tree on S with exact cable-type costs. It ignores crossings, so w(S) is a valid lower bound.
3. **Set-partitioning bound.** The LP is: minimise Σ w(S)·λ_S such that every turbine is covered exactly once and Σλ ≤ K. It is solved by column generation (Kelley cutting planes on the dual) with my own dual simplex. For any multipliers (π, μ ≤ 0), every layout satisfies cost ≥ Σπ + K·μ + K·min(0, min_S rc(S)), where rc(S) = w(S) − π(S) − μ. The minimum is taken over all 409,517 sets, so this bound is rigorous and does not depend on LP tolerances. This bound is 1.1–2.2 % of the optimum stronger than the classic capacity-indexed arc formulation (table above).
4. **Reduced-cost filtering.** Pick a target T. Any layout with cost ≤ T−1 can only use feeder trees with reduced cost ≤ gap(T) = T−1−(Σπ+Kμ)−(K−1)·min(0, min rc). The solver enumerates exactly those trees. A recursive enumerator walks the same DP decomposition and prunes with the DP values. Trees with internal crossings are discarded. Pool sizes at the final target: 4,397 / 22,530 / 640 / 205,770 trees for S1–S4.
5. **Branch-and-price-and-cut over the pool.** The master LP has three constraint families: the cover equalities, the bay limit, and clique inequalities (Σ over trees touching a set of mutually crossing cables ≤ 1). The clique inequalities are separated lazily. Columns are priced from the full pool. Branching is on arcs ("turbine i's cable goes to j", yes or no), chosen by strong branching, with reduced-cost fixing over the pool. A node is pruned only by the Lagrangian bound Σ y·b + Σ_{allowed pool trees} min(0, rc). That bound is valid for any multipliers, is accumulated in long double, and is compared with UB − 1 + 10⁻³. Artificial columns of cost 10⁸ keep the master LP feasible, so infeasibility proofs never depend on floating-point rays.
6. **Proof logic.** The first target is the SA value. If branch-and-price finds a cheaper layout it continues with the improved incumbent. The pool already contains every tree of any layout cheaper than the target, so when the search finishes, the incumbent is optimal. If the SA pool had been too large, the solver would have walked a ladder of smaller targets, each run proving "no layout below T". That fallback was not needed here, but the same code proves all four optima from scratch with SA switched off (`./cable_opt Sx ../field.json outdir 0`): S1 1.2 s, S2 1.6 s, S3 0.0 s, S4 6.8 s of exact search.

Everything is my own code: geometry, DP, dual simplex (bounded variables, bound-flipping ratio test, dense explicit inverse with periodic refactorisation), cuts and search. The optimizer is C++17 with the standard library only; the checker uses the Python standard library only.

## 3. Evidence of optimality

The proof chain is valid layout + lower bound = optimum. Concretely:
- **Upper bound.** `checker.py` validates each `results/Sx_optimal.json` and recomputes its cost.
- **Lower bound.** `results/Sx_evidence.json` records the full proof:
  - the set-partitioning dual certificate (π for every turbine, and μ);
  - the resulting bound;
  - for the final branch-and-price run: the target, gap, number of sets and trees, root bound, nodes, and result.

  The final run's result reads "incumbent proven optimal" or "solution found and proven optimal". It means no layout costs ≤ optimum − 1.
- **Independent second proof (S3).** `tests/arc_bnb` is a different exact solver: capacity-indexed arc formulation x[i→j, q], with its own branching and no set enumeration. Started with cutoff 4,758,404, it shows that no S3 layout is cheaper than 4,758,405 (9,441 nodes, 14 s, log in `tests/arc_S3_proof.txt`). I ran the same check for S1, S2 and S4 (cutoff = claimed optimum − 1). The arc relaxation's root gap is 2.5–3.2 % there, and this simple solver has no strong branching, so it did not finish within 20 minutes: it passed 200k nodes for S1 and 100k for S2, and the runs were stopped. No cheaper layout turned up before they were stopped. The optimality of S1, S2 and S4 therefore rests on the main solver, plus the validation below.
- **Validation of the optimizer** (`tests/run_tests.sh`):
  - 60 small random fields (7–10 turbines, random scenario and bay count, SA disabled) matched exhaustive enumeration of every parent assignment, including the infeasible cases. Log: `tests/random_brute_log.txt`.
  - 25 medium random fields (14–18 turbines) matched the independent arc-formulation solver. Log: `tests/medium_log.txt`.
  - On the real field, brute force over all trees confirmed w(S) and the completeness of the budgeted tree enumeration for 1,203 sampled sets (`tests/check_sets_log.txt`).

## 4. How the optima differ, and why

- **S1, the baseline.** The primary platform sits in the middle of the array: mean turbine distance 2.18 km, nearest turbine 241 m. Seven radial feeders each serve a compact sector: three feeders of 8 turbines (C3 at the root), two of 7, and two of 5 (C2 at the root). Of the 39.7 km of cable, 30.6 km is cheap C1 on the branch tips; only 5.4 km is C3.
- **S2, one bay fewer: +27,330 (+0.58 %).** With 6 bays and 48 turbines, every feeder must carry exactly 8 turbines. The two 5-turbine feeders of S1 have to be absorbed, so sector boundaries move and more cable runs at C2 and C3 loads. The 6 C3 feeder cables total 4.8 km, against 5.4 km for 6 C3 cables in S1. Because the feeder count is forced, the partition is rigid. It is the most constrained of the four cases, and both simple greedies and SA struggle with it.
- **S3, no C3 cable: +25,815 (+0.55 %).** Without C3 a feeder carries at most 5 turbines, so at least 10 feeders are needed. The optimum uses 10 of the 11 bays; an eleventh feeder cable would cost more than it saves. Feeder (platform) cable length doubles from 5.9 km to 10.1 km, but all of it is C2 at 145/m instead of C3 at 210/m. Branches are shorter, so more cable is C1. The net penalty is about the same as losing one bay in S2. So with the primary platform, C3 buys very little: about 26 k (0.55 %).
- **S4, alternative platform: +1,934,980 (+40.9 %).** The alternative platform at (−700, 1900) lies outside the west edge. Mean turbine distance is 3.83 km and the farthest turbine is 6.97 km away. Every feeder must cross the whole field from the west, so long trunks run fully loaded: 14.7 km of C3, against 5.4 km in S1, and 11.6 km of feeder cable. Five feeders carry 8 turbines; the two short ones serving the nearest western turbines carry 4 each. The layout is dominated by heavily loaded trunk cable, which is why it costs 41 % more.
- **Lower bounds.** The LP gap grows with how much the bay limit and capacity bind (S3 0.49 % → S4 1.07 %). The arc formulation is 1.6–3.2 % below the optimum, too weak to close by branching on 48 turbines. The feeder-set bound closes everything within 40 nodes.

## 5. Greedy comparison

Three textbook constructive heuristics were tried, each respecting every rule:
- **Esau-Williams** (classic length-based CMST greedy) gets stuck with 8, 8 and 9 feeders in S1, S2 and S4, more than the bays allow. It is feasible only in S3, at 4,938,885 (+3.8 %).
- **Cost-aware Esau-Williams** uses exact cable-type cost deltas. It is feasible only in S3, at 4,854,950 (+2.0 %).
- **Capacitated Prim** dead-ends in all four scenarios.

The underlying problem is bin-packing: greedy merging leaves partial feeders whose sizes cannot be combined into ≤ K feeders of ≤ Q turbines without crossings.

A **sweep + Prim** greedy did produce feasible layouts in every scenario. It sorts turbines by angle around the platform (or, for S4, by horizontal strips), cuts them into balanced groups, and wires each group by shortest admissible cable. I report its best over all start positions and group counts, which is generous to the greedy. The best feasible greedy costs (table in §1):
- S1: 5,236,860 (+10.7 %, +504 k)
- S2: 5,295,080 (+11.2 %, +535 k)
- S3: 4,854,950 (+2.0 %, cost-aware Esau-Williams)
- S4: 7,345,070 (+10.2 %, +677 k)

Greedy layouts are 10–11 % worse wherever the bay limit binds, and they often fail to find any feasible layout at all.

## 6. Interpretation choices

The rules were complete for this data set; where wording admitted two readings, I checked that the choice cannot change the answer:
- **The 1300 m limit is applied to the rounded length.** No turbine pair lies between 1300 and 1300.5 m (nearest are 1298.0 and 1304.3), so applying it to the exact distance gives the same graph.
- **Exact halves.** With integer coordinates the squared distance is an integer and can never equal (n + ½)², so the half-up rule never triggers. It is implemented exactly anyway, with integer arithmetic.
- **Unused platform.** Only the scenario's platform exists; the unused candidate position is ignored. No cable can pass through either platform position: no three of the 50 points are collinear among candidate cables.
- **Points on segments.** Under rule 5, a cable that touches another cable's interior or endpoint counts as a crossing (T-junction), as does collinear overlap. Only three collinear triples exist among the 50 points, and none involves a candidate cable (all have spans > 1300 m), so this never matters here. The checker implements it in full regardless.
- **Feeder count.** The bay limit is an upper bound only. S3's optimum leaves one bay unused.

## 7. Reproduction and environment

```
cd work
./run_all.sh            # builds, solves S1-S4 (~1 min each, mostly the SA warm-up), runs the checker
python3 checker.py ../field.json S1 results/S1_optimal.json      # validate any layout
./cable_opt S4 ../field.json /tmp/out 0                           # exact search alone, no SA
tests/run_tests.sh      # validation suite (minutes; the medium batch is the slow part)
```

Environment:
- Optimizer: C++17 built with g++ 13.3.0 (Ubuntu 24.04), flags `-O2 -std=c++17`, standard library only.
- Checker and test drivers: Python 3.11.15, standard library only.
- Machine: Linux, 4 cores. The solver is single-threaded.

Measured run times per scenario (seconds, wall clock; scenarios run one after another while other jobs used the remaining cores):

| Scenario | SA | Sets + DP + bound | Exact search | Total |
|---|---|---|---|---|
| S1 | 42.1 | 10.2 | 0.7 | 53.1 |
| S2 | 39.2 | 10.3 | 1.1 | 50.7 |
| S3 | 39.8 | 0.6 | 0.0 | 40.5 |
| S4 | 40.0 | 9.4 | 7.4 | 57.5 |

SA is randomised but seeded, so runs are reproducible. Its value only affects speed, not the proven optimum.

Files:
- `cable_opt.cpp` is the driver.
- `instance.hpp` covers data loading, exact geometry and layout evaluation.
- `heuristics.hpp` holds the greedy baselines and SA.
- `lp.hpp` is the dual simplex.
- `setpart.hpp` covers set enumeration, the DP, the set-partitioning bound and tree enumeration.
- `poolbnb.hpp` is the branch-and-price-and-cut.
- `arcmodel.hpp` is the arc formulation, used only for its comparison bound.
- `checker.py` is the independent checker.
- `tests/` holds the validation tools and logs.
