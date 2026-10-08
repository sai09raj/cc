"""TASK 13 v2 documents: case file for the L1 trip, with the decisive CT evidence spread over three documents
(relay settings CTR -> nameplate tap chart -> commissioning book), none of which states the discrepancy."""
import os, random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
import fitz
import make_docs as md

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "artifact", "bundle2")
md.OUT = OUT

TAPS_2000 = [("X1-X2", "250:5"), ("X2-X3", "400:5"), ("X3-X4", "800:5"), ("X4-X5", "550:5"), ("X1-X3", "650:5"),
             ("X2-X4", "1200:5"), ("X3-X5", "1350:5"), ("X1-X4", "1450:5"), ("X2-X5", "1750:5"), ("X1-X5", "2000:5")]
TAPS_1200 = [("X1-X2", "100:5"), ("X2-X3", "200:5"), ("X3-X4", "300:5"), ("X4-X5", "600:5"), ("X1-X3", "300:5"),
             ("X2-X4", "500:5"), ("X3-X5", "900:5"), ("X1-X4", "600:5"), ("X2-X5", "1100:5"), ("X1-X5", "1200:5")]


def fig_oneline2():
    fig, ax = plt.subplots(figsize=(11, 6.8))
    ax.set_xlim(0, 11); ax.set_ylim(0, 6.8); ax.axis("off")
    for x, lab in ((1.2, "SUBSTATION A\n230 kV"), (5.6, "SUBSTATION B\n230 kV"), (9.8, "SUBSTATION C\n230 kV")):
        ax.plot([x, x], [2.0, 5.0], color="k", lw=4); ax.text(x, 5.25, lab, ha="center", fontsize=9, weight="bold")
        ax.add_patch(Circle((x - 0.75 if x < 9 else x + 0.75, 3.5), 0.32, fill=False, lw=1.3))
        ax.text(x - 0.75 if x < 9 else x + 0.75, 3.5, "~", ha="center", va="center", fontsize=13)
        ax.plot([x - 0.43, x] if x < 9 else [x, x + 0.43], [3.5, 3.5], color="k", lw=1.2)

    def brk(x, y):
        ax.add_patch(Rectangle((x - 0.13, y - 0.13), 0.26, 0.26, fill=True, color="k"))

    def ct(x, y, dot_left):
        ax.add_patch(Circle((x, y), 0.14, fill=False, lw=1.2))
        ax.plot([x - 0.22 if dot_left else x + 0.22], [y + 0.2], "ko", ms=3.5)
    y = 4.3; y2 = 2.9
    ax.plot([1.2, 5.6], [y, y], color="k", lw=1.5); ax.plot([5.6, 9.8], [y2, y2], color="k", lw=1.5)
    brk(1.75, y); ct(2.2, y, True); brk(5.05, y); ct(4.6, y, False)
    brk(6.15, y2); ct(6.6, y2, True); brk(9.25, y2); ct(8.8, y2, False)
    ax.text(3.4, y + 0.25, "LINE L1   80 km", ha="center", fontsize=9)
    ax.text(7.7, y2 + 0.25, "LINE L2   50 km", ha="center", fontsize=9)
    for x, yy, lab in ((2.2, y - 0.55, "L1-21\nrelay A"), (4.6, y - 0.55, "L1-21\nrelay B"), (6.6, y2 - 0.55, "L2-21\nSub B"),
                       (8.8, y2 - 0.55, "L2-21\nSub C")):
        ax.text(x, yy, lab, ha="center", fontsize=7.5)
    for x, lab in ((1.2, "VT-A 2000:1"), (5.6, "VT-B 2000:1"), (9.8, "VT-C 2000:1")):
        ax.text(x + 0.1, 2.1, lab, fontsize=7)
    ax.annotate("", (4.3, 5.95), (2.5, 5.95), arrowprops=dict(arrowstyle="<->", lw=1.0))
    ax.text(3.4, 6.05, "POTT channel L1 (A <-> B)", ha="center", fontsize=8)
    ax.annotate("", (8.5, 5.95), (6.9, 5.95), arrowprops=dict(arrowstyle="<->", lw=1.0))
    ax.text(7.7, 6.05, "POTT channel L2 (B <-> C)", ha="center", fontsize=8)
    ax.text(0.25, 1.25, "Line data (both lines, positive and negative sequence): z1 = 0.05 + j0.48 ohm/km.  Line charging negligible.\n"
            "Each line relay takes its voltages from its substation's 230 kV bus VT (VT-A, VT-B, VT-C), so the two relays at\n"
            "Substation B see the same bus voltages.  Filled square = closed breaker.  CT symbol: circle with polarity dot (P1).\n"
            "Relay current convention: a current entering the CT at P1 is measured as positive, i.e. flowing from the bus into the line.",
            fontsize=8)
    ax.set_title("230 kV SYSTEM ONE-LINE (PROTECTION)    DWG S-230-001  REV E", fontsize=10)
    return md.png(fig)


def fig_ctsheet(sub, bay, dwg, rev, ct_name, nameplate, taps, cores, notes):
    fig, ax = plt.subplots(figsize=(11, 7.4))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7.4); ax.axis("off")
    ax.text(0.3, 7.0, f"SUBSTATION {sub}  -  230 kV BAY {bay}  -  CURRENT TRANSFORMER DETAILS", fontsize=11, weight="bold")
    ax.text(0.3, 6.6, f"{ct_name}   nameplate: {nameplate}", fontsize=9.5)
    xs = [0.8 + 0.9 * i for i in range(5)]
    for x0, x1 in zip(xs[:-1], xs[1:]):
        for kk in range(3):
            c = x0 + (x1 - x0) * (kk + 0.5) / 3
            ax.add_patch(Arc((c, 5.3), (x1 - x0) / 3, 0.5, theta1=0, theta2=180, lw=1.2))
    for i, x in enumerate(xs):
        ax.plot([x, x], [5.3, 4.8], color="k", lw=1.0); ax.text(x, 4.55, f"X{i + 1}", ha="center", fontsize=9)
    ax.text(0.6, 5.75, "secondary winding (multi-ratio), one per core", fontsize=8)
    ax.text(8.1, 6.6, "NAMEPLATE TAP CHART", fontsize=9, weight="bold")
    for i, (t, r) in enumerate(taps):
        yy = 6.25 - 0.27 * i
        ax.text(8.2, yy, t, fontsize=8.5); ax.text(9.5, yy, r, fontsize=8.5)
        ax.plot([8.1, 10.5], [yy - 0.08, yy - 0.08], color="0.75", lw=0.5)
    ax.text(0.3, 3.9, "SECONDARY CORES", fontsize=9, weight="bold")
    for x, h in zip((0.3, 1.1, 3.4), ("Core", "Function", "Destination")):
        ax.text(x, 3.55, h, fontsize=8.5, weight="bold")
    for i, row in enumerate(cores):
        for x, v in zip((0.3, 1.1, 3.4), row):
            ax.text(x, 3.2 - 0.32 * i, v, fontsize=8.5)
    for i, n in enumerate(notes):
        ax.text(0.3, 1.75 - 0.3 * i, n, fontsize=8.2)
    ax.add_patch(Rectangle((7.6, 0.15), 3.2, 1.05, fill=False, lw=1.0))
    ax.text(7.7, 0.95, f"DWG {dwg}   REV {rev}", fontsize=8.5, weight="bold")
    ax.text(7.7, 0.62, f"230 kV protection, bay {bay}", fontsize=8)
    ax.text(7.7, 0.32, "Scale: none", fontsize=8)
    return md.png(fig)


NOTES = ["Polarity: P1 toward the 230 kV bus (all cores).",
         "Secondary taps: as required by the ratio set in the connected device (protection settings / metering schedule).",
         "Unused taps left open; X-terminal shorting links removed only on the landed pair."]


def ct_sets():
    doc = fitz.open()
    sheets = [
        ("B", "L1", "B-E-2214", "B", "CT 52-L1  (3 x single-phase, outdoor)", "2000:5 MR  C800  RF 2.0", TAPS_2000,
         [("1", "Line protection", "L1-21 line relay (relay B), IA/IB/IC"), ("2", "Bus differential", "87B-230 zone 1"),
          ("3", "Metering", "revenue meter M-L1")]),
        ("B", "L2", "B-E-2215", "B", "CT 52-L2  (3 x single-phase, outdoor)", "2000:5 MR  C800  RF 2.0", TAPS_2000,
         [("1", "Line protection", "L2-21 line relay (Sub B), IA/IB/IC"), ("2", "Bus differential", "87B-230 zone 1"),
          ("3", "Metering", "revenue meter M-L2")]),
        ("B", "T1", "B-E-2216", "A", "CT 52-T1  (bushing CT, transformer T1 HV)", "1200:5 MR  C400  RF 1.5", TAPS_1200,
         [("1", "Transformer differential", "87T-T1, HV winding"), ("2", "Bus differential", "87B-230 zone 1")]),
    ]
    for sub, bay, dwg, rev, nm, npl, taps, cores in sheets:
        md.image_page(doc, fig_ctsheet(sub, bay, dwg, rev, nm, npl, taps, cores, NOTES), landscape=True)
    md.clean_save(doc, os.path.join(OUT, "SUBB_230kV_CT_drawings_B-E-2214_to_2216.pdf"))
    doc = fitz.open()
    md.image_page(doc, fig_ctsheet("A", "L1", "A-E-1107", "B", "CT 52-L1  (3 x single-phase, outdoor)", "1200:5 MR  C800  RF 2.0",
                                   TAPS_1200, [("1", "Line protection", "L1-21 line relay (relay A), IA/IB/IC"),
                                               ("2", "Bus differential", "87B-230 zone 2"), ("3", "Metering", "revenue meter M-L1")], NOTES),
                  landscape=True)
    md.clean_save(doc, os.path.join(OUT, "SUBA_230kV_CT_drawing_A-E-1107.pdf"))
    doc = fitz.open()
    md.image_page(doc, fig_ctsheet("C", "L2", "C-E-0310", "A", "CT 52-L2  (3 x single-phase, outdoor)", "2000:5 MR  C800  RF 2.0",
                                   TAPS_2000, [("1", "Line protection", "L2-21 line relay (Sub C), IA/IB/IC"),
                                               ("2", "Bus differential", "87B-230"), ("3", "Metering", "revenue meter M-L2")], NOTES),
                  landscape=True)
    md.clean_save(doc, os.path.join(OUT, "SUBC_230kV_CT_drawing_C-E-0310.pdf"))


def commissioning2():
    rnd = random.Random(2023)
    books = [
        ("A", "2024-03-11", "MT", [("52-L1", "1", "X1-X5"), ("52-L1", "2", "X1-X5"), ("52-L1", "3", "X1-X5"),
                                   ("52-T2", "1", "X2-X5"), ("52-T2", "2", "X1-X5")]),
        ("B", "2023-04-14", "JO", [("52-L1", "1", "X1-X5"), ("52-L1", "2", "X1-X5"), ("52-L1", "3", "X2-X4"),
                                   ("52-L2", "1", "X2-X4"), ("52-L2", "2", "X1-X5"), ("52-L2", "3", "X2-X4")]),
        ("B", "2023-04-15", "JO", [("52-T1", "1", "X2-X5"), ("52-T1", "2", "X1-X5"), ("52-BC", "1", "X1-X5"), ("52-BC", "2", "X2-X4")]),
        ("C", "2023-04-12", "RL", [("52-L2", "1", "X2-X4"), ("52-L2", "2", "X1-X5"), ("52-L2", "3", "X2-X4"),
                                   ("52-T3", "1", "X1-X4")]),
    ]
    doc = fitz.open()
    for sub, date, ini, cts in books:
        rows = []
        for ctn, core, lead in cts:
            for ph in "ABC":
                rows.append((f"{ctn} {ph}", core, lead, "OK", str(4000 + rnd.randint(-600, 900)),
                             f"{rnd.uniform(0.15, 0.48):.2f}", "PASS", ini))
        fig = md.fig_form(sub, date, rows, rnd)
        md.image_page(doc, md.png(fig, dpi=150), top=20)
    md.clean_save(doc, os.path.join(OUT, "CT_commissioning_book_A_B_C.pdf"))


MAINT = """SUBSTATION B  -  PROTECTION AND CONTROL MAINTENANCE LOG  (extract, 2026)

2026-01-19  Battery 125 V DC: annual capacity test, PASS.
2026-02-03  87B-230 bus differential: routine test, PASS. No setting change.
2026-03-11  L2-21 (Sub B): routine secondary injection test, PASS.
2026-04-02  Generating unit G2 (connected at Substation B) permanently retired. Substation B becomes a weak source for L1.
2026-05-26  L1-21 relay B: firmware upgraded v3.2 -> v3.4 (vendor service bulletin SB-114, improved event storage).
2026-05-26  L1-21 relay B: settings revision R5 applied per settings calculation 2025-11 (ECHO enabled for weak-source
            terminal; Z3P recalculated 1.80 -> 1.74 ohm sec). Functional check of POTT/echo with relay A by end-to-end test: PASS.
2026-06-14  VT-B secondary MCB replaced (trip-free operation intermittent). Voltage check at L1-21 and L2-21: PASS.
2026-07-30  L1-21 relay B: annual test, PASS (element pickups verified by secondary injection at the relay test switch).
2026-08-22  Breaker 52-L2: timing test, 2.9 cycles.
"""


def maint():
    doc = fitz.open(); md.text_page(doc, MAINT, 8.8)
    md.clean_save(doc, os.path.join(OUT, "SUBB_PC_maintenance_log_2026.pdf"))


CALC2 = md.CALC.replace("(issued 2025-11)", "(issued 2025-11, applied at Substation B as settings revision R5 on 2026-05-26)").replace(
    "Instrument transformers (both line ends, per design drawings): CT 1200:5 (CTR = 240), VT 230 kV : 115 V (PTR = 2000).",
    "Instrument transformers (both line ends): protection CT ratio 1200:5 (CTR = 240), VT 230 kV : 115 V (PTR = 2000).").replace(
    "Substation B is the weak-source terminal:", "Substation B becomes the weak-source terminal after the retirement of unit G2 (2026):")


def calc2():
    doc = fitz.open(); md.text_page(doc, CALC2, 8.8)
    md.clean_save(doc, os.path.join(OUT, "L1_protection_settings_calculation.pdf"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    md.manual()
    doc = fitz.open(); md.image_page(doc, fig_oneline2(), landscape=True)
    md.clean_save(doc, os.path.join(OUT, "system_one_line_S-230-001.pdf"))
    ct_sets(); commissioning2(); maint(); calc2(); md.patrol()
    print(sorted(os.listdir(OUT)))
