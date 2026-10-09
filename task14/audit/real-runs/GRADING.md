# GRID-14 real runs (Model A, opus-4-8 max)

- 5 of 6 runs: "server disconnected without sending a response" (counted as stump, like the 9000 s timeout).
- 1 run completed (session 60853354, 5,864 s, 120 turns, $26.76, terminal_reason completed, platform score 19).

## The completed run
Ended its turn at ~98 min with the full sweep ~4% done (729,088 of 18,874,368, C=60 only), saying it would be
"re-invoked" when the sweep finished. The session ended there, the background sweep was killed, no memo was written.
results.txt exists but is labelled PARTIAL.

| Criteria | Earned | Why |
|---|---|---|
| C1-C7 figures | 7 | all exact |
| C8-C9 package | 2 | Node v20.20.2 / Python 3.11.17; README commands |
| C10-C16 baseline + variants | 18 | all exact (independent Python reference agreed) |
| C17-C18 optimum | 0 | sweep unfinished |
| C19-C33 whole-space | 0 | partial counts only, labelled PARTIAL |
| C34-C39 checker | 7 | 3 invariants pass, 8,136 crossings, both altered copies rejected naming I2 / I1 |
| C40-C43 memo | 0 | no memo |
| C50 deliverables | 0 | memo missing |
| C44-C49 negatives | 0 | none triggered (partial values labelled, no packages, no internet) |

My total: 34 / 135 = 25.2%. Platform: 19. Both below 50.

Failure mode: engine 6-17 ms/config/worker on 16 workers, ETA 5.5-7 h; it chose to wait and ended the turn.
