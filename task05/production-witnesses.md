# R2 production witnesses

Extracted mechanically by audit/extract_witnesses.py from the same uninterrupted schedules that generate the goldens. These are author audit witnesses, not mandatory solver trace strings. Any physically valid equally optimal schedule passes. No isolated test is presented as production.

| Causal owner | Case | Action minute t | Snapshot boundary t+1 | Extracted detail |
|---|---|---:|---:|---|
| fixture-held-through-wait-transport | D0/campaign0 | 5 | 6 | `{"held":2,"limit":2}` |
| shared-oven-approach | D0/campaign0 | 7 | 8 | `{"robot":0,"source":4,"destination":1}` |
| tariff-boundary | D0/campaign0 | 7 | 8 | `{"previous_tariff":1,"tariff":2,"power":2}` |
| aggregate-power-with-robot | D0/campaign0 | 9 | 10 | `{"power":5,"limit":5}` |
| unload-completion-visible | D0/campaign0 | 9 | 10 | `{"batch":[0],"previous_actions":[{"kind":"drop"},{"kind":"move","to":8}]}` |
| persistent-family-setup | D0/campaign0 | 18 | 19 | `{"machine":"P","prior_family":0,"new_family":1,"lot":3}` |
| fixed-pair-batch | D0/campaign0 | 36 | 37 | `{"lots":[1,3]}` |
| terminal-conservation-and-bill | D0/campaign0 | 40 | 41 | `{"makespan":41,"bill":267,"fixture_held":0,"lot_states":["done","done","done","done","done"]}` |
| optional-aisle | D3/campaign0 | 5 | 6 | `{"robot":1,"source":5,"destination":4}` |

All indices are zero-based. A record at action minute t measures power/tariff over [t,t+1), then snapshots after all completions at boundary t+1 and before the next starts. Fixture count at that boundary may be lower than during the preceding minute.

The full mechanism records are in audit/production-certification/mechanism-witnesses.json. Separate production-witnesses.json contains mechanically selected early (t=0), middle (floor(M/2)) and late (M-1) records for all24 cases:72 checkpoints, each retaining actions, state and cumulative bill. This broad coverage is not72 independent grading owners.

Cross-file reconciliation: each full trace has M records; its last cumulative bill equals the case bill; all lots are done and fixture count zero. Matrix optimum pairs match independent-engine/independent-matrix.json in all24 cases. The causal interpretation of a particular valid route must not impose an unrequested route tie-break.
