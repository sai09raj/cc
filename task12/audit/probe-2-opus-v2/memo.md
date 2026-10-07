# Engineering memo: COHERE-12 directory configuration

**To:** memory-system team  **Re:** what drives makespan, where to put the directory banks, and how to size Q and B

## Bottom line

* **Recommended configuration: D0 on N2, D1 on N6, line map 55860, Q = 4, B = 1, makespan 5,470 cycles.** That is 1,255 cycles (18.7%) faster than the baseline's 6,725 (D0 N0, D1 N7, Fig. 5 map 19245, Q = 2, B = 2).
* How sure we are: I simulated all 1,048,576 configurations with the N2/N6 placement, so 5,470 is the exact best for that placement. I did **not** simulate the whole 29.4M-configuration space. The census plus a stratified sample covers 4,844,872 configurations (16.5%) (exact counts in `results.md`). No configuration simulated in any other placement came within 134 cycles of 5,470. So I expect this to be the global optimum, but it is not proven.
* **Directory placement is the knob that matters most.** Line map is second, Q is a distant third and B barely matters.

## 1. Which knob affects makespan most

Each figure below averages over the other three knobs, using whole-space estimates from census plus stratified sample (`results.md`):

| knob | best mean | worst mean | spread | share of makespan variance |
|---|---|---|---|---|
| Directory placement (28 choices) | 6,072 (N2/N6) | 8,175 (N0/N4) | **≈ 2,100 cycles** | **≈ 54%** |
| Line map (65,536 choices) | (within one placement/Q/B cell) | | typical SD ≈ 400 cycles, range ≈ 1,300 cycles | ≈ 40% |
| Q (1..4) | 6,980 (Q=4) | 7,351 (Q=1) | ≈ 370 cycles | ≈ 5% |
| B (1..8) | 7,081 (B=1) | 7,193 (B=8) | ≈ 110 cycles | < 0.5% |

Placement is ahead because every miss costs about one request-response round trip over the mesh, and the workload misses a lot: about 1,200 of 1,648 loads miss, and almost all stores need GetM or an upgrade. Contention and the Fwd/Inv three-hop transfers also scale with how far the home bank is from the cores. Q and B only matter when a request is refused. Even at Q = 2 only about 4% of messages are Nacks (401 of 9,762 in the baseline).

The line map is a strong second because traffic is very uneven. Lines L0, L1 and L2 take about 69% of all loads and stores: the workload maps 60% of operations to `s mod 3`. Which bank owns each hot line sets both the latency and the queue pressure at each bank. In the exhaustive N2/N6 census at Q = 4, putting all three hot lines on one bank gives a mean makespan of 6,123 (all on D0/N2) or 6,278 (all on D1/N6). Splitting them 2:1 across the banks gives 5,809 to 5,935. Maps that split all 16 lines roughly evenly (Hamming weight 6 to 9) do best (≈ 5,890 to 5,950), and maps that put every line on one bank do worst (6,433 / 6,633).

## 2. Why N2/N6 wins

These are zero-load round trips from each core to a bank on each node and back. They use XY routing, the Figure 2 latencies and one cycle of router wait per hop:

| node | N0 | N1 | **N2** | N3 | N4 | N5 | **N6** | N7 |
|---|---|---|---|---|---|---|---|---|
| mean core-to-node round trip (cycles) | 10.0 | 8.75 | **7.75** | 10.75 | 10.75 | 9.0 | **8.0** | 12.0 |

(`node netstats.js` prints this table.)

* N2 and N6 are the two best-connected nodes on the chip. Column 2 sits next to the fast links N2-N3 (1), N2-N6 (1) and N5-N6 (1). Most slow links are away from it: N1-N5 (3) and N6-N7 (3) are crossed only by a few routes. N2 reaches N0/N1 over 1+2 cycle links and N3 over 1. N6 reaches N5/N4 over 1+2 and N2 over 1.
* The two banks are vertical neighbours on a 1-cycle link. Under XY routing, a core in column 2 reaches either bank in at most one vertical hop, and every other core reaches column 2 by row moves, then at most one 1-cycle column hop.
* With one bank in each row, the "far" bank costs any core only one extra 1-cycle hop beyond the near one. Requests heading to N2 and to N6 from the same row share the row links only up to column 2. Three-hop transfers (requester → home → owner → requester) also stay near the middle of the mesh.
* The baseline does the opposite: its banks sit on corners N0 and N7. N7 is the worst node on the chip (mean round trip 12; 21 cycles from C0), reachable only over the 3-cycle N6-N7 or the 2-cycle N3-N7 link.
* The next-best placements also use the central nodes: N2/N5 (mean 6,362) and N1/N6 (6,488). Both lose to N2/N6 (6,072) because N5 and N1 each have a 3-cycle link (N1-N5) on their vertical path. The exhaustive Q = 4 censuses of those two placements bottom out at 5,604 and 5,627, against N2/N6's 5,470.
* The variants agree. Only moving the banks from N0/N7 to N1/N6 cuts the baseline from 6,725 to 6,198. Changing only the line map to 43690 makes it slightly worse (6,931).

## 3. How larger Q and larger B change average makespan

**Q (directory request-queue capacity): larger is better, with diminishing returns.** Whole-space mean makespan is 7,351 at Q = 1, 7,134 at Q = 2, 7,038 at Q = 3 and 6,980 at Q = 4, so the three steps change it by −217, −96, then −58 cycles. A small queue refuses requests during bursts on the hot lines. Each refusal costs a Nack trip back, a backoff and a resend trip, and it often reorders requests unfavourably. With the baseline placement and map, Nacks fall from 717 to 828 at Q = 1 to 76 to 99 at Q = 4 (across the four B values). Once a bank can hold most of the requests that are outstanding together, more capacity buys little: there are 8 cores with about 1 outstanding miss each, plus evictions. The best configuration found uses Q = 4 in 20 of the 28 placements, Q = 3 in 4 and Q = 2 in 4. Those are sample-based and within line-map noise, and Q = 1 is never best. All 10 best configurations overall have Q = 3 or 4.

**B (backoff base): larger is worse on average, and B = 1 and B = 2 are essentially tied.** Mean makespan is 7,081 at B = 1, 7,098 at B = 2, 7,131 at B = 4 and 7,193 at B = 8. A queue slot frees within a few cycles, since a bank retires one request per cycle unless it is stalled on S_D. Waiting 8, 16 or 32 cycles therefore leaves the requesting core idle long after the bank could have taken its request. Backoff saves only a few messages. The penalty depends on Q because refusals are rare when Q is large: at Q = 1, B = 8 costs about 250 cycles over B = 1 (7,252 → 7,499), but at Q = 4 the cost is only about 30 (6,970 → 6,998).

## Recommendation

1. Put the directory banks on N2 and N6. This matters more than every other choice combined.
2. Use the largest request queue (Q = 4) and the shortest backoff (B = 1; B = 2 is equivalent within noise).
3. Split the three hot lines L0 to L2 across the two banks and keep the bank loads roughly balanced. Line map 55860 (binary 1101 1010 0011 0100) sends L2, L4, L5, L9, L11, L12, L14 and L15 to D1 on N6, and the rest (including hot lines L0 and L1) to D0 on N2: 8 lines on each bank. It gives the best makespan found, 5,470 cycles.
4. Caveat: on top of a good placement and Q, makespan varies by a few hundred cycles between neighbouring line maps in a way that is hard to predict. Any specific map's advantage of a few tens of cycles is specific to this workload and should not be over-read.
