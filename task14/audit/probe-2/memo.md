# Memo: signal coordination for the GRID-14 downtown grid

**To:** Traffic operations
**From:** Signal engineering
**Re:** What drives total time in system (TTS), why the recommended timing wins, and how cycle length and phase order change the average
**Basis:** I ran every number myself. The simulator is `grid14_sim.js` (Node.js v22.22.2). A separately written Python reference model (`reference_check_sim.py`) matched it exactly, in TTS and in the step the run ended, on all 39 scenario runs I compared, including gridlocked runs. An independent checker (`grid14_checker.py`) verified the invariants on the baseline AM trace. All figures are in `results.md`.

## 1. Bottom line

* **Use a 60 s cycle.** The cycle length is the decision that matters most. Changing the baseline from 84 s to 60 s, with nothing else changed, cuts total TTS from 4,052,648 to 2,136,688 veh·s (−47.3 %).
* **Best configuration found: C = 60 s, plan 6 (21/5/21/5), lag, offsets I0..I8 = 0, 45, 15, 30, 0, 30, 15, 30, 0 s.** Its total TTS is **1,829,597 veh·s** (AM 581,162 + PM 562,701 + EVENT 685,734), 54.9 % below the baseline, with no gridlock.
* **This is the best I found. I cannot call it the optimum.** I simulated 893,362 of the 18,874,368 configurations (4.73 %). A full census would take about 33 hours on the 4 available cores at about 25 ms per configuration, against a 2.5-hour limit.
  * Within the three (cycle, plan, order) groups I enumerated completely, (60, 6, lag), (60, 6, lead) and (60, 2, lag), it is the exact optimum under the packet's tie-break.
  * Coordinate-descent searches in the other 22 groups at 60 and 72 s did not beat it.
  * Nothing I found at 72 s or longer came close: the best was 2,503,973, at 72 s.
* **Do not lengthen the cycle.** In a stratified uniform sample of 108,000 configurations, no configuration with C ≥ 96 s beat the baseline. Gridlock rises from about 0.02 % of configurations at 60 s to about 91 % at 120 s.

## 2. Which knob affects total TTS most: cycle length

I split the variance of total TTS in the stratified sample (1,500 random offset vectors in each of the 72 cycle × plan × order groups) by knob:

| Knob | Share of variance of total TTS |
|---|---:|
| Cycle length (main effect) | **74.4 %** |
| Offsets (variation inside a cycle/plan/order group) | 16.7 % |
| Phase order (main effect) | 4.9 % |
| Timing plan (main effect) | 0.01 % |
| Cycle × plan × order jointly (main effects plus interactions) | 83.3 % |

Mean total TTS over the sample, by cycle and phase order:

| Cycle | Mean total TTS | Lead | Lag | Gridlocking configurations, lead / lag |
|---|---:|---:|---:|---:|
| 60 s | 2,066,470 | 2,082,477 | 2,050,463 | 0.00 % / 0.04 % |
| 72 s | 2,946,287 | 2,922,664 | 2,969,910 | 0.03 % / 1.26 % |
| 84 s | 4,677,482 | 4,238,238 | 5,116,726 | 2.09 % / 17.33 % |
| 96 s | 7,292,478 | 5,920,453 | 8,664,503 | 5.24 % / 51.03 % |
| 108 s | 9,658,429 | 7,901,623 | 11,415,235 | 17.73 % / 70.62 % |
| 120 s | 12,774,201 | 10,540,806 | 15,007,595 | 84.14 % / 98.77 % |

Average total TTS rises steeply and monotonically with the cycle: ×1.43 from 60 to 72 s, ×6.2 from 60 to 120 s.

**Why shorter cycles win in this model.**

* **Shared lanes cause head-of-line blocking.** Every street is a single shared lane, and every movement is protected (left turns only in phase B or D, and no right turn on red). A vehicle at the stop line whose movement is red blocks everyone behind it, even when the followers' movement is green.
  * A left turner that reaches the stop line during its street's through green holds up the through traffic behind it until its left phase comes.
  * A through vehicle that reaches the stop line during the left phase holds up the left turners behind it.
* **The cost of each block scales with the cycle.** The wait until the next service is a fraction of the cycle, so a longer cycle makes every blocking event longer and lowers what each lane can carry.
* **Queues discharge slowly.** A standing queue leaves at one vehicle every two seconds, because a vehicle moves only into a cell that was empty at the start of the step. The longer greens of a long cycle therefore cannot make up for the head-of-line losses.

I measured this in the AM run with plan 1, lead and zero offsets. I counted the steps in which the stop-line vehicle was held by its own red while the vehicle directly behind it wanted the movement that was green. There were 7,780 such steps at 60 s, 13,695 at 84 s and 22,126 at 120 s.

**Long cycles also cause spillback, which compounds the losses.** Long reds build queues that fill whole blocks and stop upstream intersections from discharging, which is how the long-cycle runs end in gridlock. The EVENT scenario, with T4 at 312 veh/h and T9 at 395 veh/h, suffers most: its sampled mean TTS grows from 0.83 M veh·s at 60 s to 7.49 M at 120 s, a factor of 9, while AM grows from 0.63 M to 2.69 M, a factor of 4.

## 3. How phase order changes the average

* **On average, lead is better and lag fails more often.** The sample means are 5.60 M veh·s for lead and 7.54 M for lag. From 84 s up, lag is 21–46 % worse on average and gridlocks far more often (17 % against 2 % of configurations at 84 s, 51 % against 5 % at 96 s). In the baseline variant, switching to lag costs +5.7 %.
* **Lead clears a stopped left turner within seconds.** Lead runs A → B (north-south through, then north-south left) and C → D (east-west through, then east-west left). A left turner reaches the stop line most often during its street's through green, because that is when the queue discharges. Under lead its own left phase follows a few seconds later.
* **Lag makes that left turner wait almost a full cycle.** Lag runs B → A and D → C. A left turner that reaches the stop line during the through green waits almost a full cycle and blocks the lane the whole time. Its cost therefore grows with the cycle, which is why the lead–lag gap widens as C grows.
* **At 60 s the two orders are almost equal.** That wait is short, and lag is in fact slightly better on average over all plans and offsets: 2,050,463 against 2,082,477, or −1.5 %. All of the best configurations I found use lag.
  * A plausible reason, which I have not verified separately: when the left phase is short, starting each street's service with it clears the left turners waiting at the head first, and the long through phase then discharges an unblocked queue.
  * At this cycle the interaction of the phase sequence with the offsets matters more than the order on its own.

## 4. Offsets and timing plans

* **Offsets are the second knob.** They account for 16.7 % of the variance. Inside the best group (60 s, plan 6, lag), offsets alone move total TTS from 1,829,597 to 8,009,194 (a rare gridlocking offset vector; 100 of the 262,144 gridlock) (mean 1,967,169, all 262,144 offset vectors enumerated). The simple row progression variant of the baseline, offsets 0/21/42 s west to east, improves it by only 3.7 %.
* **Plans matter little on average.** Plan means are within 1.5 % of each other. At 60 s, plan 6 (21/5/21/5, the longest through greens and the shortest left phases) has the lowest mean and the lowest minimum, followed by plan 2 and plan 3. The through movements carry 65–75 % of every approach, so maximising through green pays off once the short cycle has made left-turn waits cheap.

## 5. Why the best configuration wins

* **It combines the three good choices.** It uses the short cycle, which minimises head-of-line blocking, the through-heavy plan 6, and lag. Lag is the better order at 60 s, and its best configuration beats the best lead configuration of the same plan by 47,990 veh·s (1,829,597 against 1,877,587, both groups fully enumerated).
* **Its offsets matter most in the EVENT scenario.** Within its group, the winner ranks 1st of 262,144 in EVENT TTS (685,734 against a group mean of 768,239), 222nd in AM and 2,263rd in PM. Most of its advantage therefore comes from handling the heavy T9 eastbound and T4 westbound flows of the EVENT demand without spillback, while remaining near the top in AM and PM.
* **A simple green-wave rule does not explain the result.** I scored each offset vector by how many of the 24 directed blocks let a vehicle released at the start of the upstream through green arrive during the downstream through green. Over the whole group the correlation with total TTS is only −0.14, and the winner scores 11 of 24 against a group average of 8. The network is congested, so the binding constraint is how queues interact and spill back across blocks, not whether free-flowing platoons arrive on green. That is why the configuration had to be found by enumeration, not by a progression formula.
* **The edge-middle and centre offsets are the critical ones.** Changing a single offset of the winner to any other allowed value costs between +5,707 veh·s (I6) and +73,938 veh·s (I3 set to 0).
  * At the corners (I0, I2, I6, I8) the cheapest change costs only +5,707 to +11,864.
  * At the five intersections fed by three or four street blocks (I1, I3, I4, I5, I7), the cheapest change costs +13,158 to +44,294. At the centre, I4, every change costs at least +44,294.
  * These offsets must be set precisely; the corners are more forgiving.

## 6. Caveats

* **Only part of the space was simulated.** The optimum statement and the "best found" label in section 1 rest on 893,362 configurations.
* **The whole-space figures are estimates.** The sum of total TTS over all 18,874,368 configurations, the counts below baseline, the gridlock counts, and the per-cycle and per-plan counts in `results.md` come from the stratified uniform sample, with 95 % confidence intervals. The completely enumerated groups enter those estimates exactly. None of these figures is an exact census.
* **The absolute TTS values describe the packet's model, not the street.** The model follows the packet's rules: synchronous one-cell moves, protected-only movements and no right turn on red. Its 0.5 veh/s queue discharge is far below real saturation flow. The comparative conclusions (short cycle, lag at 60 s, careful interior offsets) are the transferable findings.
