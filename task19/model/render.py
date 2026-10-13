"""DH-19 sheet 3: route plan (not to scale; lengths as labelled)."""
import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import net as N
POS = {"EC": (9, 7), "H1": (9.6, 10.3), "H2": (12.5, 11.3), "H3": (15.5, 11.3), "H4": (16.5, 8.2), "H5": (12.2, 6.6), "H6": (13.6, 3.6),
       "H7": (16.6, 2.4), "H8": (5.8, 8.0), "H9": (3.2, 9.4), "H10": (2.2, 12.0), "H11": (7.6, 4.2), "H12": (5.0, 1.8)}
PATHS = {"A1": ["EC", (9.15, 7.0), (9.15, 10.3), "H1"], "A2": ["H1", (11.6, 10.3), (11.6, 11.3), "H2"], "A3": ["H2", "H3"], "A4": ["H3", (16.5, 11.3), "H4"],
         "B1": ["EC", (9.15, 7.0), (9.15, 6.6), "H5"], "B2": ["H5", (13.6, 6.6), "H6"], "B3": ["H6", (13.6, 2.4), "H7"],
         "C1": ["EC", (7.6, 7.0), (7.6, 8.0), "H8"], "C2": ["H8", (3.2, 8.0), "H9"], "C3": ["H9", (2.2, 9.4), "H10"],
         "D1": ["EC", (8.85, 7.0), (8.85, 4.2), "H11"], "D2": ["H11", (5.0, 4.2), "H12"],
         "L1": ["H4", (17.4, 8.2), (17.4, 13.0), (2.2, 13.0), "H10"], "L2": ["H7", (16.6, 0.9), (5.0, 0.9), "H12"],
         "X3": ["H2", (12.5, 9.0), (14.6, 9.0), (14.6, 3.6), "H6"]}
FLIP = {"A2", "C2", "D2", "B3", "X3"}
LABEL_AT = {("B1", 0): 0.6, ("C1", 0): 0.5, ("A1", 0): 0.55, ("L1", 0): 0.24, ("X3", 0): 0.2, ("A4", 1): 0.78, ("B2", 0): 0.85}
LABEL_SIDE = {("A2", 1): -1}
ID_AT = {"A1": 0.75, "A2": 0.25, "A3": 0.3, "A4": 0.75, "B1": 0.2, "B2": 0.3, "B3": 0.8, "C1": 0.25, "C2": 0.8, "C3": 0.25, "D1": 0.45, "D2": 0.25, "L1": 0.78, "L2": 0.3, "X3": 0.45}
def pts(rid): return [POS[p] if isinstance(p, str) else p for p in PATHS[rid]]
def plen(path): return sum(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(path, path[1:]))
def point_at(path, s):
    for (xa, ya), (xb, yb) in zip(path, path[1:]):
        seg = abs(xb - xa) + abs(yb - ya)
        if s <= seg + 1e-9:
            f = s / seg if seg else 0; return (xa + (xb - xa) * f, ya + (yb - ya) * f), ((xb - xa) / seg, (yb - ya) / seg) if seg else (1, 0)
        s -= seg
    return path[-1], (1, 0)
def plan(out, routes=None):
    secs_of = {r[0]: r[3] for r in N.ROUTES}
    if routes: secs_of.update(routes)
    fig, ax = plt.subplots(figsize=(18, 13)); ax.set_aspect("equal"); ax.axis("off")
    vc = 1
    for r in N.ROUTES:
        rid = r[0]; secs = secs_of[rid]; path = pts(rid); D = plen(path); L = sum(l for _, l in secs)
        col = "#a3271c" if rid[0] in "ABCD" else "#1f5f99"
        ax.plot(*zip(*path), color=col, lw=2.6, zorder=2)
        s0 = 0.0
        for k, (t, l) in enumerate(secs):
            sm = (s0 + l * LABEL_AT.get((rid, k), 0.5)) / L * D
            (mx, my), (ux, uy) = point_at(path, sm); nx, ny = -uy, ux
            if rid in FLIP: nx, ny = -nx, -ny
            if LABEL_SIDE.get((rid, k)) == -1: nx, ny = -nx, -ny
            ax.plot([mx, mx + nx * 0.25], [my, my + ny * 0.25], color="0.4", lw=0.7, zorder=3)
            ax.text(mx + nx * 0.55, my + ny * 0.55, f"{t}\n{l} m", fontsize=8, ha="center", va="center", zorder=5, bbox=dict(fc="white", ec="0.4", lw=0.5, pad=0.2))
            s0 += l
            if k < len(secs) - 1:
                (jx, jy), (ux, uy) = point_at(path, s0 / L * D)
                ax.plot([jx - uy * 0.18, jx + uy * 0.18], [jy + ux * 0.18, jy - ux * 0.18], color="k", lw=3.5, zorder=4)
                jn_x, jn_y = uy, -ux
                if rid in FLIP: jn_x, jn_y = -jn_x, -jn_y
                ax.text(jx + jn_x * 0.42, jy + jn_y * 0.42, f"VC{vc}", fontsize=8, ha="center", va="center", zorder=5, weight="bold"); vc += 1
        (mx, my), (ux, uy) = point_at(path, ID_AT.get(rid, 0.5) * D); nx, ny = -uy, ux
        if rid not in FLIP: nx, ny = -nx, -ny
        ax.text(mx + nx * 0.42, my + ny * 0.42, rid, fontsize=8.5, weight="bold", color=col, ha="center", va="center", zorder=6, bbox=dict(fc="#fffbe6", ec=col, lw=0.6, pad=0.15))
    for n, (x, y) in POS.items():
        ax.add_patch(plt.Rectangle((x - 0.3, y - 0.3), 0.6, 0.6, fc="#f2dcd9" if n == "EC" else "#e3efd9", ec="k", zorder=7))
        ax.text(x, y, n, ha="center", va="center", fontsize=9, weight="bold", zorder=8)
    ax.annotate("", xy=(17.9, 12.4), xytext=(17.9, 11.4), arrowprops=dict(arrowstyle="-|>", lw=2)); ax.text(17.8, 12.55, "N", fontsize=12, weight="bold")
    ax.set_xlim(0.8, 18.4); ax.set_ylim(0.3, 13.6)
    ax.set_title("ASHGROVE DISTRICT HEATING - sheet 3: pipe route plan (NOT to scale; lengths as labelled). Each route is shown section by section with pipe type and\n"
                 "section length; valve chambers between sections are bars with chamber numbers. Red: branch routes A, B, C, D from the energy centre EC; blue: loop and crossover routes.", fontsize=10)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white"); plt.close(fig)
if __name__ == "__main__":
    import state; plan(sys.argv[1], state.REPAIR if len(sys.argv) > 2 else None)
