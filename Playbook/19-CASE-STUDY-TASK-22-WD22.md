# Case study: Task 22 WD-22 (Fenwick Hill water supply zone, 24 h extended-period simulation), pre-run record

**Status:** built and gated at v1; platform runs pending. Update this file with the run results and the gate F validation.

## 1. Why this shape
Tasks 16–21 all had one template: data sheet + event log + route plan, one steady-state snapshot, flows and voltages, memo citations (#108). WD-22 keeps the one ingredient that stumps (crossed-corner attribution on a drawing feeding a coupled solve) and changes everything else:
- **no log;** the state is fixed and the work is in time;
- **answer = time series:** 96 steps of 15 min; pump events from tank-level hysteresis; hourly levels; energy and cost under a two-rate tariff; a pressure deficit over an interval;
- **decision over re-runs:** five candidate P-1 start levels, each a full-day simulation; the result is non-monotone (2.40 and 2.60 breach the reserve, 2.00/2.20/2.80 do not), so no shortcut;
- **second visual:** the hourly demand multipliers exist only on a bar chart (grid every 0.05, every bar top on a grid line, stated on the chart).
Compute is tiny (one run of all five candidates takes seconds); this is not a timeout design.

## 2. Build order (as done)
1. `net.py` single source of truth; `eps.py` global-gradient solver per step (pipes, parallel pumps with non-return valve, PRV active/open rule, tank as fixed head) and explicit level update.
2. Tuned for an event-rich day: tank 12.0 m, demands ×0.775, controls P-1 2.40/4.20, P-2 1.90/3.00, J8 at 77.0 m so its pressure dips below 20.0 m in the morning trough.
3. `pick.py` (every same-type swap at every junction + every chart bar ±0.05) → `sens.json`; `greedy.py` picks 22 numeric rows; forced: energy, cost, lowest pressure, candidate 2.00/2.80 results, minimum level.
4. Corner pairs widened into the 28–33 % band (B3 490, C1 460/390 DI200, C3 CI200 350) and re-simulated.
5. `render.py` plan (4 crossed corners at J3, J5, J6, J7 using the 16-CASE-STUDY geometry, leader rule in the title) and chart; `check_leaders.py` proves every leader lands on its own section.
6. `gen_sheet.py` writes the data sheet from `net.py` (every rule: formula, pump curve, power, PRV, tank, step order, control order, initial states, event-time definition, tariff, service checks, decision rule). It runs to two pages.
7. `make_packet.py` (RGB flatten, metadata strip, leak check), `platform/build.py`, gate, `indep.py`, `score_sim.py`.

## 3. Lessons so far
- **#107:** integrated quantities accumulate formula variants. My own re-solve used 0.54 and drifted 0.0022 m. Ranges are ±0.005 m, and the strict re-grade includes a textbook-exponent case that must score 100.
- Keep chart-only numbers (0.05 grid) out of the Ideal Flow (gate B6 caught it).
- Pipe type codes must not collide with other names (pump P-1 vs pipe type P1): use descriptive codes (DI200, CI200, PVC150).
- Duplicate graded values arise from the decision too (candidate equal to the present setting; two candidates giving identical days): exclude them.
