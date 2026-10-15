"""WD-22 sheet 2 (pipe plan, schematic, not to scale) and sheet 3 (diurnal demand pattern chart)."""
import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import net as N
POS = {"J1": (1.5, 11.0), "J2": (5.5, 11.0), "J3": (9.5, 11.0), "J4": (14.0, 11.0),
       "J5": (3.5, 7.0), "J7": (9.5, 6.5), "J8": (12.5, 6.5),
       "J6": (7.0, 3.0), "J9": (14.0, 3.0), "T": (12.5, 4.5),
       "J10": (7.0, 0.8), "J11": (4.0, 0.8), "J12": (1.0, 0.8)}
PATHS = {"A1": ["J1", "J2"], "A2": ["J2", "J3"], "A3": ["J3", "J4"],
         "B1": ["J1", (1.5, 7.0), "J5"], "B3": ["J2", (5.5, 7.0), "J5"], "B2": ["J5", (3.8, 7.0), (3.8, 3.0), "J6"],
         "C1": ["J3", (9.2, 11.0), (9.2, 6.5), "J7"], "C2": ["J7", "J8"], "C3": ["J6", (6.7, 3.0), (6.7, 6.5), "J7"],
         "D1": ["J4", "J9"], "D2": ["J9", "J6"], "TK": ["J8", "T"], "L1": ["J10", "J11"], "L2": ["J11", "J12"]}
FLIP = {"A1", "A2", "A3", "C2", "D2", "L1", "L2", "B1"}
LABEL_AT = {}
ID_AT = {"A1": 0.22, "A2": 0.22, "A3": 0.22, "B1": 0.25, "B2": 0.55, "B3": 0.3, "C1": 0.3, "C2": 0.22, "C3": 0.45, "D1": 0.3, "D2": 0.22, "TK": 0.62, "L1": 0.22, "L2": 0.22}
JT_FLIP = {"TK"}
ID_SIDE = {}
# crossed corners: corner point C, vertical-route section (pid, k, u_V), horizontal-route section (pid, k, u_H)
CORNER = [((9.2, 11.0), ("C1", 0, (0, -1)), ("A2", 1, (-1, 0))),
          ((3.8, 7.0), ("B2", 0, (0, -1)), ("B3", 1, (1, 0))),
          ((6.7, 3.0), ("C3", 0, (0, 1)), ("B2", 1, (-1, 0))),
          ((9.2, 6.5), ("C1", 1, (0, 1)), ("C3", 1, (-1, 0)))]
SKIP = {(v[0], v[1]) for _, v, _ in CORNER} | {(h[0], h[1]) for _, _, h in CORNER}
COL = {"A": "#1f5f99", "B": "#2e7d32", "C": "#7b3fa0", "D": "#b3261e", "T": "#00838f", "L": "#6d4c41"}
def pts(pid): return [POS[p] if isinstance(p, str) else p for p in PATHS[pid]]
def plen(path): return sum(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(path, path[1:]))
def point_at(path, s):
    for (xa, ya), (xb, yb) in zip(path, path[1:]):
        seg = abs(xb - xa) + abs(yb - ya)
        if s <= seg + 1e-9 and seg:
            f = s / seg; return (xa + (xb - xa) * f, ya + (yb - ya) * f), ((xb - xa) / seg, (yb - ya) / seg)
        s -= seg
    return path[-1], (1, 0)
LEADERS = []      # (pid, k, leader end point on the pipe) for the fairness check
def plan(out):
    secs_of = {p[0]: p[3] for p in N.PIPES}; LEADERS.clear()
    fig, ax = plt.subplots(figsize=(18, 11.5)); ax.set_aspect("equal"); ax.axis("off")
    jt = 1
    for p in N.PIPES:
        pid = p[0]; secs = secs_of[pid]; path = pts(pid); D = plen(path); L = sum(l for _, l in secs); col = COL[pid[0]]
        ax.plot(*zip(*path), color=col, lw=2.6, zorder=2)
        s0 = 0.0
        for k, (t, l) in enumerate(secs):
            sm = (s0 + l * LABEL_AT.get((pid, k), 0.5)) / L * D
            (mx, my), (ux, uy) = point_at(path, sm); nx, ny = -uy, ux
            if pid in FLIP: nx, ny = -nx, -ny
            if (pid, k) not in SKIP:
                ax.plot([mx, mx + nx * 0.25], [my, my + ny * 0.25], color="0.4", lw=0.7, zorder=3); LEADERS.append((pid, k, (mx, my)))
                ax.text(mx + nx * 0.6, my + ny * 0.6, f"{t}\n{l} m", fontsize=8, ha="center", va="center", zorder=5, bbox=dict(fc="white", ec="0.4", lw=0.5, pad=0.2))
            s0 += l
            if k < len(secs) - 1:
                (jx, jy), (ux, uy) = point_at(path, s0 / L * D)
                ax.plot([jx - uy * 0.18, jx + uy * 0.18], [jy + ux * 0.18, jy - ux * 0.18], color="k", lw=3.5, zorder=4)
                jn_x, jn_y = uy, -ux
                if pid in FLIP: jn_x, jn_y = -jn_x, -jn_y
                if pid in JT_FLIP: jn_x, jn_y = -jn_x, -jn_y
                ax.text(jx + jn_x * 0.42, jy + jn_y * 0.42, f"K{jt}", fontsize=7.5, ha="center", va="center", zorder=5, weight="bold"); jt += 1
        (mx, my), (ux, uy) = point_at(path, ID_AT.get(pid, 0.5) * D); nx, ny = -uy, ux
        if pid not in FLIP: nx, ny = -nx, -ny
        if ID_SIDE.get(pid) == -1: nx, ny = -nx, -ny
        ax.text(mx + nx * 0.42, my + ny * 0.42, pid, fontsize=8.5, weight="bold", color=col, ha="center", va="center", zorder=6, bbox=dict(fc="#fffbe6", ec=col, lw=0.6, pad=0.15))
    box = dict(fc="white", ec="0.4", lw=0.5, pad=0.2)
    for (cx, cy), (vr, vk, (vx, vy)), (hr, hk, (hx, hy)) in CORNER:
        t, l = secs_of[vr][vk]; bx, by = cx + 0.45 * hx + 0.24 * vx, cy + 0.45 * hy + 0.24 * vy
        ax.plot([cx + 0.24 * vx, bx], [cy + 0.24 * vy, by], color="0.4", lw=0.7, zorder=3); LEADERS.append((vr, vk, (cx + 0.24 * vx, cy + 0.24 * vy)))
        ax.text(bx, by, f"{t}\n{l} m", fontsize=8, ha="center", va="center", zorder=5, bbox=box)
        t, l = secs_of[hr][hk]; bx, by = cx + 0.62 * hx + 0.74 * vx, cy + 0.62 * hy + 0.74 * vy
        ax.plot([cx + 0.78 * hx, cx + 0.78 * hx + 0.74 * vx], [cy + 0.78 * hy, cy + 0.78 * hy + 0.74 * vy], color="0.4", lw=0.7, zorder=3); LEADERS.append((hr, hk, (cx + 0.78 * hx, cy + 0.78 * hy)))
        ax.text(bx, by, f"{t}\n{l} m", fontsize=8, ha="center", va="center", zorder=5, bbox=box)
    for n, (x, y) in POS.items():
        if n == "T":
            ax.add_patch(plt.Circle((x, y), 0.55, fc="#d6f1f4", ec="k", lw=1.6, zorder=7)); ax.text(x, y, "T", ha="center", va="center", fontsize=10, weight="bold", zorder=8)
            ax.text(x + 0.75, y, "service tank T", ha="left", va="center", fontsize=8.5, weight="bold", zorder=8); continue
        ax.add_patch(plt.Rectangle((x - 0.3, y - 0.3), 0.6, 0.6, fc="#eeeeee", ec="k", lw=1.0, zorder=7))
        ax.text(x, y, n, ha="center", va="center", fontsize=8.5, weight="bold", zorder=8)
    # reservoir and pumping station
    ax.plot([-1.5, 1.2], [11.0, 11.0], color="k", lw=2.6, zorder=2)
    ax.add_patch(plt.Polygon([(-3.3, 11.6), (-1.7, 11.6), (-2.0, 10.4), (-3.0, 10.4)], fc="#cfe3f7", ec="k", lw=1.4, zorder=7))
    ax.text(-2.5, 11.0, "R", ha="center", va="center", fontsize=10, weight="bold", zorder=8); ax.text(-2.5, 11.85, "reservoir R", ha="center", fontsize=8.5, weight="bold")
    ax.add_patch(plt.Rectangle((-1.0, 10.45), 1.5, 1.1, fc="#fff3c4", ec="k", lw=1.4, zorder=7))
    ax.text(-0.25, 11.0, "PS\nP-1  P-2", ha="center", va="center", fontsize=8, weight="bold", zorder=8)
    # PRV-1 on the link J6 - J10
    ax.plot([7.0, 7.0], [2.7, 1.1], color="k", lw=2.0, zorder=2)
    ax.add_patch(plt.Polygon([(6.75, 2.15), (7.25, 2.15), (6.75, 1.65), (7.25, 1.65)], fc="white", ec="k", lw=1.4, zorder=7))
    ax.text(7.45, 1.9, "PRV-1", ha="left", va="center", fontsize=8.5, weight="bold", zorder=8)
    ax.annotate("", xy=(15.6, 12.2), xytext=(15.6, 11.4), arrowprops=dict(arrowstyle="-|>", lw=2)); ax.text(15.5, 12.35, "N", fontsize=12, weight="bold")
    ax.set_xlim(-3.6, 16.2); ax.set_ylim(0.0, 12.6)
    ax.set_title("FENWICK HILL SUPPLY ZONE - sheet 2: pipe plan (schematic, NOT to scale; lengths as labelled). Each pipe is shown section by section with pipe type and\n"
                 "section length; joints between sections are bars numbered Kn. Grey boxes: junctions J1 to J12; T: service tank; PS: pumping station; PRV-1: pressure-reducing valve.\n"
                 "Each section label belongs to the section that its leader line touches.", fontsize=10)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white"); plt.close(fig)
def chart(out):
    fig, ax = plt.subplots(figsize=(16, 9.5))
    h = list(range(24)); ax.bar([x + 0.5 for x in h], N.PATTERN, width=0.7, color="#4f81bd", edgecolor="k", lw=0.8, zorder=3)
    ax.set_ylim(0, 1.8); ax.set_xlim(0, 24)
    ax.set_yticks([i / 10 for i in range(19)]); ax.set_yticks([i / 20 for i in range(37)], minor=True)
    ax.set_yticklabels([f"{i / 10:.1f}" for i in range(19)], fontsize=10)
    ax.grid(axis="y", which="major", color="0.55", lw=0.8, zorder=0); ax.grid(axis="y", which="minor", color="0.8", lw=0.6, ls="-", zorder=0)
    ax.set_xticks(range(25)); ax.set_xticklabels([f"{x:02d}:00" for x in range(25)], fontsize=8.5, rotation=90)
    ax.set_xlabel("clock time (each bar covers one clock hour, e.g. 07:00 to 08:00)", fontsize=11)
    ax.set_ylabel("demand multiplier (applies to every junction base demand)", fontsize=11)
    ax.set_title("FENWICK HILL SUPPLY ZONE - sheet 3: diurnal demand pattern for the simulated day. Every bar top lies exactly on a grid line;\n"
                 "grid lines are every 0.05 (labelled every 0.1).", fontsize=11)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white"); plt.close(fig)
if __name__ == "__main__":
    plan(sys.argv[1]); chart(sys.argv[2])
