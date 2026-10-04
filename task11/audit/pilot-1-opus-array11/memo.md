# ARRAY-11 inter-array cable layout: engineering memo

Every figure below comes from the programs in this directory: `optimizer.py`, `checker.py`, `make_broken.py` and `analyze.py`. The detailed numbers are in `analysis.txt`, `results_table.md` and `checker_output.txt`. The runtime was CPython 3.11.15 on Linux, using only the standard library.

## 1. Inputs read from the figures

- **Platform positions (Figure 1).** P = (3200, 3000) and A = (−700, 2700).
  - P sits on the 3000 m northing major gridline, two minor gridlines east of the 3000 m easting line.
  - A sits three minor gridlines left of the 0 m easting line, and three minor gridlines below the 3000 m northing line.
  - I confirmed both readings by locating gridline pixels and crosshair pixels in the embedded raster. At 263 px per 1000 m, the crosshairs land within about 4 m of these values.
- **Cable catalogue (Figure 2).**

  | Type | Loads covered | Capacity | Price |
  |---|---|---|---|
  | C1 | 1–4 | 4 | 100 per m |
  | C2 | 5–8 | 8 | 160 per m |
  | C3 | 9–14 | 14 | 245 per m |

  - C3's step lies halfway between the 240 and 250 minor gridlines. The pixel-row interpolation gives 245.3, so I read it as 245.
  - The end dots at loads 4, 8 and 14 confirm the capacities.

## 2. Results

| Scenario | Platform | B | Cost | Feeders used | Lower bound | Gap | Proven optimal |
|---|---|---|---|---|---|---|---|
| S1 | P | 6 | 5,878,715 | 6 | 5,611,567 | 267,148 (4.54%) | no |
| S2 | P | 5 | 5,921,875 | 5 | 5,619,119 | 302,756 (5.11%) | no |
| S3 | P (no C1) | 6 | 8,075,675 | 6 | 7,870,100 | 205,575 (2.55%) | no |
| S4 | A | 6 | 7,535,670 | 5 | 6,898,889 | 636,781 (8.45%) | no |
| S5 | A | 5 | 7,535,670 | 5 | 6,898,889 * | 636,781 (8.45%) | no |

\* S5's own Lagrangian bound was 6,898,120. Any S5 layout is also feasible for S4, so the larger S4 bound applies to S5 as well.

The bound is not equal to the cost in any scenario, so **no cost is claimed as proven optimal**.

The independent checker (`checker.py`) accepted all five layouts and recomputed the same costs. It rejected each of the three broken S1 variants with the intended rule:

- CROSSING: T02–T15 crosses T07–T12.
- CAPACITY: T19–T27 carries load 8 but is labelled C1.
- LENGTH: T01–T02 is 1681 m.

## 3. Method

- **Optimizer: simulated annealing over feasible trees.** One move cuts the branch below a turbine *i*, re-roots it at any turbine *k* of that branch, and attaches *k* to a neighbour outside it.
  - Moves are rejected if they cross a cable (precomputed crossing bitmasks), exceed capacity 14, or use an edge longer than 1300 m.
  - Feeders above B are penalised.
  - Each scenario got 8 to 24 restarts of 3–6 M moves, then re-annealing from the best tree.
  - Layouts found for one scenario were also tried in the others where feasible. This is how S5 and S4 converged to the same tree.
  - Wall time was roughly 3–4 minutes per scenario per pass on about 2–4 shared cores, and three passes were run in total (`run_log*.txt`).
- **Lower bound: Lagrangian relaxation.**
  - Each turbine chooses one outgoing arc, a cable type and an integer load in that type's range. The chosen arcs must form a spanning arborescence, which Edmonds' algorithm finds exactly.
  - Flow conservation (load = 1 + children's loads) is dualised with free multipliers, and the feeder limit with π ≥ 0.
  - Violated crossing pairs are added as relax-and-cut constraints; they barely moved the bound.
  - Subgradient ascent took 4000 iterations (6–15 s). The final dual value is recomputed in exact rational arithmetic and rounded up.
  - This bound is essentially the LP of a capacity-indexed formulation. Its weakness is that it convexifies the stepped cable price: between loads 4 and 14 it pays about 14.5 per metre per turbine instead of 60 or 85 per metre at the steps. That is why the gaps are largest at platform A, where loads are high on long cables.

## 4. Losing a feeder bay

- **Platform P (S2 against S1): +43,160, or +0.73%.**
  - In S1, the six feeders carry loads 8, 8, 8, 13, 13 and 14, and are 206, 608, 691, 734, 1048 and 1120 m long.
  - S2 keeps the five shortest feeder routes (206 to 1048 m) and drops the 1120 m one. Its feeder loads become 12, 13, 13, 13 and 13.
  - Three feeders that ran C2 at 160/m with load 8 must now carry 12–13 turbines on C3 at 245/m. Turbines are also re-strung so each string reaches a remaining bay: total length goes from 52,023 m to 52,070 m.
  - The extra C3 and re-stringing cost more than the 1120 m feeder saved. The penalty is small because 5 × 14 = 70 still leaves 6 spare slots for 64 turbines.
- **Platform A (S5 against S4): 0.**
  - My best S4 layout already uses only 5 of its 6 bays. Its feeder loads are 8, 14, 14, 14 and 14, and its feeders are 683–2259 m long.
  - Platform A lies west of the whole array. A sixth feeder would be a long extra run, which costs more than it saves, so losing the sixth bay costs nothing in my results.
  - Caveat: S4 is not proven optimal (gap 8.45%). If a better 6-feeder S4 layout exists, the true S5 − S4 difference would be positive.

## 5. Removing the smallest cable type (S3 against S1): +2,196,960 (+37.4%)

- Without C1, every lightly loaded cable (loads 1–4) must use C2 at 160/m instead of 100/m.
- In the S1 layout, 54 of the 64 cables, 43,944 m in all, are C1. Simply re-labelling them would add 60 × 43,944 = 2,636,640.
- Re-optimizing recovers about 440k of that. C2's price is flat for loads 1–8, so a string can collect up to 8 turbines before any upgrade is needed. The S3 layout therefore follows shorter, more MST-like connections: 49,275 m of cable against 52,023 m in S1.
- The S3 layout still uses C3 on four feeders (2,255 m), but no load band below 9 has a cheaper option.
- The cost floor rises because most of the farm's cable metres are low-load spans, and 60 extra per metre on roughly 47 km dominates.

## 6. The alternative platform (S4 against S1): +1,656,955 (+28.2%)

- P sits near the centre of the array. The straight-line distance from turbines to P averages 2,467 m, totalling 157,890 m.
- A is off the west edge. The distance from turbines to A averages 4,035 m (maximum 7,147 m), totalling 258,245 m, about 64% more.
- All power must therefore travel further, and it travels on heavy cable:
  - Σ load × length rises from 179,181 to 279,241 turbine-metres.
  - C3 usage rises from 2,255 m to 10,066 m.
  - C2 usage rises from 5,824 m to 9,410 m.
  - Feeders total 6,549 m against 4,407 m.
  - Total cable length rises from 52,023 m to 55,115 m.
- The packet's 1300 m turbine-to-turbine limit, and the ban on crossings, force the eastern turbines to reach A through chains of turbines. That builds long, fully loaded (14) C3 trunks across the field.

## 7. Comparison with a simple greedy layout (S1)

- An Esau–Williams savings greedy gives a valid S1 layout costing **6,177,435** (`greedy_EW_S1.json`). It handles crossings, capacity, the length limit and the feeder limit, and the checker confirms the layout is valid.
- The optimized S1 layout costs **5,878,715**: 298,720 cheaper, or 4.8% below the greedy.
- The greedy commits early to merges that later block cheaper non-crossing strings.
- The same greedy could not reach a feasible layout within the feeder limit for S2–S5, because it ends with more than B branches. Another simple greedy, a capacitated Prim from the platform, got stuck in every scenario: crossings blocked connections for the remaining turbines.

## 8. Ambiguities and assumptions

- **Platform and catalogue readings.** I took these from the rasters as stated above. Exact integers were assumed because the packet says all costs are whole numbers.
- **The 1300 m limit.** I applied it to the rounded length. No turbine pair lies between 1300.0 and 1300.5 m, so the choice makes no difference.
- **Crossings at turbines and the platform.** A cable passing through a turbine or the platform always touches another cable there, so I treat it as infeasible. No such edge exists among usable lengths that a layout would need.
- **The empty platform position.** I ignore it, as the packet instructs.
- **Feeders used.** This is the number of cables ending at the platform.

## 9. Reproduction (from this directory, offline, Python ≥ 3.8)

```
python3 optimizer.py --seeds 8 --iters 3000000 --T0 100000 --T1 200                   # pass 1, all scenarios
python3 optimizer.py --keep-best --scenarios S5,S4,S2,S1,S3 --seed-base 2000 --seeds 8 --iters 6000000 --T0 150000 --T1 200   # pass 2
python3 optimizer.py --keep-best --scenarios S4,S5,S2 --seed-base 3000 --seeds 8 --iters 6000000 --T0 150000 --T1 200  # pass 3
./run_checks.sh          # writes broken_*.json and checker_output.txt
python3 analyze.py       # writes results_table.md, analysis.txt
python3 checker.py layout_S1.json   # check any single layout
```

Results are deterministic for a fixed seed list. Each pass overwrites a layout only when it finds a cheaper one.
