# Case study: Task 21 TR-21 (Hartsdown Tramway 750 V DC traction supply), fifth stump

**Result:**
- v1: all 6 runs scored 14.
- v2: 14, 14, 14, 14, 18 and 100.
- Both versions pass (at least 3 completed runs below 50). Model A = claude-opus-4-8. Every score was validated by reproducing it from the run's own reading.

## 1. The task

- **Platform entry:** Domain Electrical Engineering; subdomain "Railway Traction Power Supply — DC tramway load flow".
- **Physics:** a nonlinear DC load flow.
  - Section loop resistance r × L, from 5 conductor types.
  - Substations are E − R_i·I sources with diode rectifiers (no reverse current).
  - Trams are constant-power loads, I = P/V.
  - Solved by Newton iteration with an active-set check on the rectifiers.
- **Network:** 13 nodes, 16 routes, 4 substations (one out of service), 8 trams in a 07:30 SCADA snapshot.
- **Log traps (all solved by every run):** TSS-B out; TSS-D at tap +1 (850 V); TSS-C tap raise refused (835 V); X1 re-energised after repair; T150 stabled.
- **Memo finding:** T126 at N8 is at 591.4 V, below the 600 V minimum.
- **Drawing traps:**
  - Four crossed corners: N4, N9, N6 and N7.
  - One crowded junction at N3: two 450 m labels from different routes.
- **Rubric:** 38 criteria, +111. The 24 numeric rows (weight 4) were chosen by the sensitivity greedy, with series duplicates excluded (L1 = TSS-A, S5 = TSS-D).

## 2. What happened

| Version | Change | Runs | Reading |
|---|---|---|---|
| v1 | Leader rule NOT stated in words | 14 × 6 (identical values) | Every run read all 4 corners by proximity and never mentioned leaders. Identical answers mean an identical score, which looks like a defective task. |
| v2 | Packet only: rule stated on the drawing title and in the data sheet; renamed tr21_v2.pdf (prompt changed by one word) | 14 × 4, 18, 100 | The 100 run traced every leader. Its values equal the key, which proves the task fair. The other runs still swapped 2–3 corners. |

## 3. Platform checker flags met (each marked Invalid with a reason)

- **"Prompt Check For Multimodal Inputs":** the checker reads only the prompt text. Fix: name the drawing as a drawing in the prompt and say what exists only on it (#104, gate B15).
- **"Rubric Contradictory Criteria Check":** "X1 in service" vs "X1 current" (state vs flow), and "TSS-D 850 V" vs "TSS-C 835 V" (different substations). The checker's own text said "no clash". Mark Invalid with the reason.

## 4. Do and Don't

- **Do** state the leader rule from v1: "Each section label belongs to the section that its leader line touches." Put it on the drawing and in the data sheet.
- **Do** run the convergence audit whenever runs give identical scores (gate F):
  - extract each run's reading;
  - reproduce its values;
  - re-grade with the printed ranges;
  - confirm the key independently.
- **Do** keep a defence note ready: each run's values reproduce from its own reading, and the leaders are verified.
- **Don't** leave a reading convention unstated just because it is standard drafting practice. If every run converges on the rival reading, a reviewer can call it ambiguous.
- **Don't** expect stating the rule to destroy the stump. In TR-21 it kept 5 of 6 runs below 50.
