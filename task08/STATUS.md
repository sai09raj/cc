# Task 08 — LEDGER-8

Current active candidate: **LEDGER-8**, in `reference/`, `design/`,
`platform/`, `artifact/`. State: CONSOLIDATION ENGINE VERIFIED (balances,
cross-checked byte-for-byte against a structurally independent auditor),
SCORE-TOPOLOGY AUDITED with an honestly-documented margin caveat (below),
FULL PLATFORM PACKAGE COMPLETE (rubric, prompt, ideal-flow, metadata-
stripped PDF artifact). TWO REAL PILOTS RUN (see "Critical finding" below)
-- both scored 92-94%, which drove a real fix to the certification spec;
re-pilot needed to confirm against the fixed packet.

## Why this task exists

QUORUM-7, CISTERN-7 (shelved), and ATRIUM-9 all shared one meta-shape:
tick simulator -> parameter sweep -> lexicographic selection -> verifier
-> adversarial mutations -> hash certificate -> memo. LEDGER-8
deliberately breaks that shape: a multi-entity financial-statement
consolidation and elimination-entry audit, with no time dimension and no
parameter sweep. See `design/architecture-attack.md`.

## Real bugs found while building the reference engine

Building `reference/ledger8_engine.py` to actually balance (Assets =
Liabilities + Equity) surfaced four distinct real bugs before it did,
each now a rubric negative criterion: a sign error in the dividend
elimination (E5), two different intercompany receivables conflated into
one account (the loan receivable and the trade receivable), net income
double-counted into retained earnings, and an inconsistent
currency-translation formula for the foreign subsidiary's CTA plug. None
of these were hypothetical "a model might do this" guesses -- a careful,
rigorous implementation (mine) made each one and had to catch it via the
balance invariant before shipping.

## Score-topology finding: this task shape resists low single-mutant scores

Unlike QUORUM-7's cascading state machine (where one early bug corrupts
most of the downstream trace), LEDGER-8's facts are largely
**independent**: getting one elimination entry wrong typically leaves
most other accounts -- cash, AR, PPE, and often net income itself --
exactly correct. Empirically, even a mutant that breaks the fundamental
balance invariant (closing net income into retained earnings twice) only
diverges on 3 of the 49 criteria.

After extensive genuine reweighting (not reverse-engineered to force a
target -- see the explicit caveat in `platform/rubric.md`'s header),
the honest floor for a single, clean, isolated bug is **60-82%**:

| Mutant | Score |
|---|---|
| omit E2 (unrealized-profit deferral) | 60.4% |
| wrong NCI ownership percentage | 65.5% |
| omit E3 (intercompany loan elimination) | 77.0% |
| double-counts net income into RE (breaks balance invariant) | 76.3% |
| wrong FX rate (S3 common stock) | 77.7% |
| omit E4 (trade intercompany balance) | 79.1% |
| omit E1 (intercompany sale elimination) | 82.0% |

Canonical scores 100%. All seven mutants stay comfortably under 100%
and are real, verified-via-execution findings -- but none individually
lands under 50%, let alone the tighter 30-35% band QUORUM-7 achieved.

## Atomicity correction (post-build audit)

After publishing the first full platform package, a user-prompted review
against an unrelated task's failed rubric-quality review (a real "Fail
-- 20%+ moderate rubric errors" verdict for bundling independently-
checkable facts into single criteria) triggered an audit of this
rubric's own criteria 20, 21, and 36 using the same method: run the
task's own 7 real mutants and check whether each bundled criterion's
sub-facts pass/fail independently.

They did. Confirmed by direct execution, not assumption:
- Old #20 (`IC_Receivable`, `IC_LoanReceivable`, `IC_Payable`,
  `IC_LoanPayable` bundled as one `+5` check): omitting E4 alone left
  the two *trade* accounts wrong while the two *loan* accounts stayed
  correct; omitting E3 alone did the reverse. A submission that fixed
  one elimination but not the other was losing the full 5 points for
  half the actual mistake.
- Old #21 (`Inv_in_S1`, `Inv_in_S2`, `Inv_in_S3` bundled as one `+5`
  check): a wrong NCI percentage broke only `Inv_in_S2`; a wrong FX
  rate broke only `Inv_in_S3`. `Inv_in_S1` stayed correct in both cases.
- Old #36 (auditor existence + shares-only-constants + independent
  re-derivation + rejects *both* adversarial mutations + reports in
  memo, bundled as one `+4` check): the two adversarial mutations are
  caught by two structurally different mechanisms (internal
  self-consistency vs. hash mismatch against the auditor's own
  recomputation) -- an auditor could plausibly implement one correctly
  and not the other.

Fixed by splitting these three criteria into seven atomic ones (now
#19-20 for the two IC-account pairs, #21-23 for the three Investment
accounts individually, #38-39 for the two auditor-rejection facts --
numbering as of the final rubric after the second correction below),
raising the criteria count from 46 to 50 (still within the platform's
12-50 range) while keeping the exact same positive total (139). The
negative total was -45 immediately after this first fix, before the
second correction below changed it again. Re-running the fixed rubric
against the same 7
mutants (re-verified with `verify_fix.py`-style per-account checks, not
just the aggregate score) confirms the new criteria now track each bug
independently -- e.g. under "omit E4", the new `IC` trade-pair criterion
correctly fails while the new `IC` loan-pair criterion correctly still
passes. The aggregate mutant percentages shifted up by 1-3 points
(better partial credit for the correct half of a previously-bundled
fact) but the overall 60-82% floor and discriminating shape are
unchanged. Criterion 1 (package execution hygiene) and criterion 11
(E6 applied across all three subsidiaries) were reviewed under the same
test but left unsplit -- they bundle facts from one coherent
mechanism/delivery gate rather than facts shown to independently diverge
under a real mutant, and splitting them would have pushed the criteria
count past the platform's 50-criterion cap for a lower-confidence gain.

A parallel audit of QUORUM-7's already-submitted rubric found a larger,
higher-stakes version of the same issue (criteria 16-18, 19-28, and
others, together carrying roughly 60% of that rubric's 197-point total,
empirically confirmed to split under its own real mutants) -- but that
rubric is already submitted and out of scope to edit.

## Second correction: missing independence-prohibition negative

While entering criteria into the platform, its own "Rubric Prohibition
Criteria Check" linter caught a real gap (distinct from the atomicity
splits above): criterion 1's independence requirement ("shares only
immutable input constants with your primary implementation") had no
dedicated negative criterion penalizing a submission whose auditor
violates it -- the same hidden-prohibition pattern as Playbook mistake
#59, and a gap QUORUM-7's own rubric does not have (its criterion #41
already covers this for the verifier). A separate platform finding
("Rubric Contradictory Criteria Check" on criteria 7/8, the E1/E2 pair)
was reviewed and marked invalid -- both criteria reference "transfer
price" because it is one immutable input constant stated in the packet,
not a value derived by either entry, so the two criteria test
independently-achievable facts and are not actually contradictory.

Fixed by merging the old criterion 2 ("exactly one BS/IS, no
duplicates") into criterion 1 (both are process/delivery-hygiene facts,
the same category criterion 1 already bundled by deliberate prior
decision) to free one slot within the platform's 50-criterion cap, then
adding a new negative criterion 48 ("Delivers an auditor that shares
anything beyond immutable input constants...", -4, mirroring QUORUM-7's
#41). Net criteria count unchanged at 50; positive total unchanged at
139; negative total rose from -45 to -49 (eight named negatives now
total -41, plus the unchanged -8 trap). Criterion 1 was rewritten to fit
the 301-char cap after the merge (298 chars). Re-ran
`score_counterfactual.py` against all 7 mutants after the full
renumbering -- every score is unchanged from before this round, confirming
the renumbering didn't disturb any scoring logic.

**This is an accepted, documented tradeoff**, not an oversight: offered
the choice between (a) accepting this honest, higher threshold, (b)
redesigning for genuine multi-period interdependence, or (c) redefining
mutants as realistic bundled mistakes, the call was to accept (a). The
expectation, matching what QUORUM-7's own real pilots showed (two
independent attempts scored 31%/32% despite being individually
thorough), is that a **real** pilot run naturally combines several small
mistakes rather than making one isolated clean error, and should still
land under 50% in practice -- this expectation was wrong, as the next
section shows; the real floor turned out to be a packaging bug, not a
task-shape property.

## Critical finding: real pilots scored 92-94% due to a certification spec bug

Two real pilot runs against the (pre-fix) packet scored **94%** and
**92%** -- nowhere near the 60-82% single-mutant floor, let alone the
"should land under 50%" expectation above. Both trajectories were
inspected directly (not just their final score).

Both runs independently recovered and computed **every single dollar
value correctly** -- matching this reference's own numbers exactly:
total assets 3,236,250; liabilities 323,200; equity 2,913,050 (common
stock 1,000,000, RE 1,821,300, CTA 550, NCI 91,200); net income 378,500
(controlling 366,300, NCI 12,200). Both built genuinely independent
auditors that correctly rejected both required adversarial mutations.
Both delivered all six named products. In other words: both models
solved the actual accounting problem perfectly.

What they could not do was match the trace-integrity hash (criterion
37, +8, the single highest-weighted criterion) -- and critically, **the
two pilots didn't even match each other's hash**. Pulling the actual
serialization code each one wrote confirmed why: the old S11/packet
text ("one line per account, sorted by account name... preceded by a
header line") never specified the exact account-name tokens, a header
string, or whether zero-balance (eliminated) accounts should be
included. Pilot 1 used keys like `BS::Cash`, `IS::Sales`, skipped every
zero-balance account, and used a different header entirely. Pilot 2
used keys like `Sales -- intercompany`, `Net income (total)`, with yet
another header and its own spacing conventions. All three
implementations (this reference's and both pilots') are internally
consistent and individually defensible -- the packet simply never
pinned down which one was required. A model that is 100% correct on the
economics loses the hash criterion purely by guessing wrong on an
underspecified formatting convention, worth +8/139 and single-handedly
explaining both scores (139-8=131, 131/139=94.2%, matching pilot 1
almost exactly; pilot 2 likely lost a few more points elsewhere).

This is a packaging bug, not a task-difficulty finding, and unlike the
score-topology margin (which was a disclosed, accepted tradeoff), this
one is a straightforward defect: the single most heavily-weighted
criterion in the whole rubric was not actually testable as specified.
Fixed by rewriting S11 (both `design/semantic-contract.md` and the
actual packet text in `artifact/make_packet.py`) to be fully mechanical:
a literal header string, the 25 accounts in one fixed explicit order
(not "sorted," which still requires guessing exact name casing), an
explicit zero-inclusion rule, an explicit plain-integer value format,
and a worked example using fake numbers (`Cash=100`, `AR_Trade=0` --
verified these do not collide with any real computed value). Both
`ledger8_engine.py` and the independently-coded `ledger8_auditor.py`
were updated to the new fixed-order serialization (format only -- no
computation logic changed) and re-verified to still agree byte-for-byte:
new hash `cd5791e7dc01e208`, replacing `ccf0131030c67a99` everywhere
(rubric criterion 37, `score_counterfactual.py`). Reran the full mutant
suite after the change: all 8 scores (the original 7 plus the
independence check) are numerically identical to before the hash-format
change, confirming this was purely a serialization-format fix with zero
effect on any correctness-based criterion. The PDF artifact was rebuilt
and re-verified clean (metadata, no leaked values, fake example numbers
don't match any real answer).

**This needs a fresh real pilot to confirm the fix actually closes the
gap** -- the old 92-94% scores are now stale evidence against a packet
that no longer exists in that form.

## Third correction: removed a redundant criterion

While entering the rubric, the platform's "Rubric Overlapping Criteria"
linter caught that criterion 12 ("every Investment-in-Subsidiary account
eliminates to exactly zero") was a pure logical restatement of the three
now-atomic value criteria (`Inv_in_S1`/`S2`/`S3` = 0, then numbered
21/22/23): a submission passing all three has necessarily already
satisfied the broader claim, and one failing any of them has necessarily
already failed it. Unlike the atomicity correction above (splitting an
over-bundled criterion into parts that *do* diverge independently under
real mutants), this is the reverse case -- a broader criterion made
redundant by atomic criteria that already existed alongside it.

Checked whether a shortcut could defeat this (zero the investment
accounts without genuinely running E6) and found it can't evade
detection: E6 also drives `CommonStock`, `RetainedEarnings`, and
`NCI_Equity`, each separately tested at higher weight, so a fake
investment-zeroing would still be caught there. Removed criterion 12
(old numbering), renumbered everything after it down by one. Criteria
count: 50 -> 49. Positive total: 139 -> 137 (lost the removed
criterion's +2). Negative total unchanged (-41 named + -8 trap = -49).
Reran `score_counterfactual.py`: canonical still scores 100% (now
137/137), and all 7 mutant percentages shifted by only 0.2-0.5 points
(smaller denominator) while staying within the documented 60-82% band.

## Deliverables so far

- `reference/ledger8_engine.py` — primary consolidation engine (dict/
  named-account style), balances verified, hash `cd5791e7dc01e208`.
- `reference/ledger8_auditor.py` — independent auditor (flat
  general-ledger posting-list style), agrees byte-for-byte with the
  primary, correctly rejects both required adversarial mutations.
- `reference/score_counterfactual.py` — score-topology audit, 7 mutants.
- `design/architecture-attack.md`, `design/semantic-contract.md`.
- `platform/rubric.md` — 49 criteria, positive total 137, re-verified
  (301-char cap, ≤10 weight cap, atomicity confirmed by mutant testing,
  not just inspection) after the atomicity correction above.
- `platform/prompt.md` — 460 words, zero internal hyphens (avoids the
  platform's hyphen-stripping word-count linter, Playbook mistake #64),
  explicitly requires executing the delivered engine/auditor and
  delivering output files.
- `platform/ideal-flow.md` — Analyze/Execute & Generate/Synthesize.
- `artifact/ledger8_v2.pdf` — renamed from `ledger8.pdf` per Playbook
  mistake #46 (never reuse a filename across a content revision, since a
  platform/browser cache can serve the stale bytes); referenced by name
  in `platform/prompt.md`'s first sentence, updated together. 7 pages
  (4 rasterized figures: entity
  ownership structure, full trial-balance table, FX rate table,
  intercompany transaction facts; 3 text spec pages, grew by one page
  after S11/CERTIFICATION was rewritten to be fully mechanical).
  Verified byte-level: empty Info dict, null XMP, no PNG chunks, no
  tool/path signatures, no leaked computed/derived values anywhere in
  extracted text — only stated input constants and the fake-number
  certification example (`Cash=100`, `AR_Trade=0`).

## Remaining

- Fresh real pilot run(s) against the fixed packet (the two existing
  pilots, scored 94%/92%, were against the pre-fix certification spec
  and are stale evidence now — see "Critical finding" above).
