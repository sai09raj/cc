#!/usr/bin/env python3
"""LEDGER-8 independent auditor.

Deliberately structured differently from ledger8_engine.py: a flat
general-ledger posting list of (entity, account, debit, credit) tuples
rather than per-entity dict-of-Fractions trial balances, with the
consolidated trial balance derived by summing postings rather than by
named account addition. Shares only the immutable input constants
(S02-S04, S08) with the primary -- re-derives S05-S09 independently.
"""
import hashlib
from fractions import Fraction as F

import ledger8_engine as REF  # immutable input constants only

DEBIT_NORMAL = REF.DEBIT_NORMAL


def post(ledger, entity, account, debit=F(0), credit=F(0)):
    ledger.append((entity, account, debit, credit))


def build_ledger():
    """Post every entity's own trial balance, plus S3's translation
    adjustment, as flat (entity, account, debit, credit) postings."""
    ledger = []
    raw = REF.raw_trial_balances()
    for e in ["P", "S1", "S2"]:
        tb = raw[e]
        for acct, amt in tb.items():
            if acct in REF.IS_ACCOUNTS:
                # revenue/interest-income/dividend-income are credit-normal;
                # COGS/OpEx/interest-expense are debit-normal
                if acct in DEBIT_NORMAL:
                    post(ledger, e, acct, debit=amt)
                else:
                    post(ledger, e, acct, credit=amt)
            elif acct in DEBIT_NORMAL:
                post(ledger, e, acct, debit=amt)
            else:
                post(ledger, e, acct, credit=amt)

    # S3: translate then post (closing/average/historical rates, same
    # immutable constants as the primary -- re-applied independently here)
    s3raw = raw["S3"]
    for acct in REF.BS_ASSET_ACCOUNTS + REF.BS_LIAB_ACCOUNTS + ["CommonStock"]:
        amt = s3raw.get(acct, F(0)) * REF.S3_CLOSING_RATE
        if amt == 0:
            continue
        if acct in DEBIT_NORMAL:
            post(ledger, "S3", acct, debit=amt)
        else:
            post(ledger, "S3", acct, credit=amt)
    for acct in REF.IS_ACCOUNTS:
        amt = s3raw.get(acct, F(0)) * REF.S3_AVERAGE_RATE
        if amt == 0:
            continue
        if acct in DEBIT_NORMAL:
            post(ledger, "S3", acct, debit=amt)
        else:
            post(ledger, "S3", acct, credit=amt)
    s3_re_beg = s3raw["RetainedEarnings"] * REF.S3_HISTORICAL_RATE
    post(ledger, "S3", "RetainedEarnings", credit=s3_re_beg)

    # S3's CTA plug: computed the same way the primary states it (S03),
    # independently re-derived from this ledger's own postings rather
    # than copied.
    s3_assets = sum(d for e, a, d, c in ledger if e == "S3" and a in REF.BS_ASSET_ACCOUNTS)
    s3_liab = sum(c for e, a, d, c in ledger if e == "S3" and a in REF.BS_LIAB_ACCOUNTS)
    s3_common = sum(c for e, a, d, c in ledger if e == "S3" and a == "CommonStock")
    s3_ni = (sum(c for e, a, d, c in ledger if e == "S3" and a in REF.IS_ACCOUNTS and a not in DEBIT_NORMAL)
             - sum(d for e, a, d, c in ledger if e == "S3" and a in REF.IS_ACCOUNTS and a in DEBIT_NORMAL))
    s3_cta = s3_assets - s3_liab - s3_common - s3_re_beg - s3_ni
    if s3_cta >= 0:
        post(ledger, "S3", "CTA", credit=s3_cta)
    else:
        post(ledger, "S3", "CTA", debit=-s3_cta)

    return ledger


def balance_of(ledger, account, entities=None):
    debits = sum(d for e, a, d, c in ledger if a == account and (entities is None or e in entities))
    credits = sum(c for e, a, d, c in ledger if a == account and (entities is None or e in entities))
    return debits - credits if account in DEBIT_NORMAL or account == "CTA" and False else credits - debits


def net_balance(ledger, account):
    """Signed balance in the account's own normal-balance convention
    (positive = a normal balance for that account type)."""
    debits = sum(d for e, a, d, c in ledger if a == account)
    credits = sum(c for e, a, d, c in ledger if a == account)
    if account in DEBIT_NORMAL:
        return debits - credits
    return credits - debits


def apply_eliminations(ledger, mutant_skip_e2=False, mutant_wrong_nci_pct=False,
                        mutant_skip_loan_elim=False, mutant_unbalanced_e2=False,
                        mutant_wrong_translation_rate=False, mutant_skip_e1=False,
                        mutant_skip_e4=False):
    """Re-derive the six eliminations from the immutable S04/S08 facts
    (not copied from the primary's entries dict) and post them onto the
    flat ledger, with mutant hooks matching score_counterfactual.py."""
    entries = []

    # E1
    if not mutant_skip_e1:
        entries.append(("E1", [("SalesIC", "debit", REF.IC_SALE_PRICE),
                                ("COGS", "credit", REF.IC_SALE_PRICE)]))

    # E2
    if not mutant_skip_e2:
        up = REF.IC_SALE_PCT_UNSOLD_AT_S1 * (REF.IC_SALE_PRICE - REF.IC_SALE_COST)
        if mutant_unbalanced_e2:
            entries.append(("E2", [("COGS", "debit", up)]))  # missing offsetting credit
        else:
            entries.append(("E2", [("COGS", "debit", up), ("Inventory", "credit", up)]))

    # E3
    if not mutant_skip_loan_elim:
        entries.append(("E3", [("IC_LoanPayable", "debit", REF.IC_LOAN_PRINCIPAL),
                                ("IC_LoanReceivable", "credit", REF.IC_LOAN_PRINCIPAL),
                                ("IC_InterestExpense", "credit", REF.IC_LOAN_INTEREST),
                                ("IC_InterestIncome", "debit", REF.IC_LOAN_INTEREST)]))

    # E4
    if not mutant_skip_e4:
        entries.append(("E4", [("IC_Payable", "debit", REF.IC_RECEIVABLE_PAYABLE),
                                ("IC_Receivable", "credit", REF.IC_RECEIVABLE_PAYABLE)]))

    # E5: remove P's dividend income (debit, since it's credit-normal) and
    # restore S1's retained earnings by the same amount (credit, since RE
    # is also credit-normal and this increases it)
    entries.append(("E5", [("DividendIncomeIC", "debit", REF.IC_DIVIDEND),
                            ("RetainedEarnings", "credit", REF.IC_DIVIDEND)]))

    raw = REF.raw_trial_balances()
    s3common_rate = REF.S3_CLOSING_RATE
    if mutant_wrong_translation_rate:
        s3common_rate = REF.S3_AVERAGE_RATE  # wrong rate, on purpose
    s3_common = raw["S3"]["CommonStock"] * s3common_rate
    s3_re = raw["S3"]["RetainedEarnings"] * REF.S3_HISTORICAL_RATE
    sub_common = {"S1": raw["S1"]["CommonStock"], "S2": raw["S2"]["CommonStock"], "S3": s3_common}
    sub_re = {"S1": raw["S1"]["RetainedEarnings"], "S2": raw["S2"]["RetainedEarnings"], "S3": s3_re}
    for sub in ["S1", "S2", "S3"]:
        f = REF.OWNERSHIP[sub] if not (mutant_wrong_nci_pct and sub == "S2") else F(70, 100)
        equity = sub_common[sub] + sub_re[sub]
        nci_share = (F(1) - f) * equity
        entries.append((f"E6_{sub}", [
            ("CommonStock", "debit", sub_common[sub]),
            ("RetainedEarnings", "debit", sub_re[sub]),
            (f"Inv_in_{sub}", "credit", f * equity),
            ("NCI_Equity", "credit", nci_share),
        ]))

    for name, lines in entries:
        for acct, side, amt in lines:
            if side == "debit":
                post(ledger, "ELIM", acct, debit=amt)
            else:
                post(ledger, "ELIM", acct, credit=amt)
    return entries


def audit(mutant_double_count_ni=False, **mutant_kwargs):
    ledger = build_ledger()
    entries = apply_eliminations(ledger, **mutant_kwargs)

    final = {}
    for acct in REF.ALL_BS + ["NCI_Equity", "CTA"]:
        final[acct] = net_balance(ledger, acct)
    is_final = {acct: net_balance(ledger, acct) for acct in REF.IS_ACCOUNTS}

    total_assets = sum(final[a] for a in REF.BS_ASSET_ACCOUNTS)
    total_liab = sum(final[a] for a in REF.BS_LIAB_ACCOUNTS)

    net_income = (net_balance(ledger, "SalesExternal") + net_balance(ledger, "SalesIC")
                  + net_balance(ledger, "IC_InterestIncome") + net_balance(ledger, "DividendIncomeIC")
                  - net_balance(ledger, "COGS") - net_balance(ledger, "OpEx")
                  - net_balance(ledger, "IC_InterestExpense"))

    s2_raw = REF.raw_trial_balances()["S2"]
    s2_ni = (s2_raw["SalesExternal"] + s2_raw["SalesIC"] + s2_raw["IC_InterestIncome"]
             - s2_raw["COGS"] - s2_raw["OpEx"] - s2_raw["IC_InterestExpense"])
    nci_pct = F(1) - (REF.OWNERSHIP["S2"] if "mutant_wrong_nci_pct" not in mutant_kwargs
                       or not mutant_kwargs.get("mutant_wrong_nci_pct") else F(70, 100))
    nci_ni = nci_pct * s2_ni
    controlling_ni = net_income - nci_ni

    final["RetainedEarnings"] = final["RetainedEarnings"] + controlling_ni
    if mutant_double_count_ni:
        final["RetainedEarnings"] = final["RetainedEarnings"] + controlling_ni
    final["NCI_Equity"] = final["NCI_Equity"] + nci_ni

    equity_total = final["CommonStock"] + final["RetainedEarnings"] + final["CTA"] + final["NCI_Equity"]
    balances = total_assets == total_liab + equity_total

    # entry-balance check: every elimination entry, re-derived here,
    # must itself balance in debit-equivalent terms
    entries_ok = True
    for name, lines in entries:
        # side already explicitly states debit/credit, so the DR-equivalent
        # contribution is simply +amt for a debit, -amt for a credit --
        # independent of the account's own normal-balance direction.
        total = sum(amt if side == "debit" else -amt for acct, side, amt in lines)
        if total != 0:
            entries_ok = False

    return {
        "final": final, "is_final": is_final, "total_assets": total_assets,
        "total_liab": total_liab, "equity_total": equity_total, "balances": balances,
        "entries_ok": entries_ok, "net_income": net_income,
        "controlling_net_income": controlling_ni, "nci_net_income": nci_ni,
    }


def canonical_serialization(final, net_income, nci_net_income, is_final=None):
    lines = ["LEDGER8|CONSOLIDATED"]
    for acct in sorted(REF.ALL_BS):
        lines.append(f"{acct}={final[acct]}")
    lines.append(f"NCI_Equity={final['NCI_Equity']}")
    if is_final is not None:
        for acct in sorted(REF.IS_ACCOUNTS):
            lines.append(f"IS_{acct}={is_final[acct]}")
    lines.append(f"NetIncome={net_income}")
    lines.append(f"NCI_NetIncome={nci_net_income}")
    return "\n".join(lines)


def certificate_hash(final, net_income, nci_net_income, is_final=None):
    ser = canonical_serialization(final, net_income, nci_net_income, is_final)
    return hashlib.sha256(ser.encode()).hexdigest()[:16]


def run_adversarial_mutations():
    """S10's two required adversarial mutations, via two different
    rejection mechanisms: mutation A breaks internal double-entry
    self-consistency (caught by the entries_ok / balances checks);
    mutation B stays internally self-consistent (a wrong rate still
    produces a balanced entry) but is caught by certificate-hash
    mismatch against the auditor's own correctly-computed result --
    exactly how a real independent auditor would catch a plausible
    but economically wrong number: not by it "looking broken", but by
    disagreeing with its own from-scratch recomputation."""
    r_true = audit()
    h_true = certificate_hash(r_true["final"], r_true["net_income"], r_true["nci_net_income"],
                               r_true["is_final"])
    assert r_true["balances"] and r_true["entries_ok"], "auditor must accept the true original"

    r_a = audit(mutant_unbalanced_e2=True)
    a_rejected = not (r_a["balances"] and r_a["entries_ok"])
    print(f"[mutation A: unbalanced E2]      rejected={a_rejected}")
    assert a_rejected, "must reject an unbalanced elimination entry"

    r_b = audit(mutant_wrong_translation_rate=True)
    h_b = certificate_hash(r_b["final"], r_b["net_income"], r_b["nci_net_income"], r_b["is_final"])
    b_rejected = h_b != h_true
    print(f"[mutation B: wrong FX rate]      rejected={b_rejected}")
    assert b_rejected, "must reject a wrong-rate translation via hash mismatch"

    print(f"[true original]                  accepted=True, hash={h_true}")
    return True


if __name__ == "__main__":
    r = audit()
    print("balances:", r["balances"], "entries_ok:", r["entries_ok"])
    print("total assets:", r["total_assets"], "total liab:", r["total_liab"],
          "equity:", r["equity_total"])
    print("net income:", r["net_income"], "controlling:", r["controlling_net_income"],
          "nci:", r["nci_net_income"])
    h = certificate_hash(r["final"], r["net_income"], r["nci_net_income"], r["is_final"])
    print("hash:", h)

    ref = REF.consolidate()
    ref_hash = REF.certificate_hash(ref)
    print("primary hash:", ref_hash)
    print("hashes match:", h == ref_hash)
    for acct in sorted(REF.ALL_BS):
        if r["final"][acct] != ref["consolidated"][acct]:
            print("MISMATCH", acct, r["final"][acct], "vs", ref["consolidated"][acct])

    print()
    run_adversarial_mutations()
