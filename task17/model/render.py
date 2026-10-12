"""Render sheet 2 (single-line diagram, schematic) and sheet 3 (cable route plan, to scale)."""
import json, math, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import net as N
POS = {"PS": (9, 8), "S1": (9, 11), "S2": (12, 12), "S3": (15, 10.5), "S4": (13.5, 8.5), "S5": (5, 9.5), "S6": (3, 12), "S7": (1, 7),
       "S8": (12, 6), "S9": (10, 3.5), "S10": (14, 2.5), "S11": (6, 5), "S12": (3, 3)}
PATHS = {"F1-1": ["PS", (9.3, 8), (9.3, 11), "S1"], "F1-2": ["S1", (12, 11), "S2"], "F1-3": ["S2", (15, 12), "S3"], "F1-4": ["S3", (13.5, 10.5), "S4"],
         "F2-1": ["PS", (8.7, 8), (8.7, 9.5), "S5"], "F2-2": ["S5", (5, 12), "S6"], "F2-3": ["S6", (1, 12), "S7"],
         "F3-1": ["PS", (9.3, 8), (9.3, 6.5), (12, 6.5), "S8"], "F3-2": ["S8", (12, 3.5), "S9"], "F3-3": ["S9", (10, 2.5), "S10"],
         "F4-1": ["PS", (8.7, 8), (8.7, 5), "S11"], "F4-2": ["S11", (6, 3), "S12"],
         "IC-1": ["S3", (15, 2.5), "S10"], "IC-2": ["S6", (3, 5), "S11"], "NOP-1": ["S4", (13.5, 6), "S8"], "NOP-2": ["S7", (1, 3), "S12"]}
FLIP = {"F2-2", "IC-2", "F4-2", "NOP-2", "F2-3", "F3-3", "F1-2"}
SIDE = {"F1-1": "E", "F3-1": "E", "F2-1": "W", "F4-1": "W"}
ID_AT = {"IC-2": 0.25, "F1-1": 0.55, "F2-1": 0.8, "F3-1": 0.75, "F4-1": 0.9, "IC-1": 0.3, "F3-3": 0.75, "F3-2": 0.2}
def pts(rid): return [POS[p] if isinstance(p, str) else p for p in PATHS[rid]]
def plen(path): return sum(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(path, path[1:]))
def point_at(path, s):
    for (xa, ya), (xb, yb) in zip(path, path[1:]):
        seg = abs(xb - xa) + abs(yb - ya)
        if s <= seg + 1e-9:
            f = s / seg if seg else 0; return (xa + (xb - xa) * f, ya + (yb - ya) * f), ((xb - xa) / seg, (yb - ya) / seg) if seg else (1, 0)
        s -= seg
    return path[-1], (1, 0)

def plan(out):
    fig, ax = plt.subplots(figsize=(18, 13)); ax.set_aspect("equal"); ax.axis("off")
    jn = 1
    for r in N.ROUTES:
        rid, secs = r[0], r[3]; path = pts(rid); D = plen(path); L = sum(l for _, l in secs)
        col = "#7a2e00" if not rid.startswith(("IC", "NOP")) else "#1f5f99"
        ax.plot(*zip(*path), color=col, lw=2.4, zorder=2, ls="-" if not rid.startswith("NOP") else (0, (6, 3)))
        s0 = 0.0
        for k, (t, l) in enumerate(secs):
            sm = (s0 + l / 2.0) / L * D
            (mx, my), (ux, uy) = point_at(path, sm); nx, ny = -uy, ux
            if rid in FLIP: nx, ny = -nx, -ny
            if rid in SIDE and abs(ux) < 0.5: nx, ny = (-1.0 if SIDE[rid] == "W" else 1.0), 0.0
            ax.plot([mx, mx + nx * 0.25], [my, my + ny * 0.25], color="0.4", lw=0.7, zorder=3)
            ax.text(mx + nx * 0.55, my + ny * 0.55, f"{t} Al\n{l} m", fontsize=8, ha="center", va="center", zorder=5,
                    bbox=dict(fc="white", ec="0.4", lw=0.5, pad=0.2))
            s0 += l
            if k < len(secs) - 1:
                (jx, jy), (ux, uy) = point_at(path, s0 / L * D)
                name = "J7" if rid == "F1-3" else f"J{jn if jn < 7 else jn + 1}"
                if rid != "F1-3": jn += 1
                ax.plot([jx - uy * 0.18, jx + uy * 0.18], [jy + ux * 0.18, jy - ux * 0.18], color="k", lw=3.5, zorder=4)
                jn_x, jn_y = uy, -ux
                if rid in FLIP: jn_x, jn_y = -jn_x, -jn_y
                if rid in SIDE and abs(ux) < 0.5: jn_x, jn_y = (1.0 if SIDE[rid] == "W" else -1.0), 0.0
                ax.text(jx + jn_x * 0.38, jy + jn_y * 0.38, name, fontsize=8, ha="center", va="center", zorder=5, weight="bold")
        (mx, my), (ux, uy) = point_at(path, ID_AT.get(rid, 0.5) * D); nx, ny = -uy, ux
        if rid not in FLIP: nx, ny = -nx, -ny
        if rid in SIDE and abs(ux) < 0.5: nx, ny = (-1.0 if SIDE[rid] == "W" else 1.0), 0.0
        ax.text(mx + nx * 0.42, my + ny * 0.42, rid, fontsize=8.5, weight="bold", color=col, ha="center", va="center", zorder=6,
                bbox=dict(fc="#fffbe6", ec=col, lw=0.6, pad=0.15))
    for n, (x, y) in POS.items():
        ax.add_patch(plt.Rectangle((x - 0.28, y - 0.28), 0.56, 0.56, fc="#d9e6f2" if n != "PS" else "#f2dcd9", ec="k", zorder=7))
        ax.text(x, y, "PS" if n == "PS" else n, ha="center", va="center", fontsize=9, weight="bold", zorder=8)
    ax.text(5.6, 7.3, "KINGSMEAD PRIMARY\n(F1, F2 from section A;\nF3, F4 from section B)", fontsize=8.5, zorder=8, bbox=dict(fc="white", ec="none", pad=0.1))
    ax.annotate("", xy=(17.6, 12.6), xytext=(17.6, 11.6), arrowprops=dict(arrowstyle="-|>", lw=2)); ax.text(17.5, 12.75, "N", fontsize=12, weight="bold")
    ax.set_xlim(0, 18.3); ax.set_ylim(1.5, 13.2)
    ax.set_title("KINGSMEAD 11 kV - sheet 4: cable route plan (NOT to scale; lengths as labelled). Each route is shown section by section with cable type and section "
                 "length;\njoints are bars with joint numbers. Brown: feeder routes; blue: interconnectors; dashed: normally-open routes.", fontsize=10)
    fig.savefig(out, dpi=140, bbox_inches="tight", facecolor="white"); plt.close(fig)

def sld(out):
    fig, ax = plt.subplots(figsize=(17, 12.5)); ax.set_xlim(0, 17); ax.set_ylim(-0.8, 12.5); ax.axis("off")
    def cb(x, y, closed=True, lab=None, vert=True):
        ax.add_patch(plt.Rectangle((x - 0.13, y - 0.13), 0.26, 0.26, fc="k" if closed else "white", ec="k", lw=1.5, zorder=5))
        if lab: ax.text(x + 0.2, y, lab, fontsize=8, va="center", zorder=6)
    def line(pts, **k): ax.plot(*zip(*pts), color=k.get("c", "k"), lw=k.get("lw", 1.6), ls=k.get("ls", "-"), zorder=2)
    # grid infeed and 33 kV busbar
    ax.add_patch(plt.Circle((8.5, 12.0), 0.3, fc="white", ec="k", lw=1.5)); ax.text(8.5, 12.0, "~", ha="center", va="center", fontsize=16)
    ax.text(9.0, 12.0, "33 kV GRID INFEED", fontsize=9, va="center"); line([(8.5, 11.7), (8.5, 11.2)])
    line([(5.0, 11.2), (12.0, 11.2)], lw=4); ax.text(12.1, 11.2, "P33  33 kV", fontsize=9, va="center")
    for name, x, sec in (("T1", 6.0, "A"), ("T2", 11.0, "B")):
        line([(x, 11.2), (x, 10.6)]); cb(x, 10.75, True, f"{name} 33 kV CB")
        ax.add_patch(plt.Circle((x, 10.1), 0.32, fc="none", ec="k", lw=1.5)); ax.add_patch(plt.Circle((x, 9.65), 0.32, fc="none", ec="k", lw=1.5))
        ax.annotate("", xy=(x + 0.45, 10.35), xytext=(x - 0.45, 9.4), arrowprops=dict(arrowstyle="->", lw=1))
        ax.text(x + 0.55, 9.9, f"{name}\n15 MVA 33/11 kV\nOLTC + AVC", fontsize=8, va="center")
        line([(x, 9.33), (x, 8.7)]); cb(x, 9.0, True, f"{name} 11 kV CB")
    line([(2.0, 8.6), (8.2, 8.6)], lw=4); line([(8.8, 8.6), (15.0, 8.6)], lw=4)
    ax.text(2.0, 8.85, "11 kV SECTION A", fontsize=9); ax.text(13.3, 8.85, "11 kV SECTION B", fontsize=9)
    line([(8.2, 8.6), (8.8, 8.6)]); cb(8.5, 8.6, True); ax.text(8.5, 8.2, "BS", ha="center", fontsize=8)
    cols = {"F2": (3.5, ["S5", "S6", "S7"]), "F1": (6.5, ["S1", "S2", "S3", "S4"]), "F3": (10.5, ["S8", "S9", "S10"]), "F4": (13.5, ["S11", "S12"])}
    pos = {}
    for f, (x, subs) in cols.items():
        line([(x, 8.6), (x, 7.9)]); cb(x, 8.2, True, f"{f} CB")
        y = 7.9
        for i, s in enumerate(subs):
            y2 = 7.0 - i * 1.55; line([(x, y), (x, y2)]); ax.text(x - 0.12, (y + y2) / 2, f"{f}-{i + 1}", fontsize=8, ha="right", va="center", color="#7a2e00")
            ax.add_patch(plt.Rectangle((x - 0.3, y2 - 0.22), 0.6, 0.44, fc="#d9e6f2", ec="k", zorder=4)); ax.text(x, y2, s, ha="center", va="center", fontsize=9, weight="bold", zorder=5)
            pos[s] = (x, y2); y = y2 - 0.22
    def link(a, b, name, normally_open, yoff=0.0, route=None):
        (xa, ya), (xb, yb) = pos[a], pos[b]
        if route is None: route = [(xa + (0.3 if xb > xa else -0.3), ya + yoff), (xb - (0.3 if xb > xa else -0.3), yb + yoff)]
        line(route, c="#1f5f99", ls=(0, (5, 3)) if normally_open else "-")
        mx, my = route[len(route) // 2 - 1]; mx2, my2 = route[len(route) // 2]
        cx, cy = (mx + mx2) / 2, (my + my2) / 2
        if normally_open:
            ax.plot([cx - 0.18, cx + 0.12], [cy, cy + 0.2], color="k", lw=2, zorder=5); ax.plot(cx - 0.18, cy, "ko", ms=4, zorder=5)
            ax.text(cx + (1.6 if name == "NOP-2" else 0), cy + (-0.32 if name == "NOP-2" else 0.32), f"{name} (normally open)", ha="center", fontsize=8, color="#1f5f99")
        else:
            cb(cx, cy, True); ax.text(cx + (0.35 if name == "IC-1" else -0.6), cy + (-0.38 if name == "IC-1" else 0.3), name, ha="center", fontsize=8, color="#1f5f99")
    link("S3", "S10", "IC-1", False)
    link("S4", "S8", "NOP-1", True, route=[(6.8, pos["S4"][1]), (9.4, pos["S4"][1]), (9.4, pos["S8"][1] - 0.6), (10.2, pos["S8"][1] - 0.6), (10.2, pos["S8"][1] - 0.15)])
    yc = pos["S3"][1]; ax.plot([9.4, 9.4], [yc - 0.12, yc + 0.12], color="white", lw=6, zorder=3)
    ax.add_patch(matplotlib.patches.Arc((9.4, yc), 0.24, 0.24, theta1=270, theta2=90, color="#1f5f99", lw=1.6, zorder=4))
    yb1 = 0.9; yb2 = 0.45
    link("S6", "S11", "IC-2", False, route=[(3.2, pos["S6"][1]), (2.4, pos["S6"][1]), (2.4, yb1), (14.4, yb1), (14.4, pos["S11"][1]), (13.8, pos["S11"][1])])
    link("S7", "S12", "NOP-2", True, route=[(3.5, pos["S7"][1] - 0.22), (3.5, yb2), (15.0, yb2), (15.0, pos["S12"][1]), (13.8, pos["S12"][1])])
    # PV and capacitor
    x, y = pos["S10"]; line([(x + 0.3, y), (x + 1.1, y)]); ax.add_patch(plt.Rectangle((x + 1.1, y - 0.25), 0.7, 0.5, fc="#fff2b3", ec="k")); ax.text(x + 1.45, y, "PV-1", ha="center", va="center", fontsize=8)
    x, y = pos["S6"]; line([(x + 0.3, y), (x + 0.9, y)]); cb(x + 0.6, y, False)
    ax.plot([x + 0.9, x + 0.9], [y - 0.2, y + 0.2], "k", lw=2); ax.plot([x + 1.0, x + 1.0], [y - 0.2, y + 0.2], "k", lw=2); ax.text(x + 1.1, y, "C1", va="center", fontsize=8)
    ax.text(0.3, -0.3, "KINGSMEAD 11 kV - sheet 3: single-line diagram (schematic, not to scale). Breakers and switches shown in their NORMAL state:\n"
            "filled square = closed, open square = open, open blade = normally-open point. Route ids (F1-1 ...) refer to the cable route plan, sheet 4.", fontsize=9, va="top")
    fig.savefig(out, dpi=140, bbox_inches="tight", facecolor="white"); plt.close(fig)

if __name__ == "__main__":
    sld(sys.argv[1] + "_sld.png"); plan(sys.argv[1] + "_plan.png")
