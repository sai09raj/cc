# GRID-14 results

All numbers come from programs I ran: `grid14_sim.js` / `grid14_explore.js` (Node.js v22.22.2), and `grid14_checker.py` / `grid14_analyze.py` / `grid14_report.py` (Python 3.11.15). Reproduction commands are in `README.md`.

## 1. Values read from the figures

Cell length 7.5 m. Cells = metres / 7.5; every length gives a whole number of cells.

**Street blocks (Figure 1; each block is two links, one per direction, of equal length)**

| Block | Length (m) | Cells |
|---|---:|---:|
| I0–I1 | 240 | 32 |
| I1–I2 | 195 | 26 |
| I3–I4 | 165 | 22 |
| I4–I5 | 270 | 36 |
| I6–I7 | 210 | 28 |
| I7–I8 | 180 | 24 |
| I0–I3 | 225 | 30 |
| I3–I6 | 150 | 20 |
| I1–I4 | 180 | 24 |
| I4–I7 | 255 | 34 |
| I2–I5 | 202.5 | 27 |
| I5–I8 | 157.5 | 21 |

**Inbound boundary links (Figure 1, labelled "in")**

| Terminal | Feeds | Approach side | Length (m) | Cells |
|---|---|---|---:|---:|
| T0 | I0 | N | 285 | 38 |
| T1 | I1 | N | 330 | 44 |
| T2 | I2 | N | 270 | 36 |
| T3 | I2 | E | 307.5 | 41 |
| T4 | I5 | E | 262.5 | 35 |
| T5 | I8 | E | 322.5 | 43 |
| T6 | I6 | S | 292.5 | 39 |
| T7 | I7 | S | 277.5 | 37 |
| T8 | I8 | S | 337.5 | 45 |
| T9 | I0 | W | 315 | 42 |
| T10 | I3 | W | 300 | 40 |
| T11 | I6 | W | 270 | 36 |

Outbound boundary links: 10 cells each (Section 2). The simulator built exactly these lengths; `node grid14_sim.js network` prints them:

```
0 in:T0->I0 38
1 in:T1->I1 44
2 in:T2->I2 36
3 in:T3->I2 41
4 in:T4->I5 35
5 in:T5->I8 43
6 in:T6->I6 39
7 in:T7->I7 37
8 in:T8->I8 45
9 in:T9->I0 42
10 in:T10->I3 40
11 in:T11->I6 36
12 I0->I1 32
13 I1->I0 32
14 I1->I2 26
15 I2->I1 26
16 I3->I4 22
17 I4->I3 22
18 I4->I5 36
19 I5->I4 36
20 I6->I7 28
21 I7->I6 28
22 I7->I8 24
23 I8->I7 24
24 I0->I3 30
25 I3->I0 30
26 I3->I6 20
27 I6->I3 20
28 I1->I4 24
29 I4->I1 24
30 I4->I7 34
31 I7->I4 34
32 I2->I5 27
33 I5->I2 27
34 I5->I8 21
35 I8->I5 21
36 out:I0->T0 10
37 out:I0->T9 10
38 out:I1->T1 10
39 out:I2->T2 10
40 out:I2->T3 10
41 out:I3->T10 10
42 out:I5->T4 10
43 out:I6->T6 10
44 out:I6->T11 10
45 out:I7->T7 10
46 out:I8->T5 10
47 out:I8->T8 10
AM vehicles 2728
PM vehicles 2740
EVENT vehicles 2978
```

**Demand (Figure 2, veh/h)**

| Scenario | T0 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10 | T11 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AM | 208 | 266 | 182 | 234 | 195 | 254 | 221 | 176 | 273 | 247 | 202 | 228 |
| PM | 221 | 176 | 273 | 247 | 202 | 228 | 208 | 266 | 182 | 234 | 195 | 254 |
| EVENT | 208 | 266 | 182 | 234 | 312 | 254 | 221 | 176 | 273 | 395 | 202 | 228 |

**Turning shares (Figure 3)**: arrivals from north or south: left 20 %, through 65 %, right 15 %. Arrivals from west or east: left 10 %, through 75 %, right 15 %. Left and right are taken from the driver's point of view; the figure shows a southbound arrival with left going east and right going west, and an eastbound arrival with left going north and right going south.

**Phases (Figure 3)**: A = N and S approaches, through and right; B = N and S approaches, left; C = E and W approaches, through and right; D = E and W approaches, left. Each phase is protected, and each green is followed by a 2 s all-red. Sequence from local time 0: **lead A, B, C, D**; **lag B, A, D, C**.

**Green times (Figure 4, A/B/C/D in seconds)**; in every row, greens + 4 × 2 s all-red = C:

| C | Plan 1 | Plan 2 | Plan 3 | Plan 4 | Plan 5 | Plan 6 |
|---|---|---|---|---|---|---|
| 60 | 18/8/18/8 | 22/6/18/6 | 16/7/22/7 | 20/9/16/7 | 16/7/20/9 | 21/5/21/5 |
| 72 | 22/10/22/10 | 27/8/22/7 | 20/9/27/8 | 25/11/20/8 | 20/8/25/11 | 26/6/26/6 |
| 84 | 26/12/26/12 | 32/9/26/9 | 23/11/32/10 | 29/14/23/10 | 23/11/29/13 | 31/7/31/7 |
| 96 | 30/14/30/14 | 37/11/30/10 | 27/12/37/12 | 34/15/27/12 | 27/12/34/15 | 36/8/36/8 |
| 108 | 34/16/34/16 | 42/12/34/12 | 30/14/42/14 | 38/18/30/14 | 30/14/38/18 | 40/10/40/10 |
| 120 | 39/17/39/17 | 48/13/38/13 | 34/15/48/15 | 43/20/34/15 | 34/15/43/20 | 45/11/45/11 |

## 2. Baseline (C = 84 s, plan 1, lead, all offsets 0)

| Scenario | TTS (veh·s) | Vehicles | Run ended at step |
|---|---:|---:|---:|
| AM | 1,138,089 | 2,728 | 4966 |
| PM | 1,097,366 | 2,740 | 5092 |
| EVENT | 1,817,193 | 2,978 | 4924 |
| **Total** | **4,052,648** | | |

The baseline does not gridlock.

## 3. Variants of the baseline (only the named knob changed)

| Variant | AM | PM | EVENT | Total TTS | Change from baseline |
|---|---:|---:|---:|---:|---:|
| Baseline | 1,138,089 | 1,097,366 | 1,817,193 | **4,052,648** | +0.0 % |
| Offsets 0, 21, 42 s from west to east in each row (I0, I3, I6 = 0; I1, I4, I7 = 21; I2, I5, I8 = 42) | 1,103,417 | 1,079,152 | 1,718,450 | **3,901,019** | -3.7 % |
| Lag instead of lead | 1,220,254 | 1,189,409 | 1,872,139 | **4,281,802** | +5.7 % |
| Cycle 60 s instead of 84 s (plan 1, lead, offsets 0) | 661,621 | 641,862 | 833,205 | **2,136,688** | -47.3 % |

None of the variants gridlocks.

## 4. Whole configuration space (18,874,368 configurations)

**Configurations actually simulated: 893,362 distinct configurations (4.73 % of the space), each on all three scenarios.** Not all 18,874,368 were simulated. At about 25 ms per configuration on the 4 available cores, a full census needs about 33 hours, against a 2.5-hour limit. The whole-space figures below are therefore **estimates, not exact counts**. They come from a stratified uniform random sample: 108,000 configurations, 1,500 drawn uniformly (with replacement) from the 4^9 offset vectors of each of the 72 equal-sized (cycle, plan, order) groups. The groups enumerated completely, (60 s, plan 2, lag), (60 s, plan 6, lag), (60 s, plan 6, lead), enter the estimates with their exact values. Intervals are 95 % normal-approximation confidence intervals for the stratified estimator; counts are clipped to the size of their group.

| Item | Result |
|---|---|
| Sum of total TTS over all configurations | ≈ 123,991,232,331,031 (95 % CI 123,789,662,572,853 – 124,192,802,089,209) veh·s, i.e. ≈ 1.2399e+14 |
| Mean total TTS per configuration | ≈ 6,569,292 veh·s |
| Number with total TTS below the baseline (< 4,052,648) | ≈ 7,415,008 (95 % CI 7,393,605 – 7,436,411) |
| Number that gridlock | ≈ 5,478,296 (95 % CI 5,446,268 – 5,510,323) |

**Configurations below the baseline, by cycle length** (3,145,728 configurations per cycle)

| Cycle (s) | Configurations below baseline | Gridlocking configurations |
|---|---|---|
| 60 | ≈ 3,145,032 (95 % CI 3,144,439 – 3,145,625) | ≈ 709 (95 % CI 116 – 1,302) |
| 72 | ≈ 3,123,883 (95 % CI 3,120,079 – 3,127,687) | ≈ 20,272 (95 % CI 16,606 – 23,939) |
| 84 | ≈ 1,146,094 (95 % CI 1,125,039 – 1,167,148) | ≈ 305,485 (95 % CI 292,368 – 318,602) |
| 96 | 0 in the sample (95 % upper bound ≈ 524) | ≈ 885,173 (95 % CI 867,455 – 902,891) |
| 108 | 0 in the sample (95 % upper bound ≈ 524) | ≈ 1,389,713 (95 % CI 1,370,420 – 1,409,006) |
| 120 | 0 in the sample (95 % upper bound ≈ 524) | ≈ 2,876,943 (95 % CI 2,864,544 – 2,889,342) |

**Configurations below the baseline, by timing plan** (3,145,728 configurations per plan)

| Plan | Configurations below baseline |
|---|---|
| 1 | ≈ 1,192,406 (95 % CI 1,183,866 – 1,200,945) |
| 2 | ≈ 1,272,892 (95 % CI 1,263,550 – 1,282,235) |
| 3 | ≈ 1,266,505 (95 % CI 1,257,355 – 1,275,655) |
| 4 | ≈ 1,147,317 (95 % CI 1,139,784 – 1,154,850) |
| 5 | ≈ 1,209,882 (95 % CI 1,201,385 – 1,218,379) |
| 6 | ≈ 1,326,006 (95 % CI 1,316,774 – 1,335,238) |

Exact counts among the configurations actually simulated (this is not a whole-space figure): 827,809 below the baseline, 31,440 gridlock, and total TTS summed over them = 2,280,565,224,337 veh·s.

**Groups enumerated completely (exact over all 262,144 offset vectors)**

| Group | Sum of total TTS | Below baseline | Gridlock | Min | Mean | Max |
|---|---:|---:|---:|---:|---:|---:|
| 60-2-lag | 530,582,714,879 | 262,065 | 84 | 1,885,219 | 2,024,012 | 8,162,570 |
| 60-6-lag | 515,681,542,882 | 262,052 | 100 | 1,829,597 | 1,967,169 | 8,009,194 |
| 60-6-lead | 526,870,928,807 | 262,143 | 1 | 1,877,587 | 2,009,853 | 7,710,706 |

## 5. Optimum

**Best configuration found (not proven optimal, because only 893,362 of 18,874,368 configurations were simulated):**

* C = 60 s, plan 6, lag, offsets I0..I8 = 0, 45, 15, 30, 0, 30, 15, 30, 0 s
* AM 581,162 + PM 562,701 + EVENT 685,734 = **total TTS 1,829,597 veh·s** (no gridlock), -54.9 % against the baseline

Search used: (i) the stratified sample of all 72 groups; (ii) complete enumeration of all 4^9 offset vectors in the groups listed above, the three groups with the lowest sampled mean total TTS; (iii) coordinate descent over the offsets (one intersection at a time, all 4 values, repeated until no change), started from the 4 best sampled configurations of each of the other 22 groups with C = 60 or 72 s. Within the completely enumerated groups, the configuration above is exact under the packet's tie-break. No search in any other group found a better total.

Fifteen best configurations simulated (ties broken as in the packet):

| # | C | Plan | Order | Offsets I0..I8 | AM | PM | EVENT | Total |
|---|---|---|---|---|---:|---:|---:|---:|
| 1 | 60 | 6 | lag | 0,45,15,30,0,30,15,30,0 | 581,162 | 562,701 | 685,734 | 1,829,597 |
| 2 | 60 | 6 | lag | 0,45,15,45,30,0,15,0,15 | 579,859 | 557,581 | 695,623 | 1,833,063 |
| 3 | 60 | 6 | lag | 0,45,15,45,30,0,15,45,15 | 579,359 | 556,409 | 697,756 | 1,833,524 |
| 4 | 60 | 6 | lag | 0,45,15,15,0,30,0,45,15 | 587,065 | 560,322 | 686,494 | 1,833,881 |
| 5 | 60 | 6 | lag | 0,30,0,15,0,30,0,45,15 | 595,067 | 552,653 | 686,179 | 1,833,899 |
| 6 | 60 | 6 | lag | 0,45,15,15,0,30,45,30,0 | 585,165 | 559,598 | 689,407 | 1,834,170 |
| 7 | 60 | 6 | lag | 0,45,15,30,0,30,0,30,0 | 582,585 | 565,035 | 687,684 | 1,835,304 |
| 8 | 60 | 6 | lag | 0,45,0,30,0,30,15,30,0 | 583,522 | 557,797 | 694,014 | 1,835,333 |
| 9 | 60 | 6 | lag | 0,45,15,30,0,30,0,15,0 | 580,241 | 567,644 | 687,531 | 1,835,416 |
| 10 | 60 | 6 | lag | 15,45,15,30,15,45,15,45,15 | 582,047 | 557,727 | 696,369 | 1,836,143 |
| 11 | 60 | 6 | lag | 15,45,15,30,0,30,15,30,0 | 583,155 | 558,257 | 694,959 | 1,836,371 |
| 12 | 60 | 6 | lag | 0,45,15,15,0,30,0,30,0 | 586,175 | 565,085 | 685,857 | 1,837,117 |
| 13 | 60 | 6 | lag | 0,30,0,15,0,30,0,15,0 | 592,584 | 559,212 | 685,738 | 1,837,534 |
| 14 | 60 | 6 | lag | 0,45,15,30,15,45,0,45,0 | 583,403 | 563,114 | 691,257 | 1,837,774 |
| 15 | 60 | 6 | lag | 0,30,0,15,0,30,0,30,0 | 593,896 | 556,576 | 687,424 | 1,837,896 |

## 6. Sensitivity summaries (from the stratified sample)

Share of the variance of total TTS: cycle 74.4 %, order 4.9 %, plan 0.01 %, cycle × plan × order jointly 83.3 %, offsets (within group) 16.7 %.

| Cycle | Mean total TTS | Mean lead | Mean lag | Gridlock rate lead | Gridlock rate lag | Lowest total in sample |
|---|---:|---:|---:|---:|---:|---:|
| 60 | 2,066,470 | 2,082,477 | 2,050,463 | 0.00 % | 0.04 % | 1,859,455 |
| 72 | 2,946,287 | 2,922,664 | 2,969,910 | 0.03 % | 1.26 % | 2,554,882 |
| 84 | 4,677,482 | 4,238,238 | 5,116,726 | 2.09 % | 17.33 % | 3,572,204 |
| 96 | 7,292,478 | 5,920,453 | 8,664,503 | 5.24 % | 51.03 % | 4,985,498 |
| 108 | 9,658,429 | 7,901,623 | 11,415,235 | 17.73 % | 70.62 % | 6,448,778 |
| 120 | 12,774,201 | 10,540,806 | 15,007,595 | 84.14 % | 98.77 % | 8,341,953 |

| Plan | Mean total TTS | Order | Mean total TTS |
|---|---:|---|---:|
| 1 | 6,527,436 | lead | 5,601,043 |
| 2 | 6,524,962 | lag | 7,537,405 |
| 3 | 6,530,616 |  |  |
| 4 | 6,625,010 |  |  |
| 5 | 6,611,563 |  |  |
| 6 | 6,595,759 |  |  |

## 7. Interpretations where the specification left room

* Each of the four greens, including the last one in the sequence, is followed by its own 2 s all-red. Figure 4 confirms this: greens + 8 s = C in every row.
* Lag is read from Figure 3 as B, A, D, C, so each street gets its left phase before its through/right phase.
* Right turns are served only in the through/right phase of their approach (A or C). There is no right turn on red and no permissive left.
* A vehicle advances its own generator once on entering its inbound boundary link (cell 0, after leaving the terminal queue) and once on entering each street block. Creation does not draw, and entering an outbound boundary link does not draw. Routes are therefore independent of the signal configuration.
* Departure step e is the step in which the vehicle moves out of the last cell of its outbound link. A vehicle created at step g can enter cell 0 during the same step g.
* "Empty at the start of the step" is taken literally: a vehicle cannot move into a cell vacated in the same step, so standing queues discharge at one vehicle every 2 s.
* The run-end test is applied at the end of each step t >= 3599. Gridlock means a run reached the end of step 7199 with vehicles still waiting or in the network. Every such vehicle (including any still in a terminal queue) contributes 7200 - g.
* Simulator shortcut: if, with vehicles in the network, nothing moves for C consecutive steps and no vehicle can enter (t >= 3600, or every inbound cell 0 is occupied), the state is frozen forever. The run is then closed as if continued to step 7199, which gives identical TTS. I confirmed this against the reference model, which has no shortcut.
* Variant "offsets 0, 21 and 42 s for the intersections of each row from west to east": I0, I3, I6 = 0; I1, I4, I7 = 21; I2, I5, I8 = 42. All other settings stay at the baseline.
* The whole-space items cannot be reported exactly without simulating all 18,874,368 configurations, which did not fit in the time available. They are reported as estimates with confidence intervals.

## 8. Checker results

`grid14_checker.py` is a separate Python program that shares no code with the simulator. It reads `baseline_AM_trace.txt`, which has a POS record of every vehicle's link and cell at the end of every step, plus NEW, EXIT and WAIT records. It re-derives signal states, approach sides and movements from the packet itself. A stop-line crossing is any vehicle that is in the last cell of a link ending at an intersection at the end of step t−1 and in cell 0 of a different link at the end of step t.

```
red-crossing alteration: vehicle 0 crossing from link 0 into link 24 moved from step 84 to step 81 (it is shown in cell 0 of link 24 at steps 81..83)
double-cell alteration: at step 1000 vehicle 789 placed in link 0 cell 19, already holding vehicle 786

=== checker on baseline AM trace
trace: baseline_AM_trace.txt
config: {'C': 84, 'plan': 1, 'order': 'lead', 'offsets': [0, 0, 0, 0, 0, 0, 0, 0, 0]}; steps read: 4967; stop-line crossings checked: 8136; vehicles created: 2728; departed: 2728
I1 [no cell ever holds two vehicles]: PASS
I2 [every stop-line crossing happens during a green for its movement]: PASS
I3 [created == waiting + in network + departed at every step]: PASS
OVERALL: PASS
exit status 0

=== checker on altered copy 1 (crossing moved into red)
trace: altered_trace_red_crossing.txt
config: {'C': 84, 'plan': 1, 'order': 'lead', 'offsets': [0, 0, 0, 0, 0, 0, 0, 0, 0]}; steps read: 4967; stop-line crossings checked: 8136; vehicles created: 2728; departed: 2728
I1 [no cell ever holds two vehicles]: PASS
I2 [every stop-line crossing happens during a green for its movement]: FAIL (1 violation(s))
    step 81: vehicle 0 crossed at I0 (N-approach T, needs phase A) while signal shows D
I3 [created == waiting + in network + departed at every step]: PASS
OVERALL: REJECTED
exit status 1

=== checker on altered copy 2 (two vehicles in one cell)
trace: altered_trace_double_cell.txt
config: {'C': 84, 'plan': 1, 'order': 'lead', 'offsets': [0, 0, 0, 0, 0, 0, 0, 0, 0]}; steps read: 4967; stop-line crossings checked: 8136; vehicles created: 2728; departed: 2728
I1 [no cell ever holds two vehicles]: FAIL (1 violation(s))
    step 1000: vehicles 786 and 789 both in link 0 cell 19
I2 [every stop-line crossing happens during a green for its movement]: PASS
I3 [created == waiting + in network + departed at every step]: PASS
OVERALL: REJECTED
exit status 1
```
