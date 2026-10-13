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

## v1 platform runs (2026-10-13)
- Runs 12 and 11 (trajectories 04b8779f, 4f8516a9), both the same misread: X3's DN100 470 m label, which sits in the B2/X3 gap at H6, was given to B2. All other runs scored 100. Playbook #98.

## v2
- Two more gap traps added in render.py:
  - L1 DN80 640 m now sits in the A4/L1 gap near H4, next to A4's DN80 390 m.
  - X3 DN100 460 m now sits beside VC2, between A2 and X3.
- B2 DN125 510 m label moved into the B2/X3 gap above VC7 (4th gap trap).
- Each of the four gap misreads simulates to 12.8. Candidates rejected: B3/L2 swaps (100, series path through unloaded H7); L1 420 to C3 (24.8) and L2 340 to D2 (15.6) have no parallel gap to place them in.
- Network data, key, rubric and Ideal Flow are unchanged. Only the plan sheet and the file name changed (artifact/dh19_v2.pdf).
- The PDF metadata scan is clean and the leak check passes.
- v1 files are archived in model_v1/ and platform_v1/.
- Fix (#100): the plan page was blank in macOS Preview because its 1-bit soft mask had been set to /DeviceRGB. The drawing is now flattened to RGB with no mask, and make_packet.py asserts there is none.
