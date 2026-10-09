## Analyze

```text
Read the packet and recover the whole model. From Figure 1 read the cover letter of each 8 x 8 block (for example cell (100, 36) is houses and (76, 62) rock) and the 14 station cells (S14 at x 100, y 92). From Figure 2 read burn times and base chances (grass 2 and 100, brush 4 and 75, timber 7 and 50, houses 5 and 65), the wind factors by speed class and angle, seeds and strike rates (D 145 per mille), the 70 percent diagonal factor and the other constants. From Figure 3 read the wind of each period (scenario C, period 3: toward SW, strong) and from Figure 4 each crew's speed and capacity. Recover the rules in the text: the generators, the six phases of a step, the eligibility and draw order of spread, the crews' arrival, return and nearest-cell rule, dispatch, the run end and the loss.
```

## Execute & Generate

```text
Write a step-by-step simulator in the standard library, offline, and make it fast: the whole-space items need all 105,413,504 plans times four scenario runs, so plan the runtime, scan only burning cells, split the space across all cores and checkpoint partial results. Baseline (S1, S4, S5, S8, S9, S12, S13): A 1,992, B 4,240, C 3,455, D 4,079, total 13,766. Variants: crew 7 at S6 10,956; all at S6 18,683. Whole space: sum of total loss [SUM_TOTAL_LOSS]; [N_BELOW_BASELINE] plans below the baseline; [N_BELOW_ALL_FOUR] below it in all four scenarios; with crew 7 at each station, below the baseline: S1 [CREW7_S1_BELOW], S2 [CREW7_S2_BELOW], S3 [CREW7_S3_BELOW], S4 [CREW7_S4_BELOW], S5 [CREW7_S5_BELOW], S6 [CREW7_S6_BELOW], S7 [CREW7_S7_BELOW], S8 [CREW7_S8_BELOW], S9 [CREW7_S9_BELOW], S10 [CREW7_S10_BELOW], S11 [CREW7_S11_BELOW], S12 [CREW7_S12_BELOW], S13 [CREW7_S13_BELOW], S14 [CREW7_S14_BELOW]. Optimal: [OPT_PLAN_S1..S7], total loss [OPT_TOTAL_LOSS]; call it optimal only because all plans were simulated, and state that count. Write the baseline scenario A trace and run a separately coded checker: it passes the three invariants, reports 980 spread ignitions checked, and rejects the two altered copies, naming the invariant each violates. Record the runtime version and reproduction commands.
```

## Synthesize

```text
Write the memo from your own results. Across the space the average total loss is [AVG_TOTAL_LOSS]. Crew [CREW_MOST]'s station changes the average most: its per-station averages range from [MIN_STATION_AVG] to [MAX_STATION_AVG]. Crew 7 is best based at S[BEST7] ([CREW7_BEST_BELOW] plans below the baseline) and worst at S[WORST7] ([CREW7_WORST_BELOW]). Explain the pattern from the landscape and wind: stations near the town and upwind of it reach fires that threaten houses sooner, and each house cell costs ten times a plain cell. Note that fire growth is chaotic, so only an exhaustive sweep gives the exact counts and sums.
```
