"""GRID-14 packet: text specification + raster figures, metadata stripped."""
import io, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "..", "proto", "params.json")))
REVISION = "grid14_v1"
PW, PH = 612, 792
M = 7.5


def fmt_m(cells):
    m = cells * M
    return (f"{m:.0f} m" if m == int(m) else f"{m:.1f} m")


def png(fig, dpi=200):
    b = io.BytesIO(); fig.savefig(b, format="png", dpi=dpi, facecolor="white"); plt.close(fig); return b.getvalue()


def fig_map():
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(-2.6, 8.6); ax.set_ylim(-8.6, 2.6); ax.set_aspect("equal"); ax.axis("off")
    X = [0, 3, 6]; Y = [0, -3, -6]
    for r in range(3):
        ax.plot([-2.2, 8.2], [Y[r], Y[r]], color="0.55", lw=6, solid_capstyle="butt", zorder=1)
    for c in range(3):
        ax.plot([X[c], X[c]], [-8.2, 2.2], color="0.55", lw=6, solid_capstyle="butt", zorder=1)
    for r in range(3):
        for c in range(3):
            ax.add_patch(Rectangle((X[c] - 0.28, Y[r] - 0.28), 0.56, 0.56, color="k", zorder=3))
            ax.text(X[c] + 0.32, Y[r] + 0.32, f"I{3 * r + c}", fontsize=10, weight="bold", zorder=4)
    for r in range(3):
        for c in range(2):
            ax.text((X[c] + X[c + 1]) / 2, Y[r] + 0.22, fmt_m(P['L_EW'][r][c]), ha="center", fontsize=9, zorder=4)
    for r in range(2):
        for c in range(3):
            ax.text(X[c] + 0.2, (Y[r] + Y[r + 1]) / 2, fmt_m(P['L_NS'][r][c]), va="center", fontsize=9, rotation=90, zorder=4)
    for k in range(12):
        if k < 3:
            x, y, tx, ty, rot = X[k], 1.25, X[k], 2.45, 90
        elif k < 6:
            x, y, tx, ty, rot = 7.25, Y[k - 3], 8.45, Y[k - 3], 0
        elif k < 9:
            x, y, tx, ty, rot = X[k - 6], -7.25, X[k - 6], -8.45, 90
        else:
            x, y, tx, ty, rot = -1.25, Y[k - 9], -2.45, Y[k - 9], 0
        ax.text(tx, ty, f"T{k}", ha="center", va="center", fontsize=10, weight="bold")
        dx, dy = (0.25, 0) if rot == 90 else (0, 0.22)
        ax.text(x + dx, y + dy, "in " + fmt_m(P['L_ENTRY'][k]), ha="left" if rot == 90 else "center", va="center",
                fontsize=8.5, rotation=rot, zorder=4)
    ax.set_title("Figure 1. Network map. Each street carries one lane in each direction. Lengths are stop line to stop line\n"
                 "(boundary approaches: terminal to stop line, labelled 'in').  North is up.", fontsize=10)
    return png(fig)


def fig_demand():
    import numpy as np
    fig, ax = plt.subplots(figsize=(11, 5.6))
    x = np.arange(12); w = 0.27
    for i, (s, col) in enumerate((("AM", "#4477aa"), ("PM", "#ccbb44"), ("EVENT", "#aa3377"))):
        v = P["DEMANDS"][s]
        bars = ax.bar(x + (i - 1) * w, v, w, label=s, color=col)
        for b, val in zip(bars, v):
            ax.text(b.get_x() + b.get_width() / 2, val + 4, str(val), ha="center", fontsize=6.6, rotation=90)
    ax.set_xticks(x); ax.set_xticklabels([f"T{k}" for k in range(12)])
    ax.set_ylabel("vehicles per hour entering at the terminal"); ax.set_ylim(0, 460); ax.legend(ncol=3, loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    ax.set_title("Figure 2. Demand by terminal and scenario (value printed above each bar)", fontsize=10)
    return png(fig)


def arrow(ax, x0, y0, x1, y1, lab=None, fs=9):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=14, lw=1.4,
                                 connectionstyle="arc3,rad=0.0"))
    if lab:
        ax.text(x1, y1, lab, fontsize=fs, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.5))


def fig_turns_phases():
    fig, axs = plt.subplots(1, 3, figsize=(13, 5.0), gridspec_kw=dict(width_ratios=[1, 1, 1.5]))
    ns, ew = P["TURN_NS"], P["TURN_EW"]
    for ax, title, inc, outs in (
            (axs[0], "Arrivals from the NORTH\n(same shares for arrivals from the south)", ((0, 2.8), (0, 0.6)),
             [((0, -0.6), (0, -2.6), f"through {ns[1]}%", (0, -2.95)), ((-0.6, 0), (-2.6, 0), f"right {ns[2]}%", (-2.2, 0.35)),
              ((0.6, 0), (2.6, 0), f"left {ns[0]}%", (2.2, 0.35))]),
            (axs[1], "Arrivals from the WEST\n(same shares for arrivals from the east)", ((-2.8, 0), (-0.6, 0)),
             [((0.6, 0), (2.6, 0), f"through {ew[1]}%", (2.2, 0.35)), ((0, -0.6), (0, -2.6), f"right {ew[2]}%", (0.9, -2.3)),
              ((0, 0.6), (0, 2.6), f"left {ew[0]}%", (0.85, 2.3))])):
        ax.set_xlim(-3.2, 3.2); ax.set_ylim(-3.3, 3.2); ax.set_aspect("equal"); ax.axis("off")
        ax.add_patch(Rectangle((-0.6, -0.6), 1.2, 1.2, color="0.8"))
        ax.add_patch(FancyArrowPatch(inc[0], inc[1], arrowstyle="-|>", mutation_scale=16, lw=2.2, color="k"))
        ax.text(inc[0][0] + (0.35 if inc[0][0] == 0 else 0), inc[0][1] + (0 if inc[0][0] == 0 else 0.3), "arriving", fontsize=8)
        for a, b, lab, pos in outs:
            ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=14, lw=1.4, color="0.25"))
            ax.text(pos[0], pos[1], lab, fontsize=9.5, ha="center", va="center")
        ax.text(0, 3.05, "N", ha="center", fontsize=8, color="0.4")
        ax.set_title(title, fontsize=9.5)
    ax = axs[2]; ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.text(0.2, 9.4, "Phases (protected; one movement set at a time)", fontsize=10, weight="bold")
    rows = [("A", "north and south approaches: through and right"), ("B", "north and south approaches: left"),
            ("C", "east and west approaches: through and right"), ("D", "east and west approaches: left")]
    for i, (p, d) in enumerate(rows):
        ax.text(0.4, 8.4 - 0.9 * i, p, fontsize=12, weight="bold"); ax.text(1.2, 8.4 - 0.9 * i, d, fontsize=9.5)
    ax.text(0.2, 4.6, "Sequence within the cycle, from local time 0:", fontsize=10, weight="bold")
    for i, (lab, seq) in enumerate((("lead", "A B C D"), ("lag", "B A D C"))):
        y = 3.6 - 1.2 * i; ax.text(0.4, y + 0.1, lab, fontsize=10)
        x = 1.5
        for p in seq.split():
            ax.add_patch(Rectangle((x, y - 0.25), 1.3, 0.7, fill=False, lw=1.2)); ax.text(x + 0.65, y + 0.1, p, ha="center", fontsize=11)
            ax.add_patch(Rectangle((x + 1.3, y - 0.25), 0.4, 0.7, color="0.75")); x += 1.7
    ax.text(0.2, 0.9, "Each green is followed by an all-red interval (grey), see the text.", fontsize=8.5)
    fig.suptitle("Figure 3. Turning shares and signal phases", fontsize=10)
    return png(fig)


def fig_timing():
    fig, ax = plt.subplots(figsize=(10, 4.8)); ax.axis("off")
    cyc = sorted(int(c) for c in P["GREEN"])
    cols = ["Cycle (s)"] + [f"Plan {p + 1}  (A/B/C/D)" for p in range(6)]
    cells = [[str(c)] + ["/".join(map(str, g)) for g in P["GREEN"][str(c)]] for c in cyc]
    t = ax.table(cellText=cells, colLabels=cols, loc="center", cellLoc="center"); t.scale(1, 1.8); t.set_fontsize(9)
    ax.set_title("Figure 4. Green time of each phase in seconds, by cycle length and timing plan", fontsize=10)
    return png(fig)


def spec_text():
    return f"""GRID-14 ENGINEERING PACKET: SIGNAL COORDINATION ON A 3 x 3 URBAN GRID

1. SCOPE AND DECISION
Nine signalized intersections I0..I8 (Figure 1; I0 is the north-west corner, numbering runs west to east, then north to south) are connected by one-lane-per-direction streets; twelve boundary terminals T0..T11 feed and absorb traffic. A configuration is: the cycle length C (60, 72, 84, 96, 108 or 120 s, common to all intersections), the timing plan (1 to 6, common, Figure 4), the phase order (lead or lag, common, Figure 3) and the offset of each of the nine intersections, each one of 0, C/4, C/2 or 3C/4. That is 6 x 6 x 2 x 4^9 = 18,874,368 configurations. Each configuration is evaluated on three demand scenarios, AM, PM and EVENT (Figure 2). Figures 1 to 4 are normative together with this text.

2. ROAD MODEL
Every link is a single lane divided into cells of 7.5 m; a link's length in cells is its length in metres divided by 7.5. Each street block between two intersections is two links (one per direction) with the length shown in Figure 1. A boundary approach (inbound link, terminal to stop line) has the length labelled 'in' in Figure 1. Every outbound boundary link (intersection to terminal) is 10 cells. Cells of a link are numbered from 0 at its upstream end to n-1 at its downstream end; cell n-1 of a link that ends at an intersection is its stop-line cell. A cell holds at most one vehicle. Vehicles cannot overtake.

3. SIGNALS
Intersection j runs the four phases of Figure 3 in the configured order, each phase's green (Figure 4) followed by a 2 s all-red. With offset o_j, the local time at step t is tau = (t - o_j) mod C, and the first phase of the order starts at tau = 0. A vehicle may cross the stop line only during a green that serves its movement.

4. VEHICLES, DEMAND AND TURNS
Each terminal k keeps a generator x(next) = (1103515245 x + 12345) mod 2^31, starting from x = 1000 + 17 k. At every step t < 3600 the terminals are visited in order T0..T11; each advances its generator once and, if (x div 256) mod 3600 is less than its scenario demand (Figure 2, vehicles per hour), creates one vehicle. Vehicles are numbered 0, 1, 2, ... in creation order within the scenario run; a new vehicle joins the end of its terminal's waiting queue (unbounded, outside the network). Vehicle v has its own generator, starting from y = (2654435761 v + 12345) mod 2^31, of the same form. Whenever a vehicle enters a link that ends at an intersection (its inbound boundary link or a street block), it advances its generator once and chooses its movement at that intersection: with r = (y div 65536) mod 100 and shares (L, T, R) percent for its approach direction (Figure 3), left if r < L, through if r < L + T, right otherwise. Through leaves by the opposite side, right turns to the driver's right, left to the driver's left.

5. STEP ORDER
Steps t = 0, 1, 2, ... last 1 s. In each step: (1) vehicle creation as in Section 4; (2) all movements, decided on the occupancy at the start of the step (after creation): a vehicle in a cell other than the last cell of its link advances one cell if that cell was empty at the start of the step; a vehicle in the last cell of an outbound boundary link leaves the network; a vehicle in a stop-line cell crosses into cell 0 of the link its movement leads to if its movement has green at step t and that cell was empty at the start of the step; the first vehicle of each terminal queue enters cell 0 of its inbound link if that cell was empty at the start of the step. A vehicle moves at most once per step. Every vehicle that moved is in its new cell at the end of the step.

6. RUN END AND METRICS
A scenario run ends at the end of the first step t with t + 1 >= 3600 in which no vehicle is waiting or in the network, or at the end of step 7199, whichever comes first. A vehicle created at step g that leaves the network at step e spends e - g + 1 seconds in the system; a vehicle still waiting or in the network when a run ends at step 7199 spends 7200 - g. Total time in system (TTS) of a scenario run: the sum over its vehicles. The configuration's total TTS: the sum of its AM, PM and EVENT TTS. A configuration gridlocks when at least one of its three runs ends at step 7199 with vehicles still waiting or in the network.

7. BASELINE AND OBJECTIVE
Baseline: C = 84 s, plan 1, lead, all offsets 0. The optimal configuration has the smallest total TTS; ties are broken by smaller C, then smaller plan number, then lead before lag, then the offsets of I0, I1, ..., I8 compared in that order, smaller first."""


def text_page(doc, text, fs):
    p = doc.new_page(width=PW, height=PH)
    rc = p.insert_textbox(fitz.Rect(44, 40, PW - 44, PH - 36), text, fontsize=fs, fontname="helv")
    if rc < 0:
        raise RuntimeError("overflow %s" % rc)


def image_page(doc, data, landscape=False):
    w, h = (PH, PW) if landscape else (PW, PH)
    p = doc.new_page(width=w, height=h)
    img = fitz.open("png", data); iw, ih = img[0].rect.width, img[0].rect.height
    s = min((w - 50) / iw, (h - 60) / ih); x0 = (w - iw * s) / 2
    p.insert_image(fitz.Rect(x0, 30, x0 + iw * s, 30 + ih * s), stream=data)


def main():
    doc = fitz.open()
    t = spec_text(); cut = t.index("5. STEP ORDER")
    text_page(doc, t[:cut], 8.8); text_page(doc, t[cut:], 8.8)
    image_page(doc, fig_map()); image_page(doc, fig_demand(), landscape=True)
    image_page(doc, fig_turns_phases(), landscape=True); image_page(doc, fig_timing(), landscape=True)
    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    tmp = os.path.join(HERE, ".tmp.pdf"); doc.save(tmp, garbage=4, deflate=True, clean=True); doc.close()
    d = fitz.open(tmp); d.xref_set_key(-1, "Info", "null"); d.xref_set_key(-1, "ID", "null")
    cat = d.pdf_catalog(); pages = d.xref_get_key(cat, "Pages")[1]
    d.update_object(cat, "<< /Type /Catalog /Pages %s >>" % pages)
    out = os.path.join(HERE, f"{REVISION}.pdf"); d.save(out, garbage=4, deflate=True, clean=True, no_new_id=True); d.close(); os.remove(tmp)
    raw = open(out, "rb").read(); i = raw.find(b"% Written by")
    if i != -1:
        j = raw.find(b"\n", i); raw = raw[:i] + b"%" + b" " * (j - i - 1) + raw[j:]; open(out, "wb").write(raw)
    print("wrote", out)


if __name__ == "__main__":
    main()
