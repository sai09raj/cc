# Engineering memo: TENURE-11 collector tuning

All numbers below come from executing `gcsim.py` (Python 3.11.15) and `analysis.py`; they are in
`sweep.csv`, `selections.txt`, `analysis.txt` and `certification.txt`. Every simulator result was
recomputed by the independent JavaScript verifier `verify.js` (Node v22.22.2): all 96 sweep rows and
the baseline log match exactly.

## 1. Results at a glance

* Baseline (EDEN 24576, SURV 8192, T 2, PT off): **287 GC events** (202 minor, 85 major),
  total pause 353097, max pause 2639. Log hash **`21792195d928aa2b`**.
* 96 configurations, **84 feasible, 12 OOM** (all with T = 1).
* Selections (feasible configurations only):

| Selection | Config (idx) | EDEN / SURV / T / PT | Total pause | Max pause |
|---|---|---|---|---|
| Cost optimal | 91 | 49152 / 24576 / 3 / 768 | 147851 | 2244 |
| Latency optimal under budget (total <= 220000) | 92 | 49152 / 24576 / 3 / 1024 | 173865 | 1867 |
| Footprint optimal under ceiling (max <= 2400) | 54 | 32768 / 8192 / 3 / off | 317818 | 2396 |

* Sums over the 84 feasible configurations: total pause 22936277; major collections 6449;
  minor collections 11504; bytes copied 158850216; bytes promoted 216580000; bytes pretenured 95636288.

## 2. Constants taken from the figures

| Constant | Value | How measured (`figure_measurements.txt`) |
|---|---|---|
| OLD_SIZE | 131072 (128 KiB) | Fig. 1: long ticks 0/48/96 KiB at px 370.5/1039.5/1709.5 (13.94 px/KiB); old bar spans px 371..2156 = 128.07 KiB, ending on the 16th 8-KiB minor tick. |
| HEADER | 16 | Fig. 2: 28.8 px/byte, header/payload boundary at px 832 = 15.99 bytes. |
| Base payloads | TEMP 24, SESSION 96, BLOB 96, ENTRY 56, NODE 40, REG 112 | Fig. 3: bar tops vs. the 0 and 128 gridlines (6.24 px/byte): 24.03, 95.96, 95.96, 56.07, 40.05, 111.98. |
| Reference slots | TEMP 0, SESSION 1, BLOB 0, ENTRY 1, NODE 1, REG 4 | Fig. 3: dots counted above each bar. |
| Phases | warm [0,4000), steady [4000,16000), burst [16000,22000), drain [22000,26000); end = 26000 | Fig. 4: phase box edges at px 660.5/1542.5/1983.5/2277.5 with 73.5 px per 1000 ops. |
| Mixes | as printed in Fig. 4 | read directly. |
| Size variation | BLOB +96(i mod 13), ENTRY +24(i mod 3), NODE +8(i mod 5) | printed under Fig. 3. |

So object sizes are TEMP 40, SESSION 112, REG 128, BLOB 112..1264, ENTRY 72..120, NODE 56..88.
Only BLOBs can reach the pretenure thresholds (BLOB >= 768 when i mod 13 >= 7; >= 1024 when i mod 13 >= 10).

## 3. Tenuring threshold: total pause is not monotonic in T

Fixed EDEN 16384, SURV 8192, PT off (`analysis.txt`):

| T | Total | Minor pause (copy / promote / 2R terms) | Major pause (count) |
|---|---|---|---|
| 1 | OOM at op 1089 | | |
| 2 | 413767 | 193949 (38479 / 133336 / 10014) | 219818 (93) |
| 3 | 406957 | 191438 (38499 / 130945 / 9874) | 215519 (91) |
| 5 | 414591 | 201330 (38541 / 124979 / 25690) | 213261 (89) |

Total pause first falls (T 2 -> 3, -6810) and then rises (T 3 -> 5, +7634). Raising T keeps
survivors young longer, so fewer bytes are promoted (4269960 -> 4193808 -> 4003360), the promotion
term of the minor pause falls and there are fewer major collections (93 -> 91 -> 89). But with a
small 8192-byte survivor space the to-space is already full on almost every minor collection (the copy
term barely moves: 38479 -> 38541), so the saving in promotion is small, while a cost appears on the
remembered-set side. At T = 5 the long-lived sessions stay in the survivor space for up to four
collections, while ENTRY objects that overflow the to-space are promoted and point at those
still-young sessions. Summed over the 303 minors, R is 5007 at T 2, 4937 at T 3 and 12845 at T 5,
and at T 5 8972 of those remembered-set entries are ENTRY objects (14 at T 2). The 2R term grows from
9874 to 25690, which is more than the 5966 saved on promotion and 2258 saved on majors. So T = 3 is
the best setting here.

The same shape appears with other settings, e.g. EDEN 49152 / SURV 24576 / PT off: T1 269607, T2 236220,
T3 231645, T5 231855 (the copy term, the 2R term and the major pause all rise again from T3 to T5), and
EDEN 32768 / SURV 24576 / PT 768: T2 182581, T3 177114, T5 179802.

## 4. Pretenuring: what it buys and what it costs

PT 768 sends 2080480 bytes, and PT 1024 sends 1186496 bytes, of large BLOBs straight into the old
generation in every run that completes. Those BLOBs are never copied and never take up eden, so:

* **Gains.** Eden fills more slowly, so there are fewer minor collections and fewer bytes copied and
  promoted. At EDEN 49152 / SURV 24576 / T 3: minors 99 -> 56 (PT 768) / 74 (PT 1024), copied
  2381608 -> 1335864 / 1787064, promoted 3057488 -> 727176 / 1726168, total pause 231645 -> 147851 /
  173865. Over all 26 (EDEN, SURV, T) settings where both PT off and PT on finish, **PT 768 lowers total
  pause in 26 of 26 and PT 1024 does too in 26 of 26**. Mean total pause is 323835 for PT off, 236485 for
  PT 768 and 265070 for PT 1024. PT also rescues some T = 1 configurations from OOM: 24576/T1 and 32768/T1
  run to completion with PT 768, and 32768/T1 does with PT 1024.
* **Costs.** The old generation fills up and stays fuller: mean peak old occupancy is 111002 for PT
  off, 126727 for PT 768 and 120346 for PT 1024, against a capacity of 131072. Idx 91 peaks at 129240.
  Major collections then mark more bytes, and some are triggered outside a minor because a pretenured
  placement failed (idx 91: 58 majors, only 48 of them right before a minor). The worst pause gets
  longer: **PT 768 lowers max pause in 0 of 26 paired settings and PT 1024 in only 1 of 26**. Mean max
  pause is 2311 for PT off, 2744 for PT 768 and 2520 for PT 1024. At 49152/24576/T3 the max pause goes
  from 1729 to 2244 with PT 768 and to 1867 with PT 1024. Pretenuring can also cause or hasten OOM:
  24576/T1 fails at op 16404 with PT off but already at op 1116 with PT 1024. In short, pretenuring
  trades throughput (total pause) for tail latency and old-generation headroom.

## 5. Why the three selections differ

* **Cost optimal** looks only at total pause, so it takes the most aggressive throughput setting:
  the largest young generation (49152 + 2 x 24576), T 3 and PT 768. Idx 91 (147851) beats idx 94 T5
  (148119) and idx 88 T2 (149637). Its max pause is 2244, from major collections of a nearly full old
  generation.
* **Latency optimal under budget** wants the smallest max pause with total <= 220000. The configurations
  with the very lowest max pause are idx 90 (PT off, 1729) and idx 93 (1763), but their totals (231645
  and 231855) are over the budget because without pretenuring they copy and promote much more. The next
  lowest, 1867, is reached by idx 89 (T2) and idx 92 (T3), both PT 1024. The tie breaks on total pause, and
  idx 92 (173865) beats idx 89 (175030). PT 1024 is the compromise: it pretenures enough to stay within
  the budget, but keeps the old generation emptier (peak 103944) than PT 768 does.
* **Footprint optimal under ceiling** minimises EDEN + 2 x SURV with max pause <= 2400. No configuration
  at the smallest footprint (32768 = 16384 + 2 x 8192) qualifies: its 9 feasible configurations have max
  pauses 2865..3118. At footprint 49152 (32768 + 2 x 8192) only idx 54 (32768/8192/T3/off, max 2396)
  qualifies. Its neighbours idx 51 (T2, 2406) and idx 57 (T5, 2409) just miss, as does every
  16384/24576 configuration (footprint 65536, which would rank later anyway). The selection is very
  close to the ceiling: a margin of 4 pause units.

So the three selections pick different configurations because each optimises something different: total
work, the worst stall within a work budget, and memory within a stall budget. The configuration that is
best on one of these is never best on the others.

## 6. OOM configurations

12 configurations end in OOM, all with T = 1 (`sweep.csv`, `analysis.txt`). SURV makes no difference at
T = 1, so they come in pairs:

| idx | EDEN / SURV / T / PT | OOM op | Failing placement | Old free bytes / blocks / largest block |
|---|---|---|---|---|
| 0, 12 | 16384 / 8192, 24576 / 1 / off | 1089 | BLOB 400 B in a minor | 4496 / 52 / 320 |
| 1, 13 | 16384 / * / 1 / 768 | 17214 | BLOB 592 B in a minor | 4496 / 38 / 520 |
| 2, 14 | 16384 / * / 1 / 1024 | 2882 | BLOB 976 B in a minor | 7552 / 75 / 960 |
| 24, 36 | 24576 / * / 1 / off | 16404 | BLOB 784 B in a minor | 3264 / 28 / 448 |
| 26, 38 | 24576 / * / 1 / 1024 | 1116 | BLOB 784 B in a minor | 8000 / 65 / 768 |
| 48, 60 | 32768 / * / 1 / off | 17386 | BLOB 1168 B in a minor | 7408 / 50 / 1072 |

What drives them there: with T = 1 every object that survives a minor collection has new age 1 >= T
and is promoted. Nothing is ever copied (copied = 0 in every T = 1 row), so short-lived but still
reachable objects (the current TEMP, recent NODEs, ENTRYs and sessions that are about to be overwritten
in the ring) all go to the non-moving old generation and die there. Old occupancy stays near capacity
(123072..127808 at the failure), and the free list fills with small holes, which are only merged during
a major collection. The promotion guard checks only *total* free bytes against eden + from-space use, so
it does not start a major collection even though no single free block is large enough. Every failure is a
BLOB promotion during a minor collection whose size exceeds the largest free block, even though tens of
small blocks remain free. Only the largest eden (49152) survives T = 1 in every PT setting, because it
collects about half as often and so promotes fewer short-lived objects. PT changes when the failure
happens but does not prevent it at EDEN 16384.

## 7. Verification

`certification.txt`: the verifier ACCEPTS the true baseline log (287 events, hash
21792195d928aa2b, matching its own recomputation byte for byte; hash file consistent) and all 96 sweep
rows. It REJECTS the strict-promotion adversary (285 events, hash 051f94b582dcb620; it first differs at
event 3, where copied is 8160 instead of 8176 and promoted 20864 instead of 21184) and the depth-first adversary
(288 events, hash f13b448283bc4b0a; it differs already at event 1, where copied is 8152 instead of 8192).
