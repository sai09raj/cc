# Case study: Task 16, CW-200 (first stump by completed low scores)

**Result.** Version v3 passed: Model A (claude-opus-4-8, max) scored **23, 22, 41, 95, 100**. All five runs completed with no timeouts or disconnects. Three runs scored below 50, which is the platform rule.

This is the first task in this project that stumped the model on reasoning rather than on running out of time. Reuse this recipe.

Files are in `task16/`:
- `v7/`: the final model, solver, renderer and key.
- `platform_v3/`: the entered package.
- `artifact/cw200_v3.pdf`: the packet.
- `STATUS.md`: the full history.

---

## 1. What the task is

You are the day-shift process engineer for a pumped cooling-water system. The packet (5 pages, metadata-stripped) contains:
- a data sheet with pump curves, pipe and loss rules, controller rules and physics notes;
- a night-shift operating log of 18 entries;
- three isometric sheets: the ring main to scale, the gravity side to scale, and branch details not to scale.

The model must find the 09:00 steady state and report:
- 2 pump flows, PI-100, 6 exchanger flows, the riser, CW-208 and the outfall;
- the tank level and whether it overflows;
- 6 ring-segment flows with their directions;
- the controller state and the valve opening;
- the minimum outfall pressure and where it occurs;
- 3 figure readings;
- a memo of the line-up.

The deliverables are the solver source, a results file and the memo.

## 2. Why it worked: the five ingredients

1. **A fully coupled system, so one slip fails nearly everything.**
   - The riser discharges below the TK-1 water surface. The tank level therefore sets the riser flow, and the riser flow feeds back into the pumps, PI-100, the ring and every exchanger.
   - Before coupling (v1), a misread on the gravity side cost only that side, about 16 of 71 points.
   - After coupling, any single misread or coding slip fails 13 to 18 of the 18 numeric criteria.
   - The simulated score for one misread fell to between 23 and 37.
2. **Answers to 4 significant figures, graded on explicit accept ranges.**
   - Write criteria in the form "Reports X as 74.90 L/s (accept 74.82 to 74.98 L/s)".
   - With "within 0.1 %", the LLM grader passed values that were 0.1–0.4 % off. In v2 it gave 79 to a run that strictly scored 30.
   - Explicit ranges made the grader exact. In v3, the run scored 95 equals 104/109 by hand count.
   - This is fair only because the data sheet fixes every formula and constant (friction formula, g, ρ, ν, every K, junction energy rule). An exact solve then agrees with the key to about 1e-6.
3. **77 % of the weight on the numeric results.**
   - Weights: +5 per main flow, PI-100 and level; +4 per ring segment.
   - The line-up, memo items, files and figure readings are +1 or +2 each, so the easy parts cannot carry a run past 50.
4. **Many independent, fair decision points, the kind the runs actually missed.**
   - Two near-equal adjacent vertical runs on a to-scale sheet (CW-208's 19 000 mm drop next to CW-211's 18 000 mm rise). Runs swapped them in v1 (2 of 4), v2 (1 of 4) and v3 (1 of 5), even with leaders on every label.
   - Up/down legs in the not-to-scale branch details (details A, C, D and E). One run per round read a rise as a drop.
   - Pipe-rack rise and drop on the ring, so tee elevations must be chained from sheet to sheet.
   - One exact rule in a note: a fitting at a point counts as upstream of it, which includes the crest elbow. Runs that missed it got the tank level about 25 mm off.
   - Enough coupled code that coding slips happen. One v3 run dropped every loss on one branch.
   - Every one of these is legible and determinate. Three blind solves of the final PDF matched the key to 6 significant figures.
5. **Iterating on real platform trajectories, not local probes.**
   - Local Opus 5.5 probes solved every version exactly, so they are a fairness check only, not a difficulty measure.
   - The difficulty came from reading what the platform runs actually got wrong and adding more fair decision points of that kind.

## 3. Iteration history

| Version | Change | Runs (platform) | Strict count | Main losses |
|---|---|---|---|---|
| v1 | Gravity side decoupled (free-discharge riser); 0.5 % tolerances; 3-s.f. answers | 96, 78, 59, 59 | same | 18/19 swap (×2), detail E as a drop, pressure-head vs energy-head at tees |
| v2 | Submerged riser (coupling); ring pipe-rack offsets; explicit junction-energy note; 4 s.f.; 0.1 % tolerances; numeric weight 77 % | 40, 100, 79, 91 | 22, 100, 30, 91 | grader lenient on %; 19000 misread; detail E; crest note 3 |
| v3 | Explicit accept ranges; up and down legs in details A, C, D (4 elbows each) | **23, 22, 41, 95, 100** | same | coding slip (CW-206 losses), 18/19 swap, gravity-side model, level only |

Earlier probes that failed for this task (mistakes #84–#87) taught that each of the following, used alone, is solved by Opus at max effort:
- 3D/isometric reading;
- perception (counting, tracing, OCR);
- a single physics trap (siphon column separation);
- coupled regimes plus log state.

What made the difference was combining them, so that one slip anywhere fails nearly all criteria, and grading strictly.

## 4. Fairness gates passed (keep all of them)

- **Blind solve of every final PDF.** A subagent with no access to the key solved each version from the PDF alone. Every value matched, and each ambiguity it reported was fixed before entry: hidden labels, label placement, implicit ring elevation, and the low-alarm log entries.
- **The log is consistent with the physics.** Every log interval was replayed against the solver:
  - auto-start at 23:20;
  - low alarm standing from 23:20 to 01:40 (PI-100 2.97 < 3.0) and clearing when HV-204 closed (3.27);
  - no auto-start of D at 09:00 (3.21).
- **Regime margins are clear.** At 09:00 the tank is 0.68 m below the weir and FV-201 is 0.34 L/s short of its setpoint. Ambiguous boundary cases were avoided.
- **Every rule a value depends on is stated.** That includes energy continuity at junctions, the riser exit against the tank level, the PI-100 definition, the alarm and auto-start setpoint, and column separation.
- **The Ideal Flow, rubric and key are generated from the same `key.json`.** One formatter produces all three, which prevents the C2-type mismatches reviewers flagged before.
- **Metadata is stripped.** No Info, ID or XMP, and the build asserts that no answer value appears in the PDF text.

## 5. Rubric template that worked (40 criteria, 109 positive points)

- 3 × +1 figure readings: tee elevation, riser inlet elevation, elbow count.
- +2 for the running pumps.
- 12 × +5 numeric results: pump flows, PI-100, E-201 to E-205, riser, CW-208, outfall, level.
- +1 E-206 zero; +2 not overflowing.
- 6 × +4 ring segments, each with direction and an accept range (a small segment gets an absolute range).
- +2 controller not holding; +1 valve fully open; +2 minimum pressure; +1 location (accept a point or the start of a separated stretch).
- 8 × +1 memo line-up items, each citing its log entry (P-201A cites the 22:00 handover).
- 3 × +1 deliverable files.
- −5 for any value the response's own program does not compute.

Every criterion is 201 characters or fewer, atomic and self-contained. It names the item, the time, the value and the range.

## 6. How to replicate on a new task

1. Pick an engineering system whose answer is a deterministic function of a fully specified packet, with **strong coupling**, so every reading or rule decision feeds every graded value.
2. Put the geometry or data in **drawings that need reading**: to-scale sheets with near-equal adjacent dimensions, up/down legs in details, and elevations chained across sheets. Add a log or record that fixes the operating state.
3. State **every formula, constant and convention** in the data sheet. This is what makes 4-significant-figure grading fair.
4. Build the reference solver, the renderer and `key.json` from **one model file**. Generate the rubric and Ideal Flow from the key.
5. **Blind-solve** the final PDF with a subagent that has no key access. Fix every ambiguity it reports, then solve again.
6. Grade with **explicit accept ranges**. Put about 75 % or more of the weight on the coupled numeric results.
7. Enter on the platform and **read every trajectory**:
   - recompute the strict score yourself and compare it with the platform's;
   - list the slip each run made;
   - add more fair decision points of the same kind;
   - never add ambiguity.
8. Give the user a **field-by-field edit list** between versions: attachment, prompt line, rubric rows with full new text, Ideal Flow numbers. Then check their screenshots.

## 7. Process lessons with the user

- The user enters everything by hand. Always give exact find/replace edits or the full text of each field to paste, never "see the file".
- Check every screenshot against the files value by value. Typing slips happened every round: "neew", "operating state", a missing "with", and stale v1 sentences left in the v2 Synthesize box.
- The Model A identity changes per task (Opus 5.5 or Opus 4.8). Design for the stronger one.
- Pass rule: **at least 3 completed runs below 50.**
