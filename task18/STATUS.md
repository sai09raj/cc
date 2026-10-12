# Task 18 HOLLOWAY-18 (steel frame, Civil Engineering): status

- Recipe: the Task 16/17 coupled-solve pattern. A plane-frame stiffness analysis of a 3-bay, 4-storey steel frame with splices, simple connections, braces and a temporary-works site log.
- Drawing decision points:
  - rotated column labels either side of the splices, including the short L2-to-splice length labelled with a leader;
  - rotated storey dimensions 3750, 3600 and 3600;
  - bays 7500 and 7200;
  - simple-connection symbols;
  - storage zone and AHU-2 positions dimensioned from grid lines.
- Log traps: BR2 out; the L2 bay 3-4 beam simple at grid 4; TP-1 removed; storage zone S loaded; AHU-2 at the temporary position T.
- Rubric v1: 43 criteria, +127, 30 numeric rows. Every likely single misread simulates to 9-22 (`model/score_sim` via `pick.py`).
- Next: blind solve of `artifact/holloway_v1.pdf`, then upsize the brace (114.3x5.0 CHS buckles under 124 kN), then the platform package.
