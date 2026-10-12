# KINGSMEAD-11 v2 platform runs (Model A = claude-opus-4-8, max)

Scores **43, 44, 39**. All three completed with no timeouts, in 62 to 66 turns and 23 to 33 minutes. Three runs below 50, so the task **passes**.

## The one slip (identical in all 3 runs)

All three runs swapped the two 185 sections that meet at S1 on the route plan:
- They gave F1-1 a last section of 185/**520** m. The correct value is 420 m.
- They gave F1-2 a first section of 185/**420** m. The correct value is 520 m.

Everything else matched: the log replay, BS open, T1 MANUAL tap 9, T2 AUTO, NOP-1 and NOP-2 closed, F2-3 closed, the repair, C1, PV-1, P33 metering, the AVC tap search (tap 4) and the solver.

The swap reproduces the runs' numbers exactly in `model/pf.py`:

| Quantity | Runs | Key |
|---|---|---|
| F1-1 | 102.8 A | 103.6 A |
| F1-2 | 31.89 A | 32.34 A |
| T2 | 9.542 MVA | 9.536 MVA |
| Losses | 199.8 kW | 198.9 kW |
| Max section | 69.68 % | 69.45 % |

`score_sim.py` had already listed this exact case ("S1 corner: 420/520 labels swapped") and predicted a strict score of 34.5. The platform gave 39 to 44. The difference is the non-numeric criteria, which the runs passed: the F1-3 impedance, the memo items and the files.

## Why it worked

- The v2 plan put two 185 sections with near-equal lengths (420 and 520 m) at one corner (S1), each on a different route. The blind solve read them correctly, so the plan is legible, but a fast reader attributes them the wrong way round.
- The rubric was weighted by misread sensitivity: all 16 route currents plus transformer Mvar and losses, at +4 or +5 each. A single swap therefore fails most numeric rows. Voltages and the tap still pass, which is why the score was 39 to 44 rather than 20.
