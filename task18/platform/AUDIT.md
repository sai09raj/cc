# HOLLOWAY-18 v1 pre-entry audit

## Checks
- **Tool use and outputs.** The prompt requires the model to write and run a stiffness program and to deliver 3 files: the program source, a results file and the memo. PASS.
- **Metadata.** The PDF has no Info, ID, XMP, Producer or Creator, no vector drawings (both drawings are raster), and no answer value appears in its text. `make_packet.py` asserts all of this. PASS.
- **Rubric shape.**
  - 43 criteria, +127 positive, one -5 penalty.
  - Longest criterion is 181 characters (limit 301).
  - Every numeric row has an explicit accept range: ±0.1 % with a floor of 0.05 kNm or 0.02 mm.
  - Atomic: one value per row; the tension face is the sign of that same value.
  - Self-contained: each row states its location, time and value.
  - PASS.
- **Coverage.** Every prompt item has criteria:
  - item 1: 2 rows;
  - item 2: 4 rows;
  - item 3: 11 beam ends;
  - item 4: 1 row;
  - item 5: 14 column moments;
  - item 6: 7 memo rows (2 braces, 2 simple connections, TP-1, zone S, AHU-2);
  - 3 file rows;
  - the -5 penalty for "base every number on your own executed program".
  - PASS.
- **Reviewer feedback (#75, #76).**
  - No derived value needs an unstated rule.
  - The sign convention, the tension face, hogging, sagging and the positive displacement direction are all defined on sheet 1.
  - No presence-only or validity-only rows.
  - The Ideal Flow, rubric and prompt are generated from one `key.json` (`build_rubric.py`).
  - PASS.

## Blind solves (subagents, no key access)
1. **First solve, on the first draft packet.** Every value matched the key at 4 s.f. Its notes were fixed:
   - the splice was dimensioned only at grid 1 (now every column carries its own dimension);
   - the log's Day 7 entry now states that the L3 and roof finishes loads are present;
   - a leader-label rule was added to the data sheet.
2. **Second solve, on the final packet** (staggered grid 2 splice, 168.3x6.3 CHS braces). All 30 graded values matched exactly. Its one fair note was that "face towards grid 4" is undefined for the column on grid 4. Reworded to "the face on the grid 4 side (away from grid 1)".

## Physical consistency
- BR1 carries 138.7 kN in compression; its Euler load is about 296 kN.
- Column and beam forces are well within section capacity.
- Equilibrium: vertical reactions 3569.4 kN; horizontal reactions balance the 119 kN of wind.

## Score simulation
Simulated score for each likely single misread (all other readings correct; rubric v1, the 12 non-numeric points assumed passed):

| Misread | Score |
|---|---|
| Column splice labels swapped | 9.4–18.1 |
| Grid 2 splice read at L2 | 12.6 |
| Splices taken at floor level | 9.4 |
| Short grid 2 length read as 73 | 18.9 |
| Storey heights swapped | 15.7–18.9 |
| Bays 7.5/7.2 swapped | 9.4 |
| Simple connection at the wrong end | 9.4 |
| Storage zone or AHU-2 measured from the wrong grid | 9.4–18.1 |

Beam-section misreads are local and simulate at 25–92. Beam labels are horizontal and centred, so these are the least likely slips.

## Re-audit before sending (2026-10-12), against the reviewer photos and minor feedback
- **Mechanical audit (`platform/audit.py`): ALL CHECKS PASS.**
  - 43 criteria, all 301 characters or fewer (longest 180), all verb-led, all weights legal.
  - Every numeric row's accept range contains its stated value, and the value is in `key.json`.
  - Every decimal in the Ideal Flow appears in the rubric (no C2-type mismatch).
  - Every prompt beam end, column position and memo item has a row.
  - The -5 penalty covers "base every number on your own executed program".
  - The PDF has no Info or ID, empty metadata, no vectors, no answer values in the text, and no hits in any decompressed stream. The ICC profile naming the generator has been removed.
- **Changes in this pass:**
  - Column rows give one signed value and accept the equivalent magnitude with the tension face (the same quantity).
  - Memo rows reduced to item + state + log entry.
  - The results-file row checks content, not just presence.
  - The Synthesize box no longer asks for a "flag" sentence the prompt does not request.
- **Reviewer patterns (#75, #76):**
  - No expected value outside the packet's legal set or needing an unstated rule; two blind solves matched all 30.
  - The only required explanation is the memo, which has 7 rows.
  - No mechanism+value bundles.
  - Every metric is defined in data sheet conventions a to f.
  - No validity-only or presence-only rows.
  - The conditional prompt rule has its penalty.
