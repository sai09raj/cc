"""MV-20 sheet 3: ventilation plan of the 400 m level (schematic, not to scale; lengths as labelled)."""
import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import net as N
POS = {"PB": (2.0, 10.0), "J1": (5.5, 10.0), "J2": (9.5, 10.0), "J3": (13.5, 10.0), "J10": (17.0, 10.0),
       "J7": (5.5, 7.0), "J8": (9.5, 6.6), "J9": (13.5, 7.3), "J4": (5.5, 3.5), "J5": (9.5, 3.5), "J6": (13.5, 3.5), "UB": (17.0, 3.5)}
PATHS = {"I1": ["PB", "J1"], "I2": ["J1", "J2"], "I3": ["J2", "J3"], "I4": ["J3", "J10"],
         "W1": ["J1", (5.8, 10.0), (5.8, 7.0), "J7"], "W2": ["J7", "J4"],
         "C1": ["J2", (9.8, 10.0), (9.8, 6.6), "J8"], "C2": ["J8", (9.8, 6.6), (9.8, 3.5), "J5"],
         "E1": ["J3", (13.2, 10.0), (13.2, 7.3), "J9"], "E2": ["J9", "J6"],
         "X1": ["J7", (8.6, 7.0), (8.6, 6.6), "J8"], "X2": ["J8", (11.8, 6.6), (11.8, 7.3), "J9"],
         "T1": ["J10", "UB"], "R1": ["J4", "J5"], "R2": ["J5", "J6"], "R3": ["J6", "UB"]}
FLIP = {"R1", "R2", "W2", "T1", "E2", "X1"}
LABEL_AT = {("C1", 1): 0.3}
LABEL_SIDE = {("C2", 0): -1}
ID_AT = {"I1": 0.2, "I2": 0.35, "I3": 0.4, "I4": 0.25, "W1": 0.3, "W2": 0.6, "C1": 0.3, "C2": 0.4, "E1": 0.4, "E2": 0.7,
         "X1": 0.45, "X2": 0.8, "T1": 0.3, "R1": 0.3, "R2": 0.75, "R3": 0.25}
MARK = {"W2": (0.88, "REG-W"), "C2": (0.7, "REG-C"), "E2": (0.8, "REG-E"), "T1": (0.8, "REG-T"), "X1": (0.8, "door D1"), "X2": (0.15, "ST-7")}
# crossed corners: corner point C, vertical-route section (rid, k, u_V), horizontal-route section (rid, k, u_H)
CORNER = [((9.8, 10.0), ("C1", 0, (0, -1)), ("I3", 0, (1, 0))),
          ((9.8, 3.5), ("C2", 1, (0, 1)), ("R2", 0, (1, 0))),
          ((5.8, 7.0), ("W1", 1, (0, 1)), ("X1", 0, (1, 0))),
          ((13.2, 7.3), ("E1", 1, (0, 1)), ("X2", 1, (-1, 0)))]
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
        col = "#1d6b3a" if rid[0] == "I" or rid in ("W1", "C1", "E1") else ("#8a2be2" if rid[0] == "X" else "#b5651d")
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
                ax.text(jx + jn_x * 0.45, jy + jn_y * 0.45, f"SS{ss}", fontsize=8, ha="center", va="center", zorder=5, weight="bold"); ss += 1
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
        shaft = n in ("PB", "UB")
        ax.add_patch(plt.Circle((x, y), 0.36, fc="#cfe0f5" if n == "PB" else "#f5d0cf", ec="k", lw=1.2, zorder=7) if shaft else plt.Rectangle((x - 0.3, y - 0.3), 0.6, 0.6, fc="#eeeeee", ec="k", zorder=7))
        ax.text(x, y, n, ha="center", va="center", fontsize=9, weight="bold", zorder=8)
    ax.text(2.0, 10.6, "downcast shaft DS", ha="center", fontsize=8.5); ax.text(17.0, 2.85, "upcast shaft US\n(main / standby fans at surface)", ha="center", va="top", fontsize=8.5)
    ax.annotate("", xy=(18.0, 11.2), xytext=(18.0, 10.4), arrowprops=dict(arrowstyle="-|>", lw=2)); ax.text(17.9, 11.3, "N", fontsize=12, weight="bold")
    ax.set_xlim(1.2, 18.6); ax.set_ylim(2.0, 11.6)
    ax.set_title("BRAMHALL COLLIERY - sheet 3: ventilation plan, 400 m level (schematic, NOT to scale; lengths as labelled). Each airway is shown section by section with roadway\n"
                 "profile and section length; profile changes are bars with survey station numbers SSn. Green: intake airways; brown: return airways; violet: crosscuts. Yellow squares: regulators REG, door D1, stopping ST-7.", fontsize=10)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white"); plt.close(fig)
if __name__ == "__main__":
    plan(sys.argv[1])
