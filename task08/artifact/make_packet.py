#!/usr/bin/env python3
"""Builds ledger8.pdf, the LEDGER-8 engineering packet.

Security/fairness requirement (explicit, non-negotiable, same discipline
as every prior task's make_packet.py): all diagrams/tables are rendered
to RASTER (PNG) images with matplotlib's Agg backend and embedded into
the PDF as opaque image XObjects -- never as vector `savefig(...,
format='pdf')` paths, which would embed exact plotted/drawn coordinates
in the content stream for a model to parse programmatically instead of
reading visually.

None of the four figures, and none of SPEC_TEXT below, contains any
DERIVED value (a consolidated balance, net income, NCI split, CTA, or
the trace-integrity hash). Every number shown is a STATED input constant
from design/semantic-contract.md: each entity's own trial balance (S02),
the three FX rates (S03), and the four intercompany transaction facts
(S04) -- inputs to compute from, never the computation's own output.

After assembly, all document metadata (Info dictionary AND XMP) is
stripped so no authoring timestamps, tool paths, or producer strings ride
along with the shipped artifact.
"""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import fitz  # PyMuPDF

DPI = 300
PAGE_W, PAGE_H = 612, 792  # US letter, points

import sys
sys.path.insert(0, "../reference")
import ledger8_engine as L

RAW = L.raw_trial_balances()
ROW_ORDER = ["Cash", "AR_Trade", "IC_Receivable", "IC_LoanReceivable", "Inventory",
             "Inv_in_S1", "Inv_in_S2", "Inv_in_S3", "PPE_Net", "AP_Trade",
             "IC_Payable", "IC_LoanPayable", "CommonStock", "RetainedEarnings",
             "SalesExternal", "SalesIC", "COGS", "OpEx", "IC_InterestIncome",
             "IC_InterestExpense", "DividendIncomeIC"]
ROW_LABELS = {
    "Cash": "Cash", "AR_Trade": "Accounts receivable (trade)",
    "IC_Receivable": "Intercompany receivable (trade)",
    "IC_LoanReceivable": "Intercompany loan receivable",
    "Inventory": "Inventory", "Inv_in_S1": "Investment in S1",
    "Inv_in_S2": "Investment in S2", "Inv_in_S3": "Investment in S3",
    "PPE_Net": "PP&E, net", "AP_Trade": "Accounts payable (trade)",
    "IC_Payable": "Intercompany payable (trade)",
    "IC_LoanPayable": "Intercompany loan payable",
    "CommonStock": "Common stock", "RetainedEarnings": "Retained earnings (beginning)",
    "SalesExternal": "Sales -- external", "SalesIC": "Sales -- intercompany",
    "COGS": "Cost of goods sold", "OpEx": "Operating expenses",
    "IC_InterestIncome": "Intercompany interest income",
    "IC_InterestExpense": "Intercompany interest expense",
    "DividendIncomeIC": "Intercompany dividend income",
}
SECTION_BREAKS = {"Cash": "ASSETS", "AP_Trade": "LIABILITIES",
                   "CommonStock": "EQUITY (beginning)", "SalesExternal": "INCOME STATEMENT"}


def render_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, metadata={"Software": ""})
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def fmt(n):
    n = int(n)
    return f"{n:,}" if n else "--"


# ---------------------------------------------------------------------
# Figure 1: entity ownership structure.
# ---------------------------------------------------------------------
def diagram_ownership():
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    positions = {"P": (4.2, 4.6), "S1": (1.2, 1.4), "S2": (4.2, 1.4), "S3": (7.2, 1.4)}
    labels = {"P": "PARENT (P)\nUSD", "S1": "S1\n100% owned, USD",
              "S2": "S2\n80% owned, USD", "S3": "S3\n100% owned, EUR"}
    colors = {"P": "#3f6f8f", "S1": "#5b9270", "S2": "#5b9270", "S3": "#a06b3f"}
    for name, (x, y) in positions.items():
        ax.add_patch(plt.Rectangle((x - 1.05, y - 0.5), 2.1, 1.0, facecolor="white",
                                     edgecolor=colors[name], lw=2.2, zorder=2))
        ax.text(x, y, labels[name], ha="center", va="center", fontsize=10,
                fontweight="bold", color=colors[name], zorder=3)

    edges = [("S1", "Inv_in_S1, 100%"), ("S2", "Inv_in_S2, 80%"), ("S3", "Inv_in_S3, 100%")]
    for sub, label in edges:
        xp, yp = positions["P"]
        xs, ys = positions[sub]
        ax.annotate("", xy=(xs, ys + 0.5), xytext=(xp, yp - 0.5),
                     arrowprops=dict(arrowstyle="-|>", color="0.3", lw=1.4), zorder=1)
        mx, my = (xp + xs) / 2, (yp + ys) / 2
        ax.text(mx, my, label, ha="center", fontsize=8.3, color="0.2",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))

    ax.set_xlim(-0.2, 8.6)
    ax.set_ylim(0.4, 5.6)
    ax.axis("off")
    ax.set_title("LEDGER-8 entity structure -- ownership percentage and\n"
                  "the parent's own Investment-in-Subsidiary account name for each",
                 fontsize=10)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Figure 2: full trial balance table, all four entities.
# ---------------------------------------------------------------------
def diagram_trial_balances():
    fig, ax = plt.subplots(figsize=(8.6, 10.8))
    ax.axis("off")
    col_x = [0.02, 0.50, 0.63, 0.76, 0.89]
    headers = ["Account", "P (USD)", "S1 (USD)", "S2 (USD)", "S3 (EUR)"]
    y = 0.985
    row_h = 0.0225
    for cx, h in zip(col_x, headers):
        ax.text(cx, y, h, fontsize=9, fontweight="bold", transform=ax.transAxes)
    y -= row_h * 1.3
    ax.plot([0.0, 1.0], [y + row_h * 0.3, y + row_h * 0.3], color="0.3", lw=1.0,
            transform=ax.transAxes)

    for acct in ROW_ORDER:
        if acct in SECTION_BREAKS:
            y -= row_h * 0.4
            ax.text(0.02, y, SECTION_BREAKS[acct], fontsize=8.6, fontweight="bold",
                    color="#3f6f8f", transform=ax.transAxes)
            y -= row_h * 1.15
        vals = [RAW[e].get(acct, 0) for e in ["P", "S1", "S2", "S3"]]
        ax.text(col_x[0], y, ROW_LABELS[acct], fontsize=8.0, transform=ax.transAxes)
        for cx, v in zip(col_x[1:], vals):
            ax.text(cx, y, fmt(v), fontsize=8.0, transform=ax.transAxes, ha="left")
        y -= row_h

    ax.set_xlim(0, 1)
    ax.set_ylim(max(y - 0.02, 0), 1)
    ax.set_title("Figure 2 -- Each entity's own standalone trial balance (pre-consolidation).\n"
                  "RetainedEarnings is the BEGINNING-of-period balance; S3's column is in EUR.",
                 fontsize=10)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Figure 3: FX rate table.
# ---------------------------------------------------------------------
def diagram_fx_rates():
    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    ax.axis("off")
    rows = [
        ("Closing rate", f"{float(L.S3_CLOSING_RATE):.2f}", "Assets, liabilities, common stock"),
        ("Average rate", f"{float(L.S3_AVERAGE_RATE):.2f}", "Income-statement accounts (this period's flows)"),
        ("Historical rate", f"{float(L.S3_HISTORICAL_RATE):.2f}", "Beginning RetainedEarnings only"),
    ]
    y = 0.85
    ax.text(0.02, y, "Rate", fontsize=10, fontweight="bold", transform=ax.transAxes)
    ax.text(0.28, y, "EUR -> USD", fontsize=10, fontweight="bold", transform=ax.transAxes)
    ax.text(0.48, y, "Applies to", fontsize=10, fontweight="bold", transform=ax.transAxes)
    y -= 0.12
    ax.plot([0.0, 1.0], [y + 0.04, y + 0.04], color="0.3", lw=1.0, transform=ax.transAxes)
    colors = ["#3f6f8f", "#5b9270", "#a06b3f"]
    for (name, rate, applies), c in zip(rows, colors):
        ax.text(0.02, y, name, fontsize=9.5, color=c, fontweight="bold", transform=ax.transAxes)
        ax.text(0.28, y, rate, fontsize=9.5, transform=ax.transAxes)
        ax.text(0.48, y, applies, fontsize=9, transform=ax.transAxes)
        y -= 0.16
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("Figure 3 -- S3's three EUR-to-USD translation rates (S3 reports in EUR)", fontsize=10)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Figure 4: intercompany transaction facts.
# ---------------------------------------------------------------------
def diagram_ic_facts():
    fig, ax = plt.subplots(figsize=(8.0, 5.4))
    ax.axis("off")
    # Note: matplotlib treats a PAIR of unescaped "$" as mathtext delimiters
    # by default, so every literal dollar sign below is escaped as "\$".
    facts = [
        ("Inventory sale", "P -> S1",
         f"Transfer price \\${fmt(L.IC_SALE_PRICE)}, P's own cost \\${fmt(L.IC_SALE_COST)}.\n"
         f"{int(L.IC_SALE_PCT_UNSOLD_AT_S1*100)}% of the transferred goods remain in S1's\n"
         f"ending inventory at year end (unsold to any outside party)."),
        ("Intercompany loan", "P -> S2",
         f"Principal \\${fmt(L.IC_LOAN_PRINCIPAL)}, this year's interest \\${fmt(L.IC_LOAN_INTEREST)}\n"
         f"(P's interest income, S2's interest expense)."),
        ("Trade balance", "P <-> S1",
         f"P's own intercompany trade receivable from S1: \\${fmt(L.IC_RECEIVABLE_PAYABLE)}\n"
         f"(unrelated to the loan above; matched by S1's own payable)."),
        ("Dividend", "S1 -> P",
         f"S1 paid P an intercompany dividend of \\${fmt(L.IC_DIVIDEND)} during\n"
         f"the year, recorded by P as dividend income."),
    ]
    y = 0.95
    for title, direction, detail in facts:
        ax.text(0.02, y, title, fontsize=11, fontweight="bold", color="#3f6f8f",
                transform=ax.transAxes)
        ax.text(0.98, y, direction, fontsize=10, ha="right", color="0.3",
                transform=ax.transAxes)
        y -= 0.06
        for line in detail.split("\n"):
            ax.text(0.04, y, line, fontsize=9, transform=ax.transAxes)
            y -= 0.045
        y -= 0.05
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("Figure 4 -- The four intercompany transaction facts", fontsize=10)
    fig.tight_layout()
    return render_png(fig)


SPEC_TEXT = """LEDGER-8 -- Engineering Packet
Finance -- Corporate Accounting Consolidation
Multi-entity financial-statement consolidation and elimination-entry audit

1. ENTITY STRUCTURE (Figure 1)
One parent (P) and three subsidiaries: S1 (100% owned, domestic), S2
(80% owned, domestic), S3 (100% owned, foreign, reports in EUR). There
is no time dimension and no parameter sweep -- exactly one
consolidation, applied once, to one fixed set of four trial balances.

2. EACH ENTITY'S OWN TRIAL BALANCE (Figure 2)
Every entity states its own standalone trial balance (Figure 2):
balance-sheet accounts plus income-statement accounts (this period's
activity only). RetainedEarnings in every entity's own trial balance is
always the BEGINNING-of-period balance -- this period's income-statement
activity is not yet closed into it. Every entity's own assets equal its
own liabilities plus its own common stock plus its own beginning
retained earnings plus its own net income (an internal consistency
check, independent of consolidation).

3. FOREIGN-CURRENCY TRANSLATION -- S3 ONLY (Figure 3)
S3's assets, liabilities, and common stock translate to USD at the
stated closing rate. S3's income-statement accounts (this period's
flows) translate at the stated average rate. S3's beginning
RetainedEarnings translates at the stated historical rate -- the rate in
effect when it was earned, distinct from both the closing and average
rates. The Cumulative Translation Adjustment (CTA) is the resulting
plug: CTA = TotalAssets - TotalLiabilities - CommonStock -
RetainedEarnings(beginning, translated) - NetIncome(translated), posted
as its own equity line.

4. INTERCOMPANY TRANSACTION FACTS (Figure 4)
Four intercompany facts, each stated with its own amounts (Figure 4):
an inventory sale from P to S1 (transfer price, P's own cost, and the
fraction of the transferred goods still unsold in S1's ending
inventory); an intercompany loan from P to S2 (principal and this
year's interest); a separate, loan-unrelated trade receivable/payable
between P and S1; and an intercompany dividend S1 paid to P during the
year.

5. THE SIX REQUIRED ELIMINATION ENTRIES
Each is a genuine double-entry journal entry: converting every line to
its debit-equivalent (a positive amount on a debit-normal account --
assets, expenses -- is a debit; a positive amount on a credit-normal
account -- liabilities, equity, revenue -- is a credit) must sum to
exactly zero. E1 eliminates the full intercompany sale (the entire
transfer price) from intercompany sales revenue against cost of goods
sold. E2 separately defers the unrealized profit still in the ending
inventory: (fraction unsold) x (transfer price - seller's own cost), via
a COGS increase and matching inventory decrease -- E1 alone does not
defer unrealized profit, and E2 alone does not remove the
double-counted revenue; both are required. E3 eliminates the
intercompany loan principal (receivable against payable) and its
interest (interest income against interest expense) in full. E4
eliminates the separate, loan-unrelated trade receivable/payable in
full. E5 removes the intercompany dividend from income and restores the
payor's retained earnings by the same amount (an intercompany dividend
must have zero net effect on both consolidated net income and
consolidated retained earnings). E6: for each subsidiary, remove 100%
of its own common stock and beginning retained earnings, replacing them
with the parent's Investment-in-that-subsidiary elimination at the
parent's ownership percentage, and a new NCI_Equity line at the
complementary (non-controlling) percentage.

6. INVESTMENT BASIS (NO GOODWILL)
Every Investment-in-Subsidiary account, as given in the parent's own
trial balance, equals the parent's ownership percentage multiplied by
that subsidiary's own beginning equity (common stock at the applicable
translation rate, plus beginning retained earnings) -- the parent
invested at each subsidiary's then-book-value, with no goodwill or
purchase differential. This is what makes every Investment-in-Subsidiary
account eliminate to exactly zero in E6, for every subsidiary.

7. NET INCOME AND ITS SPLIT
Consolidated net income (post-elimination) is split between the
controlling interest and non-controlling interest (NCI). NCI's share is
the minority ownership percentage applied to S2's own standalone net
income only (S2's intercompany loan interest nets entirely against the
parent's side via E3 and does not itself change S2's own reported net
income). The controlling share closes into consolidated
RetainedEarnings; the NCI share closes into NCI_Equity, on top of what
E6 already posted for beginning NCI equity.

8. REQUIRED OUTPUT AND FEASIBILITY INVARIANT
The final consolidated balance sheet must satisfy Assets = Liabilities +
(CommonStock + consolidated RetainedEarnings + CTA + NCI_Equity)
exactly -- this is the primary feasibility invariant a submission's own
work must satisfy, independent of matching any particular reference
number.

9. INDEPENDENT VERIFICATION
A separately-coded auditor, sharing only immutable input constants with
the primary implementation, must independently re-derive the full
consolidation (or check a complete feasibility certificate) and confirm
the balance-sheet balance invariant, that every one of the six
elimination entries independently re-verifies to balance in
debit-equivalent terms, and NCI consistency (NCI_Equity plus the
controlling share of consolidated equity, summed, equals total
consolidated equity net of liabilities). Two required adversarial
mutations: an elimination entry that does not balance (a missing
offsetting line), and a currency-translation error (translating an item
at the wrong one of the three stated rates). The auditor must reject
both while still accepting the true original.

10. CERTIFICATION
Build the serialization as exactly these lines, in this exact order,
each line AccountName=Value with no spaces, no currency symbol, no
thousands separator, no decimal point (every input and every rate is an
exact decimal, so every computed amount is a plain integer -- never a
rounded float), and a leading - only for a negative value:
(1) the literal header line LEDGER8-CERT-V1;
(2) one line for each of these 16 balance-sheet accounts, in exactly
this order (not alphabetical), using the account name exactly as
spelled here, and including every one even when its value is exactly 0:
Cash, AR_Trade, IC_Receivable, IC_LoanReceivable, Inventory, Inv_in_S1,
Inv_in_S2, Inv_in_S3, PPE_Net, AP_Trade, IC_Payable, IC_LoanPayable,
CommonStock, RetainedEarnings, NCI_Equity, CTA;
(3) one line for each of these 7 income-statement accounts, in exactly
this order, same zero-inclusion rule: SalesExternal, SalesIC, COGS,
OpEx, IC_InterestIncome, IC_InterestExpense, DividendIncomeIC;
(4) two final lines, in order: NetIncome, then NCI_NetIncome.
Example (illustrative numbers only, not this task's actual answer): if
Cash were 100 and AR_Trade were 0, their lines would read exactly
Cash=100 and AR_Trade=0.
Join all 26 lines (the header plus 25 account lines) with a single \\n
character, UTF-8 encode, hash with SHA-256; report the first 16 hex
characters as the trace-integrity certificate.

Deliver: consolidation engine source; independently-coded auditor
source; the final consolidated balance sheet and income statement; a
findings report; certification evidence (the trace hash plus both
adversarial-mutation rejection results); and an engineering memo
explaining the causal chain from the intercompany facts through the six
elimination entries to the final consolidated numbers. Base every
reported number on your own executed implementation -- never
hand-derive a balance, a total, or the hash.
"""


def build_text_pages(doc):
    blocks = SPEC_TEXT.split("\n\n")
    margin = 44
    rect = fitz.Rect(margin, margin, PAGE_W - margin, PAGE_H - margin)
    fontsize = 8.0

    def fits(text, fs):
        tmp = fitz.open()
        p = tmp.new_page(width=PAGE_W, height=PAGE_H)
        rc = p.insert_textbox(rect, text, fontsize=fs, fontname="helv",
                               align=fitz.TEXT_ALIGN_LEFT)
        tmp.close()
        return rc >= 0

    pages_text = []
    current = ""
    for block in blocks:
        candidate = (current + "\n\n" + block) if current else block
        if fits(candidate, fontsize):
            current = candidate
        else:
            if current:
                pages_text.append(current)
            current = block
            if not fits(current, fontsize):
                raise RuntimeError(f"single block too large to fit page:\n{block[:80]}...")
    if current:
        pages_text.append(current)

    for text in pages_text:
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        page.insert_textbox(rect, text, fontsize=fontsize, fontname="helv",
                             align=fitz.TEXT_ALIGN_LEFT)


def build_image_page(doc, png_bytes, caption):
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    img = fitz.open("png", png_bytes)
    iw, ih = img[0].rect.width, img[0].rect.height
    margin = 40
    max_w = PAGE_W - 2 * margin
    max_h = PAGE_H - 2 * margin - 30
    scale = min(max_w / iw, max_h / ih)
    w, h = iw * scale, ih * scale
    x0 = (PAGE_W - w) / 2
    y0 = 40
    page.insert_image(fitz.Rect(x0, y0, x0 + w, y0 + h), stream=png_bytes)
    page.insert_textbox(fitz.Rect(margin, y0 + h + 6, PAGE_W - margin, y0 + h + 40),
                         caption, fontsize=9, fontname="helv",
                         align=fitz.TEXT_ALIGN_CENTER)


def main():
    doc = fitz.open()

    build_image_page(doc, diagram_ownership(),
                      "Figure 1 -- Entity structure: ownership percentage and Investment account names.")
    build_image_page(doc, diagram_trial_balances(),
                      "Figure 2 -- Each entity's own standalone trial balance (pre-consolidation).")
    build_image_page(doc, diagram_fx_rates(),
                      "Figure 3 -- S3's three EUR-to-USD translation rates.")
    build_image_page(doc, diagram_ic_facts(),
                      "Figure 4 -- The four intercompany transaction facts.")
    build_text_pages(doc)

    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    doc.xref_set_key(doc.pdf_catalog(), "Info", "null")

    out_path = "/home/user/cc/task08/artifact/ledger8.pdf"
    doc.save(out_path, garbage=4, deflate=True, clean=True)
    doc.close()

    raw = open(out_path, "rb").read()
    start = raw.find(b"% Written by")
    if start != -1:
        end = raw.find(b"\n", start)
        segment = raw[start:end]
        blanked = b"%" + b" " * (len(segment) - 1)
        raw = raw[:start] + blanked + raw[end:]
        open(out_path, "wb").write(raw)

    print("wrote", out_path)


if __name__ == "__main__":
    main()
