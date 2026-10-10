# CW-200 v1 pre-entry audit (2026-10-10)

## Standing checks
- Tool use + output files: prompt says "Using tools" and requires 3 files (solver source, results file, memo). PASS
- PDF metadata: no /Info, no /ID, no XMP, no Producer/Creator/dates/matplotlib in raw bytes or decompressed streams. PASS
- Answer values not present in PDF text (checked by make_packet.py). PASS
- Criterion length <= 301: longest 201. PASS
- Atomic: one value / one state / one file per criterion; signed ring flows are one quantity (magnitude with direction). PASS
- Self-contained: every criterion names the item, the time (09:00 handover), the value and the tolerance. PASS

## Review #76 (Fail - Major / Moderate)
- Expected value outside the packet's legal set: valve openings (35 %, 100 %) are from the FV table; vapour pressure 2.339 kPa from the data sheet; elbow count follows the data-sheet junction rule. PASS
- Values needing an unstated rule: auto-start, stop, MANUAL, saturation, column separation, PI-100, fitting-at-point are all stated (data sheet notes 2-5, controllers paragraph). Blind re-solve of final PDF: see below.
- Missing criterion for a prompt requirement: items 1-8, each memo entry (4 pumps, 2 controllers, 2 hand valves), 3 files all mapped. Added P-201A (was missing). FIXED
- Bundled mechanism + value: FIC-201 holding / FV-201 opening split into two criteria. FIXED
- Undefined metric: PI-100 (note 4), TK-1 level (EL of water surface), lowest absolute pressure (note 2/3) all defined. PASS

## Review #75 (minor)
- Rubric value vs Ideal Flow vs drawing: TK-1 inlet EL in Ideal Flow corrected 30.0 -> 31.5 m. FIXED
- Validity-only / presence-only criteria: none (every numeric criterion has the value and tolerance; E-206 zero). PASS
- Prompt "only if" rules without a negative: the only conditional rule ("every number from your own executed computation") has the -5 penalty. PASS
- Lowest-pressure location now accepts the separated stretch starting at the top of the drop (the data sheet's note 2 makes both correct). FIXED

## Entry
Copy-paste every field; screenshot each entered field and compare with these files.
