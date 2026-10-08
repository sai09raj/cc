"""TASK 13: render the incident bundle's documents as metadata-free PDFs (figures and scanned forms rasterized)."""
import io, os, random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "artifact", "bundle")
PW, PH = 612, 792


def png(fig, dpi=200):
    b = io.BytesIO(); fig.savefig(b, format="png", dpi=dpi, facecolor="white"); plt.close(fig)
    return b.getvalue()


def clean_save(doc, path):
    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    tmp = path + ".tmp"
    doc.save(tmp, garbage=4, deflate=True, clean=True); doc.close()
    d = fitz.open(tmp)
    d.xref_set_key(-1, "Info", "null"); d.xref_set_key(-1, "ID", "null")
    cat = d.pdf_catalog(); pages = d.xref_get_key(cat, "Pages")[1]
    d.update_object(cat, "<< /Type /Catalog /Pages %s >>" % pages)
    d.save(path, garbage=4, deflate=True, clean=True, no_new_id=True); d.close(); os.remove(tmp)
    raw = open(path, "rb").read()
    i = raw.find(b"% Written by")
    if i != -1:
        j = raw.find(b"\n", i); raw = raw[:i] + b"%" + b" " * (j - i - 1) + raw[j:]; open(path, "wb").write(raw)


def text_page(doc, text, fs=9.0, w=PW, h=PH):
    p = doc.new_page(width=w, height=h)
    rc = p.insert_textbox(fitz.Rect(48, 44, w - 48, h - 40), text, fontsize=fs, fontname="helv")
    if rc < 0:
        raise RuntimeError("overflow")


def image_page(doc, data, landscape=False, top=36):
    w, h = (PH, PW) if landscape else (PW, PH)
    p = doc.new_page(width=w, height=h)
    img = fitz.open("png", data); iw, ih = img[0].rect.width, img[0].rect.height
    s = min((w - 50) / iw, (h - 60) / ih); x0 = (w - iw * s) / 2
    p.insert_image(fitz.Rect(x0, top, x0 + iw * s, top + ih * s), stream=data)


# ---------------------------------------------------------------- relay manual excerpt
MANUAL_P1 = """L1-21 LINE RELAY  -  INSTRUCTION MANUAL (EXCERPT)  -  PHASE DISTANCE AND POTT FUNCTIONS

1. SAMPLING AND PHASORS
The relay samples VA, VB, VC, IA, IB, IC at 32 samples per power-system cycle (60 Hz, 1920 samples/s). Analog values are in secondary volts and secondary amperes. The oscillography record (COMTRADE 1999, ASCII) stores exactly the samples the protection functions use; the digital channels in the record are the relay's own element outputs at each sample. Sample n in the .dat file (first column, 1-based) is relay sample k = n - 1.
For every sample k >= 31 the relay computes, for each analog channel x, the full-cycle Fourier phasor
    X(k) = (sqrt(2) / 32) * SUM over i = 0..31 of  x[k - i] * exp(-j * 2 * pi * (k - i) / 32)
(an RMS phasor in a fixed reference frame). No phasor exists before sample 31, and no element can assert before then.

2. PHASE DISTANCE ELEMENTS
Three phase-to-phase loops are measured: AB, BC and CA. For loop XY the loop voltage is V = VX - VY and the loop current is I = IX - IY (phasors at the same sample). A loop is evaluated only when |I| >= 50PP; its apparent impedance is Z = V / I in secondary ohms.
Each zone is a mho circle through the origin (Figure 1). For a forward zone of reach R (setting Z1P or Z2P) and angle T (setting Z1ANG) the loop operates when |Z - (R/2) * e^(jT)| <= R/2. For the reverse zone 3 of reach R (setting Z3P) the loop operates when |Z + (R/2) * e^(jT)| <= R/2. A zone element (Z1, Z2, Z3R) is asserted at sample k when at least one of the three loops operates at sample k.

3. SECONDARY AND PRIMARY QUANTITIES
The relay converts secondary values to primary with its settings CTR and PTR: primary ohms = secondary ohms x PTR / CTR, primary amperes = secondary amperes x CTR. Reaches entered in secondary ohms are applied to the measured secondary impedance directly.

4. FAULT LOCATOR
When the relay trips it reports the distance to fault d = X / x1, where X is the reactance of the faulted loop's apparent impedance at the trip sample converted to primary with CTR and PTR, and x1 is the line's positive-sequence reactance per km (0.48 ohm/km for L1).

5. PERMISSIVE OVERREACHING TRANSFER TRIP (POTT) AND ECHO
The scheme logic is shown in Figure 2. Settings EDPU, EDUR and EBLK are in samples. All logic is evaluated once per sample, in the order: zone elements, receive (RX), echo logic, transmit (KEY), trip. The communication channel delivers a KEY asserted at the remote relay at sample k as RX at the local relay at sample k + 12 (6.25 ms, each direction). TRIP latches until reset. A breaker opens 96 samples (3 cycles) after its relay asserts TRIP.
"""


def fig_mho():
    import numpy as np
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    T = np.radians(84)
    for R, lab, rev, ls in ((3.71, "Z1 (Z1P)", False, "-"), (5.79, "Z2 (Z2P)", False, "--"), (1.74, "Z3R (Z3P)", True, "-.")):
        c = (R / 2) * np.exp(1j * T) * (-1 if rev else 1)
        ax.add_patch(Circle((c.real, c.imag), R / 2, fill=False, ls=ls, lw=1.6))
        p = c + (R / 2) * np.exp(1j * (T if not rev else T + np.pi))
        ax.annotate(lab, (p.real, p.imag), textcoords="offset points", xytext=(8, 4), fontsize=9)
    ax.plot([0, 6.5 * np.cos(T)], [0, 6.5 * np.sin(T)], color="0.5", lw=0.8)
    ax.text(6.5 * np.cos(T) + 0.1, 6.5 * np.sin(T) - 0.3, "T", fontsize=9, color="0.3")
    ax.axhline(0, color="k", lw=0.6); ax.axvline(0, color="k", lw=0.6)
    ax.set_xlim(-3.5, 4.5); ax.set_ylim(-2.5, 6.6); ax.set_aspect("equal")
    ax.set_xlabel("R (secondary ohm)"); ax.set_ylabel("X (secondary ohm)")
    ax.set_title("Figure 1. Phase mho characteristics (shapes drawn to the Substation B settings).\n"
                 "Forward zones lie on the line angle T; the reverse zone is the forward circle mirrored through the origin.",
                 fontsize=8.5)
    ax.grid(alpha=0.25)
    return png(fig)


def gate(ax, x, y, w, h, label, fs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fill=False, lw=1.3))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs)


def arrow(ax, x0, y0, x1, y1, neg=False):
    ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", lw=1.0))
    if neg:
        ax.add_patch(Circle((x1 - 0.06, y1), 0.05, fill=False, lw=1.0))


def fig_logic():
    fig, ax = plt.subplots(figsize=(10.5, 6.6))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.axis("off")
    # inputs
    for y, lab in ((6.2, "Z2"), (5.2, "RX"), (3.6, "Z1"), (3.0, "Z2"), (2.4, "Z3R"), (1.4, "Z3R"), (0.4, "RX")):
        ax.text(0.2, y, lab, fontsize=9, va="center")
    # trip
    gate(ax, 1.6, 5.35, 1.0, 1.0, "AND", 9)
    arrow(ax, 0.6, 6.2, 1.6, 6.05); arrow(ax, 0.6, 5.2, 1.6, 5.65)
    gate(ax, 3.4, 5.6, 1.0, 1.1, "OR", 9)
    ax.text(2.9, 6.75, "Z1", fontsize=9); arrow(ax, 3.1, 6.7, 3.4, 6.4)
    arrow(ax, 2.6, 5.85, 3.4, 5.9)
    gate(ax, 5.0, 5.75, 1.3, 0.8, "latch", 9); arrow(ax, 4.4, 6.15, 5.0, 6.15)
    arrow(ax, 6.3, 6.15, 7.0, 6.15); ax.text(7.1, 6.15, "TRIP", fontsize=10, va="center", weight="bold")
    # echo
    gate(ax, 1.8, 0.9, 1.2, 0.9, "EBLK\ndropout\ntimer", 7.5)
    arrow(ax, 0.8, 1.4, 1.8, 1.35)
    gate(ax, 4.0, 1.2, 1.2, 3.0, "AND", 9)
    arrow(ax, 0.8, 3.6, 4.0, 3.75, neg=True); arrow(ax, 0.8, 3.0, 4.0, 3.15, neg=True)
    arrow(ax, 0.8, 2.4, 4.0, 2.55, neg=True); arrow(ax, 3.0, 1.35, 4.0, 1.95, neg=True)
    arrow(ax, 0.8, 0.4, 3.6, 0.4); ax.plot([3.6, 3.6], [0.4, 1.4], color="k", lw=1.0); arrow(ax, 3.6, 1.4, 4.0, 1.45)
    gate(ax, 5.8, 2.2, 1.2, 1.0, "EDPU\npickup", 8); arrow(ax, 5.2, 2.7, 5.8, 2.7)
    gate(ax, 7.6, 2.2, 1.3, 1.0, "EDUR\none-shot", 8); arrow(ax, 7.0, 2.7, 7.6, 2.7)
    arrow(ax, 8.9, 2.7, 9.4, 2.7); ax.text(9.45, 2.7, "ECHO", fontsize=10, va="center", weight="bold")
    # key
    gate(ax, 8.0, 4.1, 1.0, 1.0, "OR", 9)
    ax.text(7.2, 4.85, "Z2", fontsize=9); arrow(ax, 7.5, 4.85, 8.0, 4.85)
    ax.plot([9.2, 9.2], [2.7, 3.7], color="k", lw=1.0); ax.plot([9.2, 7.7], [3.7, 3.7], color="k", lw=1.0)
    ax.plot([7.7, 7.7], [3.7, 4.35], color="k", lw=1.0); arrow(ax, 7.7, 4.35, 8.0, 4.35)
    arrow(ax, 9.0, 4.6, 9.6, 4.6); ax.text(9.65, 4.6, "KEY (to channel)", fontsize=9.5, va="center", weight="bold")
    ax.text(0.2, -0.15, "o = inverted input.  EDPU pickup: output asserts on the EDPU-th consecutive sample with the input asserted.  "
            "EDUR one-shot: output asserted for EDUR samples\nfrom a rising input; a new pulse cannot start while one is running.  "
            "EBLK dropout: output stays asserted for EBLK samples after its input deasserts.", fontsize=7.5)
    ax.set_title("Figure 2. POTT trip, echo and transmit logic (ECHO path active only when setting ECHO = Y)", fontsize=10)
    return png(fig)


def manual():
    doc = fitz.open()
    text_page(doc, MANUAL_P1, 8.6)
    image_page(doc, fig_mho())
    image_page(doc, fig_logic(), landscape=True)
    clean_save(doc, os.path.join(OUT, "L1-21_relay_manual_excerpt.pdf"))


# ---------------------------------------------------------------- one-line diagram
def fig_oneline():
    fig, ax = plt.subplots(figsize=(11, 6.8))
    ax.set_xlim(0, 11); ax.set_ylim(0, 6.8); ax.axis("off")
    for x, lab in ((1.2, "SUBSTATION A\n230 kV"), (5.6, "SUBSTATION B\n230 kV"), (9.8, "SUBSTATION C\n230 kV")):
        ax.plot([x, x], [2.0, 5.0], color="k", lw=4); ax.text(x, 5.25, lab, ha="center", fontsize=9, weight="bold")
        ax.add_patch(Circle((x - 0.75, 3.5), 0.32, fill=False, lw=1.3)); ax.text(x - 0.75, 3.5, "~", ha="center", va="center", fontsize=13)
        ax.plot([x - 0.43, x], [3.5, 3.5], color="k", lw=1.2)
    def brk(x, y):
        ax.add_patch(Rectangle((x - 0.13, y - 0.13), 0.26, 0.26, fill=True, color="k"))
    def ct(x, y, dot_left):
        ax.add_patch(Circle((x, y), 0.14, fill=False, lw=1.2))
        ax.plot([x - 0.22 if dot_left else x + 0.22], [y + 0.2], "ko", ms=3.5)
    y = 4.2
    ax.plot([1.2, 5.6], [y, y], color="k", lw=1.5); ax.plot([5.6, 9.8], [y - 1.4, y - 1.4], color="k", lw=1.5)
    brk(1.75, y); ct(2.2, y, True); brk(5.05, y); ct(4.6, y, False)
    brk(6.15, y - 1.4); ct(6.6, y - 1.4, True); brk(9.25, y - 1.4); ct(8.8, y - 1.4, False)
    ax.text(3.4, y + 0.25, "LINE L1   80 km", ha="center", fontsize=9)
    ax.text(7.7, y - 1.15, "LINE L2   50 km", ha="center", fontsize=9)
    for x, yy, lab in ((2.2, y - 0.55, "L1-21\nrelay A"), (4.6, y - 0.55, "L1-21\nrelay B"), (6.6, y - 1.95, "L2-21"), (8.8, y - 1.95, "L2-21")):
        ax.text(x, yy, lab, ha="center", fontsize=7.5)
    for x in (1.2, 5.6):
        ax.text(x + 0.12, 2.25, "VT 2000:1", fontsize=7)
    ax.annotate("", (4.3, 5.85), (2.5, 5.85), arrowprops=dict(arrowstyle="<->", lw=1.0))
    ax.text(3.4, 5.95, "POTT channel L1 (A <-> B)", ha="center", fontsize=8)
    ax.text(0.25, 1.35, "Line data (both lines, positive and negative sequence): z1 = 0.05 + j0.48 ohm/km.  Line charging negligible.\n"
            "Breaker symbols: filled square = closed.  CT symbol: circle with polarity dot (dot marks the primary terminal P1).\n"
            "Relay current convention: a current entering the CT at P1 is measured as positive, i.e. flowing from the bus into the line.",
            fontsize=8)
    ax.set_title("230 kV SYSTEM ONE-LINE (PROTECTION)    DWG S-230-001  REV D", fontsize=10)
    return png(fig)


def oneline():
    doc = fitz.open(); image_page(doc, fig_oneline(), landscape=True)
    clean_save(doc, os.path.join(OUT, "system_one_line_S-230-001.pdf"))


# ---------------------------------------------------------------- CT drawings
def fig_ct(sub, dwg, rev, ct_name, nameplate, taps, cores, notes):
    fig, ax = plt.subplots(figsize=(11, 7.4))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7.4); ax.axis("off")
    ax.text(0.3, 7.0, f"SUBSTATION {sub}  -  230 kV BAY L1  -  CURRENT TRANSFORMER DETAILS", fontsize=11, weight="bold")
    ax.text(0.3, 6.6, f"{ct_name}   nameplate: {nameplate}", fontsize=9.5)
    # winding with taps
    xs = [0.8 + 0.9 * i for i in range(5)]
    for x0, x1 in zip(xs[:-1], xs[1:]):
        for kk in range(3):
            c = x0 + (x1 - x0) * (kk + 0.5) / 3
            ax.add_patch(matplotlib.patches.Arc((c, 5.3), (x1 - x0) / 3, 0.5, theta1=0, theta2=180, lw=1.2))
    for i, x in enumerate(xs):
        ax.plot([x, x], [5.3, 4.8], color="k", lw=1.0); ax.text(x, 4.55, f"X{i + 1}", ha="center", fontsize=9)
    ax.text(0.6, 5.75, "secondary winding (multi-ratio)", fontsize=8)
    # tap chart
    ax.text(8.1, 6.6, "NAMEPLATE TAP CHART", fontsize=9, weight="bold")
    for i, (t, r) in enumerate(taps):
        yy = 6.25 - 0.27 * i
        ax.text(8.2, yy, t, fontsize=8.5); ax.text(9.5, yy, r, fontsize=8.5)
        ax.plot([8.1, 10.5], [yy - 0.08, yy - 0.08], color="0.75", lw=0.5)
    # cores table
    ax.text(0.3, 3.9, "SECONDARY CONNECTIONS (DESIGN)", fontsize=9, weight="bold")
    hdr = ("Core", "Function", "Connect", "Ratio", "Burden / destination")
    xc = (0.3, 1.1, 3.2, 4.3, 5.4)
    for x, h in zip(xc, hdr):
        ax.text(x, 3.55, h, fontsize=8.5, weight="bold")
    for i, row in enumerate(cores):
        for x, v in zip(xc, row):
            ax.text(x, 3.2 - 0.32 * i, v, fontsize=8.5)
    for i, n in enumerate(notes):
        ax.text(0.3, 1.75 - 0.3 * i, n, fontsize=8.2)
    ax.add_patch(Rectangle((7.6, 0.15), 3.2, 1.05, fill=False, lw=1.0))
    ax.text(7.7, 0.95, f"DWG {dwg}   REV {rev}", fontsize=8.5, weight="bold")
    ax.text(7.7, 0.62, "230 kV protection, bay L1", fontsize=8)
    ax.text(7.7, 0.32, "Scale: none    Sheet 1 of 1", fontsize=8)
    return png(fig)


def ct_drawings():
    tapsB = [("X1-X2", "250:5"), ("X2-X3", "400:5"), ("X3-X4", "800:5"), ("X4-X5", "550:5"), ("X1-X3", "650:5"),
             ("X2-X4", "1200:5"), ("X3-X5", "1350:5"), ("X1-X4", "1450:5"), ("X2-X5", "1750:5"), ("X1-X5", "2000:5")]
    coresB = [("1", "Line protection", "X2-X4", "1200:5", "L1-21 relay B, IA/IB/IC"),
              ("2", "Bus differential", "X1-X5", "2000:5", "87B-230 zone 1"),
              ("3", "Metering", "X2-X4", "1200:5", "revenue meter M-L1")]
    notesB = ["Polarity: P1 toward the 230 kV bus (all cores).", "Core 1 tap selected to match the L1 relays at both line ends (1200:5).",
              "Rev C: CT replaced after failure (like-for-like 2000:5 MR, C800), 2026-05."]
    doc = fitz.open()
    image_page(doc, fig_ct("B", "B-E-2214", "C", "CT 52-L1  (3 x single-phase, outdoor, free-standing)",
                           "2000:5 MR  C800  RF 2.0", tapsB, coresB, notesB), landscape=True)
    clean_save(doc, os.path.join(OUT, "SUBB_bay_L1_CT_B-E-2214.pdf"))
    tapsA = [("X1-X2", "100:5"), ("X2-X3", "200:5"), ("X3-X4", "300:5"), ("X4-X5", "600:5"), ("X1-X3", "300:5"),
             ("X2-X4", "500:5"), ("X3-X5", "900:5"), ("X1-X4", "600:5"), ("X2-X5", "1100:5"), ("X1-X5", "1200:5")]
    coresA = [("1", "Line protection", "X1-X5", "1200:5", "L1-21 relay A, IA/IB/IC"),
              ("2", "Bus differential", "X1-X5", "1200:5", "87B-230 zone 2"),
              ("3", "Metering", "X1-X5", "1200:5", "revenue meter M-L1")]
    notesA = ["Polarity: P1 toward the 230 kV bus (all cores).", "Core 1 at full ratio (1200:5).", ""]
    doc = fitz.open()
    image_page(doc, fig_ct("A", "A-E-1107", "B", "CT 52-L1  (3 x single-phase, outdoor, free-standing)",
                           "1200:5 MR  C800  RF 2.0", tapsA, coresA, notesA), landscape=True)
    clean_save(doc, os.path.join(OUT, "SUBA_bay_L1_CT_A-E-1107.pdf"))


# ---------------------------------------------------------------- commissioning records (scanned forms)
def fig_form(sub, date, rows, rnd):
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.set_xlim(0, 8.5); ax.set_ylim(0, 11); ax.axis("off")
    ax.text(0.4, 10.4, f"SUBSTATION {sub}  -  CT SECONDARY CIRCUIT COMMISSIONING RECORD", fontsize=10.5, weight="bold")
    ax.text(0.4, 10.05, f"Form P-14 (rev 3)      Date tested: {date}      Test set: Omicron CPC 100", fontsize=8.5)
    hdr = ("CT / phase", "Core", "Leads landed\n(terminals)", "Polarity", "IR (Mohm)", "Loop R (ohm)", "Ratio\ncheck", "Init.")
    xc = (0.4, 1.7, 2.35, 3.75, 4.6, 5.45, 6.4, 7.25)
    for x, h in zip(xc, hdr):
        ax.text(x, 9.45, h, fontsize=7.6, weight="bold", va="center")
    ax.plot([0.35, 8.1], [9.15, 9.15], color="k", lw=0.8)
    for i, row in enumerate(rows):
        yy = 8.85 - 0.33 * i
        for x, v in zip(xc, row):
            ax.text(x + rnd.uniform(-0.02, 0.02), yy + rnd.uniform(-0.02, 0.02), v, fontsize=8.0, family="DejaVu Sans")
        ax.plot([0.35, 8.1], [yy - 0.15, yy - 0.15], color="0.7", lw=0.5)
    ax.text(0.4, 0.9, "Ratio check: secondary injection compared with the nameplate ratio of the landed tap.  "
            "PASS = within 1 %.\nAll circuits restored and returned to service after test.", fontsize=7.5)
    ax.text(0.4, 0.35, "Tested by: ____J. Okafor____     Witness: ____R. Lindqvist____", fontsize=8)
    return fig


def commissioning():
    rnd = random.Random(1307)
    rowsB = []
    for ct, core, lead, ir in (("52-L1", "1", "X1-X5", 4100), ("52-L1", "2", "X1-X5", 3900), ("52-L1", "3", "X2-X4", 4400),
                               ("52-L2", "1", "X2-X4", 3800), ("52-L2", "2", "X1-X5", 4200), ("52-T1", "1", "X1-X4", 3600)):
        for ph in "ABC":
            rowsB.append((f"{ct} {ph}", core, lead, "OK", str(ir + rnd.randint(-150, 150)),
                          f"{rnd.uniform(0.18, 0.46):.2f}", "PASS", "JO"))
    rowsA = []
    for ct, core, lead, ir in (("52-L1", "1", "X1-X5", 5200), ("52-L1", "2", "X1-X5", 5000), ("52-L1", "3", "X1-X5", 4800),
                               ("52-T2", "1", "X2-X5", 4500)):
        for ph in "ABC":
            rowsA.append((f"{ct} {ph}", core, lead, "OK", str(ir + rnd.randint(-150, 150)),
                          f"{rnd.uniform(0.15, 0.40):.2f}", "PASS", "MT"))
    doc = fitz.open()
    for sub, date, rows in (("A", "2024-03-11", rowsA), ("B", "2026-05-27", rowsB)):
        fig = fig_form(sub, date, rows, rnd)
        data = png(fig, dpi=150)
        image_page(doc, data, top=20)
    clean_save(doc, os.path.join(OUT, "CT_commissioning_records.pdf"))


# ---------------------------------------------------------------- settings calculation
CALC = """230 kV LINE L1 (SUBSTATION A - SUBSTATION B)  -  PROTECTION SETTINGS CALCULATION SUMMARY  (issued 2025-11)

Line data: 80 km, z1 = 0.05 + j0.48 ohm/km  ->  ZL1 = 4.00 + j38.40 = 38.61 ohm at 84.05 deg (primary).
Instrument transformers (both line ends, per design drawings): CT 1200:5 (CTR = 240), VT 230 kV : 115 V (PTR = 2000).
Secondary conversion factor: CTR / PTR = 0.120.

Zone 1 (forward, instantaneous): 80 % of ZL1 = 30.89 ohm primary  ->  3.71 ohm secondary.
Zone 2 (forward, POTT keying and permissive trip): 125 % of ZL1 = 48.26 ohm primary  ->  5.79 ohm secondary.
Zone 3 reverse (Substation B only, blocks echo): must cover the remote zone 2 overreach beyond bus B with a 1.5 margin:
    1.5 x (48.26 - 38.61) = 14.48 ohm primary  ->  1.74 ohm secondary.
Maximum torque angle: 84 deg (all phase mho elements).  Loop current supervision 50PP = 0.50 A secondary.

Scheme: POTT, phase elements, fiber channel 6.25 ms each direction.
Substation B is the weak-source terminal: echo enabled at B (EDPU 1 cycle = 32 samples, EDUR 2 cycles = 64 samples,
EBLK 2 cycles = 64 samples after zone 3 reverse).  Echo disabled at A.

Coordination check: for any fault behind Substation B that Substation A's zone 2 can reach, Substation B's zone 3 reverse
asserts before the echo pickup expires, so B does not echo for external faults beyond bus B.

Ground protection of L1 is a separate directional earth-fault scheme and is not part of this summary.
"""


def calc():
    doc = fitz.open(); text_page(doc, CALC, 8.8)
    clean_save(doc, os.path.join(OUT, "L1_protection_settings_calculation.pdf"))


PATROL = """LINE PATROL REPORT  -  230 kV LINE L2 (SUBSTATION B - SUBSTATION C)

Date: 2026-09-14          Patrol crew: Line crew 4 (ground patrol)          Report time: 17:05

Finding: flashover marks on the insulator strings of phases B and C at tower 18 (suspension tower), with a burnt bird
nest on the crossarm between the two phases. No damage to conductors. No marks on phase A. No contact with ground
or structure found (phase-to-phase flashover).

Location: tower 18 is 6.5 km from Substation B along line L2 (span table L2, chainage 6.50 km).

Action: nest removed, insulators washed and inspected, line L2 released for service at 18:30.
"""


def patrol():
    doc = fitz.open(); text_page(doc, PATROL, 9.5)
    clean_save(doc, os.path.join(OUT, "L2_patrol_report.pdf"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    manual(); oneline(); ct_drawings(); commissioning(); calc(); patrol()
    print(sorted(os.listdir(OUT)))
