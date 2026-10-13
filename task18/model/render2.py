"""HOLLOWAY-18 v2 drawings: framing plans (lines B, C, D) and the column schedule / bracing elevations."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import frame as F

X = F.GRID_X; LY = F.LINE_Y; Y = F.LEVEL_Y
BEAMS = {"B": F.BEAM_B, "C": {k: v[0] for k, v in F.BEAM.items()}, "D": F.BEAM_D}
SIMPLE = {"B": F.SIMPLE_B, "C": F.SIMPLE_C, "D": F.SIMPLE_D}
LVNAME = {"L1": "LEVEL L1", "L2": "LEVEL L2", "L3": "LEVEL L3", "R": "ROOF"}
YS = 0.62   # plan drawing scale in y (lines drawn closer than true, not to scale)

def fig_page(title, sheet):
    fig = plt.figure(figsize=(11, 8.5), dpi=300)
    fig.text(0.5, 0.968, title, ha="center", va="center", fontsize=12, weight="bold")
    fig.text(0.96, 0.02, f"sheet {sheet} of 5", ha="right", fontsize=8)
    fig.text(0.04, 0.02, "Holloway Road extension - not to be scaled, use dimensions", ha="left", fontsize=8)
    return fig

def hdim(ax, x1, x2, y, text, fs=8):
    ax.annotate("", (x1, y), (x2, y), arrowprops=dict(arrowstyle="<|-|>", lw=0.6, mutation_scale=6, shrinkA=0, shrinkB=0))
    for x in (x1, x2): ax.plot([x, x], [y - 0.25, y + 0.25], color="k", lw=0.5)
    ax.text((x1 + x2) / 2, y + 0.15, text, ha="center", va="bottom", fontsize=fs)

def vdim(ax, x, y1, y2, text, fs=8):
    ax.annotate("", (x, y1), (x, y2), arrowprops=dict(arrowstyle="<|-|>", lw=0.6, mutation_scale=6, shrinkA=0, shrinkB=0))
    for y in (y1, y2): ax.plot([x - 0.25, x + 0.25], [y, y], color="k", lw=0.5)
    ax.text(x - 0.2, (y1 + y2) / 2, text, ha="right", va="center", fontsize=fs, rotation=90)

def plan(ax, lvl):
    py = {l: -LY[l] * YS for l in LY}          # B at top
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-4.2, 25.2); ax.set_ylim(py["D"] - 3.6, py["B"] + 2.4)
    for g, x in X.items():
        ax.plot([x, x], [py["D"] - 1.1, py["B"] + 1.0], color="0.6", lw=0.4, ls=(0, (8, 3, 1, 3)))
        ax.add_patch(Circle((x, py["B"] + 1.5), 0.42, fill=False, lw=0.8)); ax.text(x, py["B"] + 1.5, g, ha="center", va="center", fontsize=9)
    for l, y in py.items():
        ax.plot([-1.1, X["4"] + 1.1], [y, y], color="0.6", lw=0.4, ls=(0, (8, 3, 1, 3)))
        ax.add_patch(Circle((-1.6, y), 0.42, fill=False, lw=0.8)); ax.text(-1.6, y, l, ha="center", va="center", fontsize=9)
        for a, b in zip("123", "234"):
            ax.plot([X[a], X[b]], [y, y], color="k", lw=2.0, solid_capstyle="butt")
            ax.text((X[a] + X[b]) / 2, y + 0.18, BEAMS[l][(lvl, f"{a}-{b}")], ha="center", va="bottom", fontsize=6.6, zorder=9, bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))
        for (sl, bay, gend) in SIMPLE[l]:
            if sl != lvl: continue
            a, b = bay.split("-"); off = 0.38 if gend == a else -0.38
            ax.add_patch(Circle((X[gend] + off, y), 0.14, facecolor="white", edgecolor="k", lw=0.8, zorder=5))
    for g, x in X.items():
        ax.plot([x, x], [py["D"], py["B"]], color="0.35", lw=0.9)            # ties
        for l, y in py.items():
            ax.add_patch(Rectangle((x - 0.17, y - 0.17), 0.34, 0.34, facecolor="k", zorder=6))
    for a, b in zip("123", "234"):
        hdim(ax, X[a], X[b], py["D"] - 2.2, f"{round((X[b] - X[a]) * 1000)}")
    vdim(ax, -2.9, py["C"], py["B"], f"{round((LY['C'] - LY['B']) * 1000)}")
    vdim(ax, -2.9, py["D"], py["C"], f"{round((LY['D'] - LY['C']) * 1000)}")
    load = F.AREA[lvl]; lname = "roof load" if lvl == "R" else "floor load"
    ax.text(-4.0, py["D"] - 3.3, f"{LVNAME[lvl]} FRAMING PLAN   {lname} {load:.1f} kN/m² on all bays   ties on grid lines 1-4: {F.TIE}",
            fontsize=7.6, weight="bold", ha="left", va="bottom")
    if lvl == F.STORAGE["level"]:
        s = F.STORAGE; x0, x1 = X["2"] + s["a"], X["2"] + s["b"]
        y0, y1 = py["C"] - (LY["D"] - LY["C"]) / 2 * YS, py["C"] + (LY["C"] - LY["B"]) / 2 * YS
        g = 0.32   # keep the hatch clear of the beam line and its label
        ax.add_patch(Rectangle((x0, y0), x1 - x0, py["C"] - g - y0, facecolor="none", hatch="////", edgecolor="0.45", lw=0.6))
        ax.add_patch(Rectangle((x0, py["C"] + g + 0.42), x1 - x0, y1 - py["C"] - g - 0.42, facecolor="none", hatch="////", edgecolor="0.45", lw=0.6))
        for yy in (y0, y1): ax.plot([x0, x1], [yy, yy], color="0.25", lw=0.6)
        for xx in (x0, x1): ax.plot([xx, xx], [y0, y1], color="0.25", lw=0.6, ls=(0, (3, 2)))
        ax.text(x1 + 0.2, y0 + 0.2, f"storage zone S +{s['q']:.1f} kN/m²\n(full width of the frame C load strip)", fontsize=6.4, va="bottom")
        hdim(ax, X["2"], x0, y0 - 0.55, f"{round(s['a'] * 1000)}", fs=6.8); hdim(ax, x0, x1, y0 - 0.55, f"{round((s['b'] - s['a']) * 1000)}", fs=6.8)
    if lvl == "R":
        p = F.PLANT
        for tag, a, ls in (("T", F.PLANT_TEMP_A, "-"), ("F", p["a"], "--")):
            x = X["3"] + a
            ax.add_patch(Rectangle((x - 0.45, py["C"] - 0.75), 0.9, 0.6, fill=False, lw=0.8, ls=ls, zorder=7))
            ax.text(x, py["C"] - 0.45, tag, ha="center", va="center", fontsize=7.5, weight="bold", zorder=8)
        hdim(ax, X["3"], X["3"] + F.PLANT_TEMP_A, py["C"] - 1.25, f"{round(F.PLANT_TEMP_A * 1000)}", fs=6.8)
        hdim(ax, X["3"] + F.PLANT_TEMP_A, X["3"] + p["a"], py["C"] - 1.25, f"{round((p['a'] - F.PLANT_TEMP_A) * 1000)}", fs=6.8)
        ax.text(X["4"] + 0.9, py["C"] - 0.6, f"AHU-2 {p['P']:.0f} kN on line C beam\nT temporary position\nF final position", fontsize=6.4, va="center")
        a1 = F.AHU1; x = X["2"] + a1["a"]
        ax.add_patch(Rectangle((x - 0.45, py["D"] - 0.75), 0.9, 0.6, fill=False, lw=0.8)); ax.text(x, py["D"] - 0.45, "AHU-1", ha="center", va="center", fontsize=5.6)
        hdim(ax, X["2"], x, py["D"] - 1.25, f"{round(a1['a'] * 1000)}", fs=6.8)
        ax.text(x + 0.7, py["D"] - 0.45, f"AHU-1 {a1['P']:.0f} kN on line D beam", fontsize=6.4, va="center")

def plans(path, levels, sheet):
    fig = fig_page(f"FRAMING PLANS - {LVNAME[levels[0]]} AND {LVNAME[levels[1]]}", sheet)
    for i, l in enumerate(levels):
        ax = fig.add_axes([0.03, 0.52 - i * 0.47, 0.94, 0.42]); plan(ax, l)
    fig.text(0.04, 0.045, "Legend: ■ column   ○ simple connection at this beam end (other beam ends rigid)   beam labels are written above the beam they describe",
             fontsize=7.2)
    fig.savefig(path, dpi=300); plt.close(fig)

def schedule(path):
    fig = fig_page("COLUMN SCHEDULE, BRACING ELEVATIONS AND WIND", 5)
    ax = fig.add_axes([0.03, 0.08, 0.44, 0.84]); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 16)
    hdr = ["Column", "Below splice", "Splice", "Above splice", "Base"]; cx = [0.2, 1.5, 4.25, 5.85, 8.6]
    for x, h in zip(cx, hdr): ax.text(x, 15.2, h, fontsize=7.6, weight="bold")
    ax.plot([0.1, 9.9], [15.0, 15.0], color="k", lw=0.8)
    rows = sorted(F.COLSCHED.items())
    for i, (m, (lo, sl, sh, up, base)) in enumerate(rows):
        y = 14.4 - i * 1.0
        for x, t in zip(cx, [m, lo, f"{sl} + {round(sh * 1000)}", up, {"pin": "pinned", "fixed": "fixed"}[base]]):
            ax.text(x, y, t, fontsize=7.6, va="center")
        ax.plot([0.1, 9.9], [y - 0.5, y - 0.5], color="0.6", lw=0.4)
    ax.text(0.2, 1.6, "Splice: height above the level shown, on the column centreline.\nColumn mark = frame line / grid line.", fontsize=7, va="top")
    for k, line in enumerate(("C", "D")):
        ex = fig.add_axes([0.49 + k * 0.255, 0.36, 0.25, 0.56]); ex.axis("off"); ex.set_aspect("equal")
        ex.set_xlim(-4.5, 24); ex.set_ylim(-2.5, 19)
        for g, x in X.items():
            ex.plot([x, x], [0, Y["R"]], color="k", lw=1.2)
            ex.text(x, Y["R"] + 1.2, g, ha="center", fontsize=7)
        for l in list(Y)[1:]:
            ex.plot([0, X["4"]], [Y[l], Y[l]], color="k", lw=1.2)
            ex.text(X["4"] + 0.5, Y[l], l, fontsize=6.5, va="center")
        brs = F.BRACE if line == "C" else F.BRACE_D; sec = F.BRACE_SEC if line == "C" else F.BRACE_D_SEC
        for bid, (ga, la), (gb, lb) in brs:
            ex.plot([X[ga], X[gb]], [Y[la], Y[lb]], color="k", lw=0.9)
            ex.text((X[ga] + X[gb]) / 2 + 0.3, (Y[la] + Y[lb]) / 2 - 0.5, bid, fontsize=6.5)
        ex.text(X["2"], -1.6, f"ELEVATION ON LINE {line}\nbraces {sec}, pin-ended", ha="center", va="top", fontsize=6.8, weight="bold")
        if line == "C":
            for a, b in zip(list(Y), list(Y)[1:]):
                vdim(ex, -1.6, Y[a], Y[b], f"{round((Y[b] - Y[a]) * 1000)}", fs=7.5)
            ex.text(-1.6, 17.3, "storey heights", fontsize=6, ha="center")
    wx = fig.add_axes([0.52, 0.08, 0.44, 0.22]); wx.axis("off"); wx.set_xlim(0, 10); wx.set_ylim(0, 5)
    wx.text(0, 4.6, "WIND ON FRAME C\nhorizontal point loads at the grid 1 joints of line C, acting towards grid 4", fontsize=7.4, weight="bold", va="top")
    for i, l in enumerate(("L1", "L2", "L3", "R")):
        wx.text(0.2 + i * 2.4, 2.8, f"{ {'R': 'roof'}.get(l, l)}: {F.WIND[l]:.0f} kN", fontsize=8)
    wx.text(0, 1.6, "Bracing elevations show bracing and levels only; member sizes are on the\nframing plans and the column schedule.", fontsize=7, va="top")
    fig.savefig(path, dpi=300); plt.close(fig)

if __name__ == "__main__":
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
    plans(f"{d}/v2_s3.png", ("L1", "L2"), 3); plans(f"{d}/v2_s4.png", ("L3", "R"), 4); schedule(f"{d}/v2_s5.png")
