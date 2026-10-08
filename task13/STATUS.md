# Task 13 — L1 POTT misoperation investigation (Electrical Engineering, power-system protection)

Design per the community tips (Playbook 08, section 5): a diagnosis task. Line L1 tripped at
Substation A by POTT for a B-C fault on line L2 6.5 km past Substation B. Relay A behaved
correctly (Z2 + received permissive). Relay B echoed the permissive because its zone 3
reverse did not assert. B's settings are coordinated on paper. The root cause is one step
upstream: B's L1 protection CT core is landed on X1-X5 (2000:5, per the commissioning record
and the nameplate tap chart) instead of the design X2-X4 (1200:5), while relay B's settings
assume 1200:5. B therefore measures impedances 1.667x too large, and its zone 3 reverse
(designed with a 1.5 margin) misses the fault. With the design ratio, the replay shows Z3R
asserting at sample 350, no echo and no trip at A.

Evidence needs files combined: B's recorded currents are 0.6x A's for the same through
current (prefault and fault), and the commissioning record (background) plus CT drawing B
give the landed tap and its ratio.

- Reference: `reference/` (net.py network, waves.py synthesis, relay.py replay,
  build_case.py, gen_data.py, make_docs.py). Bundle: `artifact/L1_event_2026-09-14.zip`.
- Draft prompt: `platform/prompt.md` (291 words).
- Next: early opus-alias blind probe; read its trajectory and harden the shortcuts it used.

## Probe 1 (opus alias, draft v1): SOLVED exactly in ~7 min, 27 tool calls

Every reported value matched the answer key (root cause, element samples, impedances,
2,269 A, counterfactual Z3R at 350, corrective settings). Trajectory:
1. It read all 16 files first: every text file, every PDF rendered, and the commissioning
   records re-rendered at high resolution. Nothing in a 16-file bundle is "background".
2. Before writing any code it had the cause from documents alone: drawing B-E-2214 says
   core 1 "X2-X4 (1200:5)", the commissioning record row says "X1-X5", and the drawing's
   "Rev C: CT replaced 2026-05" note plus the 2026-05-27 test date point straight at it.
3. It confirmed numerically: A/B secondary current ratio 1.6667 in every phase, prefault
   and fault, and the L1 voltage drop / current matching the line impedance only at 2000:5.
4. The prompt's item 4 (primary current at B) and "primary ohms" at B invited that check.
Gate 8.5: redesign/harden before any platform work.

## v2 (case file L1_trip_case_2026-09-14.zip, 24 files) — hardened against probe 1's path

- Relay B's oscillography is not in the case file (overwritten during restoration); only its
  SER. Its inputs must be reconstructed: bus B voltages from the L2-21 Sub B record, L1 current
  at B = -(A's current). The direct A-vs-B current fingerprint is gone.
- No document states the design tap. Chain: B's settings CTR 240 (1200/5) -> nameplate tap chart
  on B-E-2214 (1200:5 = X2-X4) -> 2023 commissioning book row "52-L1 core 1 X1-X5" (2000:5).
  The CT was never replaced; the error is latent since 2023 and exposed by echo being enabled
  in May 2026.
- Decoys with evidence against them: firmware upgrade v3.2->v3.4 and settings revision R5
  (Z3P 1.80->1.74, echo enabled) both on 2026-05-26; Z3P 1.80 would also have missed the fault.
- Answer key (`reference/answer_key2.py`): a reconstruction at the set ratio 240 gives Z3R at 350
  and no echo, contradicting B's SER; any in-service ratio >= 330 reproduces the SER exactly;
  of the nameplate taps only X2-X5 (1750:5) and X1-X5 (2000:5) qualify, and the book says X1-X5.

## Probe 2 (opus alias, v2): SOLVED exactly in ~8 min, 31 tool calls

Same pattern as probe 1. Tool calls 1-19: it extracted every file, rendered every drawing
sheet (all three Substation B CT sheets, A and C), all four commissioning-book pages and a zoom
of the logic diagram. Tool call 20, its first program, already hard-codes relay B's CT as
2000:5 (X1-X5) - the diagnosis came from the documents before any computation. Routine
protection practice (check every CT tap in service against the relay's CTR) is exactly what
it did; spreading the chain over three files did not slow it. The reconstruction of relay B
then confirmed it, and it rejected the decoys (firmware, Z3P change) with replays.
It also noticed a bundle inconsistency: the one-line still shows a generator at B although
G2 is retired, and the T1 bay is not drawn.

## v3 (L1_trip_case_r3_2026-09-14.zip, 27 files) — cause moved off the routine checklist

Waveforms and SERs unchanged (relay B still receives 0.60 of the true current). New cause:
CT tap X2-X4 and polarity are correct (commissioning book now shows X2-X4) and pass every
routine check. The BF-50 breaker-failure relay replaced on 2025-02-12 was terminated in
PARALLEL with relay B's current inputs (as-built schedule rows: TS-L1:2 -> Z01 and TS-L1:2 ->
BF50 A1; Z02 -> TB:10 and A2 -> TB:10) instead of in series (AC schematic B-E-3301). Burdens
0.04 ohm (relay) and 0.06 ohm (BF-50) split the current 0.60 / 0.40. The 2025-06 relay test
injected with BF-50 isolated, so it passed. Corrective action: re-terminate BF-50 in series.

## Probe 3 (opus alias, v3): SOLVED exactly in ~13 min, 44 tool calls

Same pattern again. Calls 1-25: every text file, every PDF page rendered and viewed (manual
with a zoom on the logic figure, one-line, all five CT sheets, both AC schematics, all three
cable schedules re-rendered at 150 dpi, all four commissioning pages). Call 30, its first
program, already contains the parallel BF-50 diagnosis and the 0.04/0.06 burden split. It
then confirmed by replay, ruled out the CT tap with the documents, and even noted which
alternatives the event data alone cannot exclude.

## Conclusion so far

Three versions, three exact solves in 7-13 minutes. Moving the cause off the routine checklist
did not help: with ~30 pages the model reads every page and traces terminal tables row by
row. The community tips' "background file" effect did not appear at this bundle size.
