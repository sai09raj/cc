# PRE-HANDOVER GATE: run before giving the user ANY rubric, prompt, Ideal Flow or artifact

The user should never have to paste this list or the reviewer photos again. Run every item yourself and report the result as a table (one line per check) together with the files.

## A. User's standing requirements (verbatim intent)

1. **Tool use and file output:** every prompt must require tool use and at least one output file. Any file type or tool is allowed, for input and for output.
2. **Metadata:** strip all metadata from every artifact, whether a visual, a PDF or any other form. Otherwise the model can recover the solution from it and will not score below 50.
3. **Length:** every rubric criterion is 301 characters or fewer.
4. **Atomic and self-contained:** after writing the rubric, check every criterion is atomic and self-contained.
5. **Reviewer feedback:** check the rubric set against every reviewer feedback item in section B, and confirm none applies.
6. **User preferences:** short answers; clickable links (SendUserFile), not zips, except the Playbook zip; exact field-by-field before/after edits in chat when asked; check the user's screenshots for typos value by value; record every lesson in the Playbook.

## B. Reviewer feedback received so far (each one is a check)

| # | Feedback (source) | Severity | Check to run |
|---|---|---|---|
| B1 | Expected value outside the legal set the packet allows (age limit 164 where only 64/96/128/192 exist) | **Major, counterproductive** | Machine-check every expected value against the packet's stated tables and options. |
| B2 | 22 criteria needed an **unstated rule** (controller leaves WRITE mode); all 5 runs followed the packet literally and got a different value | **Major, counterproductive** | **Independent re-solve:** a second solver written only from numbers parsed from the packet text and values read off the drawing image must match every graded value. Also do the code-to-source audit: every rule in the reference code appears in the packet. |
| B3 | Nothing graded the prompt's **required explanation** ("why one knob is not enough") | **Major, missing criterion** | Map every clause of the prompt to at least one criterion, including every "explain", "why", "state", "list" and each named item. |
| B4 | **Mechanism description plus a trace value** in one criterion (C13–C24); C19/C24 bundled 5–6 rules; C31 bundled 2 constants with a 5-part explanation | **Moderate, atomicity** | One value or one fact per criterion. Flag any criterion containing "and", "because", ";" or a parenthetical second fact, and split or justify it. Never describe how the solver works inside a value criterion. |
| B5 | Criteria graded **undefined metrics** (`assembly_highwater`, `commit_gap_cycles`); runs that matched everything else failed them | **Moderate, overly specific** | Every graded quantity has a definition in the packet: what it is, where or when it is measured, its units and its sign convention. |
| B6 | Criterion said platform A at (-700, 200), but the plan and the Ideal Flow said (-700, 2700) | **Minor, counterproductive (C2-type)** | Generate the rubric, Ideal Flow and key from one key.json. Every number in the Ideal Flow must be in the rubric or the packet and must match the drawing. |
| B7 | Lower-bound criteria passed any bound ≤ the true minimum, so a trivial 0 passed | **Minor, slightly broad** | No validity-only criteria: when the prompt asks for the best or a correct value, grade the value with an explicit range. |
| B8 | A scenario was mislabelled (S4 called "5 bays", value called S5's) | **Minor** | Labels and names in every criterion are generated from the key, never retyped. |
| B9 | A criterion checked only that a count was **present**, not that it was correct | **Minor, slightly broad** | Presence-only rows are allowed only for file delivery. |
| B10 | **Uncounted gap:** no penalty for claiming "proven optimal" when the bound did not support it | **Minor** | For every claim a response could make wrongly (optimal, meets, safe, compliant), a criterion must reward the correct verdict or penalise the false claim. |
| B11 | Platform "Rubric Contradictory Criteria Check": a memo row repeated a state already graded in a results row (#99) | Critical flag | Grade a state once. If the results rows grade it, the memo row grades only the citation. |
| B12 | Platform checker invented a criterion ("L1 reported as not computed") | False positive | Mark Invalid, quote the real rows, and show that one response can satisfy them all. |
| B13 | Platform grader passed near-misses when tolerances were given as percentages (#90) | Grading | Give every numeric criterion an explicit accept range ("accept a to b"), never a percentage. |
| B14 | Drawing page blank in macOS Preview: soft mask set to /DeviceRGB (#100) | Artifact | Flatten images to RGB before inserting them; no SMask; render every page with a second engine (pypdfium2). |

## C. Mechanical checks: run the script

```
python3 Playbook/tools/gate.py <platform_dir> <artifact.pdf> [packet_text_files...]
```

It checks: criterion length ≤ 301; compound-criterion flags (B4); explicit ranges, with no percentages (B13); Ideal Flow numbers present in the rubric or packet (B6); the prompt requires running code and delivering files (A1); PDF metadata, XMP, ID, generator strings and ICC profiles (A2); soft masks and 1-bit RGB images (B14); a second-renderer pass of every page (B14); and duplicate criteria (B11). Anything it cannot judge (B1–B3, B5, B7, B10) stays a manual line in the report table, with the evidence: independent re-solve result, prompt-clause map, packet definitions.

## D. Report format to the user

One table: check | result | evidence. Then the files (clickable), then exact field edits if anything changed.

## E. Reviewer feedback, verbatim (transcribed from the user's photos; keep for reference)

### E1. Photo 1: "[Fail - 15%+ Major Rubric Errors]" (Quality: Overall Task 2)

> [Fail - 15%+ Major Rubric Errors] 24 of the 50 criteria (48%) have major errors, well above the 15% limit. C39 is counterproductive: it expects an age limit of L=164, but Panel F only allows 64, 96, 128, or 192, so a correct answer can never pass it (the CB's own notes show the intended value was 64). The rubric is also missing a critical criterion, because nothing checks the prompt's required explanation of why changing one knob is not enough or the causal design argument. The remaining 22 criteria (C15–C24, C27–C33, C35, C36, C38, C40, C41) are counterproductive because their expected values cannot be derived from the image. Following the packet as written gives a baseline of 14008 cycles, and all five model runs produced exactly this result with the same dispatch hash. The CB's key expects 9026 cycles, which requires an unstated rule that the controller leaves WRITE mode once no writes are waiting. These criteria therefore penalize responses that correctly follow the specification.

Maps to checks B1 (legal values), B2 (unstated rule: independent re-solve), B3 (required explanation graded).

### E2. Photos 2 and 3: "[Fail - 20%+ Moderate Rubric Errors]" (Quality: Overall Task 2)

> [Fail - 20%+ Moderate Rubric Errors] Seventeen of the 50 criteria (34%) contain moderate errors, which is above the 20% threshold, so this dimension falls under Fail. Most of these are atomicity problems. Criteria C13 through C24 each combine two unrelated checks: a description of how one part of the simulator should work, and an exact value for one row of the trace file. For example, C18 asks whether credit is restored only when the K packet arrives back upstream in stage 1, and in the same criterion asks whether trace row 770 equals (1217,D,e3,23,3,V,3). These two checks don't really belong together, because the value of any given trace row depends on the entire simulation working correctly, not on the specific mechanism named in the criterion. A response could implement credit restoration perfectly and still get row 770 wrong because of an unrelated bug elsewhere, and it would lose the full criterion. The model runs confirm this: the two lowest-scoring runs (fc88bc and bdaada) failed all twelve of these criteria together, which shows that the trace probes alone decide the outcome and the mechanism descriptions add nothing to the grading. Two of these criteria are even more overloaded. C19 bundles K creation, duplicate detection, the J-window rule, exact-attempt U/V joining, expiry at age 72, and smallest-attempt commit, plus a trace probe. C24 bundles control-before-DATA ordering, tie-breaking keys, blocked-edge exclusion, independent E-run counters, the BURST rule, and X-only gating, plus another trace probe. C31 has the same problem in a different form: it combines two constant values (μ=3 and ω=72) with a five-part written explanation of the baseline failure chain, so a response that reports the constants correctly but explains the failure poorly, or the reverse, can't be graded cleanly. ---- The remaining four moderate errors are overly specific criteria. C32, C33, C46, and C48 each require exact values for `assembly_highwater` and `commit_gap_cycles`, but the device contract never defines either metric. Panel B9 lists them and says they "follow B3–B8," yet none of those panels explains what they measure or when they are sampled. Because of this, a response can reasonably interpret these metrics differently from the task author and be marked wrong for it. This is exactly what happened: runs 4036e1 and 5aa4f4 matched the trace, all twelve probes, all five checkpoints, and the recommended configuration exactly, yet failed these four criteria only because of differences in those two undefined metrics. Together, the thirteen atomicity errors and four overly specific errors make up the seventeen moderate errors.

Maps to checks B4 (one value or fact per criterion; no mechanism plus value) and B5 (every graded metric defined).

### E3. Minor-issues review (text supplied by the user)

> There were only some minor issues:
> C2 (Counterproductive): It expects platform A at (-700, 200), but the site plan, and the ideal flow, put A at (-700, 2700). The criterion penalizes the correct reading.
> C17-C21 (Slightly Broad): Each lower-bound criterion accepts any bound that doesn't exceed the true minimum, so a trivial bound such as 0 passes, even though the prompt asks for the strongest bound you can establish. C20 also mislabels its scenario: it gives S4 "5 feeder bays" (it has 6) and calls its value "S5's true minimum," although the number, 7,480,955, is correct for S4.
> C12 (Slightly Broad): It checks only that a feeder count is reported for each scenario, not whether the count is correct.
> Uncounted gap: No criterion penalizes calling a cost "proven optimal" when the reported bound is below the cost. C39 only catches costs that exceed the true minimum.

Maps to checks B6 (C2-type mismatch), B7 (validity-only), B8 (mislabel), B9 (presence-only), B10 (uncounted false claim).

### E4. Platform checker flags (screenshots during entry)

> Rubric Contradictory Criteria Check: "Clarify target separation: A3 state summary vs memo citation; avoid mixing state and evidence in one criterion." (DH-19 rows 1 and 31.) Maps to check B11.

> Rubric Contradictory Criteria Check: "'L1 open' vs 'L1 reported as not computed' - same memo target, incompatible required state vs penalty." (DH-19; no such criterion existed.) Maps to check B12: mark Invalid with the reason.

## F. After the runs: validate the scores

1. For each run, extract its section reading and log state from the trajectory, feed them into the model, and confirm its reported values match within rounding. If they match, its solver is right and the loss comes from reading or state, not from the task.
2. Re-grade each run with the accept ranges as printed in the rubric, and compare with the platform score.
3. Check that the non-numeric rows (state, verdicts, memo citations, files) were earned or lost for real reasons.
4. Any mismatch means a task or rubric defect: investigate before claiming the stump.
