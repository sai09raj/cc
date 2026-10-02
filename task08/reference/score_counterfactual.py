#!/usr/bin/env python3
"""Programmatic score-topology counterfactual scorer for LEDGER-8's
rubric. Criterion numbering matches platform/rubric.md exactly (49
criteria, <=10 weight, <=301 chars each). Uses ledger8_auditor.py's
mutant hooks directly (not a separate reimplementation), since LEDGER-8
has no sweep to run mutants across -- one static consolidation, scored
fact by fact against the frozen reference values.
"""
import ledger8_auditor as A
from fractions import Fraction as F

PACKAGE_WEIGHT = 3  # criterion 1

LOCAL_WEIGHT = {
    2: 2, 3: 3, 4: 2, 5: 4, 6: 3, 7: 5, 8: 3, 9: 2, 10: 4, 11: 3, 12: 3,
}

BS_WEIGHT = {
    13: 2, 14: 2, 15: 3, 16: 2, 17: 2, 18: 2, 19: 3, 20: 1, 21: 2, 22: 2,
    23: 2, 24: 8, 25: 6, 26: 5,
}
REF_BS = {
    13: ("Cash", 570250), 14: ("AR_Trade", 536400), 15: ("Inventory", 382800),
    16: ("PPE_Net", 1746800), 17: ("AP_Trade", 323200), 23: ("CommonStock", 1000000),
    24: ("RetainedEarnings", 1821300), 25: ("NCI_Equity", 91200), 26: ("CTA", 550),
}
IC_TRADE_ACCOUNTS = ["IC_Receivable", "IC_Payable"]
IC_LOAN_ACCOUNTS = ["IC_LoanReceivable", "IC_LoanPayable"]
INV_ACCOUNT = {20: "Inv_in_S1", 21: "Inv_in_S2", 22: "Inv_in_S3"}

IS_WEIGHT = {27: 2, 28: 3, 29: 4, 30: 2, 31: 5, 32: 5}
REF_IS = {27: ("SalesExternal", 2619000), 28: ("SalesIC", 0),
          29: ("COGS", 1687000), 30: ("OpEx", 553500)}
REF_NET_INCOME = 378500
REF_CONTROLLING_NI = 366300
REF_NCI_NI = 12200

GRAND_ASSETS_WEIGHT, GRAND_LIAB_WEIGHT = 8, 5
REF_TOTAL_ASSETS, REF_TOTAL_LIAB = 3236250, 323200
BALANCE_INVARIANT_WEIGHT = 6
HASH_WEIGHT = 8
REF_HASH16 = "cd5791e7dc01e208"

REJECT_A_WEIGHT = 2   # criterion 37: rejects unbalanced-entry mutation
REJECT_B_METHOD_WEIGHT = 2  # criterion 38: methodology + rejects wrong-rate mutation + memo
MEMO_E1E2_WEIGHT = 3   # criterion 39
MEMO_NCI_CTA_WEIGHT = 3  # criterion 40

NEG_WEIGHT = {41: 4, 42: 6, 43: 4, 44: 5, 45: 5, 46: 5, 47: 4, 48: 8}

TOTAL = (PACKAGE_WEIGHT + sum(LOCAL_WEIGHT.values()) + sum(BS_WEIGHT.values())
         + sum(IS_WEIGHT.values()) + GRAND_ASSETS_WEIGHT + GRAND_LIAB_WEIGHT
         + BALANCE_INVARIANT_WEIGHT + HASH_WEIGHT + REJECT_A_WEIGHT
         + REJECT_B_METHOD_WEIGHT + MEMO_E1E2_WEIGHT + MEMO_NCI_CTA_WEIGHT)


def score(name, mutant_kwargs=None, local_fail=(), reject_a_fail=False,
          reject_b_fail=False, hash_ok=True, negative_fail=(),
          memo_e1e2_fail=False, memo_nci_cta_fail=False):
    mutant_kwargs = mutant_kwargs or {}
    r = A.audit(**mutant_kwargs)
    final, is_final = r["final"], r["is_final"]
    earned = 0

    earned += PACKAGE_WEIGHT
    for cid, wgt in LOCAL_WEIGHT.items():
        if cid not in local_fail:
            earned += wgt

    for cid, wgt in BS_WEIGHT.items():
        if cid == 18:
            ok = all(final.get(a) == 0 for a in IC_TRADE_ACCOUNTS)
        elif cid == 19:
            ok = all(final.get(a) == 0 for a in IC_LOAN_ACCOUNTS)
        elif cid in INV_ACCOUNT:
            ok = final.get(INV_ACCOUNT[cid]) == 0
        else:
            acct, ref_val = REF_BS[cid]
            ok = final.get(acct) == F(ref_val)
        if ok:
            earned += wgt

    for cid, wgt in IS_WEIGHT.items():
        if cid == 31:
            ok = r["net_income"] == F(REF_NET_INCOME)
        elif cid == 32:
            ok = (r["controlling_net_income"] == F(REF_CONTROLLING_NI)
                  and r["nci_net_income"] == F(REF_NCI_NI))
        else:
            acct, ref_val = REF_IS[cid]
            ok = is_final.get(acct) == F(ref_val)
        if ok:
            earned += wgt

    if r["total_assets"] == F(REF_TOTAL_ASSETS):
        earned += GRAND_ASSETS_WEIGHT
    if r["total_liab"] == F(REF_TOTAL_LIAB):
        earned += GRAND_LIAB_WEIGHT
    if r["balances"]:
        earned += BALANCE_INVARIANT_WEIGHT

    h = A.certificate_hash(final, r["net_income"], r["nci_net_income"], is_final)
    if hash_ok and h == REF_HASH16:
        earned += HASH_WEIGHT

    if not reject_a_fail:
        earned += REJECT_A_WEIGHT
    if not reject_b_fail:
        earned += REJECT_B_METHOD_WEIGHT
    if not memo_e1e2_fail:
        earned += MEMO_E1E2_WEIGHT
    if not memo_nci_cta_fail:
        earned += MEMO_NCI_CTA_WEIGHT

    for cid in negative_fail:
        earned -= NEG_WEIGHT[cid]

    pct = 100 * earned / TOTAL
    print(f"{name}: {earned}/{TOTAL} = {pct:.1f}%  balances={r['balances']}  "
          f"hash_match={h == REF_HASH16}  net_income={r['net_income']}")
    return earned, pct


if __name__ == "__main__":
    print(f"Rubric total positive weight: {TOTAL}\n")

    score("canonical (sanity, must be 100%)")

    score("omit E1 (intercompany sale not eliminated)",
          mutant_kwargs=dict(mutant_skip_e1=True), local_fail={6},
          hash_ok=False, negative_fail={41}, memo_e1e2_fail=True)

    score("omit E2 (unrealized profit not deferred)",
          mutant_kwargs=dict(mutant_skip_e2=True), local_fail={7},
          hash_ok=False, negative_fail={42}, memo_e1e2_fail=True)

    score("omit E4 (trade IC balance not eliminated)",
          mutant_kwargs=dict(mutant_skip_e4=True), local_fail={9},
          hash_ok=False, negative_fail={43})

    score("omit E3 (intercompany loan not eliminated)",
          mutant_kwargs=dict(mutant_skip_loan_elim=True), local_fail={8},
          hash_ok=False, negative_fail={44})

    score("wrong NCI ownership percentage (70% instead of 80%)",
          mutant_kwargs=dict(mutant_wrong_nci_pct=True), local_fail={12},
          hash_ok=False, negative_fail={45}, memo_nci_cta_fail=True)

    score("wrong FX rate for S3 common stock",
          mutant_kwargs=dict(mutant_wrong_translation_rate=True), local_fail={3},
          hash_ok=False, negative_fail={46}, memo_nci_cta_fail=True)

    score("double-counts net income into retained earnings (closes it twice)",
          mutant_kwargs=dict(mutant_double_count_ni=True),
          hash_ok=False, negative_fail={48}, memo_nci_cta_fail=True)

    score("auditor shares derived data with primary (violates independence)",
          negative_fail={47})
