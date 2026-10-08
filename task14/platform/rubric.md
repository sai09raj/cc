# GRID-14 rubric (v1, packet grid14_v1.pdf)

Positive total **135**; six negative criteria. **50 criteria**, weights within -10..+10, bodies of 301 characters or fewer, one value, claim or requirement each. Accept any language, organization and format; numbers with or without separators.

Answer key: exhaustive simulation of all 18,874,368 configurations with `proto/cgrid_fast.c` (36 cloud workers, 144 part files, `proto/aggregate.py` -> `reference/aggregate.json`). The fast C, cell-scan C, JavaScript and Python engines agree exactly on every compared configuration.

Score topology: whole-space criteria carry 87/135 = 64.4 % of positive weight; a run with a correct simulator, correct optimum, checker and memo but no exhaustive sweep earns at most 48/135 = 35.6 %. The three zero-valued cycle counts (96, 108, 120 s) carry +1 each because a sample guesses them.


## Values read from the figures

| # | Wt | Criterion |
|---|---|---|
| 1 | +1 | States the block between I0 and I1 as 32 cells long (240 m). |
| 2 | +1 | States the block between I4 and I5 as 36 cells long (270 m). |
| 3 | +1 | States the block between I2 and I5 as 27 cells long (202.5 m). |
| 4 | +1 | States the block between I5 and I8 as 21 cells long (157.5 m). |
| 5 | +1 | States the inbound boundary link at T1 as 44 cells long (330 m). |
| 6 | +1 | States the inbound boundary link at T8 as 45 cells long (337.5 m). |
| 7 | +1 | States the EVENT demand at terminal T9 as 395 vehicles per hour. |

## Package

| # | Wt | Criterion |
|---|---|---|
| 8 | +1 | Records the exact language and runtime version used (for example "Node.js v20.11.1"), not only the language name. |
| 9 | +1 | Gives concrete commands that rerun its simulator and its checker to reproduce the reported results. |

## Baseline and variants

| # | Wt | Criterion |
|---|---|---|
| 10 | +2 | Reports the baseline's (cycle 84 s, plan 1, lead, all offsets 0) AM TTS as exactly 1,138,089 vehicle-seconds. |
| 11 | +2 | Reports the baseline's (cycle 84 s, plan 1, lead, all offsets 0) PM TTS as exactly 1,097,366 vehicle-seconds. |
| 12 | +2 | Reports the baseline's (cycle 84 s, plan 1, lead, all offsets 0) EVENT TTS as exactly 1,817,193 vehicle-seconds. |
| 13 | +3 | Reports the baseline's (cycle 84 s, plan 1, lead, all offsets 0) total TTS as exactly 4,052,648 vehicle-seconds. |
| 14 | +3 | Reports the total TTS of the baseline with offsets 0, 21, 42 s for the intersections of each row from west to east (cycle 84 s, plan 1, lead) as exactly 3,901,019. |
| 15 | +3 | Reports the total TTS of the baseline with lag instead of lead (cycle 84 s, plan 1, all offsets 0) as exactly 4,281,802. |
| 16 | +3 | Reports the total TTS of the baseline with a cycle of 60 s instead of 84 s (plan 1, lead, all offsets 0) as exactly 2,136,688. |

## Optimal configuration

| # | Wt | Criterion |
|---|---|---|
| 17 | +4 | Identifies the optimal configuration (smallest total TTS; ties by cycle, plan, lead before lag, offsets of I0..I8) as cycle 60 s, plan 6, lag, offsets I0..I8 = 0, 45, 15, 30, 0, 30, 15, 30, 0 s. |
| 18 | +3 | Reports the optimal configuration's (cycle 60 s, plan 6, lag, offsets 0, 45, 15, 30, 0, 30, 15, 30, 0 s) total TTS as exactly 1,829,597 vehicle-seconds. |

## Whole-space characterization ("below the baseline" = total TTS less than 4,052,648)

| # | Wt | Criterion |
|---|---|---|
| 19 | +10 | Reports the sum of total TTS over all 18,874,368 configurations as exactly 123,858,216,502,180 vehicle-seconds. |
| 20 | +10 | Reports the number of configurations, out of 18,874,368, whose total TTS is below the baseline's 4,052,648 as exactly 7,425,123. |
| 21 | +10 | Reports the number of configurations, out of 18,874,368, that gridlock (a run ends at step 7199 with vehicles left) as exactly 5,485,845. |
| 22 | +6 | Reports the number of configurations with cycle 60 s whose total TTS is below 4,052,648 as exactly 3,145,241. |
| 23 | +6 | Reports the number of configurations with cycle 72 s whose total TTS is below 4,052,648 as exactly 3,126,728. |
| 24 | +6 | Reports the number of configurations with cycle 84 s whose total TTS is below 4,052,648 as exactly 1,153,154. |
| 25 | +1 | Reports the number of configurations with cycle 96 s whose total TTS is below 4,052,648 as exactly 0. |
| 26 | +1 | Reports the number of configurations with cycle 108 s whose total TTS is below 4,052,648 as exactly 0. |
| 27 | +1 | Reports the number of configurations with cycle 120 s whose total TTS is below 4,052,648 as exactly 0. |
| 28 | +6 | Reports the number of configurations with plan 1 whose total TTS is below 4,052,648 as exactly 1,188,148. |
| 29 | +6 | Reports the number of configurations with plan 2 whose total TTS is below 4,052,648 as exactly 1,278,030. |
| 30 | +6 | Reports the number of configurations with plan 3 whose total TTS is below 4,052,648 as exactly 1,265,778. |
| 31 | +6 | Reports the number of configurations with plan 4 whose total TTS is below 4,052,648 as exactly 1,146,190. |
| 32 | +6 | Reports the number of configurations with plan 5 whose total TTS is below 4,052,648 as exactly 1,208,142. |
| 33 | +6 | Reports the number of configurations with plan 6 whose total TTS is below 4,052,648 as exactly 1,338,835. |

## Checker

| # | Wt | Criterion |
|---|---|---|
| 34 | +1 | The checker's recorded output reports that in the baseline AM trace no cell ever holds two vehicles. |
| 35 | +1 | The checker's recorded output reports that in the baseline AM trace every stop-line crossing happens during a green for that vehicle's movement. |
| 36 | +1 | The checker's recorded output reports that at every step of the baseline AM trace vehicles created equal vehicles waiting plus in the network plus departed. |
| 37 | +2 | The checker's recorded output reports checking exactly 8,136 stop-line crossings in the baseline AM trace. |
| 38 | +1 | The checker's recorded output rejects the altered baseline AM trace with a crossing moved into a red interval, naming the green-crossing invariant as violated. |
| 39 | +1 | The checker's recorded output rejects the altered baseline AM trace with two vehicles in one cell, naming the one-vehicle-per-cell invariant as violated. |

## Memo

| # | Wt | Criterion |
|---|---|---|
| 40 | +2 | The memo identifies the cycle length as the knob with the largest effect on total TTS, larger than the plan, the phase order or the offsets. |
| 41 | +2 | The memo attributes the best configuration's advantage mainly to its 60 s cycle, the cycle length with the lowest average total TTS across the space. |
| 42 | +1 | The memo states that a longer cycle raises the average total TTS across the configuration space. |
| 43 | +1 | The memo states that lag gives a higher average total TTS than lead across the configuration space. |

## Negative criteria

| # | Wt | Criterion |
|---|---|---|
| 44 | -10 | Uses a third party package or external tool (for example NumPy, SUMO, VISSIM, Aimsun) to compute any simulation result. |
| 45 | -8 | Reports a whole-space sum or count over the 18,874,368 configurations while stating it simulated fewer configurations than that (an estimate or extrapolation presented as the value). |
| 46 | -6 | Calls its reported configuration optimal (rather than the best found) while stating it simulated fewer than all 18,874,368 configurations. |
| 47 | -5 | The checker imports, calls or copies code from the simulator instead of being separately coded. |
| 48 | -8 | Hard codes any reported simulation result (a TTS, count or sum) as a literal in its delivered source code instead of computing it by running its simulator. |
| 49 | -5 | Accesses the internet or any external source (packages, code, documentation or results) while building or running its simulator or checker. |

## Package completeness (contents graded by the sections above)

| # | Wt | Criterion |
|---|---|---|
| 50 | +1 | Delivers as files a simulator source, a separately coded checker source, a baseline AM trace, a results file and an engineering memo. |

## Reverse coverage

| Prompt requirement | Criteria |
|---|---|
| State the listed figure values | 1-7 |
| Runtime version, reproduction commands | 8-9 |
| Baseline AM, PM, EVENT and total TTS; three variants | 10-16 |
| Optimal configuration and its total TTS | 17-18 |
| Sum of total TTS; count below baseline; gridlock count | 19-21 |
| Count below baseline for each cycle and for each plan | 22-33 |
| Separate checker: three invariants, crossings checked, two altered traces | 34-39, 47 |
| Memo: largest knob, why the best wins, cycle and phase-order effects | 40-43 |
| Standard library only, offline | 44, 49 |
| Call it optimal only if all configurations simulated; number simulated | 45, 46 |
| Base every number on your own executed programs | 48 |
| Deliver the five files | 50 |

