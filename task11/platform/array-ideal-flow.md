## Analyze

```text
Read the packet and recover the full problem. Take the 64 turbine
coordinates from the table, not from the dots on the site plan. Measure
the two platform positions from the site plan's gridlines: P at (3200,
3000) and A at (-700, 2700). Read the cable catalogue step chart: C1
carries up to 4 turbines at 100 per metre, C2 up to 8 at 160, C3 up to
14 at 245, each type covering loads from just above the previous type's
capacity. Recover the layout rules: every turbine has one outgoing cable
and the cables form trees rooted at the platform; a cable's load is the
turbine it leaves plus everything upstream; lengths are Euclidean and
rounded half up to whole metres; turbine to turbine spans are at most
1300 metres while platform cables are unlimited; no two cables may
cross, touch or overlap except at a shared endpoint; at most B cables
end at the platform; each cable uses the cheapest type that carries its
load. Recognize the problem as a capacitated minimum spanning tree with
step costs, a span limit and a planarity constraint, and that capacity
14 makes exhaustive enumeration of feeder groups impossible.
```

## Execute & Generate

```text
Using only the standard library, offline, build a heuristic that
produces strong valid layouts (for example a savings or Esau Williams
start improved by local search that moves subtrees between feeders and
reattaches turbines, rechecking crossings and capacities), and an exact
or bounding method that certifies how far each layout can be from
optimal (for example an LP relaxation of a capacity indexed arc
formulation solved by a home made simplex, used for bounds and inside a
branch and bound). Push the search until the layout cost meets the
bound where possible. Results: S1 5,878,715; S2 5,921,875; S3
8,075,675; S4 7,480,955; S5 7,516,700. Report for each scenario the
layout, the cost, the feeders used, the best lower bound, how it was
obtained and the gap, calling a cost proven optimal only when the bound
equals it. Build a separately coded checker that recomputes loads,
types, lengths and costs and tests every rule, run it on the five
layouts and on three broken S1 layouts (a crossing, an underrated
cable, a span over 1300 metres), and confirm it accepts the first five
and rejects each broken one with the right rule. Record the exact
runtime version and the reproduction commands.
```

## Synthesize

```text
Write the engineering memo from your own executed results. State the
amount of each change and explain its cause. Losing one bay at platform
P costs 43,160 (S2 against S1): the 64 turbines must ride on five
feeders, so lightly loaded strings merge onto fuller, more heavily
loaded feeders. Losing one bay at platform A costs 35,745 (S5 against
S4): the same merging, here two lightly loaded feeders combining into
one. Removing C1 costs 2,196,960 (S3 against S1): cables carrying 4 or
fewer turbines, which make up most of the cable length, must now use
the 160 per metre type instead of the 100 per metre type, partly offset
by reshaping the layout. Moving to platform A costs 1,602,240 (S4
against S1): A lies at the western edge of the field rather than near
its centre, so cables must run much farther to reach it. Compare the S1
layout with a simple greedy layout's cost, report every scenario's
feeders used, lower bound, bound method and gap, and call a cost proven
optimal only where the bound equals it.
```
