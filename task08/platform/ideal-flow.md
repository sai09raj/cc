## Analyze

```text
Read the packet and reconstruct each entity's own standalone trial
balance (P, S1, S2, S3), recognizing that every entity's own
RetainedEarnings, as stated, is the beginning of period balance: this
period's income statement activity is not yet closed into it. Recover
S3's three EUR to USD translation rates (closing, average, historical)
and which account category each governs -- closing for assets,
liabilities, and common stock; average for this period's income
statement flows; historical for beginning RetainedEarnings specifically,
distinct from the other two, producing a translation plug (CTA) once net
income is subtracted out. Recover the four intercompany transaction
facts with their own stated amounts (the inventory sale's transfer
price, seller cost, and unsold fraction; the loan's principal and
interest; the separate trade receivable/payable; and the dividend), and
the ownership percentages (S1 100%, S2 80%, S3 100%) that drive both the
no goodwill investment basis and the non controlling interest split.
Treat the six elimination entries as one coherent double entry system,
not independent patches: the sale elimination and the unrealized profit
deferral together remove both the double counted revenue and the
still-unsold profit, and no single entry substitutes for the other.
```

## Execute & Generate

```text
Implement a deterministic, offline consolidation engine that combines
the four trial balances (translating S3 at its three rates), applies all
six elimination entries as genuine double entry postings (every line
converted to its debit equivalent must sum to exactly zero), closes
consolidated net income into RetainedEarnings once and the non
controlling interest's share of S2's own standalone net income into
NCI_Equity once, and emits one consolidated balance sheet and one
consolidated income statement. Build a separately coded auditor, sharing
only immutable input constants with the primary engine, that
independently re-derives the full consolidation (or checks a complete
feasibility certificate) and confirms the balance invariant (assets
equal liabilities plus equity) together with every elimination entry's
own balance and non controlling interest consistency. Run the two
required adversarial mutations -- an elimination entry missing its
offsetting line, and an intercompany item translated at the wrong one of
the three stated rates -- against a preserved original, and confirm the
auditor rejects both while accepting the original. Deliver engine
source, auditor source, the final consolidated statements, a findings
report, certification evidence (both mutation rejection results plus the
SHA256 trace integrity hash of the final serialized result), and a memo.
Equivalent languages, source organization, output schemas, and account
naming conventions all pass; exactly one physically valid consolidated
result exists for this fixed set of facts.
```

## Synthesize

```text
Using your own executed engine's actual eliminated amounts, explain why
the full sale elimination and the separate unrealized profit deferral
are both required together: the sale elimination alone still leaves the
unsold fraction's embedded profit sitting in ending inventory and
retained earnings, while the deferral alone still leaves intercompany
revenue and cost of goods sold both overstated by the full transfer
price. Explain why the dividend elimination must leave both consolidated
net income and consolidated retained earnings unaffected (an
intercompany dividend is an internal transfer, not new income, so
removing it from income and restoring the payor's retained earnings by
the same amount are two sides of one correction). Explain why non
controlling equity accrues this period's NCI income share on top of what
the beginning equity elimination already posted, rather than replacing
it, mirroring how the controlling share accrues into consolidated
retained earnings. Explain why every Investment in Subsidiary account
eliminates to exactly zero under the no goodwill basis (the parent
invested at each subsidiary's own then book value, so the elimination
entry's offsetting side matches the investment account exactly). Report
your verifier's agreement, the final balance invariant confirmation, and
the trace integrity hash, reconciling all of it against the same six
elimination entries and translation rules.
```
