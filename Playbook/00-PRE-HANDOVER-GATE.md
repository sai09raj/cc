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
