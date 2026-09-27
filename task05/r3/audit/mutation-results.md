# R3 mutation-test results

Realistic wrong-implementation mutants, each a plausible mistake a competent solver
could make while still believing it followed the spec. All were run against the
canonical reference (`reference/kilnworks_sim.py` / `reference/mutant_per_campaign_reset.py`).
A mutant "kills" (is detected) when it changes at least one design's `(makespan, bill)`
pair versus the reference.

| Mutant | Semantic rule attacked | Designs changed | Kill? |
|---|---|---:|---|
| `mutant_disable_fault` | S07 node-4 fault | 6/6 | yes |
| `mutant_oven_no_timer` | S06 bounded pairing timer | 6/6 | yes |
| `mutant_tiebreak_high` | S03/S05/S06 lowest-index tie-break | 6/6 | yes |
| per-campaign reset (`mutant_per_campaign_reset.py`) | S02 continuous cross-campaign chaining | 6/6 | yes |
| negative prep start (`kilnworks_verify.py`) | S04/S09 boundary/timing | rejected by verifier | yes |
| forced route/node collision (`kilnworks_verify.py`) | S05 edge/node capacity | rejected by verifier, first invalid minute identified | yes |

These are the post-convergence numbers (see `audit/independent-reconstruction.md`),
run against the frozen goldens D0=187/1331, D1=165/1294, D2=187/1447, D3=185/1401,
D4=155/1413, D5=142/1290. Full per-design detail is reproducible by running:

```
python3 reference/kilnworks_sim.py
python3 reference/mutant_per_campaign_reset.py
python3 reference/kilnworks_verify.py
```

## Important finding: headline recommendation is not a safe proxy

The per-campaign-reset mutant gets every one of the six per-design `(makespan, bill)`
pairs wrong (6/6 changed, by 15-25% on makespan and up to 15% on bill), **but still
recommends the same two design IDs** (`D5` unrestricted at its own wrong key
`(177,1291,22,D5)` vs the true `(142,1356,22,D5)`; `D1` under `capital<=9` at its own
wrong key `(194,1191,7,D1)` vs the true `(165,1315,7,D1)`), because the relative
ordering across designs happens to survive the systematic per-design distortion.
This is the same trap documented in Task 04 Revision E
(`Playbook/12-CASE-STUDY-TASK-04.md`): a wrong integrated engine can still recover the
headline selection ID while getting every underlying number wrong.

**Consequence for the rubric (score-topology.md):** criteria that check "identifies
D5/D1" must carry modest weight. The bulk of positive weight must sit on (a) the exact
per-design makespan/bill values, and (b) production-trace witnesses drawn from the
actual continuous, interleaved, fault-affected run (cross-campaign batch composition,
fault-window blockage, campaign-boundary carryover) that the per-campaign-reset
mutant cannot produce at all, since it never runs a continuous trace.
