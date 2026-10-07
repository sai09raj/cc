# COHERE-12 v2 probe (`opus` alias), graded against platform/rubric.md v2

Budget 2.5 h, Python/Node only, no compilers, 4 cores. Used about 2 h 02 min.
Simulator speed after optimisation: about 5.0-5.3 ms per configuration per core (Node).
Simulated 4,844,872 of 29,360,128 configurations (16.5%): N2/N6 exhaustively, N2/N5 and
N1/N6 at Q = 4 exhaustively, random samples elsewhere. Reported whole-space numbers as
estimates with intervals, clearly labelled.

| Criteria | Points | Earned | Note |
|---|---|---|---|
| 1-12 figures | 12 | 12 | all latencies, layout, line map 19245 |
| 13-14 package | 2 | 2 | Node v22.22.2, Python 3.11.15, commands |
| 15-18 baseline | 10 | 10 | 6725 / 39 / 9762 / 401 exact (re-run by author) |
| 19-21 variants | 9 | 9 | 6931 / 6198 / 6141 exact |
| 22-23 optimum | 7 | 7 | N2/N6, Q 4, B 1, map 55860, 5470 (found by exhausting N2/N6 only) |
| 24-34 whole space | 86 | 0 | estimates only, e.g. 9,227,923 vs 9,223,852; sum 209,213,635,173 vs 209,223,156,016 |
| 35-36 checker | 2 | 2 | both invariants pass |
| 37-40 memo | 6 | 6 | placement dominant; N2/N6 lowest round trip; Q lowers, B raises mean |
| 41-43 negatives | - | 0 | no third party; estimates labelled as estimates (42 not triggered); checker separate |

**Total 48/134 = 35.8%.** Exactly the designed ceiling for a correct simulator without a
full sweep. Simulation itself was transcribed exactly again (mistake #74 holds); the
difficulty is now the volume of exact work: about 41 core-hours at the probe's speed, which
is about 3.2 h on the platform's ~12.6 effective cores even with zero build time.

Ambiguities raised: the p95 "issue cycle" (probe chose the reference reading; clarified in
packet v3, values unchanged); Figure 2 axis has no numeric labels (caption states the scale;
read correctly). All other items it listed follow the packet's literal text and match the
reference.
