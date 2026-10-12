"""Render sheet 3 (frame elevation) and sheet 4 (loading diagram) for HOLLOWAY-18 from frame.py."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle
import frame as F

X, Y = F.GRID_X, F.LEVEL_Y
LV = list(Y)
def ysp(g): return Y[F.SPLICE[g][0]] + F.SPLICE[g][1]

def base_fig(title, sheet):
    fig = plt.figure(figsize=(11, 8.5), dpi=300)
    ax = fig.add_axes([0.04, 0.05, 0.92, 0.88]); ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-4.6, 25.6); ax.set_ylim(-3.4, 18.6)
    fig.text(0.5, 0.965, title, ha="center", va="center", fontsize=12, weight="bold")
    fig.text(0.96, 0.02, f"sheet {sheet} of 4", ha="right", fontsize=8)
    fig.text(0.04, 0.02, "Holloway Road extension - frame C - not to be scaled, use dimensions", ha="left", fontsize=8)
    return fig, ax

def grids(ax, lw_member=2.6, col="k"):
    for g, x in X.items():
        ax.plot([x, x], [-0.9, Y["R"] + 1.1], color="0.55", lw=0.5, ls=(0, (8, 3, 1, 3)))
        ax.add_patch(Circle((x, Y["R"] + 1.55), 0.42, fill=False, lw=0.9)); ax.text(x, Y["R"] + 1.55, g, ha="center", va="center", fontsize=11)
    for l in LV[1:]:
        ax.text(X["4"] + 2.6, Y[l], {"R": "ROOF", "L1": "L1", "L2": "L2", "L3": "L3"}[l], ha="left", va="center", fontsize=10, weight="bold")
        ax.plot([X["4"] + 0.4, X["4"] + 2.4], [Y[l]] * 2, color="0.55", lw=0.5, ls=(0, (8, 3, 1, 3)))
    ax.text(X["4"] + 2.6, 0, "G (base)", ha="left", va="center", fontsize=10, weight="bold")

def frame_lines(ax, lw=2.6, color="k", braces=True):
    for g, x in X.items():
        ax.plot([x, x], [0, Y["R"]], color=color, lw=lw, solid_capstyle="butt")
    for (l, bay) in F.BEAM:
        a, b = bay.split("-"); ax.plot([X[a], X[b]], [Y[l]] * 2, color=color, lw=lw, solid_capstyle="butt")
    if braces:
        for bid, (ga, la), (gb, lb) in F.BRACE:
            ax.plot([X[ga], X[gb]], [Y[la], Y[lb]], color=color, lw=1.3)

def hdim(ax, x1, x2, y, text, fs=9, ext=None):
    ax.annotate("", (x1, y), (x2, y), arrowprops=dict(arrowstyle="<|-|>", lw=0.7, mutation_scale=7, shrinkA=0, shrinkB=0))
    for x in (x1, x2): ax.plot([x, x], [y - 0.18, y + 0.18 if ext is None else ext], color="k", lw=0.5)
    ax.text((x1 + x2) / 2, y + 0.12, text, ha="center", va="bottom", fontsize=fs)

def vdim(ax, x, y1, y2, text, fs=9, side=-1):
    ax.annotate("", (x, y1), (x, y2), arrowprops=dict(arrowstyle="<|-|>", lw=0.7, mutation_scale=7, shrinkA=0, shrinkB=0))
    for y in (y1, y2): ax.plot([x - 0.18, x + 0.18], [y, y], color="k", lw=0.5)
    ax.text(x + side * 0.14, (y1 + y2) / 2, text, ha="right" if side < 0 else "left", va="center", fontsize=fs, rotation=90)

def elevation(path):
    fig, ax = base_fig("FRAME C - ELEVATION ON GRID LINE C", 3)
    grids(ax); frame_lines(ax)
    # storey dimensions (left) and bay dimensions (below)
    for a, b in zip(LV, LV[1:]):
        vdim(ax, X["1"] - 2.3, Y[a], Y[b], f"{round((Y[b] - Y[a]) * 1000)}", fs=10)
    for a, b in zip("123", "234"):
        hdim(ax, X[a], X[b], -2.2, f"{round((X[b] - X[a]) * 1000)}", fs=10)
    hdim(ax, X["1"], X["4"], -3.05, f"{round((X['4'] - X['1']) * 1000)}", fs=9)
    # splices: symbol and its own dimension on every column
    for g, x in X.items():
        sl, sh = F.SPLICE[g]; ys_ = ysp(g)
        ax.plot([x - 0.28, x + 0.28], [ys_ + 0.05] * 2, color="k", lw=1.0); ax.plot([x - 0.28, x + 0.28], [ys_ - 0.05] * 2, color="k", lw=1.0)
        vdim(ax, x - 0.85, Y[sl], ys_, f"{round(sh * 1000)}", fs=7.5)
    # column labels: one per length between floor / splice / base, written beside the column (right side);
    # the short length between a floor and the splice above it is labelled on the left with a leader
    for g, x in X.items():
        low, up = F.COL[g]; sl = F.SPLICE[g][0]; ys_ = ysp(g)
        pts = []
        for l in LV:
            pts.append((l, Y[l]))
            if l == sl: pts.append(("SP", ys_))
        for (a, ya), (b, yb) in zip(pts, pts[1:]):
            sec = low if yb <= ys_ + 1e-9 else up
            xt = x + 0.22
            if b == "SP":
                xl = x - 0.22; yt = Y[sl] - 0.25
                ax.annotate("", (x - 0.03, (ya + yb) / 2), (xl - 0.1, yt + 0.05), arrowprops=dict(arrowstyle="-", lw=0.5, shrinkA=0, shrinkB=0))
                ax.text(xl, yt, sec, rotation=90, ha="right", va="top", fontsize=7.2)
            elif a == "SP":
                ax.text(xt, ya + 0.25, sec, rotation=90, ha="left", va="bottom", fontsize=7.2)
            else:
                ax.text(xt, (ya + yb) / 2, sec, rotation=90, ha="left", va="center", fontsize=7.2)
    # beam labels
    for (l, bay), (sec, cl, cr) in F.BEAM.items():
        a, b = bay.split("-"); ax.text((X[a] + X[b]) / 2, Y[l] + 0.16, sec, ha="center", va="bottom", fontsize=7.6)
        for end, flag, x in (("L", cl, X[a]), ("R", cr, X[b])):
            if flag == "S":
                xc = x + (0.32 if end == "L" else -0.32)
                ax.add_patch(Circle((xc, Y[l]), 0.13, facecolor="white", edgecolor="k", lw=0.9, zorder=5))
    # braces
    for bid, (ga, la), (gb, lb) in F.BRACE:
        xm, ym = (X[ga] + X[gb]) / 2, (Y[la] + Y[lb]) / 2
        ax.text(xm + 0.25, ym - 0.35, f"{bid}\n{F.BRACE_SEC}", fontsize=7, ha="left", va="top")
    # bases
    for g, x in X.items():
        if F.BASE[g] == "pin":
            ax.add_patch(Polygon([[x, 0], [x - 0.35, -0.5], [x + 0.35, -0.5]], closed=True, fill=False, lw=1.0))
            ax.plot([x - 0.5, x + 0.5], [-0.5, -0.5], color="k", lw=0.9)
        else:
            ax.add_patch(Rectangle((x - 0.45, -0.45), 0.9, 0.45, fill=False, hatch="////", lw=0.9))
    # legend
    lx, ly = 21.6, 18.55
    ax.text(lx, ly, "Legend", fontsize=8, weight="bold", va="top")
    ax.add_patch(Circle((lx + 0.3, ly - 0.55), 0.13, facecolor="white", edgecolor="k", lw=0.9))
    ax.text(lx + 0.6, ly - 0.55, "simple connection (beam end)", fontsize=6.8, va="center")
    ax.text(lx + 0.6, ly - 0.95, "other beam ends rigid", fontsize=6.8, va="center")
    ax.add_patch(Polygon([[lx + 0.3, ly - 1.2], [lx + 0.12, ly - 1.5], [lx + 0.48, ly - 1.5]], closed=True, fill=False, lw=0.9))
    ax.text(lx + 0.6, ly - 1.35, "pinned base", fontsize=7, va="center")
    ax.add_patch(Rectangle((lx + 0.08, ly - 1.95), 0.45, 0.25, fill=False, hatch="////", lw=0.9))
    ax.text(lx + 0.6, ly - 1.83, "fixed base", fontsize=7, va="center")
    ax.plot([lx + 0.1, lx + 0.5], [ly - 2.2, ly - 2.2], color="k", lw=1.0); ax.plot([lx + 0.1, lx + 0.5], [ly - 2.3, ly - 2.3], color="k", lw=1.0)
    ax.text(lx + 0.6, ly - 2.25, "column splice", fontsize=7, va="center")
    ax.text(lx, ly - 2.6, "Dimensions in mm.", fontsize=7, va="top")
    fig.savefig(path, dpi=300); plt.close(fig)

def loading(path):
    fig, ax = base_fig("FRAME C - LOADING DIAGRAM", 4)
    grids(ax); frame_lines(ax, lw=1.2, color="0.45", braces=False)
    for g, x in X.items():
        ax.add_patch(Rectangle((x - 0.3, -0.25), 0.6, 0.25, fill=False, lw=0.6, edgecolor="0.45"))
    for l in LV[1:]:
        for a, b in zip("123", "234"):
            ax.text((X[a] + X[b]) / 2, Y[l] + 0.95, f"{F.AREA[l]:.1f} kN/m²", ha="center", va="bottom", fontsize=8.5)
            xs = [X[a] + 0.35 + i * 0.6 for i in range(int((X[b] - X[a] - 0.5) / 0.6) + 1)]
            for xx in xs:
                ax.annotate("", (xx, Y[l] + 0.05), (xx, Y[l] + 0.75), arrowprops=dict(arrowstyle="-|>", lw=0.5, mutation_scale=5, color="0.3"))
    # storage zone S
    s = F.STORAGE; x0 = X["2"] + s["a"]; x1 = X["2"] + s["b"]; yl = Y[s["level"]]
    ax.add_patch(Rectangle((x0, yl + 0.06), x1 - x0, 0.55, facecolor="none", hatch="xxxx", edgecolor="k", lw=0.8))
    ax.text(x1 + 0.25, yl - 0.35, f"storage zone S\n+{s['q']:.1f} kN/m²", ha="left", va="top", fontsize=8)
    hdim(ax, X["2"], x0, yl - 1.55, f"{round(s['a'] * 1000)}", fs=8)
    hdim(ax, x0, x1, yl - 1.55, f"{round((s['b'] - s['a']) * 1000)}", fs=8)
    # AHU-2 positions T and F
    p = F.PLANT; yr = Y["R"]
    for tag, a in (("T", F.PLANT_TEMP_A), ("F", p["a"])):
        x = X["3"] + a
        ax.add_patch(Rectangle((x - 0.45, yr + 0.08), 0.9, 0.7, fill=False, lw=0.9, ls="-" if tag == "T" else "--"))
        ax.text(x, yr + 0.43, tag, ha="center", va="center", fontsize=9, weight="bold")
        ax.annotate("", (x, yr + 0.02), (x, yr + 0.08), arrowprops=dict(arrowstyle="-|>", lw=0.8, mutation_scale=7))
    ax.text(X["3"] + 3.3, yr + 1.6, f"AHU-2, {p['P']:.0f} kN point load\nT = temporary landing position\nF = final position", fontsize=7.5, ha="center", va="bottom")
    hdim(ax, X["3"], X["3"] + F.PLANT_TEMP_A, yr - 0.75, f"{round(F.PLANT_TEMP_A * 1000)}", fs=8)
    hdim(ax, X["3"] + F.PLANT_TEMP_A, X["3"] + p["a"], yr - 0.75, f"{round((p['a'] - F.PLANT_TEMP_A) * 1000)}", fs=8)
    # temporary prop TP-1 (L3 bay 2-3 midspan down to L2)
    xm = (X["2"] + X["3"]) / 2
    ax.plot([xm, xm], [Y["L2"] + 0.68, Y["L3"] - 0.05], color="k", lw=1.0, ls=(0, (4, 2)))
    ax.text(xm + 0.2, (Y["L2"] + Y["L3"]) / 2 + 0.6, "TP-1 (temporary prop,\nsee site log)", fontsize=7, va="center")
    # wind
    for l, H in F.WIND.items():
        ax.annotate("", (X["1"] - 0.08, Y[l]), (X["1"] - 1.9, Y[l]), arrowprops=dict(arrowstyle="-|>", lw=1.3, mutation_scale=10))
        ax.text(X["1"] - 1.95, Y[l] + 0.15, f"{H:.0f} kN", ha="left", va="bottom", fontsize=8.5)
    ax.text(X["1"] - 4.4, Y["R"] + 2.3, "WIND (towards grid 4)", fontsize=8, weight="bold", ha="left")
    ax.text(-4.4, -2.4, "Area loads act on the full span of every bay at the level shown.\nDimensions in mm.", fontsize=7.5, va="top")
    fig.savefig(path, dpi=300); plt.close(fig)

if __name__ == "__main__":
    import sys
    elevation(sys.argv[1] if len(sys.argv) > 1 else "/tmp/s3.png"); loading(sys.argv[2] if len(sys.argv) > 2 else "/tmp/s4.png")
