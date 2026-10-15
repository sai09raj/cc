# Task 21 TR-21 (Hartsdown Tramway 750 V DC traction supply; Electrical Engineering): status

- **Recipe:** MV-20 at v1 (17-CASE-STUDY), on a different physics: a nonlinear DC load flow with constant-power trams and diode rectifiers.
- **Model:**
  - section loop resistance r x L, from 5 conductor types;
  - substations E - R_i I, with a diode block on reverse current;
  - trams I = P/V at stops;
  - Newton solve with an active-set check of the rectifiers.
- **Log state at 07:30:**
  - TSS-B out (tripped 05:40, still out 07:10);
  - TSS-D tap +1, 850 V (06:15);
  - TSS-C tap raise refused (06:55), 835 V;
  - X1 isolated 02:00, re-energised 05:20;
  - T150 stabled, drawing nothing;
  - 8 trams in the SCADA snapshot.
  - Finding: T126 at N8 is at 591.4 V, below the 600 V minimum. No rectifier is blocked.
- **Crossed corners** (same conductor type, lengths 23–33 % apart):
  - N4 M1/M2, K3 360/470;
  - N9 X1/N9R, K4 520/410;
  - N6 S3/S4, K3 470/580;
  - N7 S6/S5, K2 440/330.
  - Crowded junction N3: L4 K1 450 and S6 K2 450.
  - Strict simulation with the printed ranges: corners 13.5 / 24.3 / 17.1 / 13.5, N3 31.5, every log slip 10.8–13.5.
- **Graded set:** 24 numeric rows at weight 4, chosen by the sensitivity greedy: 3 substation currents, 12 route currents, 8 tram voltages and the loss. Series duplicates are excluded (L1 = TSS-A, S5 = TSS-D).
- **Rubric v1:** 38 criteria, +111, longest 151 characters.
- **Checks:**
  - Gate: all checks pass.
  - Independent re-solve (scipy, using numbers parsed from the packet text and lengths read off the plan): matches all 24 values to 3e-14.
  - Leaders: checked in code.
  - PDF: 10 objects, text identical to the source, no answer strings (one coincidental 3 s.f. match: the ungraded L4 current 820.3 A against T126's 820 kW input).

## v1 platform runs: 5 of 6 at 14 (validity audit, 2026-10-15)
- **Three trajectories analysed (Opus 4.8, 12–13 min each):** all report identical values (TSS-A 2882, TSS-C 3855, TSS-D 3088, loss 963.7 kW).
- **Cause:** every run read all four crossed corners by proximity, giving the swap:
  - M1 got 470, M2 got 360;
  - X1 got 410, N9R got 520;
  - S3 got 580, S4 got 470;
  - S6 got 330, S5 got 440.

  The other 12 routes and every log trap were read correctly. No run mentions leader lines.
- **Their values are our model fed that swapped reading** (max difference 0.05 %, 4 s.f. rounding). The strict re-grade with the printed ranges gives 13.5, matching the platform's 14: 0/24 numeric rows, 15/15 non-numeric.
- **The key is correct:**
  - the independent re-solve matches it to 3e-14;
  - every leader lands on its own section (checked in code and at 200 dpi).
- **Risk:**
  - Neither this packet nor KINGSMEAD, DH-19 or MV-20 states the leader convention in words; it relies on standard drafting practice.
  - Identical scores across runs invite a reviewer question about whether the drawing is ambiguous.
  - Option: add an explicit sentence to the title or data sheet (a label belongs to the section its leader line touches). This makes the task fairer, but it will probably raise scores.
