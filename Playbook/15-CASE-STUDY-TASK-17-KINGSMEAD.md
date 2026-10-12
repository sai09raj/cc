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

## 2a. v1 mistakes that v2 fixed: do not repeat them

| # | v1 mistake | Effect in v1 | v2 fix |
|---|---|---|---|
| 1 | Route plan had one route per line, mostly single-section routes and clear labels: **no attribution decisions** | 4 of 5 runs scored 100 in about 19 min | Every route has 2 or 3 jointed sections; routes share trenches leaving the primary; near-equal same-type lengths (185/420 and 185/520) meet at the S1 corner on different routes |
| 2 | Difficulty was built on the **log traps** (NOP-1 left closed, T1 MANUAL, C1 in, PV cap, BS open). Simulated at 14 to 22 when missed | Opus replayed every trap correctly in every run; those simulations meant nothing | Keep the traps for fairness and story, but put the difficulty in the drawing attribution that feeds the coupled solve |
| 3 | Rubric weight sat on **insensitive quantities**: many bus voltages at +/-2 V, which barely move under a misread, and only 9 of 16 route currents graded | The one run that misread still scored 59 | Weighted by sensitivity ranking (`rank.py`, `sens.py`): all 16 route currents and T1/T2 Mvar at +4, losses at +5, voltages cut to A, B and S2 at +2 or +3 |
| 4 | Accepted single-misread simulations **at or above 50** (repair added in series 50, IC-1 length 53, repair ignored 64) | Showed that a realistic slip would not pass the gate | Before entry, every plausible single misread must simulate to about 40 or below (v2: 19 to 43). The platform adds about 5 to 10 points for memo and file rows |
| 5 | The **one misread that happened** (the 510 m section past J3 given to F3-3) was not followed up with more decision points of that kind | Only 1 of 5 runs below 50 | Studied the slip that did happen and multiplied it: more corners and trenches where sections from different routes meet |
| 6 | An early **to-scale** plan was illegible | Would have been an unfair misread | Not-to-scale plan with every length printed; difficulty comes from attribution, not from legibility. Labels near corners were moved off ambiguous spots (F2-1 300/610 after the v2 blind solve) |
| 7 | Infeed metering point was **unstated** (P33 or the source EMF), found by the v1 blind solve | Two defensible answers for infeed and losses | Data sheet states "metered at P33"; also stated: transformer impedance the same on every tap, and the definition of section loading |
| 8 | Ideal Flow text carried values **typed by hand** (the v1 Synthesize box still said "F4-1, 185 after J4" after the key changed) | Mismatch risk between rubric and Ideal Flow | All three Ideal Flow boxes and the rubric regenerated from `key.json`; the user's screenshots are checked value by value |

**Rule.** If v1 runs mostly score 100, do not add more logic traps. Find the reading decision the one low run missed, put several more fair decisions of that kind into the drawing, and move the rubric weight onto the quantities those misreads change.

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
