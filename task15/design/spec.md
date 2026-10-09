# FIRE-15 packet text (source for the PDF text pages)

## 1. Purpose
A district fire agency stations seven initial-attack crews for a lightning day. Each crew is based
at one of 14 candidate stations (several crews may share a station). This packet defines the
landscape, weather, lightning, fire spread, crew behaviour and loss used to compare stationing plans.
All quantities are integers; every rule below is exact.

## 2. Landscape (Figure 1)
The district is a 128 x 128 grid of 15 m cells. Cell (x, y) has x = 0..127 from west to east and
y = 0..127 from north to south. "Row-major order" means by y, then by x (smallest first).
Figure 1 divides the grid into 16 x 16 blocks of 8 x 8 cells; block (bx, by) holds cells with
x div 8 = bx and y div 8 = by, and every cell of a block has the block's cover:
W water and R rock do not burn; G grass, B brush, T timber and H houses burn.
The 14 candidate stations S1..S14 are cells marked in Figure 1 with their (x, y).

## 3. Weather (Figure 3)
Each scenario A, B, C, D has a wind that is constant over each period of 120 steps
(steps 0-119 are period 1, ..., steps 840-959 are period 8). Figure 3 gives each period's direction
(the direction the wind blows toward: N, NE, E, SE, S, SW, W, NW) and speed class (calm,
moderate or strong).

## 4. Generators
LCG: x' = (1103515245 x + 12345) mod 2^31.
Each scenario has a lightning generator seeded with its seed and a spread generator seeded with
7 x seed + 1 (Figure 2). Each draw advances the generator once and uses the new value.

## 5. One time step t (t = 0, 1, 2, ...)
Phase 1, lightning. If t < 480: draw L from the lightning generator; if (L div 256) mod 1000 is
below the scenario's strike rate (Figure 2), draw X then Y from the same generator and strike cell
((X div 256) mod 128, (Y div 256) mod 128). A strike on a burnable, never-ignited cell ignites it
as a new fire: fires are numbered 1, 2, 3, ... in ignition order, the cell starts burning with its
cover's burn time (Figure 2), and the fire's ignition step is t. Other strikes do nothing.

Phase 2, spread. Take the cells burning at this point in row-major order. For each, look at its
eight neighbours in the order N, NE, E, SE, S, SW, W, NW (N is y - 1, E is x + 1). A neighbour is
eligible if it lies on the grid, is burnable and has never been ignited (not burning, not burnt,
not marked earlier in this phase). For each eligible neighbour, and only then, draw R from the
spread generator and compute r = (R div 65536) mod 1000. Its chance p (per mille) is
  p = floor(base(cover of the neighbour) x wind factor(speed class, angle) / 100),
and for the diagonal directions NE, SE, SW, NW additionally p = floor(p x 70 / 100). The angle
is the number of 45-degree steps between the spread direction (from the burning cell to the
neighbour) and the direction the wind blows toward: 0, 1, 2, 3 or 4 (Figure 2 gives the factors).
If r < p the neighbour is marked: it will start burning at the end of this step as part of the
burning cell's fire.

Phase 3, crews, in crew order 1..7 (Figure 4 gives each crew's speed and capacity).
- A travelling crew whose arrival step is t or earlier arrives: it stands on its fire's ignition
  cell and starts working.
- A returning crew whose return step is t or earlier is back at its station and becomes available.
- A working crew then puts out up to its capacity of cells, one at a time: each time it takes the
  burning cell of its own fire nearest to where it stands (Manhattan distance |dx| + |dy|; ties to
  the first cell in row-major order), puts it out (the cell is burnt and no longer burns) and
  stands on that cell. Marked cells are not burning yet and cannot be put out.

Phase 4, burning. Every cell still burning loses one step of remaining burn time; at zero it is
burnt. Then every marked cell starts burning with its cover's burn time.

Phase 5, release. A working crew whose fire has no burning cell left starts returning: its return
step is t + 1 + ceil(d / speed), with d the Manhattan distance from where it stands to its station.

Phase 6, dispatch. A fire is reported at step (ignition step + 10). Go through the fires in number
order; a fire is dispatched if it is reported (t is at least its report step), has no crew yet and
still has a burning cell. It gets the available crew with the smallest travel time
ceil(d / speed), d the Manhattan distance from the crew's station to the fire's ignition cell (ties
to the lower crew number). That crew becomes travelling with arrival step t + 1 + travel time.
If no crew is available, dispatching stops for this step. A fire is dispatched at most once.
A crew is available only while at its station and not assigned.

## 6. End of a run and loss
After step t the run ends if t + 1 = 960, or if t + 1 >= 480 and no cell is burning.
Burnt cells are all cells that ever burned (including cells put out and cells still burning
at the end). Scenario loss = burnt cells + 9 x burnt house cells. A plan's total loss is the sum
of its losses in scenarios A, B, C and D.

## 7. Plans and objective
A plan gives the station of each crew 1..7: 14^7 = 105,413,504 plans. The optimal plan has the
smallest total loss; ties go to the plan with the smaller station number for crew 1, then crew 2,
and so on.
