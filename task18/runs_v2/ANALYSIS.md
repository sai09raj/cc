# HOLLOWAY-18 v2 platform runs: 6 of 6 scored 100 (about 35 to 39 min)

Two trajectories were analysed (`88f55926`, `aa4db3cb`). Both runs:
- read the line C beams correctly from the framing plans;
- read rows C/1 to C/4 of the column schedule correctly;
- took the 6.3 m load strip from 6000 and 6600;
- applied every log trap;
- matched every value exactly.

One run cropped the drawings and pixel-analysed them about 45 times. The traps I added did not work:
- "Label written above the beam" is a stated rule and the labels are clean text, so the model reads them perfectly.
- A table row next to a near-identical row is still read correctly.
- The load-strip rule is stated in the data sheet, so the model computes it directly.

**Conclusion.** A model with tools does not make attribution mistakes on clean text labels or tables, even with near-identical neighbours. The only misreads seen on the platform so far were:
- CW-200: near-equal adjacent vertical dimensions on a sheet drawn to scale;
- KINGSMEAD: lengths of jointed sections meeting at a corner of a route path.

Both are spatial, not text lookups. HOLLOWAY v2 relied on text lookups.
