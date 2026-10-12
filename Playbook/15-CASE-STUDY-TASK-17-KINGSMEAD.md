# Case study: Task 17, KINGSMEAD-11 (second stump by completed low scores)

**Result.** Version v2 passed: Model A (claude-opus-4-8, max) scored **43, 44, 39**. All runs completed with no timeouts, in 23 to 33 minutes. This confirms the CW-200 recipe (`14-CASE-STUDY-TASK-16-CW200.md`) in a second, different domain.

Files are in `task17/`:
- `model/`: `net.py`, `pf.py`, `state.py`, `render.py`, `make_key.py`, `make_packet.py`, `score_sim.py`.
- `artifact/kingsmead_v2.pdf`.
- `platform/`: prompt, rubric and Ideal Flow.
- `runs_v2/ANALYSIS.md`.

## 1. What the task is

You are the day-shift engineer at a 33/11 kV primary substation. The packet has 4 sheets, metadata-stripped:
- **Sheet 1, data sheet.** Cable R/X/ratings, the source, the transformers (impedance on the 11 kV side, tap ratio on the 33 kV side, same impedance on every tap), the AVC rule (the tap closest to 11.20 kV), loads, PV-1, C1, infeed metered at P33, and the section-loading definition.
- **Sheet 2, night-shift log** (8 entries) that leaves the network in a trap state:
  - BS open with T1 MANUAL on tap 9 and T2 AUTO, so reactive power circulates through the meshed 11 kV network (T1 at −1.508 Mvar);
  - NOP-1 left closed after the F1-3 repair;
  - NOP-2 closed with F2-3 not opened (a half-done transfer);
  - F1-3 repaired with 410 m of 185;
  - PV-1 capped at 2500 kW.
- **Sheet 3, single-line diagram.**
- **Sheet 4, cable route plan, not to scale.** Every route has 2 or 3 jointed sections. Routes share trenches leaving the primary, and labels sit near shared corners.

The model must report the 09:00 Newton-Raphson AC load flow:
- F1-3 Z, the taps, T1 and T2 MVA and Mvar;
- voltages at A, B and S2;
- all 16 route currents with their directions;
- the infeed at P33 and the losses;
- C1 and PV-1;
- the highest-loaded section;
- a handover memo.

## 2. v1 to v2: what turned 100s into 39 to 44

| Version | Plan | Rubric | Runs |
|---|---|---|---|
| v1 | One route per line, labels clear, mostly single-section routes | Voltage-heavy (+/-2 V barely moves under a misread) | 100, 100, 100, 100, 59 |
| v2 | 2–3 jointed sections per route, shared trenches, near-equal 185 lengths (420/520) meeting at the S1 corner on different routes | Re-weighted by **misread sensitivity**: all 16 route currents, T1/T2 Mvar, losses at +4/+5; voltages reduced | **43, 44, 39** |

**The slip.** All three v2 runs swapped the 420 m and 520 m 185 sections at S1 between F1-1 and F1-2. The log traps, the AVC, the circulating Mvar and the solver were all correct. One fair attribution decision on the drawing decided the task.

## 3. Lessons (add to the CW-200 recipe)

1. **Logic traps alone do not stump Opus.** It replayed every log trap correctly in all runs, both v1 and v2. The score loss comes from **drawing attribution**: which jointed section belongs to which route. That attribution feeds a coupled solve.
2. **Put near-equal values next to each other on different routes**, such as 420 and 520 of the same cable type at one corner, and 18 000 against 19 000 in CW-200. Both are legible to a careful reader, as the blind solve showed, and both were misread in practice.
3. **Choose graded quantities by a sensitivity ranking** (`rank.py`, `sens.py`):
   - Route currents and transformer Mvar move under any misread.
   - Bus voltages and the tap barely move.
   - Put the weight where a misread shows, then simulate every plausible single misread (`score_sim.py`). Each one should score below 50.
4. **The simulator predicts the platform.** The predicted strict score was 34.5 and the platform gave 39 to 44. Non-numeric rows (memo, files, F1-3 Z) add about 5 to 10 points, so aim for simulated misreads at or below 40.
5. **The same misread in all runs is normal.** Opus is consistent: a decision point it gets wrong, it gets wrong in most runs. One strong trap is worth more than several weak ones.

## 4. Fairness gates passed

- A blind subagent solve of the v2 PDF matched the key. Its one note, the F2-1 label near a corner, was fixed by moving the label.
- Infeed metering at P33 is stated explicitly. v1's blind solve had flagged P33 against the source EMF.
- Every rule is on sheet 1:
  - tap model;
  - AVC rule;
  - constant-power loads;
  - C1 scaling with V²;
  - PV pf absorbing;
  - section-loading definition.
- Rubric: 49 criteria, +119, longest 184 characters, explicit accept ranges, atomic, generated from `key.json` together with the Ideal Flow.

## 5. Process notes

- The user typed every field. Screenshot checks caught slips each round:
  - "6.311 MVA" for "6.311 Mvar";
  - "impedence";
  - a duplicated Synthesize block;
  - "results fiel".
- Give the v1→v2 edit list as exact rows to delete and insert, with old and new numbering explained, for example "delete old C5–C31, insert new C5–C35".
