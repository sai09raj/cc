# Task 16 — ISO-16 (piping isometric reading; draft stage)

Design aim (Rule Zero, QM tip 2026-10-10): difficulty must come from reading a dense 3D diagram exactly, not
from compute. Iterate as the tip says: draft -> blind probe -> read the trajectory -> close easy paths.

- proto/network.py: authored 3D cooling-water network (pump P1, header CW-101 DN150, branches CW-102..107,
  tees T1-T6, consumers C1-C6, END1), 30 elbows, 6 gate valves, 1 check valve, 1 reducer.
- proto/build.py: 3D geometry and answer key; proto/render.py: isometric (not to scale, compressed lengths,
  crossing breaks with depth from the viewer at east-south-above).
- Probe 1 (opus, 40 min, extraction only): node coordinates, length per DN, elbow count. Key in the scratch
  probe folder: lengths DN150 41,100 / DN100 17,900 / DN80 21,250 / DN50 8,950; 30 elbows.

## Probe 1 result (schematic isometric): solved
Opus read every coordinate (13/13) and every length exactly; its elbow count (29) was right and my key (30)
wrong (the main turns through tee T6). A clean schematic iso with dimension strings is not hard for it.

## v2 draft: 3D perspective views (proto3d/)
scene.py: pipe rack (columns on grid, beam levels TOS +4500/+7000), 8 equipment items with tagged nozzle
elevations, 10 lines (headers CW-201 DN200 at +7000 and CW-210 DN150 at +4500, branches). render3d.py:
shaded perspective, two views (from SE and from NW), floor survey grid every 1500 mm. Every vertex lies on the
1500 grid and every horizontal run at a TOS level or nozzle EL (stated in the conventions page).
Key: lengths DN200 30,000 / DN150 40,000 / DN100 47,200 / DN80 39,500 / DN50 11,100; 19 elbows.
Probe 2 (opus, 40 min) launched on the two views.
