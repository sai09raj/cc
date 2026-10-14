"""MV-20 sheet 3: ventilation plan of the 400 m level (schematic, not to scale; lengths as labelled)."""
import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import net as N
POS = {"A": (1.6, 8.0), "N1": (5.0, 8.0), "N2": (9.0, 8.0), "N3": (13.0, 8.0), "B": (17.0, 8.0),
       "N9": (5.0, 11.5), "N4": (9.0, 11.5), "C": (13.0, 11.5),
       "N5": (5.0, 4.5), "N6": (9.0, 4.5), "N7": (13.0, 4.5), "D": (17.0, 4.5), "N8": (9.0, 1.5)}
PATHS = {"L1": ["A", "N1"], "L2": ["N1", "N2"], "L3": ["N2", "N3"], "L4": ["N3", "B"],
         "M1": ["N2", (9.3, 8.0), (9.3, 11.5), "N4"], "M2": ["N4", "C"], "M3": ["C", "N3"],
         "S1": ["N1", "N5"], "S2": ["N5", "N6"], "S3": ["N2", (9.3, 8.0), (9.3, 4.5), "N6"], "S4": ["N6", "N7"], "S5": ["N7", "D"],
         "S6": ["N3", (13.3, 8.0), (13.3, 4.5), "N7"], "S7": ["N6", "N8"], "N9R": ["N4", "N9"], "X1": ["N9", (5.3, 11.5), (5.3, 8.0), "N1"]}
FLIP = {"L1", "S2", "S4", "S5", "N9R", "M3", "X1"}
LABEL_AT = {("L4", 0): 0.35, ("S6", 0): 0.45}
LABEL_SIDE = {}
ID_AT = {"L1": 0.25, "L2": 0.7, "L3": 0.7, "L4": 0.75, "M1": 0.3, "M2": 0.75, "M3": 0.25, "S1": 0.3, "S2": 0.25, "S3": 0.3,
         "S4": 0.75, "S5": 0.75, "S6": 0.7, "S7": 0.3, "N9R": 0.3, "X1": 0.65}
MARK = {}
# crossed corners: corner point C, vertical-route section (rid, k, u_V), horizontal-route section (rid, k, u_H)
CORNER = [((9.3, 11.5), ("M1", 1, (0, -1)), ("M2", 0, (1, 0))),
          ((5.3, 11.5), ("X1", 0, (0, -1)), ("N9R", 1, (1, 0))),
          ((9.3, 4.5), ("S3", 1, (0, 1)), ("S4", 0, (1, 0))),
          ((13.3, 4.5), ("S6", 1, (0, 1)), ("S5", 0, (1, 0)))]
SKIP = {(v[0], v[1] % 2) for _, v, _ in CORNER} | {(h[0], h[1] % 2) for _, _, h in CORNER}
def pts(rid): return [POS[p] if isinstance(p, str) else p for p in PATHS[rid]]
def plen(path): return sum(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(path, path[1:]))
def point_at(path, s):
    for (xa, ya), (xb, yb) in zip(path, path[1:]):
        seg = abs(xb - xa) + abs(yb - ya)
        if s <= seg + 1e-9 and seg:
            f = s / seg; return (xa + (xb - xa) * f, ya + (yb - ya) * f), ((xb - xa) / seg, (yb - ya) / seg)
        s -= seg
    return path[-1], (1, 0)
def plan(out):
    secs_of = {r[0]: r[3] for r in N.ROUTES}
    fig, ax = plt.subplots(figsize=(18, 11)); ax.set_aspect("equal"); ax.axis("off")
    ss = 1
    for r in N.ROUTES:
        rid = r[0]; secs = secs_of[rid]; path = pts(rid); D = plen(path); L = sum(l for _, l in secs)
        col = {"L": "#b3261e", "M": "#1f5f99", "S": "#2e7d32", "N": "#1f5f99", "X": "#7b3fa0"}[rid[0]]
        ax.plot(*zip(*path), color=col, lw=2.6, zorder=2)
        s0 = 0.0
        for k, (t, l) in enumerate(secs):
            sm = (s0 + l * LABEL_AT.get((rid, k), 0.5)) / L * D
            (mx, my), (ux, uy) = point_at(path, sm); nx, ny = -uy, ux
            if rid in FLIP: nx, ny = -nx, -ny
            if LABEL_SIDE.get((rid, k)) == -1: nx, ny = -nx, -ny
            if (rid, k) not in SKIP:
                ax.plot([mx, mx + nx * 0.25], [my, my + ny * 0.25], color="0.4", lw=0.7, zorder=3)
                ax.text(mx + nx * 0.55, my + ny * 0.55, f"{t}\n{l} m", fontsize=8, ha="center", va="center", zorder=5, bbox=dict(fc="white", ec="0.4", lw=0.5, pad=0.2))
            s0 += l
            if k < len(secs) - 1:
                (jx, jy), (ux, uy) = point_at(path, s0 / L * D)
                ax.plot([jx - uy * 0.18, jx + uy * 0.18], [jy + ux * 0.18, jy - ux * 0.18], color="k", lw=3.5, zorder=4)
                jn_x, jn_y = uy, -ux
                if rid in FLIP: jn_x, jn_y = -jn_x, -jn_y
                ax.text(jx + jn_x * 0.45, jy + jn_y * 0.45, f"CP{ss}", fontsize=8, ha="center", va="center", zorder=5, weight="bold"); ss += 1
        if rid in MARK:
            f, name = MARK[rid]; (mx, my), (ux, uy) = point_at(path, f * D); nx, ny = -uy, ux
            if rid in FLIP: nx, ny = -nx, -ny
            ax.add_patch(plt.Rectangle((mx - 0.12, my - 0.12), 0.24, 0.24, fc="#ffd84d", ec="k", lw=1.0, zorder=6))
            ax.text(mx - nx * 0.5, my - ny * 0.5, name, fontsize=7.5, style="italic", ha="center", va="center", zorder=6)
        (mx, my), (ux, uy) = point_at(path, ID_AT.get(rid, 0.5) * D); nx, ny = -uy, ux
        if rid not in FLIP: nx, ny = -nx, -ny
        ax.text(mx + nx * 0.42, my + ny * 0.42, rid, fontsize=8.5, weight="bold", color=col, ha="center", va="center", zorder=6, bbox=dict(fc="#fffbe6", ec=col, lw=0.6, pad=0.15))
    box = dict(fc="white", ec="0.4", lw=0.5, pad=0.2)
    for (cx, cy), (vr, vk, (vx, vy)), (hr, hk, (hx, hy)) in CORNER:
        t, l = secs_of[vr][vk]; bx, by = cx + 0.45 * hx + 0.24 * vx, cy + 0.45 * hy + 0.24 * vy
        ax.plot([cx + 0.24 * vx, bx], [cy + 0.24 * vy, by], color="0.4", lw=0.7, zorder=3)
        ax.text(bx, by, f"{t}\n{l} m", fontsize=8, ha="center", va="center", zorder=5, bbox=box)
        t, l = secs_of[hr][hk]; bx, by = cx + 0.62 * hx + 0.74 * vx, cy + 0.62 * hy + 0.74 * vy
        ax.plot([cx + 0.78 * hx, cx + 0.78 * hx + 0.74 * vx], [cy, cy + 0.74 * vy], color="0.4", lw=0.7, zorder=3)
        ax.text(bx, by, f"{t}\n{l} m", fontsize=8, ha="center", va="center", zorder=5, bbox=box)
    for n, (x, y) in POS.items():
        sub = n in ("A", "B", "C", "D")
        ax.add_patch(plt.Rectangle((x - 0.3, y - 0.3), 0.6, 0.6, fc="#ffe9a8" if sub else "#eeeeee", ec="k", lw=1.6 if sub else 1.0, zorder=7))
        ax.text(x, y, n, ha="center", va="center", fontsize=9, weight="bold", zorder=8)
        if sub: ax.text(x, y + 0.48, f"TSS-{n}", ha="center", va="bottom", fontsize=8.5, weight="bold", zorder=8)
    ax.annotate("", xy=(18.1, 12.6), xytext=(18.1, 11.8), arrowprops=dict(arrowstyle="-|>", lw=2)); ax.text(18.0, 12.75, "N", fontsize=12, weight="bold")
    ax.set_xlim(0.8, 18.6); ax.set_ylim(0.8, 13.2)
    ax.set_title("HARTSDOWN TRAMWAY 750 V DC - sheet 3: traction supply route plan (schematic, NOT to scale; lengths as labelled). Each route is shown section by section with\n"
                 "conductor type and section length; conductor change points are bars with numbers CPn. Yellow boxes: traction substation feeding points TSS-A to TSS-D; grey boxes: tram stops.", fontsize=10)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white"); plt.close(fig)
if __name__ == "__main__":
    plan(sys.argv[1])
