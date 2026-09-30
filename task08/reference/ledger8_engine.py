#!/usr/bin/env python3
"""LEDGER-8 canonical reference consolidation engine.

Primary implementation for design/semantic-contract.md S01-S12.
Consolidates a parent (P) and three subsidiaries (S1 100% domestic,
S2 80% domestic, S3 100% foreign) into a single consolidated balance
sheet and income statement, applying elimination entries, NCI, and
foreign-currency translation. Offline, stdlib-only, deterministic.

Every entity's own RetainedEarnings, as given, is a BEGINNING-of-period
balance (this period's own activity is NOT yet closed into it -- that is
what the separate income-statement accounts and the final net_income
figure are for). This is the one convention that makes every account
additive and auditable end to end: combining entities, translating
currency, and applying eliminations are all plain vector addition on a
consistent (asset/liability/equity) x (beginning stock, or flow) basis,
with net income (post-elimination, split between controlling and NCI
shares) closed in exactly once, at the very end.
"""
from fractions import Fraction as F
import hashlib

# ---------------------------------------------------------------------
# S02: entity structure (immutable input constants)
# ---------------------------------------------------------------------
ENTITIES = ["P", "S1", "S2", "S3"]
OWNERSHIP = {"S1": F(100, 100), "S2": F(80, 100), "S3": F(100, 100)}
S3_CLOSING_RATE = F(108, 100)     # EUR -> USD: assets, liabilities, common stock
S3_AVERAGE_RATE = F(110, 100)     # EUR -> USD: this period's income-statement flows
S3_HISTORICAL_RATE = F(105, 100)  # EUR -> USD: beginning retained earnings only

BS_ASSET_ACCOUNTS = ["Cash", "AR_Trade", "IC_Receivable", "IC_LoanReceivable",
                     "Inventory", "Inv_in_S1", "Inv_in_S2", "Inv_in_S3", "PPE_Net"]
BS_LIAB_ACCOUNTS = ["AP_Trade", "IC_Payable", "IC_LoanPayable"]
BS_EQUITY_ACCOUNTS = ["CommonStock", "RetainedEarnings"]
IS_ACCOUNTS = ["SalesExternal", "SalesIC", "COGS", "OpEx",
               "IC_InterestIncome", "IC_InterestExpense", "DividendIncomeIC"]

ALL_BS = BS_ASSET_ACCOUNTS + BS_LIAB_ACCOUNTS + BS_EQUITY_ACCOUNTS
DEBIT_NORMAL = set(BS_ASSET_ACCOUNTS) | {"COGS", "OpEx", "IC_InterestExpense"}
# Everything else (liabilities, equity, revenue, IC_InterestIncome,
# DividendIncomeIC, NCI_Equity, CTA) is credit-normal.


# ---------------------------------------------------------------------
# S03: each entity's own standalone trial balance (local currency; S3's
# figures are in EUR, all others in USD; RetainedEarnings is always the
# BEGINNING-of-period balance). Every account not listed is implicitly
# zero for that entity. Inv_in_S1/S2/S3 (P's investment accounts) are
# set to ownership% x that subsidiary's own BEGINNING equity, in USD (no
# goodwill/differential -- a stated simplifying assumption: the parent
# invested at each subsidiary's then-book-value).
# ---------------------------------------------------------------------
def raw_trial_balances():
    return {
        "P": {
            "Cash": F(450250), "AR_Trade": F(220000), "IC_Receivable": F(45000),
            "IC_LoanReceivable": F(150000),
            "Inventory": F(150000), "Inv_in_S1": F(285000), "Inv_in_S2": F(316000),
            "Inv_in_S3": F(327750), "PPE_Net": F(900000),
            "AP_Trade": F(160000), "IC_Payable": F(0), "IC_LoanPayable": F(0),
            "CommonStock": F(1000000), "RetainedEarnings": F(1450000),
            "SalesExternal": F(1200000), "SalesIC": F(100000), "COGS": F(820000),
            "OpEx": F(260000), "IC_InterestIncome": F(9000),
            "IC_InterestExpense": F(0), "DividendIncomeIC": F(5000),
        },
        "S1": {
            "Cash": F(20000), "AR_Trade": F(90000), "IC_Receivable": F(0),
            "Inventory": F(70000), "Inv_in_S1": F(0), "Inv_in_S2": F(0),
            "Inv_in_S3": F(0), "PPE_Net": F(240000),
            "AP_Trade": F(50000), "IC_Payable": F(45000), "IC_LoanPayable": F(0),
            "CommonStock": F(200000), "RetainedEarnings": F(85000),
            "SalesExternal": F(430000), "SalesIC": F(0), "COGS": F(310000),
            "OpEx": F(80000), "IC_InterestIncome": F(0),
            "IC_InterestExpense": F(0), "DividendIncomeIC": F(0),
        },
        "S2": {
            "Cash": F(46000), "AR_Trade": F(140000), "IC_Receivable": F(0),
            "Inventory": F(110000), "Inv_in_S1": F(0), "Inv_in_S2": F(0),
            "Inv_in_S3": F(0), "PPE_Net": F(380000),
            "AP_Trade": F(70000), "IC_Payable": F(0), "IC_LoanPayable": F(150000),
            "CommonStock": F(300000), "RetainedEarnings": F(95000),
            "SalesExternal": F(560000), "SalesIC": F(0), "COGS": F(370000),
            "OpEx": F(120000), "IC_InterestIncome": F(0),
            "IC_InterestExpense": F(9000), "DividendIncomeIC": F(0),
        },
        # S3's figures are in EUR (local currency) -- translated in s3_translated().
        "S3": {
            "Cash": F(50000), "AR_Trade": F(80000), "IC_Receivable": F(0),
            "Inventory": F(60000), "Inv_in_S1": F(0), "Inv_in_S2": F(0),
            "Inv_in_S3": F(0), "PPE_Net": F(210000),
            "AP_Trade": F(40000), "IC_Payable": F(0), "IC_LoanPayable": F(0),
            "CommonStock": F(250000), "RetainedEarnings": F(55000),
            "SalesExternal": F(390000), "SalesIC": F(0), "COGS": F(250000),
            "OpEx": F(85000), "IC_InterestIncome": F(0),
            "IC_InterestExpense": F(0), "DividendIncomeIC": F(0),
        },
    }


# ---------------------------------------------------------------------
# S04: intercompany transaction facts (immutable input constants),
# used to derive the elimination entries in S06.
# ---------------------------------------------------------------------
IC_SALE_PRICE = F(100000)          # P sold inventory to S1 at this transfer price
IC_SALE_COST = F(70000)            # P's own cost basis for those goods
IC_SALE_PCT_UNSOLD_AT_S1 = F(40, 100)  # fraction of the transferred goods still
                                         # in S1's ending inventory at year end

IC_LOAN_PRINCIPAL = F(150000)      # S2's loan payable to P (matches S2.IC_LoanPayable)
IC_LOAN_INTEREST = F(9000)         # interest S2 owes P for the year (matches both
                                     # P.IC_InterestIncome and S2.IC_InterestExpense)
IC_RECEIVABLE_PAYABLE = F(45000)   # P's trade IC_Receivable from S1 (matches
                                     # S1.IC_Payable); unrelated to the loan above
IC_DIVIDEND = F(5000)              # dividend S1 paid to P during the year


def s3_translated():
    """S03: translate S3's EUR trial balance to USD. Assets, liabilities,
    and common stock at the closing rate; this period's income-statement
    flows at the average rate; beginning RetainedEarnings at the
    historical rate in effect when it was earned. The cumulative
    translation adjustment (CTA) is the resulting imbalance between total
    assets and total liabilities+common-stock+beginning-RE, posted as its
    own equity line -- CTA exists precisely because the same underlying
    EUR equity is translated at three different rates depending on which
    stated rule applies to it."""
    raw = raw_trial_balances()["S3"]
    out = {}
    for acct in BS_ASSET_ACCOUNTS + BS_LIAB_ACCOUNTS + ["CommonStock"]:
        out[acct] = raw.get(acct, F(0)) * S3_CLOSING_RATE
    for acct in IS_ACCOUNTS:
        out[acct] = raw.get(acct, F(0)) * S3_AVERAGE_RATE
    out["RetainedEarnings"] = raw["RetainedEarnings"] * S3_HISTORICAL_RATE
    net_income = (out["SalesExternal"] + out["SalesIC"] + out["IC_InterestIncome"]
                  + out["DividendIncomeIC"] - out["COGS"] - out["OpEx"]
                  - out["IC_InterestExpense"])
    total_assets = sum(out[a] for a in BS_ASSET_ACCOUNTS)
    total_liab = sum(out[a] for a in BS_LIAB_ACCOUNTS)
    # CTA is a pure translation plug, independent of this period's net
    # income -- matching every other entity, S3's own balance requires
    # assets = liab + commonstock + RE_beginning + net_income, with CTA
    # as the one extra term unique to a translated foreign entity.
    cta = total_assets - total_liab - out["CommonStock"] - out["RetainedEarnings"] - net_income
    out["CTA"] = cta
    return out


def combined_trial_balance():
    """S05: sum the four entities' own trial balances (S3 already
    translated to USD) into one pre-elimination combined column. Every
    RetainedEarnings figure summed here is a BEGINNING-of-period balance."""
    raw = raw_trial_balances()
    s3 = s3_translated()
    combined = {a: F(0) for a in ALL_BS + IS_ACCOUNTS}
    combined["CTA"] = F(0)
    combined["NCI_Equity"] = F(0)
    for e in ["P", "S1", "S2"]:
        for a, v in raw[e].items():
            combined[a] += v
    for a in ALL_BS + IS_ACCOUNTS:
        combined[a] += s3[a]
    combined["CTA"] += s3["CTA"]
    return combined


def elimination_entries():
    """S06: the six required elimination journal entries, each stated as
    a list of (account, signed_amount) pairs that must sum to zero in
    double-entry (debit-equivalent) terms. Returns them named, so a
    verifier can re-derive and cross-check each one independently."""
    unrealized_profit = IC_SALE_PCT_UNSOLD_AT_S1 * (IC_SALE_PRICE - IC_SALE_COST)
    entries = {}
    # E1: eliminate the full intercompany sale (S06a)
    entries["E1_intercompany_sale"] = [
        ("SalesIC", -IC_SALE_PRICE), ("COGS", -IC_SALE_PRICE),
    ]
    # E2: defer unrealized profit still sitting in S1's ending inventory (S06b)
    entries["E2_unrealized_profit"] = [
        ("COGS", unrealized_profit), ("Inventory", -unrealized_profit),
    ]
    # E3: eliminate the intercompany loan balance and its interest (S06c)
    entries["E3_intercompany_loan"] = [
        ("IC_LoanPayable", -IC_LOAN_PRINCIPAL), ("IC_LoanReceivable", -IC_LOAN_PRINCIPAL),
        ("IC_InterestExpense", -IC_LOAN_INTEREST), ("IC_InterestIncome", -IC_LOAN_INTEREST),
    ]
    # E4: eliminate the remaining (non-loan) trade intercompany receivable/payable (S06d)
    entries["E4_intercompany_trade"] = [
        ("IC_Payable", -IC_RECEIVABLE_PAYABLE), ("IC_Receivable", -IC_RECEIVABLE_PAYABLE),
    ]
    # E5: eliminate the intercompany dividend -- remove P's dividend income
    # and restore S1's beginning retained earnings by the same amount,
    # since an intercompany dividend must have zero effect on both
    # consolidated net income and consolidated retained earnings (S06e)
    entries["E5_intercompany_dividend"] = [
        ("DividendIncomeIC", -IC_DIVIDEND), ("RetainedEarnings", IC_DIVIDEND),
    ]
    # E6: remove each subsidiary's own CommonStock and beginning
    # RetainedEarnings from the combined totals in full (100%), replacing
    # them with the parent's Investment-in-Sub elimination (parent's
    # ownership %) and a new NCI_Equity line (the complementary %) --
    # balances by construction for any ownership fraction (S06f)
    raw = raw_trial_balances()
    s3 = s3_translated()
    sub_common = {"S1": raw["S1"]["CommonStock"], "S2": raw["S2"]["CommonStock"],
                  "S3": s3["CommonStock"]}
    sub_re = {"S1": raw["S1"]["RetainedEarnings"], "S2": raw["S2"]["RetainedEarnings"],
              "S3": s3["RetainedEarnings"]}
    sub_equity = {s: sub_common[s] + sub_re[s] for s in ("S1", "S2", "S3")}
    entries["E6_investment_elimination"] = []
    for sub in ["S1", "S2", "S3"]:
        f = OWNERSHIP[sub]
        nci_share = (F(1) - f) * sub_equity[sub]
        entries["E6_investment_elimination"].append(("CommonStock", -sub_common[sub]))
        entries["E6_investment_elimination"].append(("RetainedEarnings", -sub_re[sub]))
        entries["E6_investment_elimination"].append((f"Inv_in_{sub}", -f * sub_equity[sub]))
        entries["E6_investment_elimination"].append(("NCI_Equity", nci_share))
    return entries, unrealized_profit, sub_equity


def validate_entry_balances(entries):
    """Each elimination entry must be a genuine balanced double-entry
    journal entry: converting every signed delta to its debit-equivalent
    (a positive delta on a debit-normal account is a debit; a positive
    delta on a credit-normal account is a debit-equivalent of the
    opposite sign) must sum to exactly zero."""
    for name, lines in entries.items():
        dr_equiv_total = F(0)
        for acct, amt in lines:
            is_debit_normal = acct in DEBIT_NORMAL
            dr_equiv_total += amt if is_debit_normal else -amt
        assert dr_equiv_total == 0, f"{name} does not balance: {dr_equiv_total}"


def consolidate():
    """S07: apply all elimination entries to the combined trial balance,
    compute NCI, and produce the final consolidated balance sheet and
    income statement."""
    combined = combined_trial_balance()
    entries, unrealized_profit, sub_equity = elimination_entries()
    validate_entry_balances(entries)

    consolidated = dict(combined)
    for name, lines in entries.items():
        for acct, amt in lines:
            consolidated[acct] += amt

    net_income = (consolidated["SalesExternal"] + consolidated["SalesIC"]
                  + consolidated["IC_InterestIncome"] + consolidated["DividendIncomeIC"]
                  - consolidated["COGS"] - consolidated["OpEx"]
                  - consolidated["IC_InterestExpense"])

    # S08: NCI's share of net income is a below-the-line allocation of
    # consolidated net income (standard practice -- not itself a
    # journaled GL account): S2 is the only partially-owned sub, so NCI's
    # income share is the minority % of S2's own standalone net income
    # (S2's intercompany loan interest nets against P's side via E3 and
    # does not itself change S2's own reported net income). NCI_Equity
    # accrues this period's NCI income share on top of what E6 already
    # posted for beginning equity, exactly mirroring how consolidated
    # RetainedEarnings accrues the controlling share of net income.
    s2_raw = raw_trial_balances()["S2"]
    s2_net_income = (s2_raw["SalesExternal"] + s2_raw["SalesIC"]
                      + s2_raw["IC_InterestIncome"] - s2_raw["COGS"] - s2_raw["OpEx"]
                      - s2_raw["IC_InterestExpense"])
    nci_net_income = (F(1) - OWNERSHIP["S2"]) * s2_net_income
    nci_equity_beginning = consolidated["NCI_Equity"]
    nci_equity = nci_equity_beginning + nci_net_income

    controlling_net_income = net_income - nci_net_income
    consolidated["RetainedEarnings"] = consolidated["RetainedEarnings"] + controlling_net_income
    consolidated["NCI_Equity"] = nci_equity

    consolidated_equity_total = (consolidated["CommonStock"]
                                  + consolidated["RetainedEarnings"]
                                  + consolidated["CTA"] + nci_equity)
    total_assets = sum(consolidated[a] for a in BS_ASSET_ACCOUNTS)
    total_liab = sum(consolidated[a] for a in BS_LIAB_ACCOUNTS)

    return {
        "combined": combined,
        "entries": entries,
        "unrealized_profit": unrealized_profit,
        "consolidated": consolidated,
        "net_income": net_income,
        "controlling_net_income": controlling_net_income,
        "nci_equity": nci_equity,
        "nci_net_income": nci_net_income,
        "total_assets": total_assets,
        "total_liab": total_liab,
        "consolidated_equity_total": consolidated_equity_total,
        "balances": total_assets == total_liab + consolidated_equity_total,
    }


def canonical_serialization(result):
    """S11: deterministic serialization of the final consolidated
    balance sheet + income statement for hashing. One line per account,
    sorted by name, amount as an exact decimal string (Fraction with a
    denominator of 1 after all elimination arithmetic, since every input
    and every rate is itself an exact decimal)."""
    c = result["consolidated"]
    lines = ["LEDGER8|CONSOLIDATED"]
    for acct in sorted(ALL_BS):
        lines.append(f"{acct}={c[acct]}")
    lines.append(f"NCI_Equity={c['NCI_Equity']}")
    for acct in sorted(IS_ACCOUNTS):
        lines.append(f"IS_{acct}={c[acct]}")
    lines.append(f"NetIncome={result['net_income']}")
    lines.append(f"NCI_NetIncome={result['nci_net_income']}")
    return "\n".join(lines)


def certificate_hash(result):
    ser = canonical_serialization(result)
    return hashlib.sha256(ser.encode()).hexdigest()[:16]


if __name__ == "__main__":
    r = consolidate()
    print("balances (Assets == Liab + Equity):", r["balances"])
    print("total assets:", r["total_assets"])
    print("total liab:", r["total_liab"])
    print("consolidated equity total:", r["consolidated_equity_total"])
    print("net income:", r["net_income"])
    print("controlling net income:", r["controlling_net_income"])
    print("nci equity:", r["nci_equity"])
    print("nci net income:", r["nci_net_income"])
    print("unrealized profit deferred:", r["unrealized_profit"])
    print("hash:", certificate_hash(r))
