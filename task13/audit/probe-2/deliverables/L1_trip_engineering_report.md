# 230 kV Line L1: Substation A breaker trip of 2026-09-14 14:22:07. Engineering investigation report

**Classification:** misoperation of the L1 POTT scheme (unwanted trip of L1 at Substation A for an external fault on L2).
**Root cause:** the CT circuit feeding relay B (Substation B L1-21) is landed on the wrong ratio tap. It uses the full winding X1-X5 = 2000:5 (ratio 400). Relay B is set CTR = 240 (1200:5, tap X2-X4). Because of this, relay B's reverse zone Z3R did not see the reverse fault, and relay B echoed relay A's permissive signal.

All numbers in this report come from `replay_L1_relays.py`, run against the case file (outputs: `L1_trip_results.json`, `replay_digital_channels.csv`, `replay_digital_channels_without_root_cause.csv`, `replay_figure.png`).
Sample convention: relay sample k = .dat sample number n - 1. k = 0 is 14:22:07.3450, and there are 1920 samples/s (32 per cycle). SER times are truncated to 0.1 ms, as the relays print them.

---

## 1. Summary of findings

| Item | Result |
|---|---|
| Fault | Phase B to phase C (no ground) on **line L2**, **6.53 km from Substation B** (two-ended B/C calculation; the patrol found tower 18 at 6.50 km). Fault resistance about 1.5 ohm primary |
| Fault inception | **Sample k = 320** (dat n = 321), 14:22:07.5116. It is simultaneous in all three records, and the BC voltage step occurs at k = 320 |
| Relay A, first assertions (replay) | Z2 **351**, KEY **351**, RX **406**, TRIP **406**. Z1, Z3R (disabled) and ECHO (disabled) never assert. Breaker 52A opens at **502** |
| Relay B, first assertions (replay) | RX **363**, ECHO **394**, KEY **394**. Z1, Z2, Z3R and TRIP never assert |
| Root cause | Relay B's CT is landed on X1-X5 (2000:5) while the relay setting is CTR = 240 (1200:5). Relay B measures 0.60 of the true current, so its impedances read 1.667 times too large and Z3R (1.74 ohm) does not reach the reverse L2 fault. The echo logic then returned the permissive signal, and relay A tripped by POTT (Z2 AND RX) |
| Without the root cause | Relay B Z3R asserts at **k = 350**, before RX arrives at 363, which blocks the echo. Relay B never keys, relay A gets no RX and **does not trip** (relay A keys on Z2 at 351 only). L1 stays in service |
| Corrective action | Re-land relay B's CT circuit (52-L1 core 1 at Substation B) on **X2-X4 = 1200:5**. No setting change is needed (R5 stays valid). If the X1-X5 tap must be kept, use the alternative settings **CTR = 400, Z1P = 6.18, Z2P = 9.65, Z3P = 2.90 ohm sec, 50PP = 0.30 A** |

---

## 2. Data used and how relay B's inputs were reconstructed

* **Relay A**: oscillography `SUBA_L1-21_20260914_142207` (VA, VB, VC and IA, IB, IC in secondary units, plus recorded digital channels Z1, Z2, KEY, RX, TRIP, 52A), the settings export (R4) and the event report.
* **Relay B**: settings (R5) and SER only. Its oscillography was overwritten during restoration switching. The inputs were reconstructed as follows.
  * *Voltages*: one-line S-230-001 states that every line relay takes its voltages from its substation's bus VT, so both relays at Substation B see the same VT-B voltages (2000:1). The Substation B L2-21 record (PTR 2000) supplies them.
  * *Currents*: line L1 has negligible charging (one-line note) and no fault (see the check in section 6). The primary current entering L1 at B is therefore exactly minus the primary current entering L1 at A, sample by sample. All records are GPS-synchronised, start at 14:22:07.345000 and use the same sampling rate. Relay A's CT matches its setting (1200:5 on X1-X5, commissioning 2024-03-11; CTR 240), so I_A,primary = 240 x i_A,sec. Both CTs have P1 toward their own bus. Relay B's secondary current is therefore **i_B,sec = -240 x i_A,sec / N_B**, where N_B is the ratio of the tap that is actually landed. The Substation B commissioning record (2023-04-14) shows 52-L1 core 1 (L1-21 relay B) landed on **X1-X5**. Drawing B-E-2214 gives X1-X5 = **2000:5**, so N_B = 400.
* The **L2 relays** (Substation B and Substation C) were replayed with the same engine to validate it.

## 3. Replay program (as the manual specifies)

`replay_L1_relays.py` implements the manual excerpt literally:

* Full-cycle Fourier RMS phasor in a fixed reference frame, X(k) = sqrt(2)/32 * sum x[k-i] e^(-j2pi(k-i)/32), for k >= 31.
* Loops AB, BC and CA use V = VX - VY and I = IX - IY. A loop is evaluated only when |I| >= 50PP, and Z = V/I in secondary ohms.
* Forward mho: |Z - (R/2)e^(jT)| <= R/2 (Z1P, Z2P). Reverse mho: |Z + (R/2)e^(jT)| <= R/2 (Z3P), with T = Z1ANG = 84 degrees. A zone asserts when any loop operates.
* Figure 2 logic is evaluated each sample in the order zones -> RX -> echo -> KEY -> TRIP:
  * ECHO = EDUR one-shot of the EDPU pickup of AND(not Z1, not Z2, not Z3R, not EBLK-dropout(Z3R), RX). Pickup is on the 32nd consecutive sample. The one-shot lasts 64 samples and is non-retriggerable. The EBLK dropout lasts 64 samples.
  * KEY = Z2 + ECHO. TRIP = latch(Z1 + Z2*RX).
* The channel turns remote KEY at sample k into local RX at k + 12. A breaker opens 96 samples after TRIP.
* Relays A and B (and, for validation, L2 B and C) are run together, sample by sample, because each relay's RX depends on the other relay's KEY.

### Validation of the engine

| Record | Replay vs recorded digital channels (640 samples) |
|---|---|
| SUBB L2-21 (Z1, Z2, KEY, RX, TRIP, 52A) | 0 mismatched samples on every channel |
| SUBC L2-21 (Z1, Z2, KEY, RX, TRIP, 52A) | 0 mismatched samples on every channel |
| **SUBA L1-21 (relay A)** | **0 mismatched samples on every channel** |

## 4. Replay results and comparison with the event reports

### Relay A (from its own record)

| Element | SER (event report) | Replay: first sample k (time) | Match |
|---|---|---|---|
| Z2 asserted | 14:22:07.5278 | 351 (.5278) | yes |
| KEY asserted | .5278 | 351 | yes |
| RX asserted | .5564 | 406 (.5564) | yes |
| TRIP asserted (Z2*RX) | .5564 | 406 | yes |
| Z2 / KEY deasserted | .5772 | 446 | yes |
| RX deasserted | .5897 | 470 | yes |
| 52A open | .6064 | 502 (= 406 + 96) | yes |
| Z1 | never | never | yes |
| Fault locator | 92.0 km | 92.01 km (BC loop at k = 406) | yes |

Relay A's BC loop measures about 1.23 + j5.26 ohm sec (91 km equivalent) during the fault. That is inside Z2 (5.79 ohm, which reaches 100.5 km of line impedance) and outside Z1 (3.71 ohm). The fault is 80 + 6.5 = 86.5 km from A. The relay overestimates it because of the infeed at bus B: the other bays at B (T1) supply about 4.4 kA of the 8.6 kA that flows into L2. Relay A behaved exactly as designed for an external fault inside its Z2 overreach. It keyed, and it tripped only because it received a permissive signal.

### Relay B (reconstructed inputs, CT as landed, ratio 400)

| Element | SER (event report) | Replay | Match |
|---|---|---|---|
| RX asserted | .5340 | 363 (= A KEY 351 + 12) | yes |
| ECHO asserted | .5502 | 394 (32nd consecutive sample of the echo AND) | yes |
| KEY asserted | .5502 | 394 | yes |
| RX deasserted | .5835 | 458 (= A KEY drop 446 + 12) | yes |
| ECHO / KEY deasserted | .5835 | 458 (= 394 + 64) | yes |
| Z1, Z2, Z3R, TRIP | not reported (no trip) | never asserted | yes |

Every timestamp in both event reports is reproduced to the sample.

## 5. Sequence of events

| k | Time 14:22:07. | Event |
|---|---|---|
| 320 | .5116 | BC flashover on L2, tower 18 (bird nest), 6.5 km from B. The records trigger |
| 338 / 340 | .5210 / .5220 | Substation B L2-21 Z2/KEY assert at 338, then Z1 at 340, and it TRIPs (zone 1) |
| 347 / 350 | .5257 / .5272 | Substation C L2-21 Z2/KEY assert at 347, RX at 350 (B KEY 338 + 12): POTT TRIP |
| **350** | .5272 | (*Relay B Z3R should have asserted here: section 8*) |
| 351 | .5278 | Relay A Z2 asserts (external fault inside its overreach). Relay A keys a permissive signal to B |
| 363 | .5340 | Relay B receives RX. Its Z1, Z2 and Z3R are all deasserted because the BC loop reads -1.23 - j1.11 ohm sec, outside Z3R. The echo AND starts timing |
| 394 | .5502 | Echo AND has held for 32 samples: relay B ECHO and KEY assert |
| 406 | .5564 | Relay A RX asserts. Z2 AND RX gives a **POTT TRIP of L1 at A** (misoperation) |
| 436 / 446 | .5720 / .5772 | L2 breakers at B and C open (each 96 samples after its trip). The fault is cleared |
| 446 | .5772 | Relay A Z2 / KEY drop |
| 458 | .5835 | Relay B RX, ECHO and KEY drop |
| 502 | .6064 | L1 breaker at A open |

## 6. Root cause and evidence

**Why relay B echoed.** The echo logic is meant to return the permissive signal only when the weak-source terminal sees nothing (no Z1, Z2 or Z3R). For an external fault behind B, Z3R has to assert and block the echo. The settings calculation's coordination check states that for any fault behind B within A's Z2, B's Z3R asserts before the echo pickup expires. In this event, B's Z3R never asserted.

**Why Z3R did not assert.** Relay B's currents are 240/400 = **0.60** of the values its CTR setting assumes. Its BC loop therefore reads **-1.227 - j1.114 ohm sec (|Z| = 1.66 ohm)** instead of the true **-0.736 - j0.668 ohm sec (0.99 ohm)**. To include the as-found point, the reverse mho circle at 84 degrees would need a reach of **2.22 ohm**, and the setting is 1.74 ohm. The true point needs only 1.33 ohm, so it is comfortably inside. Relay B's loop current was 10.4 A sec, far above 50PP = 0.5 A, so current supervision played no part.

**Underlying cause.** The Substation B commissioning record (Form P-14, 2023-04-14, J. Okafor / R. Lindqvist) lists 52-L1 core 1 → "L1-21 line relay (relay B)" with leads landed on **X1-X5**. On drawing B-E-2214 (2000:5 MR, non-standard tap chart) that is **2000:5**. The 1200:5 ratio that the relay settings and the settings calculation ("protection CT ratio 1200:5 (CTR = 240), both line ends") require is **X2-X4**, which is the tap used on the same substation's L2 relay core and on the L1 metering core.

The "Ratio check: PASS" on the form only compares the injection with the nameplate ratio *of the landed tap*, so the form could not detect a mismatch with the relay CTR. The CTs at Substation A are 1200:5 nameplate, where X1-X5 is correct. The same terminal designation on the B CTs gives 2000:5, which is a plausible origin of the error.

**Why it appeared only now.** Z3R at B exists only to block the echo. Echo was enabled at B in settings revision R5 on 2026-05-26 (maintenance log). Before then the under-measuring relay B had no echo to block, and an external fault behind B could not cause relay A to trip.

None of the later checks inject current through the CT:
* The R5 end-to-end test exercises the scheme logic and the channel.
* The 2026-07-30 annual test injects "at the relay test switch".
* The 2026-06-14 VT check is a voltage check.

None of them can reveal a CT tap error. An in-service comparison of load current at both line ends would have shown relay B reading 60 % of relay A.

### Evidence that this cause, and no other, explains the records

1. **Relay B's inputs, four hypotheses, each replayed against relay A's record and both SERs:**

| Relay B CT hypothesis | Relay B replay | Relay A replay | Reproduces records? |
|---|---|---|---|
| 1200:5 as designed (240), correct polarity | Z3R at 350, no echo, no key | no trip | **No** (relay A did trip, relay B did echo) |
| **2000:5 X1-X5 as landed (400), correct polarity** | **RX 363, ECHO/KEY 394, no Z3R** | **TRIP 406** | **Yes: every SER entry, and 0 mismatches on relay A's channels** |
| 1200:5, reversed polarity | Z2 339, Z1 342, TRIP 342 | TRIP 351 | No (relay B did not trip) |
| 2000:5, reversed polarity | Z2 343, Z1 348, TRIP 348 | TRIP 355 | No |

   A scan of the effective ratio at relay B gives a relay A trip for any ratio from 330 to 600 and no trip from 200 to 325. The landed tap (400) falls in the trip band, and the designed ratio (240) in the no-trip band.

2. **No fault on L1.** From relay A's current and the bus voltages at A and B, the L1 series impedance during the fault is (V_A - V_B)/I_A / 80 km = **0.0517 + j0.4784 ohm/km**. That is the line's nameplate 0.05 + j0.48, which is not possible with a fault on L1. The patrol and the operations log also report no fault found on L1.

3. **The fault is on L2.** The two-ended B/C calculation gives **6.53 km** from B (patrol: tower 18 at 6.50 km). Both L2 relays tripped correctly (B by zone 1, C by POTT), and their replays match their records bit for bit.

### Other causes considered and ruled out

| Candidate | Evidence against it |
|---|---|
| Relay A settings or relay A hardware | Relay A's settings match the calculation (Z1P 3.71, Z2P 5.79, ECHO N). Its replay matches its own recorded channels with 0 mismatches. Its Z2 operation for a fault 86.5 km away with infeed is by design |
| Spurious channel signal or noise | Relay A's RX at 406 = relay B KEY at 394 + 12 exactly. Relay B's SER logs ECHO and KEY at 394, and RX drops at 470 = 458 + 12 |
| Relay B CT polarity reversed | Relay B would have tripped by Z1 at 342 (section 6, table), and it did not trip |
| Z3P recalculation 1.80 → 1.74 in R5 | With Z3P = 1.80 and the CT as landed, the replay still gives no Z3R, ECHO at 394 and a relay A trip at 406. The reach needed is 2.22 ohm. With the correct CT, 1.74 has margin (1.33 needed) |
| Echo timers (EDPU, EDUR, EBLK) or the coordination concept | They are as calculated. With the correct CT, Z3R picks up at 350, 13 samples before RX at 363 and 44 samples before the echo pickup would complete. The concept works |
| Loop current below 50PP (weak source) | Relay B's BC loop current was 10.4 A sec as measured (17.3 A sec at relay A), far above 0.5 A |
| VT-B problem (MCB replaced 2026-06-14) | The same VT feeds Substation B L2-21. That relay measured the fault correctly (zone 1, 6.15 km reactance) and its replay matches its record exactly |
| Firmware v3.2 → v3.4 (2026-05-26) | Relay B's SER is reproduced exactly by the manual's documented logic. The relay did what its logic specifies, given the wrong current input |
| CT saturation at B | A transient effect would not give the steady ×0.60 scaling that reproduces every SER timestamp. The documented tap error alone explains the records |

## 7. What the relays would have done without the root cause (replay)

The replay was run with relay B's CT on 1200:5 (secondary current = -i_A,sec):
* **Relay B:** BC loop at -0.736 - j0.668 ohm sec. **Z3R asserts at k = 350** (BC loop). RX arrives at 363 while Z3R and its EBLK extension are asserted. The echo AND never becomes true, so there is **no ECHO, no KEY and no TRIP**. Z3R stays asserted (with a brief dip at 437-440) until 444. EBLK then holds the block until 508, which is beyond the end of RX at 458.
* **Relay A:** Z2 and KEY assert at 351 and drop at 446. It receives **no RX** and does **not trip**. L1 stays in service, and the L2 fault is cleared by the L2 relays alone.
* Output: `replay_digital_channels_without_root_cause.csv`.

The counterfactual uses relay A's recorded inputs. These differ from the counterfactual system only after relay A's breaker opened at 502, which is after the fault was cleared (446) and after every element had dropped out.

## 8. Corrective actions

1. **Re-land relay B's CT circuit** (Substation B, CT 52-L1 core 1, three phases) from X1-X5 to **X2-X4 (1200:5)**, so that it matches CTR = 240, the R5 settings and the settings calculation. **No setting change** is needed. Settings R5 stay as they are: CTR 240, Z1P 3.71, Z2P 5.79, Z3P 1.74, 50PP 0.50, ECHO Y, EDPU 32, EDUR 64, EBLK 64. The replay with this correction gives no trip at A and no echo at B.
2. **Alternative, only if the 2000:5 tap must be kept:** change relay B's settings to **CTR = 400, Z1P = 6.18, Z2P = 9.65, Z3P = 2.90 ohm sec, 50PP = 0.30 A** (the same primary values: 30.89, 48.26 and 14.48 ohm, and 120 A). The replay with these settings also gives Z3R at 350, no echo and no trip at A.
3. **Interim measure until item 1 is done:** set ECHO = N at relay B, or apply item 2. Note that with the tap error, relay B's forward zones also underreach. Effective Z2 is only 75 % of L1 (effective Z1 48 %), so relay B cannot key for internal L1 faults near A.
4. **Verify after the change** with primary (or CT-terminal) injection through the relay, and with an in-service load check. Relay B's phase currents must equal relay A's in magnitude (both CTR 240) and be 180 degrees apart. Repeat the POTT/echo end-to-end test, including a reverse-fault test of the Z3R echo block.
5. **Audit and procedure:**
   * Audit every CT circuit at Substations B and C (2000:5 MR CTs) against the CTR setting of the device it feeds.
   * Revise Form P-14 so that the ratio check is against the ratio required by the device setting, not only against the tap that happens to be landed.
   * Add a load-current comparison between line ends to commissioning and to every scheme or settings change that enables a function (such as ECHO).
6. **Records:**
   * Update one-line S-230-001: G2 is retired and the T1 bay at B is missing.
   * Increase or offload relay B's event storage so that oscillography survives restoration switching.

## 9. Deliverables

* `replay_L1_relays.py`: replay program. Usage: `python3 replay_L1_relays.py <case_dir> <out_dir>`.
* `replay_digital_channels.csv`: replayed Z1, Z2, Z3R, RX, ECHO, KEY, TRIP and 52A for relays A and B for each sample (as found), with relay A's recorded channels alongside.
* `replay_digital_channels_without_root_cause.csv`: the same, with relay B's CT corrected.
* `L1_trip_results.json`: every reported value and the supporting evidence.
* `replay_figure.png`: BC-loop impedance trajectories against the relay B mho characteristics, and replay timing.
