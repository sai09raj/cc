# KINGSMEAD-11: edits from v1 (entered) to v2

## 1. Attachment
Remove kingsmead_v1.pdf, attach kingsmead_v2.pdf.

## 2. Prompt (1 edit)
Line 1: `kingsmead_v1.pdf` -> `kingsmead_v2.pdf`. Nothing else changes.

## 3. Rubric
- Keep C1-C4 as they are.
- DELETE v1 rows C5 to C31 (27 rows: transformer, voltage, current, infeed, losses, C1, PV, highest-section rows).
- DELETE v1 row C40 ("The handover memo lists route F2-3 as still closed ...").
- INSERT the 31 rows below in place of the deleted block (after C4). Every other row (memo rows, files, -5 penalty) stays.
- Final count must be 49 criteria, positive weight 119.

| New # | Weight | Criterion |
|---|---|---|
| 5 | +3 | Reports the T1 loading at its 11 kV terminals at the 09:00 handover as 4.514 MVA (accept 4.509 to 4.519 MVA). |
| 6 | +4 | Reports T1 reactive power at its 11 kV terminals at the 09:00 handover as -1.508 Mvar (accept -1.510 to -1.506 Mvar, or that magnitude stated as flowing from the 11 kV busbar into T1). |
| 7 | +4 | Reports the T2 loading at its 11 kV terminals at the 09:00 handover as 9.536 MVA (accept 9.525 to 9.546 MVA). |
| 8 | +4 | Reports T2 reactive power at its 11 kV terminals at the 09:00 handover as 6.311 Mvar into the 11 kV busbar (accept 6.304 to 6.318 Mvar). |
| 9 | +2 | Reports the voltage of 11 kV section A at the 09:00 handover as 11.039 kV (accept 11.037 to 11.042 kV). |
| 10 | +2 | Reports the voltage of 11 kV section B at the 09:00 handover as 11.189 kV (accept 11.186 to 11.191 kV). |
| 11 | +3 | Reports the voltage of substation S2 at the 09:00 handover as 10.986 kV (accept 10.983 to 10.988 kV). |
| 12 | +4 | Reports the current in route F1-1 at the 09:00 handover as 103.6 A (accept 103.47 to 103.69 A). |
| 13 | +4 | Reports the current in route F2-1 at the 09:00 handover as 147.4 A (accept 147.20 to 147.50 A). |
| 14 | +4 | Reports the current in route F3-1 at the 09:00 handover as 250.0 A (accept 249.76 to 250.27 A). |
| 15 | +4 | Reports the current in route F4-1 at the 09:00 handover as 244.8 A (accept 244.52 to 245.02 A). |
| 16 | +4 | Reports the current in route F1-2 at the 09:00 handover as 32.34 A (accept 32.30 to 32.37 A) with active power flowing from S1 to S2. |
| 17 | +4 | Reports the current in route F1-3 at the 09:00 handover as 45.07 A (accept 45.02 to 45.12 A) with active power flowing from S3 to S2. |
| 18 | +4 | Reports the current in route F1-4 at the 09:00 handover as 60.26 A (accept 60.19 to 60.32 A) with active power flowing from S4 to S3. |
| 19 | +4 | Reports the current in route F2-2 at the 09:00 handover as 119.9 A (accept 119.76 to 120.01 A) with active power flowing from S5 to S6. |
| 20 | +4 | Reports the current in route F2-3 at the 09:00 handover as 22.33 A (accept 22.30 to 22.36 A) with active power flowing from S6 to S7. |
| 21 | +4 | Reports the current in route F3-2 at the 09:00 handover as 94.81 A (accept 94.71 to 94.91 A) with active power flowing from S8 to S9. |
| 22 | +4 | Reports the current in route F3-3 at the 09:00 handover as 71.32 A (accept 71.24 to 71.39 A) with active power flowing from S10 to S9. |
| 23 | +4 | Reports the current in route F4-2 at the 09:00 handover as 71.56 A (accept 71.48 to 71.63 A) with active power flowing from S11 to S12. |
| 24 | +4 | Reports the current in route IC-1 at the 09:00 handover as 63.97 A (accept 63.90 to 64.04 A) with active power flowing from S10 to S3. |
| 25 | +4 | Reports the current in route IC-2 at the 09:00 handover as 92.82 A (accept 92.72 to 92.92 A) with active power flowing from S11 to S6. |
| 26 | +4 | Reports the current in route NOP-1 at the 09:00 handover as 96.47 A (accept 96.37 to 96.58 A) with active power flowing from S8 to S4. |
| 27 | +4 | Reports the current in route NOP-2 at the 09:00 handover as 22.43 A (accept 22.40 to 22.45 A) with active power flowing from S12 to S7. |
| 28 | +1 | Reports the active power drawn from the 33 kV infeed at the 09:00 handover as 11.44 MW (accept 11.427 to 11.451 MW). |
| 29 | +1 | Reports the reactive power drawn from the 33 kV infeed at the 09:00 handover as 5.523 Mvar (accept 5.517 to 5.529 Mvar). |
| 30 | +5 | Reports the network losses at the 09:00 handover as 198.9 kW (accept 198.4 to 199.3 kW). |
| 31 | +1 | Reports the C1 output at the 09:00 handover as 1207 kvar (accept 1205.5 to 1207.6 kvar). |
| 32 | +1 | Reports the PV-1 export at the 09:00 handover as 2500 kW. |
| 33 | +1 | Reports the PV-1 reactive absorption at the 09:00 handover as 821.7 kvar (accept 821.2 to 822.3 kvar). |
| 34 | +2 | Identifies the 420 m type 185 section of route F3-1 (the section after joint J9) as the cable section loaded highest relative to its rating at the 09:00 handover. |
| 35 | +2 | Reports that section's loading at the 09:00 handover as 69.45 % of rating (accept 69.35 to 69.55 %). |

## 4. Ideal Flow
- Analyze: paste the whole box from ideal-flow-analyze.txt (wording changed in the first sentence).
- Execute & Generate: paste the whole box from ideal-flow-execute-generate.txt (all numbers changed).
- Synthesize: one edit: `the highest-loaded section (F4-1, 185 after J4)` -> `the highest-loaded section (F3-1, 185 after J9)`.
