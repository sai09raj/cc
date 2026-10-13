# Task 19 DH-19 (Ashgrove district heating; Mechanical / energy): status

- **Recipe:** KINGSMEAD spatial attribution.
  - A route plan in which every route has 2 or 3 jointed sections.
  - Near-equal section lengths meet at corners and nodes: A1/C1 at EC, B2/X3 470/470 at H6, C2/C3 at H9.
  - A meshed hydraulic network (X3, L1 and L2 all open), coupled to the thermal solution through consumer flow Q/(cp (Ts - 45)).
- **Log traps:**
  - A3 repaired with 290 m of DN125;
  - XV3 left open;
  - H7 isolated, but its node passes flow;
  - L2 isolation deferred;
  - setpoint 92 C.
- **Rubric v1:** 39 criteria, +108, explicit ranges.
- **Score simulation:** most single misreads land at 13-37; A1/B1 at 50.5 and A2/A3 at 56.9 are weak.
- **Blind solve:** matched all values exactly. Fixed:
  - EC exits separated, so no hidden leader;
  - XV3 defined as the X3 valve pair.
- **Audit:** PASS. 39 criteria, longest 189 characters; PDF clean.
- **Next:** platform entry and runs.
