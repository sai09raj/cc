# 230 kV Line L1 Trip at Substation A, 14 September 2026: Protection Investigation Report

**Event:** 2026-09-14 14:22:07, POTT trip of breaker L1 at Substation A. No fault on L1.
**Conclusion:** Misoperation of the L1 POTT scheme (Substation A trip). The root cause is a CT secondary wiring error at Substation B: the L1 relay current circuit is on the wrong CT tap, 2000:5 instead of 1200:5. This error has been present since the CT was replaced in May 2026.

All numbers in this report come from `l1_replay.py`, which writes `results.json`, `replay_full_results.json` and `replayed_digitals.csv`. The figures come from `l1_plots.py`. Sample numbers are **relay samples k = n - 1**, where n is the first column of the .dat file (manual section 1). The sample rate is 1920 samples/s, so 1 sample = 0.521 ms. k = 0 is 14:22:07.345000.

---

## 1. Summary

| Item | Result |
|---|---|
| Fault | **B-C phase-to-phase** (no ground) on **line L2**, tower 18, 6.5 km from Substation B. The fault is external to L1. |
| Fault inception | **k = 320** (n = 321), 14:22:07.5117. This is also the record trigger. |
| Fault cleared (L2 breakers) | First post-fault sample **k = 461**. The fault lasted 141 samples (73.4 ms). |
| Relay A first assertions | Z2 **351**, KEY **351**, RX **406**, TRIP **406**. Z1 never asserted. Z3R and ECHO are disabled. 52A opened at k = 502. |
| Relay B first assertions | RX **363**, ECHO **394**, KEY **394**. Z1, Z2, Z3R and TRIP never asserted. |
| BC loop Z at k = 400, A | **1.1635 + j5.2128 ohm sec** (5.341 ohm at 77.42 deg) = **9.696 + j43.440 ohm primary** (44.51 ohm) |
| BC loop Z at k = 400, B | **-1.1992 - j1.1126 ohm sec** (1.636 ohm at -137.15 deg). True primary (CT 2000:5): **-5.996 - j5.563 ohm** (8.179 ohm). Relay B's own conversion with CTR 240 gives -9.994 - j9.272 ohm (13.63 ohm), which is wrong by a factor of 1.667. |
| L1 phase-B primary current at B, k = 400 | **2269 A** (5.6724 A sec x 400). Relay B would report 1361 A with CTR 240. Cross-check: A measures 2269 A, 180.0 deg opposite. |
| Root cause | Relay B's CT core 1 is landed on X1-X5 (2000:5) instead of the design tap X2-X4 (1200:5), while relay B is still set to CTR = 240. Relay B therefore sees impedances 1.667 x too large. Its zone 3 reverse did not detect the reverse fault, so the echo was not blocked. B echoed A's permissive back and A tripped. |
| Without the root cause (replay) | B's Z3R asserts at k = 350 and blocks the echo, so B sends no KEY. A never receives RX and **does not trip**. **B does not trip.** |
| Corrective action | Re-land B core 1 on X2-X4 (1200:5). **No setting change** is needed (CTR 240, Z1P 3.71, Z2P 5.79, Z3P 1.74, 50PP 0.50). If the core has to stay on 2000:5, use the alternative settings CTR = 400, Z1P = 6.18, Z2P = 9.65, Z3P = 2.90 ohm sec and 50PP = 0.30 A. |

## 2. Data examined

- **COMTRADE records** from both relays: 640 samples each at 1920 samples/s, triggered at 14:22:07.511667. Relay A has 6 analog and 6 digital channels (Z1, Z2, KEY, RX, TRIP, 52A). Relay B has 6 analog and 7 digital channels (Z1, Z2, Z3R, RX, ECHO, KEY, 52A).
- **Event reports.** A reports a POTT trip (Z2 and RX) on the BC loop with a fault location of 92.0 km. B reports KEY with no trip, and its echo was issued.
- **Settings exports.** The two relays are set identically, CTR 240, PTR 2000, Z1P 3.71, Z2P 5.79 and 50PP 0.50, with these differences:

  | Setting | A | B |
  |---|---|---|
  | Z3P | OFF | 1.74 |
  | ECHO | N | Y |

  Both relays use EDPU/EDUR/EBLK = 32/64/64.
- **Manual excerpt.** It defines the phasor and mho equations, the logic order, the 12-sample channel, EDPU/EDUR/EBLK and the 96-sample breaker operating time. Figure 2 shows the echo AND gate with inputs not-Z1, not-Z2, not-Z3R, not-EBLK(Z3R) and RX.
- **Settings calculation (2025-11).** CT 1200:5 at both ends (CTR 240). Z3P of 1.74 ohm sec is set to cover A's zone-2 overreach beyond bus B with a factor of 1.5. It contains the coordination statement "B's Z3R asserts before the echo pickup expires".
- **One-line S-230-001 rev D.** Shows A - L1 (80 km) - B - L2 (50 km) - C. Both VTs are 2000:1, and the CT P1 terminals face the bus.
- **Bay drawings.**
  - A-E-1107: CT 1200:5 MR, core 1 on X1-X5, giving 1200:5.
  - B-E-2214 rev C: CT 2000:5 MR, replaced like-for-like in 2026-05. Core 1, which feeds L1-21 relay B, is designed on **X2-X4 = 1200:5**, "selected to match the L1 relays at both line ends".
- **CT commissioning records.**
  - A, 2024-03-11: all L1 cores on X1-X5 (1200:5), as designed.
  - **B, 2026-05-27: core 1 of 52-L1 is recorded as landed on X1-X5**, which is 2000:5 on that CT, against the design tap X2-X4. The ratio check still shows PASS. Per the footnote, the check compares against "the nameplate ratio of the landed tap", so a wrong tap passes. Cores 2 (X1-X5) and 3 (X2-X4) match the drawing.
- **Operations log.** L2 tripped correctly at both ends in zone 1. L1 at A tripped and L1 at B did not. L1 was restored with no fault found.
- **L2 patrol report.** Phase B-C flashover at tower 18, 6.5 km from B, caused by a burnt bird nest. There were no ground marks.

## 3. Replay of both relays (`l1_replay.py`)

The program implements the manual exactly:

- **Phasors.** 32-sample full-cycle Fourier RMS phasors in a fixed reference, for k >= 31.
- **Loops.** AB, BC and CA loops with V = VX - VY and I = IX - IY. A loop is evaluated only when |I| >= 50PP.
- **Zones.** Mho circles through the origin: forward Z1 and Z2 are centred at +(R/2)e^jT, and Z3R is centred at -(R/2)e^jT, with T = 84 deg.
- **Per-sample logic order.** Zones, then RX (remote KEY delayed 12 samples), then echo, then KEY = Z2 + ECHO, then TRIP = Z1 + Z2*RX (latched).
- **Echo timers.**
  - EBLK dropout timer on Z3R: asserted while Z3R is asserted and for 64 samples after it drops.
  - EDPU pickup: asserts on the 32nd consecutive sample with its input asserted.
  - EDUR one-shot: 64 samples, and it cannot be retriggered while running.
- **Breaker.** 52A opens 96 samples after TRIP.

**Result: the replay reproduces every digital channel of both records at every one of the 640 samples, with zero mismatches.** Relay A was checked on Z1, Z2, KEY, RX, TRIP and 52A. Relay B was checked on Z1, Z2, Z3R, RX, ECHO, KEY and 52A. `replayed_digitals.csv` lists the replayed channels of both relays next to the recorded channels.

Two further checks agree with the evidence:

- **Fault locator.** The replayed BC loop at A's trip sample k = 406 is 1.1418 + j5.2985 ohm sec. That gives X = 44.15 ohm primary and a distance of 92.0 km, the same as A's event report. The true electrical distance is 80 + 6.5 = 86.5 km. The overestimate is the expected effect of infeed from the B source.
- **Event-recorder times.** The times convert exactly to the replayed edges, for example A KEY at 14:22:07.5278 = k 351 and B ECHO at .5502 = k 394.

## 4. Sequence of events

| k | Time | Event |
|---|---|---|
| 320 | 07.5117 | BC fault on L2 near B. Record trigger. |
| 350 | | B Z3R *would* assert here if B's CT were on the design tap (counterfactual). As found, it never asserts. |
| 351 | 07.5278 | **A Z2 (BC loop) asserts, so A KEYs.** This is correct: Z2 is an overreaching element, and 44.5 ohm primary is inside the 48.26 ohm reach. Z1 (30.9 ohm) correctly stays out. |
| 363 | 07.5341 | B receives RX (351 + 12). Z1, Z2 and Z3R are all deasserted and EBLK is inactive, so the echo AND gate is satisfied. |
| 394 | 07.5502 | B's EDPU completes after 32 consecutive samples (363..394). **B ECHO and KEY assert** for 64 samples. |
| 406 | 07.5565 | A receives RX (394 + 12). Z2 AND RX gives **A TRIP**. |
| 458 | 07.5835 | B's echo ends (394 + 64). |
| 461 | | First post-fault sample: L2 has cleared the fault, about 73 ms after inception. |
| 464 / 470 | | A's Z2 and KEY drop, then A's RX drops (458 + 12). |
| 476 | 07.5929 | B's RX drops (464 + 12). |
| 502 | 07.6064 | **Breaker L1 at A opens** (406 + 96), after the external fault had already cleared. |

See `fig_digital_sequence.png`.

## 5. Analysis and root cause

### 5.1 Fault type and location
At k = 400, both relays show the following:

- I0 is about 0 and V0 is about 0. At B, I0 = 0.0006 A, V0 = 0.002 V, while I2 = 2.90 A and V2 = 29.0 V. The fault is unbalanced but does not involve ground.
- IA is unchanged from pre-fault: 1.478 A at A and 0.887 A at B.
- The superimposed currents satisfy dIB = -dIC exactly. At A, both are 8.381 A, with angles of -73.1 and 106.9 deg.
- VB and VC collapse toward each other. At B they are 38.1 and 30.1 V, against a pre-fault 66.4 V.

This is the signature of a **B-C phase-to-phase fault**. It matches the patrol finding of a B-C flashover with no ground contact on L2.

The B relay's BC impedance lies in the third quadrant, at -137 deg, which means the fault is reverse (behind bus B). The phase-B currents at A and B are exactly 180.0 deg apart. L1 is carrying a through-current, so the fault is external to L1. This agrees with "no fault found on L1".

### 5.2 Why A tripped
A behaved exactly as set. Its overreaching Z2 (125 %) is designed to see faults beyond bus B, and it keys permission. It tripped only because it received RX. That RX was **B's echo**: it arrived 12 samples after B's ECHO/KEY, and B's Z2 never asserted. A's trip is therefore a consequence of B's behaviour.

### 5.3 Why B echoed: the CT tap error
The echo at B should have been blocked by Z3R. The settings calculation's coordination check requires Z3R to assert before the echo pickup completes for any fault that A's Z2 can reach behind B. As found, **Z3R never asserted**. B's BC apparent impedance settled at about -1.20 - j1.11 ohm sec (1.636 ohm at -137 deg). The closest approach was k = 368, at 1.613 ohm, which is **0.24 ohm outside** the 1.74 ohm reverse circle.

The evidence that B's measured current is wrong by exactly 2000/1200 = 1.667:

1. **Through-current comparison across L1.** Line charging is negligible, so primary current in at A equals primary current out at B. The ratio of A's secondary current to B's secondary current is **1.6667**, with an angle of 0.00 deg against -I. This holds for every phase, both during the fault (k = 340..449, standard deviation 1e-4) and under pre-fault load (k = 40..299). With A on 1200:5, verified at commissioning and on the drawing, the CT ratio that B's current implies is **2000.0:5**.
2. **Absolute check against the line impedance.** The BC loop voltage drop along L1 is (V_BC at A - V_BC at B) x PTR. Divide it by the BC loop primary current and the result should be ZL1:
   - At k = 400, using A's current at 240 gives 3.70 + j37.88 ohm.
   - Using B's current at 400 gives the same, 3.70 + j37.88 ohm.
   - Using B's current at 240 gives 6.17 + j63.13 ohm.

   The expected value is ZL1 = 4.00 + j38.40 ohm. So A's CTR of 240 is right, and B's real ratio is 400, not 240.
3. **Documents.** B-E-2214 rev C specifies core 1 on X2-X4 (1200:5). The 2026-05-27 commissioning record shows core 1 on **X1-X5**, which on the replacement 2000:5 MR CT is 2000:5. The ratio test passed only because it compared against the nameplate ratio of the landed tap. The error was introduced when the failed CT was replaced in May 2026. The metering core on the same CT is correctly on X2-X4.

Relay B still uses CTR = 240. Its secondary currents are 0.6 times what the design expects, so every impedance it measures is 1.667 times too large. On the design tap, the B BC loop at k = 400 would read -0.720 - j0.668 ohm sec (0.98 ohm). That is well inside the Z3R circle, whose reach along -137 deg is about 1.31 ohm. As found, it read 1.636 ohm, which is outside. See `fig_impedance_plane.png`.

The same error also scales relay B's primary metering. Relay B would report the phase-B current at k = 400 as 1361 A, while the true value is **2269 A**. That is the true primary current, and it matches the 2269 A measured at A.

### 5.4 What each relay would have done without the CT error (counterfactual replay)
The replay was rerun with B's currents restored to the design tap (x 2000/1200) and all settings unchanged:

- **B**: Z3R asserts at **k = 350** on the BC loop. That is 13 samples before RX arrives at k = 363, and 44 samples before the echo pickup would have completed at k = 394. Z3R holds until k = 461, and EBLK extends the block to k = 525, beyond the RX dropout at k = 476. B produces **no ECHO and no KEY, and does not trip**. This is correct, because the fault is behind B.
- **A**: Z2 and KEY are asserted from k = 351 to 463, which is correct. **RX never asserts, so A does not TRIP**, and L1 stays in service. L2 clears the fault by itself.

The replay with the alternative settings (CT left on 2000:5, CTR = 400 with the reaches rescaled) gives the same result: B's Z3R asserts at k = 350 and there is no echo and no trip.

### 5.5 Causes considered and ruled out

| Hypothesis | Evidence against |
|---|---|
| Fault on L1 (correct trip) | B sees the fault as reverse (Z at -137 deg). The A and B phase currents are exactly 180 deg apart, so L1 carried a through-current. B's Z1 and Z2 never asserted. The patrol found the fault on L2. L1 was restored with no fault found. |
| Relay A settings or A Z2 overreach | Overreach is the purpose of POTT Z2 (125 % ZL1). A's Z1 correctly did not operate. A tripped only on RX. |
| Relay A CT or VT | A's commissioning record shows X1-X5 = 1200:5 as designed. The line-impedance check with CTR 240 reproduces ZL1 (37.9 vs 38.4 ohm reactance). Pre-fault voltages of 67.8 V and 66.4 V sec are consistent with 230 kV on 2000:1. |
| Channel fault or noise (spurious RX) | Both RX signals are exactly the remote KEY delayed by 12 samples. There are no other RX transitions. The replay reproduces RX exactly. |
| Relay or logic malfunction at B | The replay reproduces all of B's channels exactly from the manual logic. B did exactly what its inputs told it. |
| Echo timers (EDPU/EDUR/EBLK) mis-set | They match the settings calculation. On correct currents, Z3R asserts 44 samples before the pickup would complete. |
| Z3P setting too small by design | On the design tap, the fault sits at 0.98 ohm against a reach of about 1.31 ohm along -137 deg, so Z3R operates. As found, the relay would need Z3P of at least 2.13 ohm to see it. That shortfall is caused by the 1.667 factor, not by the calculation. |
| 50PP supervision blocking B's loops | B's BC loop current is 10.5 A sec, far above the 0.50 A threshold, even with the error. |
| CT polarity reversal at B | The phase angles are consistent with P1 toward the bus at both ends (180 deg apart for a through-current). B's impedance is in the expected reverse quadrant. |
| Ground fault or sequence issue | I0 and V0 are about 0. The phase-to-phase loops are the correct elements for this fault. |

## 6. Corrective actions

1. **Recommended: restore the design wiring.** Re-land the Substation B 52-L1 core 1 secondary (L1-21 relay B IA/IB/IC) on **tap X2-X4 (1200:5)**, as drawing B-E-2214 rev C requires. **Relay B settings stay as they are:** CTR = 240, PTR = 2000, Z1P = 3.71, Z2P = 5.79, Z3P = 1.74 ohm sec, Z1ANG = 84 deg, 50PP = 0.50 A, ECHO = Y, EDPU/EDUR/EBLK = 32/64/64. This keeps both line ends on identical ratios, as the settings calculation intends.
2. **Alternative, only if the core must stay on X1-X5 (2000:5).** Change relay B to **CTR = 400, Z1P = 6.18, Z2P = 9.65, Z3P = 2.90 ohm sec and 50PP = 0.30 A**, with Z1ANG 84 deg and the logic settings unchanged. These preserve the same primary reaches: 30.89, 48.26 and 14.48 ohm, and 120 A. Update the settings calculation and drawing B-E-2214 to match. The replay confirms this also prevents the misoperation.
3. **Return-to-service checks before the POTT/echo scheme goes back in service:**
   - Secondary injection, plus an on-load comparison of both line ends. Relay A secondary current should equal relay B secondary current with a ratio of 1.000 at 180 deg; the event data shows 1.667 as found.
   - A Z3R directional check at B.
4. **Process.** Amend commissioning form P-14 so the ratio check compares against the **design ratio and the relay CTR setting**, not only the nameplate of the landed tap. Add an end-to-end load current comparison to the post-maintenance checklist for line protection. Review other circuits disturbed during the May 2026 work at Substation B. Cores 2 and 3 of 52-L1 agree with the drawing.
5. **Classification.** The Substation A L1-21 relay operated incorrectly as a scheme. The cause was the CT secondary connection error at Substation B. The relay hardware, the settings and the A-end installation are not at fault.

## 7. Deliverables

| File | Content |
|---|---|
| `l1_replay.py` | Reads the COMTRADE files and settings, replays both relays, validates the replay against the records, and runs the analyses and counterfactuals. Run with `python3 l1_replay.py <event dir> --out <dir>`; it needs numpy only. |
| `replayed_digitals.csv` | Replayed Z1, Z2, Z3R, RX, ECHO, KEY, TRIP and 52A for A and B at every sample, alongside the recorded channels. |
| `results.json` | Items 1-6 and supporting values. |
| `replay_full_results.json` | Full analysis detail: phasors, per-loop first assertions, edges, impedance trajectories, CT-ratio checks and counterfactuals. |
| `l1_plots.py`, `fig_impedance_plane.png`, `fig_digital_sequence.png` | The plotting script and the two evidence figures. |
