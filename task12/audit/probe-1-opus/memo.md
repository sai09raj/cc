# COHERE-12: directory placement, queue depth Q and backoff B

All numbers below come from `sim.py` (CPython 3.11.15, standard library only), run on the
workload in packet Section 7. The checker (`checker.py`) passes on the baseline trace.

## Values read from the figures

* Figure 1: node Ni is at row i div 4, column i mod 4 (N0..N3 = row 0, N4..N7 = row 1). Core Ci is on Ni.
  The directory placements (D0 node / D1 node) are P1 N0/N7, P2 N1/N6, P3 N3/N4 and P4 N2/N5.
* Figure 2 (I measured the bar ends in pixels; the gridlines are 1 cycle apart, starting at 0): N0-N1 1, N1-N2 2, N2-N3 1,
  N4-N5 2, N5-N6 1, N6-N7 3, N0-N4 1, N1-N5 3, N2-N6 1, N3-N7 2. Each link has the same latency in both directions.

## Baseline (P1, Q=2, B=2) and the selections

| config | makespan | p95 load miss | mean load miss | messages | Nacks |
|---|---|---|---|---|---|
| Baseline P1/Q2/B2 | 685 | 44 | 19.4 | 886 | 38 |
| **Fastest P2/Q4/B1** | **586** | **31** | 14.9 | 801 | 13 |
| Leanest P2/Q4/B4 | 638 | 31 | – | **795** | 8 |
| P2/Q2/B2 (placement change only) | 635 | 36 | 18.0 | 892 | 51 |
| P1/Q4/B1 (Q and B change only) | 690 | 37 | 18.9 | 845 | 23 |

Baseline core finish cycles (C0..C7) are 545, 552, 648, 685, 488, 622, 662, 669.
For the Fastest configuration they are 469, 500, 452, 586, 531, 485, 509, 555. C3 finishes last in both.

## Why the Fastest configuration beats the baseline

The makespan drops from 685 to 586 (99 cycles, 14%). Two things cause this, and only their combination gets the full gain.

1. **Placement.** The workload is skewed. Lines 0, 1 and 2 take 193 of the 256 memory operations.
   Lines with even numbers are homed at D0, so D0 serves 164 of the 256 (64%).
   P1 puts D0 in the corner at N0 and D1 at N7, whose route west starts on the slowest link (N6-N7, 3 cycles).
   The mean unloaded one-way latency from a core to a home is 3.25 cycles under P1 and 2.62 under P2.
   Weighted by the actual accesses, the core-to-home round trip is 6.65 cycles under P1 and 5.76 under P2.
   Changing only the placement (P1 to P2, keeping Q=2, B=2) cuts the makespan from 685 to 635.
   Averaged over all 16 (Q, B) pairs, the mean makespan is P1 687.4, P2 648.4, P3 730.6 and P4 641.6,
   so P2 and P4 are the good placements and P3 is the worst.
2. **Deeper queue and short backoff.** At P2, raising Q from 2 to 4 and lowering B from 2 to 1 cuts the Nacks from 51 to 13.
   It also cuts the mean load-miss latency from 18.0 to 14.9 cycles, p95 from 36 to 31, and the makespan from 635 to 586.
   There are fewer Nacks because the directory rarely refuses a burst of requests to the hot lines.
   When it does refuse one, B=1 brings the retry back after only 1 cycle.

The two effects do not simply add up. On P1, the same Q/B change (P1/Q4/B1) gives 690, slightly *worse* than the baseline.
The run has many races: small timing shifts change which request reaches a directory first, so single rows vary by tens of cycles.
The placement is the robust part of the gain, and Q/B tuning on top of it is configuration-specific.

## How Q and B trade Nacks against makespan (means over the 4 placements)

| Nacks | B=1 | B=2 | B=4 | B=8 |
|---|---|---|---|---|
| Q=1 | 99.0 | 94.5 | 73.8 | 62.2 |
| Q=2 | 53.0 | 45.0 | 34.5 | 32.5 |
| Q=3 | 34.5 | 29.8 | 27.5 | 21.8 |
| Q=4 | 19.0 | 15.8 | 14.0 | 10.5 |

| makespan | B=1 | B=2 | B=4 | B=8 |
|---|---|---|---|---|
| Q=1 | 706.8 | 708.2 | 701.0 | 713.0 |
| Q=2 | 684.5 | 664.0 | 664.0 | 661.5 |
| Q=3 | 651.0 | 683.2 | 662.2 | 686.5 |
| Q=4 | 651.5 | 661.2 | 666.0 | 667.2 |

* **Q is the main lever for Nacks and the only lever that reliably helps makespan.** The mean Nacks fall from 82.4 (Q=1) to 41.2, 28.4 and then 14.8 (Q=4).
  Over the same range, the mean messages fall from 967.6 to 825.4.
  Each Nack costs one wasted request, the Nack itself, and one resend.
  The mean makespan improves mostly from Q=1 (707.2) to Q≥2 (661.5 to 670.8).
  After that the gains are small and noisy, because a request accepted into a long queue still waits behind the requests ahead of it.
* **B trades Nacks for idle time.** Larger B lowers the mean Nacks (51.4, 46.2, 37.4, 31.8 for B=1, 2, 4, 8) and the mean messages (909.5 down to 866.2).
  The reason is that a refused cache stays away longer, so its resend is more likely to find room.
  The makespan does not improve, though (673.4, 679.2, 673.3, 682.1): a refused core sits idle for the whole backoff even when the queue has already drained.
  So B mainly buys message and Nack savings. It shows in the Leanest choice, P2/Q4/B4: 795 messages and 8 Nacks, at the cost of 52 more cycles than P2/Q4/B1.
* For speed, use a deep queue with a short backoff (the Fastest choice, Q=4, B=1).
  For traffic, use a deep queue with a moderate-to-long backoff (Leanest, Q=4, B=4).
  Q=1 is the worst setting on every metric.

## Sweep totals (64 rows)

Sum of makespan is 43328, sum of messages is 56774, and sum of Nacks is 2669.
20 configurations have a makespan ≤ 640.

## Caveats

* The result comes from one deterministic workload, and the ranking between neighbouring configurations is sensitive to timing.
  P4 has a slightly better *mean* makespan than P2 (641.6 vs 648.4), but P2 produces the single best configuration.
* Interpretation choices are listed in README.md. The main one: load-miss latency is measured from the cycle the GetS was first sent.
  Measuring from the first attempt of the LD changes p95 in 36 of the 64 rows, but it changes neither the baseline p95 (44) nor the Fastest or Leanest selections.
