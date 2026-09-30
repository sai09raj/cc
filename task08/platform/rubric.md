# LEDGER-8 rubric

Positive total **139**; seven negative criteria totaling **-37** (**-4**,
**-6**, **-4**, **-5**, **-5**, **-5**, **-8**), plus a negative trap
**-8**. **46 criteria** (within the platform's 12-50 range). Every
weight is capped at 10. Every criterion body is 301 characters or
fewer. Criteria are binary. Accept equivalent correct work throughout:
equivalent languages, source organization, output schemas, file layout,
and formula notation.

Score-topology note: unlike a cascading state-machine task, this
task's facts are largely independent (an error in one elimination
entry typically leaves most other accounts correct), so single-bug
mutants score 60-82% individually rather than comfortably under 50% --
see `STATUS.md` for the full finding. Weights below are set by genuine
severity judgment, not reverse-engineered to force any mutant under a
target score.

### Package (1-2, weight 3)

| # | Wt | Criterion |
| --- | --- | --- |
| 1 | +2 | Executes the delivered offline consolidation engine and auditor with a documented, reproducible command, records actual tool versions in a declared offline, stdlib-only environment, and delivers all six named products as files. |
| 2 | +1 | Delivers exactly one consolidated balance sheet and one consolidated income statement -- no alternate, partial, or duplicate versions. |

### Local semantics/rules (3-14, weight 39)

| # | Wt | Criterion |
| --- | --- | --- |
| 3 | +2 | Every entity's own `RetainedEarnings`, as stated in its trial balance, is treated as a BEGINNING-of-period balance -- this period's income-statement activity is closed into it only once, after eliminations, not already embedded in it. |
| 4 | +3 | S3's assets, liabilities, and common stock translate to USD at the stated closing rate. |
| 5 | +2 | S3's income-statement accounts (this period's flows) translate to USD at the stated average rate, distinct from the closing rate. |
| 6 | +4 | S3's beginning `RetainedEarnings` translates to USD at the stated historical rate -- a third rate, distinct from both the closing and average rates. |
| 7 | +3 | E1 eliminates the full intercompany sale (the entire transfer price, not just the unrealized portion) from intercompany sales revenue against cost of goods sold. |
| 8 | +5 | E2 separately defers the unrealized profit still in the buyer's ending inventory (unsold fraction x (transfer price - seller's own cost)) via a COGS increase and matching inventory decrease. |
| 9 | +3 | E3 eliminates both the intercompany loan principal (receivable against payable) and its interest (interest income against interest expense). |
| 10 | +2 | E4 eliminates the separate, loan-unrelated intercompany trade receivable/payable in full. |
| 11 | +4 | E5 removes the intercompany dividend from income and restores the payor's retained earnings by the same amount, rather than reducing it further. |
| 12 | +3 | E6 removes 100% of each subsidiary's own common stock and beginning retained earnings, replacing them with the parent's ownership-percentage elimination and a complementary-percentage NCI_Equity line, for all three subsidiaries. |
| 13 | +2 | Every Investment-in-Subsidiary account eliminates to exactly zero (the stated no-goodwill assumption: investment basis equals ownership percentage times that subsidiary's own beginning equity). |
| 14 | +3 | NCI's share of net income equals the minority ownership percentage applied to S2's own standalone net income only, not to any consolidated or intercompany-adjusted figure. |

### Consolidated balance sheet facts (15-25, weight 42)

| # | Wt | Criterion |
| --- | --- | --- |
| 15 | +2 | Reports consolidated `Cash` as `570250` (exact). |
| 16 | +2 | Reports consolidated `AR_Trade` as `536400` (exact). |
| 17 | +3 | Reports consolidated `Inventory` as `382800` (exact). |
| 18 | +2 | Reports consolidated `PPE_Net` as `1746800` (exact). |
| 19 | +2 | Reports consolidated `AP_Trade` as `323200` (exact). |
| 20 | +5 | Reports all four intercompany asset/liability accounts (`IC_Receivable`, `IC_LoanReceivable`, `IC_Payable`, `IC_LoanPayable`) as exactly `0`. |
| 21 | +5 | Reports all three Investment-in-Subsidiary accounts (`Inv_in_S1`, `Inv_in_S2`, `Inv_in_S3`) as exactly `0`. |
| 22 | +2 | Reports consolidated `CommonStock` as `1000000` (exact). |
| 23 | +8 | Reports consolidated `RetainedEarnings` as `1821300` (exact). |
| 24 | +6 | Reports `NCI_Equity` as `91200` (exact). |
| 25 | +5 | Reports the cumulative translation adjustment (`CTA`) as `550` (exact). |

### Consolidated income statement facts (26-31, weight 21)

| # | Wt | Criterion |
| --- | --- | --- |
| 26 | +2 | Reports consolidated `SalesExternal` as `2619000` (exact). |
| 27 | +3 | Reports consolidated `SalesIC` as exactly `0` (the full intercompany sale eliminated, not merely netted). |
| 28 | +4 | Reports consolidated `COGS` as `1687000` (exact). |
| 29 | +2 | Reports consolidated `OpEx` as `553500` (exact). |
| 30 | +5 | Reports consolidated net income as `378500` (exact). |
| 31 | +5 | Reports the controlling-interest/NCI net income split as `366300` / `12200` (exact, both values). |

### Grand totals and balance invariant (32-35, weight 27)

| # | Wt | Criterion |
| --- | --- | --- |
| 32 | +8 | Reports total consolidated assets as `3236250` (exact). |
| 33 | +5 | Reports total consolidated liabilities as `323200` (exact). |
| 34 | +6 | Explicitly confirms the balance invariant (total assets = total liabilities + total equity) holds on the delivered consolidated balance sheet. |
| 35 | +8 | Matches the first 16 hex characters of the trace-integrity hash (algorithm in the packet) to `ccf0131030c67a99`. |

### Independent verification and memo (36-38, weight 10)

| # | Wt | Criterion |
| --- | --- | --- |
| 36 | +4 | Delivers a separately-coded auditor, sharing only immutable input constants, that independently re-derives the consolidated balance sheet, rejects both required adversarial mutations, and reports this evidence in the memo. |
| 37 | +3 | Explains in the memo, citing the actual eliminated amounts, why E1 alone does not defer unrealized profit and why E2 alone does not remove the double-counted revenue -- both are required. |
| 38 | +3 | Explains in the memo why NCI_Equity accrues this period's NCI income share on top of E6's beginning-equity NCI post, mirroring how consolidated RetainedEarnings accrues the controlling share. |

### Negative criteria — elimination-rule prohibitions (39-44)

| # | Wt | Criterion |
| --- | --- | --- |
| 39 | -4 | Omits E1 (the full intercompany sale elimination), leaving SalesIC and COGS overstated by the transfer price even though net income is unaffected. |
| 40 | -6 | Omits E2 (the unrealized-profit deferral), leaving ending inventory and retained earnings overstated by the unrealized profit. |
| 41 | -4 | Omits E4 (the trade intercompany receivable/payable elimination), leaving both accounts non-zero on the consolidated balance sheet. |
| 42 | -5 | Omits E3 (the intercompany loan elimination), leaving the loan principal and its interest income/expense non-zero. |
| 43 | -5 | Uses an ownership/NCI percentage other than the one stated for a subsidiary when computing E6 or the NCI income split. |
| 44 | -5 | Translates any S3 account at a rate other than the one stated for that account's category (closing, average, or historical). |

### Negative criteria — closing-mechanics prohibition (45)

| # | Wt | Criterion |
| --- | --- | --- |
| 45 | -8 | Closes net income (or any component of it) into retained earnings more than once, or closes it before eliminations are applied, breaking the balance invariant (total assets != total liabilities + total equity). |

### Negative trap (46)

| # | Wt | Criterion |
| --- | --- | --- |
| 46 | -8 | Embeds precomputed final account balances or the trace-integrity hash as literals substituting for executing the delivered engine. Immutable input constants don't trigger this; omission alone doesn't either. |
