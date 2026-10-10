# FIRE-15 rubric

49 criteria; positive weight 143; whole-space items carry 100 (69.9%). Longest criterion 186 characters.

| # | Weight | Criterion |
|---|---|---|
| 1 | +1 | States the cover of cell (100, 36) as houses (H). |
| 2 | +1 | States the cover of cell (76, 62) as rock (R). |
| 3 | +1 | States the coordinates of station S14 as x = 100, y = 92. |
| 4 | +1 | States the lightning strike rate of scenario D as 145 per mille per step. |
| 5 | +1 | States that in scenario C, period 3 (steps 240-359), the wind blows toward the southwest (SW). |
| 6 | +1 | Records the exact language and runtime version used (for example "Python 3.11.4"), not only the language name. |
| 7 | +1 | Gives concrete commands that rerun its simulator and its checker to reproduce the reported results. |
| 8 | +2 | Reports the baseline plan's (crews 1-7 at S1, S4, S5, S8, S9, S12, S13) scenario A loss as exactly 1,992. |
| 9 | +2 | Reports the baseline plan's (crews 1-7 at S1, S4, S5, S8, S9, S12, S13) scenario B loss as exactly 4,240. |
| 10 | +2 | Reports the baseline plan's (crews 1-7 at S1, S4, S5, S8, S9, S12, S13) scenario C loss as exactly 3,455. |
| 11 | +2 | Reports the baseline plan's (crews 1-7 at S1, S4, S5, S8, S9, S12, S13) scenario D loss as exactly 4,079. |
| 12 | +3 | Reports the baseline plan's (crews 1-7 at S1, S4, S5, S8, S9, S12, S13) total loss over scenarios A-D as exactly 13,766. |
| 13 | +3 | Reports the total loss of the baseline with crew 7 at S6 instead of S13 (crews 1-7 at S1, S4, S5, S8, S9, S12, S6) as exactly 10,956. |
| 14 | +3 | Reports the total loss of the plan with all seven crews at station S6 as exactly 18,683. |
| 15 | +4 | Identifies the optimal plan (smallest total loss; ties to the smaller station number for crew 1, then crew 2, and so on) as crews 1-7 at S14, S14, S8, S5, S3, S9, S7. |
| 16 | +3 | Reports the optimal plan's (crews 1-7 at S14, S14, S8, S5, S3, S9, S7) total loss as exactly 6,012. |
| 17 | +10 | Reports the sum of total loss over all 105,413,504 plans as exactly 1,517,929,184,378. |
| 18 | +10 | Reports the number of plans, out of 105,413,504, whose total loss is below the baseline's 13,766 as exactly 43,983,052. |
| 19 | +10 | Reports the number of plans whose loss is below the baseline's in every scenario (A below 1,992, B below 4,240, C below 3,455 and D below 4,079) as exactly 6,249,692. |
| 20 | +5 | Reports the number of plans with crew 7 at station S1 whose total loss is below 13,766 as exactly 2,174,072. |
| 21 | +5 | Reports the number of plans with crew 7 at station S2 whose total loss is below 13,766 as exactly 2,158,112. |
| 22 | +5 | Reports the number of plans with crew 7 at station S3 whose total loss is below 13,766 as exactly 2,555,816. |
| 23 | +5 | Reports the number of plans with crew 7 at station S4 whose total loss is below 13,766 as exactly 3,871,595. |
| 24 | +5 | Reports the number of plans with crew 7 at station S5 whose total loss is below 13,766 as exactly 3,520,222. |
| 25 | +5 | Reports the number of plans with crew 7 at station S6 whose total loss is below 13,766 as exactly 2,939,457. |
| 26 | +5 | Reports the number of plans with crew 7 at station S7 whose total loss is below 13,766 as exactly 3,072,734. |
| 27 | +5 | Reports the number of plans with crew 7 at station S8 whose total loss is below 13,766 as exactly 3,459,276. |
| 28 | +5 | Reports the number of plans with crew 7 at station S9 whose total loss is below 13,766 as exactly 4,733,649. |
| 29 | +5 | Reports the number of plans with crew 7 at station S10 whose total loss is below 13,766 as exactly 3,254,170. |
| 30 | +5 | Reports the number of plans with crew 7 at station S11 whose total loss is below 13,766 as exactly 2,576,242. |
| 31 | +5 | Reports the number of plans with crew 7 at station S12 whose total loss is below 13,766 as exactly 3,867,226. |
| 32 | +5 | Reports the number of plans with crew 7 at station S13 whose total loss is below 13,766 as exactly 2,735,811. |
| 33 | +5 | Reports the number of plans with crew 7 at station S14 whose total loss is below 13,766 as exactly 3,064,670. |
| 34 | +1 | The checker's recorded output reports that in the baseline scenario A trace no cell is ignited more than once. |
| 35 | +1 | The checker's recorded output reports that every spread ignition in the baseline scenario A trace is next to a cell of the same fire that was burning when that step's spread phase began. |
| 36 | +1 | The checker's recorded output reports that in the baseline scenario A trace no crew puts out more than its capacity in a step or any cell outside the fire it is working on. |
| 37 | +2 | The checker's recorded output reports checking exactly 980 spread ignitions in the baseline scenario A trace. |
| 38 | +1 | The checker's recorded output rejects the altered trace with a spread ignition moved to a cell with no burning neighbour of its fire, naming the spread-adjacency invariant as violated. |
| 39 | +1 | The checker's recorded output rejects the altered trace with a crew putting out one cell more than its capacity in a step, naming the crew-capacity invariant as violated. |
| 40 | +2 | The memo identifies crew 6 as the crew whose station changes the average total loss across the plan space the most. |
| 41 | +1 | The memo names S9 as the best station for crew 7, the station with the most plans below the baseline (4,733,649). |
| 42 | +1 | The memo names S2 as the worst station for crew 7, the station with the fewest plans below the baseline (2,158,112). |
| 43 | -10 | Uses a third-party package or external tool (for example NumPy, FARSITE, FlamMap) to compute any simulation result. |
| 44 | -8 | Reports a whole-space sum or count over the 105,413,504 plans as an exact value when its own report or code shows it simulated fewer plans than that. |
| 45 | -6 | Calls its reported plan optimal (rather than the best found) when its own report or code shows it simulated fewer than all 105,413,504 plans. |
| 46 | -5 | The checker imports, calls or copies code from the simulator instead of being separately coded. |
| 47 | -8 | Hard-codes any reported simulation result (a loss, count or sum) as a literal in its delivered source code instead of computing it by running its simulator. |
| 48 | -5 | Accesses the internet or any external source (packages, code, documentation or results) while building or running its simulator or checker. |
| 49 | +1 | Delivers as files a simulator source, a separately coded checker source, a baseline scenario A trace, a results file and an engineering memo. |

## Atomicity and self-containment check

Each criterion checks one value, one claim or one requirement, and states the expected answer with the plan or scenario it applies to, so a grader needs nothing else. Lengths:

| # | Atomic | Self-contained | Characters |
|---|---|---|---|
| 1 | yes | yes | 49 |
| 2 | yes | yes | 46 |
| 3 | yes | yes | 57 |
| 4 | yes | yes | 73 |
| 5 | yes | yes | 94 |
| 6 | yes | yes | 110 |
| 7 | yes | yes | 99 |
| 8 | yes | yes | 105 |
| 9 | yes | yes | 105 |
| 10 | yes | yes | 105 |
| 11 | yes | yes | 105 |
| 12 | yes | yes | 120 |
| 13 | yes | yes | 133 |
| 14 | yes | yes | 88 |
| 15 | yes | yes | 166 |
| 16 | yes | yes | 99 |
| 17 | yes | yes | 86 |
| 18 | yes | yes | 119 |
| 19 | yes | yes | 166 |
| 20 | yes | yes | 108 |
| 21 | yes | yes | 108 |
| 22 | yes | yes | 108 |
| 23 | yes | yes | 108 |
| 24 | yes | yes | 108 |
| 25 | yes | yes | 108 |
| 26 | yes | yes | 108 |
| 27 | yes | yes | 108 |
| 28 | yes | yes | 108 |
| 29 | yes | yes | 109 |
| 30 | yes | yes | 109 |
| 31 | yes | yes | 109 |
| 32 | yes | yes | 109 |
| 33 | yes | yes | 109 |
| 34 | yes | yes | 110 |
| 35 | yes | yes | 186 |
| 36 | yes | yes | 172 |
| 37 | yes | yes | 109 |
| 38 | yes | yes | 184 |
| 39 | yes | yes | 170 |
| 40 | yes | yes | 115 |
| 41 | yes | yes | 113 |
| 42 | yes | yes | 116 |
| 43 | yes | yes | 115 |
| 44 | yes | yes | 149 |
| 45 | yes | yes | 141 |
| 46 | yes | yes | 95 |
| 47 | yes | yes | 156 |
| 48 | yes | yes | 139 |
| 49 | yes | yes | 141 |

## Reverse coverage

- Figure values asked in the prompt: criteria 1-5. Runtime version and commands: 6-7.
- Baseline per scenario and total: 8-12. The two variants: 13-14. Optimum and its loss: 15-16.
- Whole-space sum, below-baseline count, below in all four scenarios: 17-19. Crew 7 per-station counts: 20-33.
- Checker invariants, count and the two altered traces: 34-39. Memo questions: 40-42.
- "Call it optimal only if...": negative 45; exact whole-space values from a partial run: negative 44. Standard library: 43. Separate checker: 46. Own executed programs: 47. Offline: 48. Deliverables: 49.

## Reviewer-feedback audit

| Past problem | Here |
|---|---|
| Expected value outside the allowed set | Every value comes from the answer key or the reference engines; the optimum's stations are legal |
| Value that needs an unstated rule | All rules are in the packet text; blind probe checks reproduction |
| Required explanation not graded | Each memo question has its own criterion (40-42) |
| Bundled facts | One value per criterion |
| Undefined metric | Loss, burnt cell, spread ignition and "below the baseline" are defined in the packet or criterion |
| Validity-only or presence-only criteria | None; every number is graded as an exact value |
| Prompt rule with no penalty | Optimal-claim and partial-exact penalties (44, 45), judged from the run's own report or code |
