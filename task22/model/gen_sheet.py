"""Write packet/datasheet.txt from net.py (sheet 1 of 3)."""
import net as N
a, b = N.PUMP
pt = "\n".join(f"  {c:<7s} {d:<36s} internal diameter {D:.0f} mm, Hazen-Williams C = {C:.0f}" for c, (d, D, C) in N.PIPE.items())
nd = "\n".join(f"  {n:<4s} elevation {z:5.1f} m   base demand {q:4.1f} L/s" for n, (z, q) in N.NODE.items())
c1, c2 = N.CTRL["P-1"], N.CTRL["P-2"]
txt = f"""FENWICK HILL SUPPLY ZONE - 24 h EXTENDED-PERIOD SIMULATION - DATA SHEET (sheet 1 of 3)

Arrangement. Reservoir R (fixed water level {N.H_RES:.1f} m above datum) supplies pumping station PS, which holds two identical pumps P-1 and P-2 in parallel discharging into junction J1. The pipes joining junctions J1 to J12 and the service tank T are shown only on sheet 2 (pipe plan, not to scale). Each pipe consists of the sections shown on the plan, in the order shown, separated at joints (bars numbered Kn). Each section label on the plan belongs to the section that its leader line touches. Pressure-reducing valve PRV-1 joins J6 (upstream) to J10 (downstream) and feeds the low zone J10, J11, J12 through pipes L1 and L2. All pipes and valves are open. All heads and levels are in metres above the common datum except the tank level, which is measured from the tank floor.

Hydraulic model (solve the full network at every time step).
  Head loss in a pipe section (Hazen-Williams, SI units): h = 10.67 x L x Q^1.852 / (C^1.852 x D^4.87), with h and L in m, Q in m3/s, D the internal diameter in m. A pipe's head loss is the sum over its sections, with flow direction from higher to lower head. Minor losses are neglected.
  Pressure head at a junction = head at the junction - elevation of the junction.
  Pumps: each running pump adds head H = {a:.1f} - {b} x q^2 (H in m, q in L/s through that pump); running pumps share the station flow equally. There are no suction losses: pump suction head = {N.H_RES:.1f} m and pump discharge head = head at J1. A non-return valve prevents reverse flow through the station. With no pump running, the station passes no flow.
  Pump power drawn (kW) = 9.81 x Q x H / {N.ETA:.2f}, with Q the total station flow in m3/s and H the head added (head at J1 - {N.H_RES:.1f} m).
  PRV-1: when the head at J6 is at or above {N.PRV['setting']:.1f} m, the valve holds the head at J10 at exactly {N.PRV['setting']:.1f} m and passes exactly the low-zone demand. When the head at J6 is below {N.PRV['setting']:.1f} m, the valve is wide open with no head loss (head at J10 = head at J6).
  Service tank T: vertical cylinder, internal diameter {N.TANK['diameter']:.1f} m, floor at {N.TANK['base']:.1f} m; pipe TK enters at the tank floor. Head at the tank = {N.TANK['base']:.1f} + tank level. Within a time step the tank acts as a fixed head.
  Junction demand = base demand x the demand multiplier of the clock hour (sheet 3). Demands do not depend on pressure.

Pipe types (code on the plan):
{pt}

Junctions:
{nd}

FENWICK HILL SUPPLY ZONE - DATA SHEET (sheet 1, continued)

Time stepping. The day runs from 00:00 to 24:00 in 96 steps of 15 min. For each step starting at time t:
  1. Evaluate the pump controls with the tank level at t (P-1 first, then P-2).
  2. Solve the network steady state with the tank head at the level at t, the pumps running after step 1, and the demand multiplier of the clock hour containing t.
  3. Update the level: level(t + 15 min) = level(t) + Q_T x 900 / A, with Q_T the flow into the tank through TK in m3/s (negative when the tank empties) and A = pi x {N.TANK['diameter']:.1f}^2 / 4 the tank plan area.
  4. Step energy = pump power x 0.25 h; step cost = step energy x the tariff of the clock hour containing t.
  The tank level at a clock time is the level at the step boundary at that time; the level at 24:00 is the level after the last step.

Pump controls (tank level, in m from the tank floor). P-1 starts when the level is at or below {c1[0]:.2f} m and stops when the level is at or above {c1[1]:.2f} m. P-2 starts when the level is at or below {c2[0]:.2f} m and stops when the level is at or above {c2[1]:.2f} m. Between its start and stop levels a pump keeps its previous state. At 00:00 the tank level is {N.TANK['init']:.2f} m, P-1 is running and P-2 is stopped (their states before the 00:00 control evaluation). A pump event time is the step start time at which that pump's state changes.

Electricity tariff: GBP {N.TARIFF[0]:.2f} per kWh from 00:00 to 07:00 and from 23:00 to 24:00; GBP {N.TARIFF[7]:.2f} per kWh from 07:00 to 23:00.

Service standards. Minimum pressure head {N.P_MIN:.1f} m at every junction with a base demand above zero, checked on the network solution of every step (step start times 00:00 to 23:45). Tank reserve {N.RESERVE:.2f} m: the tank level must not fall below it at any step boundary from 00:00 to 24:00.

Operations review. The operations manager asks for the P-1 start level to be reviewed. Candidate P-1 start levels: {", ".join(f"{s:.2f}" for s in N.SETPOINTS)} m (the present setting is {c1[0]:.2f} m). For each candidate, simulate the same day with every other setting unchanged (P-1 stop level {c1[1]:.2f} m, P-2 levels {c2[0]:.2f} and {c2[1]:.2f} m). Recommend the candidate with the lowest daily energy cost among those that keep the tank level at or above the {N.RESERVE:.2f} m reserve at every step boundary.
"""
open("../packet/datasheet.txt", "w").write(txt); print(len(txt))
