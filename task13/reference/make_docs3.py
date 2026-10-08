"""TASK 13 v3 documents. Root cause moved off the routine checklist: relay B's CT tap and polarity are correct; the
breaker-failure relay BF-50 replaced in 2025-02 was terminated in PARALLEL with relay B's current inputs instead of in
series, so relay B receives 0.06 / (0.04 + 0.06) = 0.60 of the CT secondary current. Evidence: the as-built terminal
schedule (terminal numbers) combined with the AC schematic (intended series chain) and the device data sheets (burdens)."""
import os, random, shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import fitz
import make_docs as md
import make_docs2 as md2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "artifact", "bundle3")
md.OUT = OUT; md2.OUT = OUT


def fig_oneline3():
    fig, ax = plt.subplots(figsize=(11, 6.8))
    ax.set_xlim(0, 11); ax.set_ylim(0, 6.8); ax.axis("off")
    for x, lab in ((1.2, "SUBSTATION A\n230 kV"), (5.6, "SUBSTATION B\n230 kV"), (9.8, "SUBSTATION C\n230 kV")):
        ax.plot([x, x], [2.0, 5.0], color="k", lw=4); ax.text(x, 5.25, lab, ha="center", fontsize=9, weight="bold")
    for x in (0.45, 10.55):
        ax.add_patch(Circle((x, 3.5), 0.32, fill=False, lw=1.3)); ax.text(x, 3.5, "~", ha="center", va="center", fontsize=13)
    ax.plot([0.77, 1.2], [3.5, 3.5], color="k", lw=1.2); ax.plot([9.8, 10.23], [3.5, 3.5], color="k", lw=1.2)
    ax.text(0.45, 2.95, "230 kV\nsystem", ha="center", fontsize=7); ax.text(10.55, 2.95, "230 kV\nsystem", ha="center", fontsize=7)
    # transformer T1 at B to 115 kV system
    ax.plot([5.6, 5.0], [3.4, 3.4], color="k", lw=1.2)
    ax.add_patch(Circle((4.78, 3.4), 0.22, fill=False, lw=1.2)); ax.add_patch(Circle((4.48, 3.4), 0.22, fill=False, lw=1.2))
    ax.plot([4.26, 3.9], [3.4, 3.4], color="k", lw=1.2); ax.plot([3.9, 3.9], [2.9, 3.9], color="k", lw=3)
    ax.text(4.63, 2.95, "T1 230/115 kV\n250 MVA", ha="center", fontsize=7); ax.text(3.75, 2.6, "115 kV\nnetwork", ha="center", fontsize=7)

    def brk(x, y):
        ax.add_patch(Rectangle((x - 0.13, y - 0.13), 0.26, 0.26, fill=True, color="k"))

    def ct(x, y, dot_left):
        ax.add_patch(Circle((x, y), 0.14, fill=False, lw=1.2)); ax.plot([x - 0.22 if dot_left else x + 0.22], [y + 0.2], "ko", ms=3.5)
    y = 4.4; y2 = 2.6
    ax.plot([1.2, 5.6], [y, y], color="k", lw=1.5); ax.plot([5.6, 9.8], [y2, y2], color="k", lw=1.5)
    brk(1.75, y); ct(2.2, y, True); brk(5.05, y); ct(4.6, y, False)
    brk(6.15, y2); ct(6.6, y2, True); brk(9.25, y2); ct(8.8, y2, False)
    ax.text(3.4, y + 0.25, "LINE L1   80 km", ha="center", fontsize=9); ax.text(7.7, y2 + 0.25, "LINE L2   50 km", ha="center", fontsize=9)
    for x, yy, lab in ((2.2, y - 0.55, "L1-21 relay A\n(+ BF-50)"), (4.6, y + 0.35, "L1-21 relay B\n(+ BF-50)"), (6.6, y2 - 0.6, "L2-21 Sub B\n(+ BF-50)"),
                       (8.8, y2 - 0.6, "L2-21 Sub C")):
        ax.text(x, yy, lab, ha="center", fontsize=7.2)
    for x, lab in ((1.2, "VT-A 2000:1"), (5.6, "VT-B 2000:1"), (9.8, "VT-C 2000:1")):
        ax.text(x + 0.1, 1.75, lab, fontsize=7)
    ax.annotate("", (4.3, 6.0), (2.5, 6.0), arrowprops=dict(arrowstyle="<->", lw=1.0)); ax.text(3.4, 6.1, "POTT channel L1 (A <-> B)", ha="center", fontsize=8)
    ax.annotate("", (8.5, 6.0), (6.9, 6.0), arrowprops=dict(arrowstyle="<->", lw=1.0)); ax.text(7.7, 6.1, "POTT channel L2 (B <-> C)", ha="center", fontsize=8)
    ax.text(0.25, 0.85, "Line data (both lines, positive and negative sequence): z1 = 0.05 + j0.48 ohm/km.  Line charging negligible.\n"
            "Each line relay takes its voltages from its substation's 230 kV bus VT, so the two relays at Substation B see the same\n"
            "bus voltages.  Filled square = closed breaker.  CT symbol: circle with polarity dot (P1).  Relay current convention: a current\n"
            "entering the CT at P1 is measured as positive (bus into line).  Unit G2 at Substation B retired 2026-04 (removed from drawing).",
            fontsize=7.8)
    ax.set_title("230 kV SYSTEM ONE-LINE (PROTECTION)    DWG S-230-001  REV F", fontsize=10)
    return md.png(fig)


def fig_schematic(bay, dwg, devices):
    """AC current schematic: CT core 1 -> test switch -> devices in series -> star point (design)."""
    fig, ax = plt.subplots(figsize=(11, 7.4))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7.4); ax.axis("off")
    ax.text(0.3, 7.0, f"SUBSTATION B  -  BAY {bay}  -  AC CURRENT SCHEMATIC, CT 52-{bay} CORE 1 (PROTECTION)", fontsize=11, weight="bold")
    ys = {"A": 5.6, "B": 4.6, "C": 3.6}
    for ph, y in ys.items():
        ax.add_patch(Circle((0.8, y), 0.18, fill=False, lw=1.2)); ax.text(0.55, y + 0.28, f"CT {ph}", fontsize=7.5)
        ax.text(1.05, y + 0.12, "X2", fontsize=7); ax.text(1.05, y - 0.32, "X4", fontsize=7)
        ax.plot([0.98, 1.6], [y, y], color="k", lw=1.0)
        ax.add_patch(Rectangle((1.6, y - 0.18), 0.6, 0.36, fill=False, lw=1.0)); ax.text(1.9, y, "TS", ha="center", va="center", fontsize=7)
        x = 2.2
        for dev, tin, tout in devices:
            ax.plot([x, x + 0.5], [y, y], color="k", lw=1.0)
            ax.add_patch(Rectangle((x + 0.5, y - 0.22), 1.5, 0.44, fill=False, lw=1.1))
            ax.text(x + 1.25, y + 0.02, dev, ha="center", va="center", fontsize=7.2)
            ax.text(x + 0.5, y + 0.28, tin[ph], fontsize=6.5); ax.text(x + 1.75, y + 0.28, tout[ph], fontsize=6.5)
            x += 2.0
        ax.plot([x, x + 0.5], [y, y], color="k", lw=1.0); ax.plot([x + 0.5, x + 0.5], [y, 2.8], color="k", lw=1.0)
        ax.plot([0.8, 0.8], [y - 0.18, 2.8 if ph == "C" else y - 0.6], color="k", lw=0.8)
    xe = 2.2 + 2.0 * len(devices) + 0.5
    ax.plot([0.8, xe], [2.8, 2.8], color="k", lw=1.0); ax.text(xe + 0.1, 2.75, "N (star point, earthed at TB)", fontsize=7.5)
    ax.text(0.3, 2.1, "Design: all devices on core 1 are connected in SERIES in each phase (CT X2 -> TS -> device 1 in/out -> device 2 in/out -> N).",
            fontsize=8)
    ax.text(0.3, 1.75, "Tap X2-X4 per relay CTR 240 (1200:5).  Terminal numbers of each device as shown (in / out).", fontsize=8)
    ax.add_patch(Rectangle((7.6, 0.15), 3.2, 1.05, fill=False, lw=1.0))
    ax.text(7.7, 0.95, f"DWG {dwg}   REV A", fontsize=8.5, weight="bold"); ax.text(7.7, 0.62, f"230 kV protection, bay {bay}", fontsize=8)
    ax.text(7.7, 0.32, "Design issue 2023", fontsize=8)
    return md.png(fig)


TIN_21 = {"A": "Z01", "B": "Z03", "C": "Z05"}; TOUT_21 = {"A": "Z02", "B": "Z04", "C": "Z06"}
TIN_BF = {"A": "A1", "B": "B1", "C": "C1"}; TOUT_BF = {"A": "A2", "B": "B2", "C": "C2"}


def schematics():
    doc = fitz.open()
    for bay, dwg, dev in (("L1", "B-E-3301", [("L1-21 line relay", TIN_21, TOUT_21), ("BF-50 breaker fail", TIN_BF, TOUT_BF)]),
                          ("L2", "B-E-3302", [("L2-21 line relay", TIN_21, TOUT_21), ("BF-50 breaker fail", TIN_BF, TOUT_BF)])):
        md.image_page(doc, fig_schematic(bay, dwg, dev), landscape=True)
    md.clean_save(doc, os.path.join(OUT, "SUBB_AC_schematics_B-E-3301_3302.pdf"))


def schedule_rows(bay, parallel):
    tb = f"TB-{bay}"; rows = []
    for k, ph in enumerate("ABC"):
        t = 3 * k + 1
        rows.append((f"CT52{bay}-{ph}:X2", f"{tb}:{t}", "CT secondary, phase " + ph))
        rows.append((f"{tb}:{t}", f"TS-{bay}:{2 * k + 1}", "to test switch"))
        rows.append((f"TS-{bay}:{2 * k + 2}", f"{bay}-21:{TIN_21[ph]}", "relay current in"))
        if parallel:
            rows.append((f"TS-{bay}:{2 * k + 2}", f"BF50-{bay}:{TIN_BF[ph]}", "BF current in"))
            rows.append((f"{bay}-21:{TOUT_21[ph]}", f"{tb}:10", "to star point"))
        else:
            rows.append((f"{bay}-21:{TOUT_21[ph]}", f"BF50-{bay}:{TIN_BF[ph]}", "relay out to BF in"))
        rows.append((f"BF50-{bay}:{TOUT_BF[ph]}", f"{tb}:10", "to star point"))
    rows.append((f"CT52{bay}-A:X4 / B:X4 / C:X4", f"{tb}:10", "CT common (star point)"))
    rows.append((f"{tb}:10", "earth bar E1", "single earth of CT circuit"))
    return rows


def fig_schedule(bay, rev, date, rows, rnd, note):
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.set_xlim(0, 8.5); ax.set_ylim(0, 11); ax.axis("off")
    ax.text(0.4, 10.4, f"SUBSTATION B  -  BAY {bay}  -  CABLE AND TERMINATION SCHEDULE (AS BUILT)", fontsize=10.5, weight="bold")
    ax.text(0.4, 10.05, f"Circuit: CT 52-{bay} core 1, protection      Revision {rev}  {date}      {note}", fontsize=8.3)
    for x, h in zip((0.4, 0.9, 3.0, 5.1), ("#", "From (device:terminal)", "To (device:terminal)", "Function")):
        ax.text(x, 9.5, h, fontsize=8.3, weight="bold")
    ax.plot([0.35, 8.1], [9.3, 9.3], color="k", lw=0.8)
    for i, (a, b, fn) in enumerate(rows):
        yy = 9.0 - 0.36 * i
        for x, v in zip((0.4, 0.9, 3.0, 5.1), (str(i + 1), a, b, fn)):
            ax.text(x + rnd.uniform(-0.015, 0.015), yy + rnd.uniform(-0.015, 0.015), v, fontsize=8.1)
        ax.plot([0.35, 8.1], [yy - 0.15, yy - 0.15], color="0.75", lw=0.5)
    ax.text(0.4, 0.6, "Terminations verified against cable cores at the panel.  Drawing references: AC schematic B-E-33xx, CT details B-E-22xx.",
            fontsize=7.5)
    return md.png(fig, dpi=150)


def schedules():
    rnd = random.Random(33)
    doc = fitz.open()
    for bay, rev, date, par, note in (("L1", "C", "2025-02-12", True, "Rev C: BF-50 replaced"),
                                      ("L2", "B", "2023-04-11", False, ""), ("T1", "B", "2023-04-11", None, "")):
        if par is None:
            rows = []
            for k, ph in enumerate("ABC"):
                rows += [(f"CT52T1-{ph}:X2", f"TB-T1:{3 * k + 1}", "CT secondary, phase " + ph),
                         (f"TB-T1:{3 * k + 1}", f"TS-T1:{2 * k + 1}", "to test switch"),
                         (f"TS-T1:{2 * k + 2}", f"87T:{['I1', 'I3', 'I5'][k]}", "differential in"),
                         (f"87T:{['I2', 'I4', 'I6'][k]}", "TB-T1:10", "to star point")]
            rows += [("CT52T1-A:X5 / B:X5 / C:X5", "TB-T1:10", "CT common (star point)"), ("TB-T1:10", "earth bar E1", "single earth of CT circuit")]
        else:
            rows = schedule_rows(bay, par)
        md.image_page(doc, fig_schedule(bay, rev, date, rows, rnd, note), top=20)
    md.clean_save(doc, os.path.join(OUT, "SUBB_cable_termination_schedules_L1_L2_T1.pdf"))


DATA21 = """L1-21 / L2-21 LINE RELAY  -  TECHNICAL DATA (EXCERPT)

Current inputs (IA, IB, IC):  nominal 5 A;  continuous 15 A;  1 s thermal 500 A.
    Terminals: IA Z01 (in) / Z02 (out), IB Z03 / Z04, IC Z05 / Z06.  Polarity: current entering the "in" terminal is positive.
    Burden: 0.04 ohm per phase, resistive (0.04 ohm x (5 A)^2 = 1.0 VA at nominal current).
    Measuring range: 0.05 A to 100 A, linear; accuracy +/- 1 %.
Voltage inputs (VA, VB, VC):  nominal 67 V phase to neutral (115 V phase to phase);  burden < 0.1 VA.
Sampling: 32 samples per cycle, see the instruction manual for the protection algorithms.
Event storage: 4 oscillography records of 640 samples; the oldest is overwritten first.
Self-supervision: analog input channels are checked continuously for offset and saturation; a failure asserts ALARM.
"""
DATABF = """BF-50 BREAKER FAILURE RELAY (NUMERICAL)  -  TECHNICAL DATA (EXCERPT)

Current inputs (IA, IB, IC):  nominal 5 A;  continuous 10 A;  1 s thermal 300 A.
    Terminals: IA A1 (in) / A2 (out), IB B1 / B2, IC C1 / C2.  Polarity: current entering the "in" terminal is positive.
    Burden: 0.06 ohm per phase, resistive (1.5 VA at nominal current).
Function: retrip and backup trip when a phase current above the 50BF pickup persists after a breaker trip command.
Recording: the BF-50 stores operation records only (no oscillography).
"""


def datasheets():
    doc = fitz.open(); md.text_page(doc, DATA21, 9.0); md.text_page(doc, DATABF, 9.0)
    md.clean_save(doc, os.path.join(OUT, "device_technical_data_L1-21_BF-50.pdf"))


def commissioning3():
    rnd = random.Random(2023)
    books = [("A", "2024-03-11", "MT", [("52-L1", "1", "X1-X5"), ("52-L1", "2", "X1-X5"), ("52-L1", "3", "X1-X5"), ("52-T2", "1", "X2-X5")]),
             ("B", "2023-04-14", "JO", [("52-L1", "1", "X2-X4"), ("52-L1", "2", "X1-X5"), ("52-L1", "3", "X2-X4"),
                                        ("52-L2", "1", "X2-X4"), ("52-L2", "2", "X1-X5"), ("52-L2", "3", "X2-X4")]),
             ("B", "2023-04-15", "JO", [("52-T1", "1", "X2-X5"), ("52-T1", "2", "X1-X5"), ("52-BC", "1", "X1-X5"), ("52-BC", "2", "X2-X4")]),
             ("C", "2023-04-12", "RL", [("52-L2", "1", "X2-X4"), ("52-L2", "2", "X1-X5"), ("52-L2", "3", "X2-X4"), ("52-T3", "1", "X1-X4")])]
    doc = fitz.open()
    for sub, date, ini, cts in books:
        rows = []
        for ctn, core, lead in cts:
            for ph in "ABC":
                rows.append((f"{ctn} {ph}", core, lead, "OK", str(4000 + rnd.randint(-600, 900)), f"{rnd.uniform(0.15, 0.48):.2f}", "PASS", ini))
        md.image_page(doc, md.png(md.fig_form(sub, date, rows, rnd), dpi=150), top=20)
    md.clean_save(doc, os.path.join(OUT, "CT_commissioning_book_A_B_C.pdf"))


MAINT3 = """SUBSTATION B  -  PROTECTION AND CONTROL MAINTENANCE LOG  (extract, 2025-2026)

2025-02-12  BF-50 breaker failure relays, bays L1 and L2: L1 unit replaced (obsolete electromechanical unit -> numerical BF-50).
            Trip output test to breaker 52-L1: PASS.  L2 unit replacement postponed to 2027.
2025-06-03  L1-21 relay B: routine test by secondary injection at the relay test switch with BF-50 isolated by its own test
            switch; element pickups within tolerance: PASS.
2026-01-19  Battery 125 V DC: annual capacity test, PASS.
2026-02-03  87B-230 bus differential: routine test, PASS. No setting change.
2026-03-11  L2-21 (Sub B): routine secondary injection test, PASS.
2026-04-02  Generating unit G2 (connected at Substation B) permanently retired. Substation B becomes a weak source for L1.
2026-05-26  L1-21 relay B: firmware upgraded v3.2 -> v3.4 (vendor service bulletin SB-114, improved event storage).
2026-05-26  L1-21 relay B: settings revision R5 applied per settings calculation 2025-11 (ECHO enabled for weak-source
            terminal; Z3P recalculated 1.80 -> 1.74 ohm sec). Functional check of POTT/echo with relay A by end-to-end test: PASS.
2026-06-14  VT-B secondary MCB replaced (trip-free operation intermittent). Voltage check at L1-21 and L2-21: PASS.
2026-07-30  L1-21 relay B: self-test and event retrieval check, PASS.
2026-08-22  Breaker 52-L2: timing test, 2.9 cycles.
"""


def maint3():
    doc = fitz.open(); md.text_page(doc, MAINT3, 8.8)
    md.clean_save(doc, os.path.join(OUT, "SUBB_PC_maintenance_log_2025_2026.pdf"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(os.path.join(HERE, "..", "artifact", "bundle2")):
        if f.endswith((".cfg", ".dat", ".txt")):
            shutil.copy(os.path.join(HERE, "..", "artifact", "bundle2", f), OUT)
    md.manual()
    doc = fitz.open(); md.image_page(doc, fig_oneline3(), landscape=True); md.clean_save(doc, os.path.join(OUT, "system_one_line_S-230-001.pdf"))
    md2.ct_sets(); commissioning3(); maint3(); md2.calc2(); md.patrol(); schematics(); schedules(); datasheets()
    print(sorted(os.listdir(OUT)))
