# Case study: Task 19 DH-19 (Ashgrove district heating), third proven stump

**Result (v3):** every platform run scored 12 or 19, with Model A = claude-opus-4-8. It took three versions; this file records exactly what to do from v1 next time.

## 1. The task

- **Domain:** district heating, mechanical/energy. The energy centre EC feeds 12 substations through 15 pipe routes: branch routes A1–A4, B1–B3, C1–C3 and D1–D2, two loops (L1, L2) and the crossover X3.
- **Coupled hydraulic and thermal solve:**
  - Darcy–Weisbach with Swamee–Jain friction;
  - exponential supply heat loss with flow-weighted mixing;
  - consumer flow Q/(cp (Ts − 45)), solved iteratively;
  - pump dp = 2 × the index-node supply drop + 60 kPa.
- **Packet (3 pages):** a data sheet (every formula and constant), a control-room log, and a route plan drawing (not to scale; each section labelled with pipe size and length).
- **Log traps:** A3 repaired with 290 m of DN125; XV3 left open; H7 isolated but its node passes flow; L2 isolation deferred; setpoint 92 °C. Every run solved all of them in all three versions. They are not where the points are lost.
- **Rubric:** 39 criteria, +108. 75 % or more of the weight is on route flows, node temperatures, pump dp and heat loss, each with an explicit accept range.

## 2. Version history

| Version | Drawing | Runs (Opus 4.8) | What it taught |
|---|---|---|---|
| v1 | Natural label placement: corner labels at EC and H9, plus one label in the gap between the parallel B2 and X3 lines at H6 (DN125 470 / DN100 470) | 12, 11, rest 100 (2 of 6 below 50) | Both low runs gave X3's 470 m section to B2 (the gap label). The corner labels at EC and H9 caught nobody. They were mixed pipe sizes and not crossed. |
| v2 | Four gap labels, three of them in the same B2/X3 gap | 18, rest 100 (1 of 6) | Clustered labels look suspicious, so runs zoomed in 60–75 times and followed every leader. A gap misread also moves a section from one route to another, which changes the section count, and the valve-chamber bars let the model check that count. The 18 run dropped an untrapped label (D1 340 m). |
| v3 | Gap labels back to v1. **Four crossed corners** copying the KINGSMEAD S1 geometry, same pipe size, spread across the plan | **all runs 12 or 19** | Swap caught at H1 (A1/A2 DN150 330/420) in 2 of 2 sampled runs, H12 (D2/L2 DN80 250/340) 2 of 2, H8 (C1/C2 DN125 520/400) 1 of 2, H4 (A4/L1 DN80 390/640) 0 of 2. Runs finished in about 19–20 min with 55–63 tool calls. They did not spot the traps, so they did not slow down to check them. |

## 3. The crossed-corner recipe (exact geometry; code in `task19/model/render.py`, `CORNER`)

1. **Pick the pair.** At one node, route P's last section and route Q's first section have the **same pipe size** and **near-equal lengths**: a difference of about 20–35 % (330/420, 250/340, 400/520). The 390/640 pair (64 % difference) caught nobody. A swap keeps every route's section count, pipe-size sequence and total bar count, so no consistency check catches it.
2. **Draw the corner.**
   - P runs straight along the **edge of the node box**, 0.3 units from its centre on a 0.6 box, and Q leaves the node perpendicular to P. The corner point C is where P meets Q's line.
   - P's label box goes at C + 0.45·u_Q + 0.24·u_P, hugging Q's line, with a short leader back to P.
   - Q's label box goes at C + 0.62·u_Q + 0.74·u_P, lower and beside P's line, with a leader at C + 0.78·u_Q running to Q's line past the right of P's box.
   - Suppress the normal mid-section labels for those two sections.
   - The labels are crossed: reading by nearness gives the swap, and reading the leaders gives the truth.
3. **Keep it fair.** Every leader must clearly touch its own line and must not touch the other label box. Check at the model's zoom (crop each corner at 150 dpi).
4. **Spread the traps out.** Use 3 or 4 crossed corners at different nodes of the plan; never cluster them, and add no extra legend text about leaders. One extra natural gap label is fine.
5. **Simulate each swap.** Each single swap must score 40 or below on the rubric. Here they scored 33.0, 31.2, 15.6 and 25.7. Pick pairs whose swap moves the meshed flow split (a pair in series through an unloaded node, like B3/L2 through H7, scores 100 and is useless).

## 4. Package lessons from this task

- **#99:** a memo row that repeats a state already graded by a results row is flagged as "contradictory criteria". If the state is graded elsewhere, the memo row grades only the citation.
- **#100:** a soft mask set to /DeviceRGB makes macOS Preview show a blank drawing page. Flatten drawings to RGB before inserting them, and render every page with a second engine (pypdfium2) before handover.
- **False-positive flags:** "Rubric Contradictory Criteria Check" once invented a criterion ("L1 reported as not computed"). Mark it Invalid and give the reason: quote the real rows and show that one response can satisfy all of them.
- **Changing only the drawing** keeps key.json, the rubric and the Ideal Flow valid. The user's platform edits were then only the attachment and the file name in the prompt. Plan revisions so that only the drawing changes.
- **Ideal Flow:** example corners named in the Analyze step need not be the trap corners, as long as every value stated is true for the drawing.

## 5. Do it in one version next time

- Do: at v1, build the route plan with 3–4 crossed same-type corners (section 3), spread out, each simulated to 40 or below, plus at most one natural gap label.
- Do: weight the rubric by misread sensitivity (route flows, pump dp, heat loss), using explicit ranges.
- Do: before handover, check every image in a second PDF renderer; make memo rows citation-only where the state is graded elsewhere.
- Don't: rely on gap labels that move a section between routes when valve bars or joints let the model count sections.
- Don't: cluster traps or make one area of the drawing look busy; it makes the model slow down and check.
- Don't: use mixed pipe sizes or large length differences for a swap; the model rejects them.
- Don't: trust a blind subagent solve as the difficulty test. Blind solves read every label correctly while real runs still slipped.

## 6. Confirmed at v1 on the next task (MV-20, mine ventilation)

The recipe in section 3, applied from the first version, passed with 21, 35 and 14. One addition: a crowded junction where two labels with the same length belong to different routes (X1's P3 310 and C2's P4 310 at J8) also caught runs, which dropped or merged the two labels. Sequence: model, then sensitivity-chosen rubric, then crossed corners, then gate, then independent re-solve, then entry.
