# Task 20 MV-20 (Bramhall Colliery mine ventilation; Mining): status

- **Recipe:** DH-19 v3, applied at v1 (playbook 16-CASE-STUDY-TASK-19-DH19.md).
- **Model:** Atkinson airways, p = R Q|Q|, with R = k L per / A^3 per section. Regulators are orifices, R = rho/(2 (0.65 A)^2). The standby fan curve closes the circuit through the DS and US shafts. Node pressures are gauge, relative to the surface.
- **Log state at 08:00:**
  - standby fan in service (main fan tripped 04:10, held at 06:30; the +5 deg blade change was never made);
  - REG-E 3.6 m2 (reset deferred 07:55);
  - REG-T 1.0 m2;
  - door D1 open, so X1 carries air;
  - ST-7 replaced by brattice (3.5), so X2 carries air;
  - the C face is 28.60 m3/s, below the 30.0 minimum.
- **Crossed corners** (same profile, lengths within 20-26 %): J2 C1/I3 P2 360/450, J5 C2/R2 P5 350/440, J7 W1/X1 P3 380/470, J9 E1/X2 P4 280/360. Strict simulated scores 17.1, 17.1, 20.7 and 17.1. Every log slip scores 13 or below.
- **Rubric v1:** 39 criteria, +111, longest 162 characters. Numeric rows (24 x 4) chosen by the sensitivity greedy, with series duplicates excluded (R1 = W2, I1 = fan, T1 = I4). Memo rows are citation-only where a state is graded elsewhere (#99).
- **PDF:** 3 pages, one 8-bit DeviceRGB image, no mask; pdfium renders page 3; metadata clean; no leaks. Every leader was checked in code to land on its own section.
