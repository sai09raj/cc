# Task 08 — LEDGER-8

Current active candidate: **LEDGER-8**, in `reference/`, `design/`,
`platform/`, `artifact/`. State: CONSOLIDATION ENGINE VERIFIED (balances,
cross-checked byte-for-byte against a structurally independent auditor),
SCORE-TOPOLOGY AUDITED with an honestly-documented margin caveat (below),
FULL PLATFORM PACKAGE COMPLETE (rubric, prompt, ideal-flow, metadata-
stripped PDF artifact). NOT YET pilot-tested.

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
diverges on 3 of the 46 criteria.

After extensive genuine reweighting (not reverse-engineered to force a
target -- see the explicit caveat in `platform/rubric.md`'s header),
the honest floor for a single, clean, isolated bug is **60-82%**:

| Mutant | Score |
|---|---|
| omit E2 (unrealized-profit deferral) | 60.4% |
| wrong NCI ownership percentage | 63.3% |
| omit E3 (intercompany loan elimination) | 75.5% |
| wrong FX rate (S3 common stock) | 75.5% |
| double-counts net income into RE (breaks balance invariant) | 76.3% |
| omit E4 (trade intercompany balance) | 77.0% |
| omit E1 (intercompany sale elimination) | 82.0% |

Canonical scores 100%. All seven mutants stay comfortably under 100%
and are real, verified-via-execution findings -- but none individually
lands under 50%, let alone the tighter 30-35% band QUORUM-7 achieved.

**This is an accepted, documented tradeoff**, not an oversight: offered
the choice between (a) accepting this honest, higher threshold, (b)
redesigning for genuine multi-period interdependence, or (c) redefining
mutants as realistic bundled mistakes, the call was to accept (a). The
expectation, matching what QUORUM-7's own real pilots showed (two
independent attempts scored 31%/32% despite being individually
thorough), is that a **real** pilot run naturally combines several small
mistakes rather than making one isolated clean error, and should still
land under 50% in practice -- this is unconfirmed until task #27's
real-pilot step runs for LEDGER-8.

## Deliverables so far

- `reference/ledger8_engine.py` — primary consolidation engine (dict/
  named-account style), balances verified, hash `ccf0131030c67a99`.
- `reference/ledger8_auditor.py` — independent auditor (flat
  general-ledger posting-list style), agrees byte-for-byte with the
  primary, correctly rejects both required adversarial mutations.
- `reference/score_counterfactual.py` — score-topology audit, 7 mutants.
- `design/architecture-attack.md`, `design/semantic-contract.md`.
- `platform/rubric.md` — 46 criteria, positive total 139, re-verified
  (301-char cap, ≤10 weight cap, atomicity) after final edits.
- `platform/prompt.md` — 460 words, zero internal hyphens (avoids the
  platform's hyphen-stripping word-count linter, Playbook mistake #64),
  explicitly requires executing the delivered engine/auditor and
  delivering output files.
- `platform/ideal-flow.md` — Analyze/Execute & Generate/Synthesize.
- `artifact/ledger8.pdf` — 6 pages (4 rasterized figures: entity
  ownership structure, full trial-balance table, FX rate table,
  intercompany transaction facts; 2 text spec pages). Verified
  byte-level: empty Info dict, null XMP, no PNG chunks, no tool/path
  signatures, no leaked computed/derived values anywhere in extracted
  text — only stated input constants.

## Remaining

- Real pilot run(s) (task #27-equivalent for this task).
