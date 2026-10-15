# Task 22 WD-22 (Fenwick Hill water supply zone, 24 h extended-period simulation; Civil Engineering): status

- **Platform entry:** Domain **Civil Engineering**. Subdomain: "Water Distribution Engineering — extended-period simulation of a pumped network with a service tank (Hazen-Williams, pump level controls, PRV, operating cost)".
- **Shape (deliberately different from tasks 16–21):** no event log and no single snapshot. The answer is a 24 h time series (96 steps of 15 min): pump start/stop events driven by tank-level hysteresis, hourly tank levels, energy and cost under a two-rate tariff, a pressure-deficit finding over time, and a **control-setting decision** that needs five full-day re-simulations. Two visuals: pipe plan (sheet 2) and demand-pattern bar chart (sheet 3).
- **Model** (`model/eps.py`): per step a global-gradient Newton solve (14 pipes of 2 sections, 5 pipe types, 2 parallel pumps H = 68.0 − 0.0042 q² with a non-return valve, PRV-1 at 72.0 m, tank as a fixed head), then explicit level update; controls P-1 2.40/4.20 m, P-2 1.90/3.00 m evaluated at step start, P-1 first.
- **Key results:** P-1 stop 03:15, start 05:30; P-2 start 07:15, stop 23:15. Minimum level 0.890 m at 10:00 (below the 1.00 m reserve). Energy 1132 kWh, cost GBP 212.47. Lowest pressure 19.90 m at J8 (09:45 step); J8 below 20.0 m from 08:30 to 10:30, no other junction. Candidates: 2.00 and 2.20 → 1.172 m, GBP 212.95; 2.40 → 0.890; 2.60 → 0.988 (breach); 2.80 → 1.078 m, GBP 210.54 → **recommend 2.80 m**. Non-monotone (a higher P-1 start delays P-2 into the peak), so every candidate must be simulated.
- **Crossed corners** (same type, lengths 28–33 % apart): J3 A2/C1 DI200 360/460; J5 B2/B3 DI200 380/490; J6 B2/C3 CI200 460/350; J7 C1/C3 DI200 390/520. Crowded J3: A3 DI200 400 next to A2 360 and C1 460. Leader rule on the drawing title and in the data sheet. Every leader checked in code (`check_leaders.py`: 28 leaders, each on its own section, on no other pipe) and at zoom.
- **Graded set:** 22 numeric rows at +4 (14 hourly levels 11:00–24:00, minimum level, energy, cost, lowest pressure, cost and minimum level for candidates 2.00 and 2.80), chosen by the sensitivity greedy; duplicates excluded (10:00 level = minimum level; 2.20 = 2.00; 2.40 = base case). 17 non-numeric points (4 events at +2, event completeness, minimum-level time, pressure node/time/interval/only-J8, two reserve breaches, recommendation +3) plus 3 file rows.
- **Rubric v1:** 39 criteria, +110, longest 162 characters.
- **Fairness decision:** the independent re-solve first used the textbook exponent 0.54 instead of 1/1.852 and drifted up to 0.0022 m in level. Level ranges were set to ±0.005 m so a solver with that approximation still scores 100, while every trap still fails.

## Pre-handover checks (2026-10-15)
| Check | Result |
|---|---|
| gate.py (A1, A2, A3, B4, B6, B11, B13, B14 ×2) | all PASS (B4 flags #5, a list of four times in one claim: atomic) |
| Independent re-solve (`indep.py`: scipy fsolve on heads; constants parsed from the PDF text; sections transcribed from the rendered plan; pattern read off the chart) | events identical, worst difference over every graded value 2.2e-12 |
| PDF (`wd22_v1.pdf`, 4 pages) | no Info/ID/XMP/ICC/SMask, no generator strings in any stream, no vector drawings, no answer strings in text, pdfium renders every page |
| Leaders | 28/28 on their own section |

## Strict re-grade with the printed ranges (`model/score_sim.py`)
| Scenario | Score |
|---|---|
| Correct reading | 100.0 |
| Correct reading, textbook 0.54 exponent (fairness) | 100.0 |
| Corner J3 A2/C1 | 21.8 |
| Corner J5 B2/B3 | 21.8 |
| Corner J6 B2/C3 | 15.5 |
| Corner J7 C1/C3 | 37.3 |
| Crowded J3 A2/A3, A3/C1 | 21.8, 37.3 |
| Any two corners | 18.2–30.0 |
| All four corners | 21.8 |
| Chart bar ±0.05 at 00, 03, 07, 08 h | 15.5–26.4 |
| Chart bar ±0.05 at 12 h | 41.8–45.5 |
| Chart bar ±0.05 at 18, 22 h | 68.2–89.1 (not a designed trap) |

Simulation predicts grading only, not whether runs misread (gate, simulation limits).
