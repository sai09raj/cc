# Task 16 — ISO-16 (piping isometric reading; draft stage)

Design aim (Rule Zero, QM tip 2026-10-10): difficulty must come from reading a dense 3D diagram exactly, not
from compute. Iterate as the tip says: draft -> blind probe -> read the trajectory -> close easy paths.

- proto/network.py: authored 3D cooling-water network (pump P1, header CW-101 DN150, branches CW-102..107,
  tees T1-T6, consumers C1-C6, END1), 30 elbows, 6 gate valves, 1 check valve, 1 reducer.
- proto/build.py: 3D geometry and answer key; proto/render.py: isometric (not to scale, compressed lengths,
  crossing breaks with depth from the viewer at east-south-above).
- Probe 1 (opus, 40 min, extraction only): node coordinates, length per DN, elbow count. Key in the scratch
  probe folder: lengths DN150 41,100 / DN100 17,900 / DN80 21,250 / DN50 8,950; 30 elbows.
