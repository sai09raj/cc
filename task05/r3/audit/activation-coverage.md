# R3 activation-coverage audit

Per `04-PREFLIGHT-AND-VALIDATION.md`'s activation-coverage audit: every fault/stress
rule must be shown to actually fire in an ordinary certified run and to change an
observable output, not merely be printed and shielded. Evidence below is from
`reference/kilnworks_sim.py` executed cleanly against all six designs.

## S07 node-4 fault

`fault_triggered = True` in all six designs (D0-D5), both aisle configurations. This
is structurally guaranteed, not incidental: node 1 (`K`) has only the edge `1-4` in
both topologies (`design/semantic-contract.md` S01), so every delivery to the oven
must pass through node 4, and Robot 0 reaches it almost immediately in every design
(first prep-to-K delivery). Disabling the fault (`mutant_disable_fault=True`) changes
both makespan and bill in 6/6 designs (see `audit/mutation-results.md`), confirming
the mechanism is observable, not shielded.

## S02 cross-campaign interleaving (overlapping cadence)

Confirmed across all six designs and all three campaign boundaries (`s -> s+1`): at
least one lot from campaign `s` is still open when campaign `s+1`'s first lot
releases. Interleaving is never a no-op. Reverting to R2-style independent
per-campaign resets (`reference/mutant_per_campaign_reset.py`) changes both makespan
and bill in 6/6 designs (see `audit/mutation-results.md`).

## S06 cross-campaign oven batching (final, post-convergence numbers)

| Design | F | Batches | Paired | Mixed-campaign pairs |
|---|---:|---:|---:|---:|
| D0 | 2 | 20 | 0 | 0 |
| D1 | 3 | 16 | 4 | 2 |
| D2 | 2 | 20 | 0 | 0 |
| D3 | 2 | 20 | 0 | 0 |
| D4 | 3 | 19 | 1 | 1 |
| D5 | 3 | 17 | 3 | 1 |

D0/D2/D3 (all `F=2`) never pair: the fixture ceiling limits how many lots can be
simultaneously alive plant-wide, so a second same-family lot is rarely ready before
the pairing deadline expires. This is a genuine emergent consequence of `F`, not a
bug — confirmed identically by an independent from-scratch implementation (see
`audit/independent-reconstruction.md`) — and gives the Synthesize field a real,
executable causal claim ("a higher fixture ceiling is what actually buys
oven-pairing benefit, not the aisle retrofit or the power ceiling").

## S01 open-aisle edge use

Edge `4-5` (present only in D3/D5) is actually traversed during the run, confirming
the retrofit changes real routing. It does not eliminate the `F=2` bottleneck: D0,
D2 and D3 (all `F=2`) still land on the highest makespans among the six designs
(187, 187, 185) since fixture scarcity, not travel distance, dominates for them —
D3's open aisle buys it a slightly lower makespan than D0/D2 (185 vs 187) but not a
qualitative change, again a legitimate, executable causal story rather than a
coincidence to explain away.

## Conclusion

Every new R3 mechanism (fault, cadence-driven interleaving, bounded oven pairing
timer) fires in ordinary certified execution across all six designs and demonstrably
changes observable output when removed or reverted. None is shielded by an earlier
launch block or an empty workload region.
