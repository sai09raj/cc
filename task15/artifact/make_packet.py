"""FIRE-15 packet: text specification + raster figures, metadata stripped."""
import io, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "..", "proto", "params.json")))
REVISION = "fire15_v1"
PW, PH = 612, 792
COL = {"W": "#9ecae1", "R": "#bdbdbd", "G": "#e6e28a", "B": "#a6cf7a", "T": "#4f8f4a", "H": "#e8956b"}
NAME = {"W": "water", "R": "rock", "G": "grass", "B": "brush", "T": "timber", "H": "houses"}
DIRN = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
SPD = ["calm", "moderate", "strong"]


def png(fig, dpi=200):
    b = io.BytesIO(); fig.savefig(b, format="png", dpi=dpi, facecolor="white"); plt.close(fig); return b.getvalue()


def fig_map():
    fig = plt.figure(figsize=(10, 12.2))
    ax = fig.add_axes([0.07, 0.25, 0.88, 0.70])
    B = P["BLOCK"]
    for by, row in enumerate(P["BLOCKS"]):
        for bx, ch in enumerate(row):
            ax.add_patch(Rectangle((bx * B, by * B), B, B, facecolor=COL[ch], edgecolor="0.35", lw=0.6))
            ax.text(bx * B + B / 2, by * B + B / 2, ch, ha="center", va="center", fontsize=9.5,
                    color="white" if ch == "T" else "black", weight="bold")
    for i, (x, y) in enumerate(P["STATIONS"]):
        ax.plot(x + 0.5, y + 0.5, marker="o", ms=9, mfc="red", mec="black", mew=1.2, zorder=5)
        ax.text(x + 2.2, y - 1.4, f"S{i + 1}", fontsize=10, weight="bold", color="black", zorder=6,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))
    ax.set_xlim(0, 128); ax.set_ylim(128, 0); ax.set_aspect("equal")
    ax.set_xticks(range(0, 129, 8)); ax.set_yticks(range(0, 129, 8))
    ax.tick_params(labelsize=8, top=True, labeltop=True)
    ax.set_xlabel("x (cells, west to east)"); ax.set_ylabel("y (cells, north to south)")
    ax.set_title("Figure 1. Landscape: 16 x 16 blocks of 8 x 8 cells (cell = 15 m). North is up.\n"
                 "Letters: W water, R rock (do not burn); G grass, B brush, T timber, H houses (burn).", fontsize=10)
    ax2 = fig.add_axes([0.07, 0.02, 0.88, 0.17]); ax2.axis("off")
    cells = [[f"S{i + 1}", str(x), str(y)] for i, (x, y) in enumerate(P["STATIONS"])]
    half = (len(cells) + 1) // 2
    rows = [cells[i] + (cells[i + half] if i + half < len(cells) else ["", "", ""]) for i in range(half)]
    t = ax2.table(cellText=rows, colLabels=["Station", "x", "y", "Station", "x", "y"], loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.scale(1, 1.25); t.set_fontsize(9)
    ax2.set_title("Candidate stations (cell coordinates; the red dot marks the station cell)", fontsize=9.5)
    return png(fig)


def fig_params():
    fig = plt.figure(figsize=(11, 7.6))
    a1 = fig.add_axes([0.03, 0.55, 0.44, 0.36]); a1.axis("off")
    rows = [[NAME[k] + f" ({k})", str(P["BURN"][k]), str(P["BASE"][k])] for k in "GBTH"]
    t = a1.table(cellText=rows, colLabels=["Cover", "Burn time (steps)", "Base (per mille)"], loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.scale(1, 1.7); t.set_fontsize(10); a1.set_title("(a) Burnable covers", fontsize=10)
    a2 = fig.add_axes([0.52, 0.55, 0.45, 0.36]); a2.axis("off")
    rows = [[s] + [str(v) for v in P["WF"][s]] for s in SPD]
    t = a2.table(cellText=rows, colLabels=["Speed class", "angle 0", "angle 1", "angle 2", "angle 3", "angle 4"], loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.scale(1, 1.7); t.set_fontsize(10)
    a2.set_title("(b) Wind factor (percent) by angle in 45-degree steps\nbetween spread direction and wind-toward direction", fontsize=10)
    a3 = fig.add_axes([0.03, 0.10, 0.44, 0.34]); a3.axis("off")
    rows = [[s, str(P["SEED"][s]), str(P["RATE"][s])] for s in "ABCD"]
    t = a3.table(cellText=rows, colLabels=["Scenario", "Seed", "Strike rate (per mille)"], loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.scale(1, 1.7); t.set_fontsize(10); a3.set_title("(c) Lightning by scenario", fontsize=10)
    a4 = fig.add_axes([0.52, 0.10, 0.45, 0.34]); a4.axis("off")
    rows = [["Diagonal factor (NE, SE, SW, NW)", f"{P['DIAG']} %"], ["Report delay after ignition", f"{P['DET']} steps"],
            ["Lightning steps", f"0 to {P['T_LIGHT'] - 1}"], ["Last step", str(P["T_END"] - 1)],
            ["Wind period", f"{P['PERIOD']} steps"], ["House weight in loss", str(P["HOUSE_W"])]]
    t = a4.table(cellText=rows, colLabels=["Constant", "Value"], loc="center", cellLoc="center", colWidths=[0.66, 0.34])
    t.auto_set_font_size(False); t.scale(1, 1.5); t.set_fontsize(10); a4.set_title("(d) Other constants", fontsize=10)
    fig.suptitle("Figure 2. Fire and lightning parameters (one step = one minute)", fontsize=11)
    return png(fig)


def fig_wind():
    fig, ax = plt.subplots(figsize=(11, 6.4))
    ax.set_xlim(-0.75, 8.6); ax.set_ylim(4.3, -0.6); ax.axis("off")
    for p in range(8):
        ax.text(p + 1.05, -0.3, f"period {p + 1}\nsteps {p * 120}-{p * 120 + 119}", ha="center", fontsize=8.5)
    vec = [(0, -1), (0.707, -0.707), (1, 0), (0.707, 0.707), (0, 1), (-0.707, 0.707), (-1, 0), (-0.707, -0.707)]
    for i, s in enumerate("ABCD"):
        y = i + 0.55
        ax.text(-0.7, y, f"Scenario {s}", fontsize=10, weight="bold", va="center")
        for p, (d, sp) in enumerate(P["WIND"][s]):
            cx = p + 1.05
            ax.add_patch(Rectangle((cx - 0.47, y - 0.45), 0.94, 0.9, fill=False, ec="0.6"))
            dx, dy = vec[d]; L = 0.12 + 0.08 * sp
            ax.add_patch(FancyArrow(cx - dx * L, y - 0.08 - dy * L, 2 * dx * L, 2 * dy * L, width=0.02 + 0.015 * sp,
                                    head_width=0.09, head_length=0.07, length_includes_head=True, color="k"))
            ax.text(cx, y + 0.33, f"{DIRN[d]}  {SPD[sp]}", ha="center", fontsize=8)
    ax.set_title("Figure 3. Wind by scenario and period. Arrows point the way the wind blows toward (north is up);\n"
                 "the label gives that direction and the speed class.", fontsize=10)
    return png(fig)


def fig_crews():
    fig, ax = plt.subplots(figsize=(9, 4.0)); ax.axis("off")
    rows = [[f"Crew {k + 1}", str(s), str(c)] for k, (s, c) in enumerate(P["CREWS"])]
    t = ax.table(cellText=rows, colLabels=["Crew", "Speed (cells per step)", "Capacity (cells put out per step)"], loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.scale(1, 1.6); t.set_fontsize(10)
    ax.set_title("Figure 4. Initial-attack crews", fontsize=10)
    return png(fig)


def spec_text():
    return """FIRE-15 ENGINEERING PACKET: STATIONING INITIAL-ATTACK CREWS FOR A LIGHTNING DAY

1. DECISION
A district fire agency stations seven initial-attack crews (Figure 4) for a lightning day. Each crew is based at one of the 14 candidate stations S1..S14 (Figure 1); several crews may share a station. A plan gives the station of each crew 1..7, so there are 14^7 = 105,413,504 plans. Each plan is evaluated on four scenarios A, B, C and D (Figures 2 and 3). Figures 1 to 4 are normative together with this text. All quantities are integers and every rule is exact.

2. LANDSCAPE
The district is a 128 x 128 grid of 15 m cells; cell (x, y) has x = 0..127 from west to east and y = 0..127 from north to south. "Row-major order" means by y, then by x, smallest first. Figure 1 divides the grid into 16 x 16 blocks of 8 x 8 cells; block (bx, by) holds the cells with x div 8 = bx and y div 8 = by, and every cell of a block has the block's cover. Water and rock do not burn; grass, brush, timber and houses burn. Distances are Manhattan distances |dx| + |dy| in cells.

3. GENERATORS AND WEATHER
All random numbers come from the generator x(next) = (1103515245 x + 12345) mod 2^31; each draw advances a generator once and uses the new value. Each scenario has a lightning generator seeded with the scenario's seed s and a spread generator seeded with 7 s + 1 (Figure 2c). The wind is constant within each period of 120 steps (Figure 3).

4. ONE TIME STEP t (t = 0, 1, 2, ...), IN THIS ORDER
Phase 1, lightning. If t is below 480, draw L from the lightning generator. If (L div 256) mod 1000 is below the scenario's strike rate, draw X and then Y from the same generator; the strike hits cell ((X div 256) mod 128, (Y div 256) mod 128). A strike on a burnable cell that has never been ignited starts a new fire there: fires are numbered 1, 2, 3, ... in the order they start, the cell starts burning with its cover's burn time (Figure 2a), and t is the fire's ignition step. Any other strike does nothing.

Phase 2, spread. Take the cells burning at this point in row-major order. For each, visit its eight neighbours in the order N, NE, E, SE, S, SW, W, NW (N is y - 1, E is x + 1). A neighbour is eligible if it is on the grid, burnable and never ignited (not burning, not burnt and not marked earlier in this phase). For each eligible neighbour, and only for eligible ones, draw R from the spread generator and let r = (R div 65536) mod 1000. The chance in per mille is p = floor(base x factor / 100), with the base of the neighbour's cover (Figure 2a) and the wind factor (Figure 2b) for the current speed class and the angle: the number of 45-degree steps (0 to 4) between the spread direction (from the burning cell to the neighbour) and the direction the wind blows toward. For a diagonal neighbour (NE, SE, SW, NW) then p = floor(p x 70 / 100). If r < p the neighbour is marked: it joins the burning cell's fire and starts burning at the end of this step.

Phase 3, crews, taken in crew order 1..7. First, a travelling crew whose arrival step is t or earlier arrives: it stands on its fire's ignition cell and is working; a returning crew whose return step is t or earlier is back at its station and available. Then a working crew puts out up to its capacity of cells (Figure 4), one at a time: each time it takes the burning cell of its own fire nearest to where it stands (ties go to the first in row-major order), puts it out (the cell is burnt and stops burning) and stands on that cell. Marked cells are not burning yet and cannot be put out.

Phase 4, burning. Every cell still burning loses one step of remaining burn time and is burnt when it reaches zero. Then every marked cell starts burning with its cover's burn time.

Phase 5, release. A working crew whose fire has no burning cell left starts returning; its return step is t + 1 + ceil(d / speed), with d the distance from where it stands to its station.

Phase 6, dispatch. A fire is reported at its ignition step + 10. Go through the fires in number order. A fire is dispatched if t is at least its report step, it has had no crew yet and it still has a burning cell: it gets the available crew with the smallest travel time ceil(d / speed), d the distance from the crew's station to the fire's ignition cell (ties go to the lower crew number), and that crew becomes travelling with arrival step t + 1 + travel time. If no crew is available, dispatching stops for this step. Each fire gets at most one crew. A crew is available only while it is at its station with no fire; at step 0 every crew is available at its station.

5. RUN END AND LOSS
A scenario run ends after step t if t + 1 = 960, or if t + 1 >= 480 and no cell is burning. The burnt cells of a run are all cells that ever burned, including cells put out and cells still burning at the end. Scenario loss = burnt cells + 9 x burnt cells whose cover is houses. A plan's total loss is the sum of its losses in scenarios A, B, C and D.

6. BASELINE AND OBJECTIVE
Baseline plan (current stationing): crews 1..7 at S1, S4, S5, S8, S9, S12, S13. The optimal plan has the smallest total loss; ties go to the plan with the smaller station number for crew 1, then for crew 2, and so on up to crew 7."""


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
    t = spec_text(); cut = t.index("Phase 2, spread.")
    text_page(doc, t[:cut], 9.0); text_page(doc, t[cut:], 9.0)
    image_page(doc, fig_map()); image_page(doc, fig_params(), landscape=True)
    image_page(doc, fig_wind(), landscape=True); image_page(doc, fig_crews(), landscape=True)
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
