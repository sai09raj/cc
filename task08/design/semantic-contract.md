# LEDGER-8 semantic contract

Executable contract for the reference consolidation engine. Every rule
below must be visibly recoverable from the packet (diagram, table, or
stated prose); this file is the internal design source, not the
artifact itself.

## S01 — Entity structure

One parent (P) and three subsidiaries: S1 (100% owned, domestic), S2
(80% owned, domestic), S3 (100% owned, foreign). All entities report in
USD except S3, which reports in EUR and must be translated (S03). There
is no time dimension and no parameter sweep: exactly one consolidation,
applied once, to one fixed set of four trial balances.

## S02 — Each entity's own trial balance (input constants)

Every entity states its own standalone trial balance: asset, liability,
and equity accounts (balance-sheet), plus revenue/expense accounts
(income-statement, this period's activity only). `RetainedEarnings` in
every entity's own trial balance is always the BEGINNING-of-period
balance — this period's income-statement activity is not yet closed
into it. Every entity's own assets equal its own liabilities plus its
own common stock plus its own beginning retained earnings plus its own
net income (S02's own internal consistency check, independent of
consolidation).

## S03 — Foreign-currency translation (S3 only)

S3's assets, liabilities, and common stock translate to USD at the
stated CLOSING rate. S3's income-statement accounts (this period's
flows) translate at the stated AVERAGE rate. S3's beginning
RetainedEarnings translates at the stated HISTORICAL rate (the rate in
effect when it was earned, distinct from both the closing and average
rates). The Cumulative Translation Adjustment (CTA) is the resulting
plug: `CTA = TotalAssets - TotalLiabilities - CommonStock -
RetainedEarnings(beginning, translated) - NetIncome(translated)`,
posted as its own equity line. CTA exists because the same underlying
foreign-currency net income is translated at the average rate as a flow
but must reconcile against balance-sheet items translated at a
different (closing) rate.

## S04 — Intercompany transaction facts (input constants)

1. **Inventory sale**: P sold inventory to S1 at a stated transfer price,
   above P's own cost. A stated fraction of that inventory remains in
   S1's ending inventory at year end (unsold to any outside party).
2. **Loan**: S2 owes P a stated intercompany loan principal, plus stated
   interest for the year (recorded as P's interest income and S2's
   interest expense).
3. **Trade balance**: P separately carries a stated intercompany trade
   receivable from S1 (unrelated to the loan above), matched by S1's
   intercompany payable.
4. **Dividend**: S1 paid P a stated intercompany dividend during the
   year, recorded by P as dividend income.

## S05 — Combining (before any elimination)

Sum all four entities' own trial balances (S3 already translated per
S03) into one pre-elimination combined column, account by account. This
combined column is not itself a deliverable; it is the starting point
for S06.

## S06 — The six required elimination entries

Each entry below is a genuine double-entry journal entry: converting
every line to its debit-equivalent (a positive amount on a debit-normal
account — assets, expenses — is a debit; a positive amount on a
credit-normal account — liabilities, equity, revenue — is a credit) must
sum to exactly zero. An entry that does not balance this way is not a
valid elimination, regardless of what it appears to accomplish.

- **E1 (intercompany sale)**: eliminate the full transfer-price amount
  from intercompany sales revenue against cost of goods sold, in full —
  this removes the entire intercompany transaction, not just the
  unrealized portion.
- **E2 (unrealized profit)**: separately defer the unrealized profit
  still sitting in the buyer's ending inventory — `(fraction unsold) x
  (transfer price - seller's own cost)` — by increasing COGS and
  decreasing inventory by that amount. E1 and E2 are both required; E1
  alone does not defer unrealized profit, and E2 alone does not remove
  the double-counted revenue.
- **E3 (intercompany loan)**: eliminate the loan principal (receivable
  against payable) and the loan's interest (interest income against
  interest expense) in full.
- **E4 (intercompany trade balance)**: eliminate the separate,
  loan-unrelated trade receivable/payable in full.
- **E5 (intercompany dividend)**: remove the dividend from income (it is
  not real consolidated income — group cash simply moved between two
  entities inside the group) and restore the payor's retained earnings
  by the same amount (an intercompany dividend must have zero net effect
  on both consolidated net income and consolidated retained earnings).
- **E6 (investment/equity elimination)**: for each subsidiary, remove
  100% of that subsidiary's own common stock and beginning retained
  earnings from the combined totals, replacing them with (a) the
  elimination of the parent's Investment-in-that-subsidiary account at
  the parent's ownership percentage, and (b) a new NCI_Equity line at
  the complementary (non-controlling) percentage. This balances for any
  ownership fraction, including 100% (where the NCI share is zero).

## S07 — Net income and its split

Consolidated net income (post-elimination) is computed from the
post-E1-through-E6 combined income-statement accounts. It is split
between the controlling interest and non-controlling interest (NCI):
NCI's share is the minority ownership percentage applied to the
partially-owned subsidiary's (S2's) OWN standalone net income only (S2's
intercompany loan interest nets entirely against the parent's side via
E3 and does not itself change S2's own reported net income). The
controlling share closes into consolidated RetainedEarnings; the NCI
share closes into NCI_Equity (added on top of what E6 already posted for
beginning NCI equity) — NCI_Equity accrues this period's NCI income
exactly as consolidated RetainedEarnings accrues the controlling share.

## S08 — Investment basis (no goodwill)

Every Investment-in-Subsidiary account, as given in the parent's own
trial balance, equals the parent's ownership percentage multiplied by
that subsidiary's own beginning equity (common stock at the applicable
translation rate, plus beginning retained earnings) — a stated
simplifying assumption: the parent invested at each subsidiary's
then-book-value, with no goodwill or purchase differential. This is what
makes every Investment-in-Subsidiary account eliminate to exactly zero
in E6, for every subsidiary, regardless of ownership percentage.

## S09 — Required outputs

The final consolidated balance sheet must satisfy Assets = Liabilities +
(CommonStock + consolidated RetainedEarnings + CTA + NCI_Equity) exactly
— this is the primary feasibility invariant (S10) a submission's own
work must satisfy, independent of matching any particular reference
number.

## S10 — Independent verification (feasibility invariants + certificate)

A separately-coded auditor, sharing only immutable input constants with
the primary implementation, must independently re-derive the full
consolidation (or check a complete feasibility certificate) and confirm:
**balance-sheet balance** (S09's invariant); **entry balance** (every one
of the six elimination entries independently re-verified to balance in
debit-equivalent terms); **NCI consistency** (NCI_Equity plus the
controlling share of consolidated equity, summed, equals total
consolidated equity net of liabilities). Two required adversarial
mutations: an elimination entry that does not balance (a missing
offsetting line), and a currency-translation error (translating an
item at the wrong one of the three stated rates). The auditor must
reject both while still accepting the true original.

## S11 — Certification

Build the serialization as exactly these lines, in this exact order,
each line `AccountName=Value` with no spaces, no currency symbol, no
thousands separator, no decimal point (every input and every rate is an
exact decimal, so every computed amount is a plain integer — never a
rounded float), and a leading `-` only for a negative value:

1. The literal header line `LEDGER8-CERT-V1`.
2. One line for each of these 16 balance-sheet accounts, in exactly
   this order (not alphabetical), using the account name exactly as
   spelled here, and including every one even when its value is
   exactly 0: `Cash`, `AR_Trade`, `IC_Receivable`, `IC_LoanReceivable`,
   `Inventory`, `Inv_in_S1`, `Inv_in_S2`, `Inv_in_S3`, `PPE_Net`,
   `AP_Trade`, `IC_Payable`, `IC_LoanPayable`, `CommonStock`,
   `RetainedEarnings`, `NCI_Equity`, `CTA`.
3. One line for each of these 7 income-statement accounts, in exactly
   this order, same zero-inclusion rule: `SalesExternal`, `SalesIC`,
   `COGS`, `OpEx`, `IC_InterestIncome`, `IC_InterestExpense`,
   `DividendIncomeIC`.
4. Two final lines, in order: `NetIncome`, then `NCI_NetIncome`.

Example (illustrative numbers only, not the task's actual answer): if
`Cash` were 100 and `AR_Trade` were 0, their lines would read exactly
`Cash=100` and `AR_Trade=0`.

Join all 26 lines (the header plus 25 account lines) with a single `\n`
character, UTF-8 encode, hash with SHA-256; report the first 16 hex
characters as the trace-integrity certificate.

## S12 — Deliverables

Consolidation engine source; independently-coded auditor source; the
final consolidated balance sheet and income statement; a findings
report (nothing to flag under the stated facts — see the score-topology
audit for what a genuine violation would require); certification
evidence (the trace hash plus the two adversarial-mutation rejection
results); and a memo explaining the causal chain from the intercompany
facts (S04) through the six elimination entries (S06) to the final
consolidated numbers.
