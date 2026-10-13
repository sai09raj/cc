# HOLLOWAY-18 v1 platform runs (Model A)

Scores: **97, 97, 71**. Two trajectories were analysed: 97 (`c415cec1`) and 71 (`5b3eb079`). Both finished in about 30 minutes.

**The 97 runs** read every drawing value correctly, applied every log trap and matched all 30 values exactly.

**The 71 run** read every member, storey, bay, base, brace, connection and load correctly. Its only slip was the small rotated splice dimensions:
- it read grid 1 as L2 + 600;
- it read grid 2 as L1 + **500** and grids 3 and 4 as L2 + **500** (the drawing says 600).

That slip moved only the splice moments and a few nearby values (grid 2 splice -47.79 against -45.30; grid 3 splice -26.70 against -24.62; roof sway 17.67 against 17.64), so the run still scored 71.

## Why v1 was too easy
- The drawing is a single elevation of frame C. Every member is labelled on itself, so there is no attribution decision: each label sits on exactly one member.
- The only misread that happened, a small rotated dimension, changes local values only, because the splice position barely affects the frame stiffness.
- Log traps were all solved, as in KINGSMEAD and CW-200.
