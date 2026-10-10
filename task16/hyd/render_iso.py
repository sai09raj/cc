"""Render the draft network as a single isometric sheet (not to scale)."""
import math, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import net as NW

C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))
LW = {150: 3.2, 100: 2.4, 80: 1.9, 50: 1.4}
NEXT_DN = {150: 100, 100: 80, 80: 50}
NODE_OFF = {}
LINE_SEG = {"CW-304": 1}


def scale(L):
    return 0.55 * L ** 0.62          # not to scale: monotone compression


def iso_dir(dr):
    return {"E": (C30, -S30), "W": (-C30, S30), "N": (C30, S30), "S": (-C30, -S30), "U": (0, 1), "D": (0, -1)}[dr]


def depth(p):                         # larger = nearer the viewer (viewer toward east, south, above)
    return p[0] - p[1] + p[2]


def upright(ang):
    return ang - 180 if ang > 90 else (ang + 180 if ang < -90 else ang)


def layout():
    pos = {NW.START[0]: (0.0, 0.0)}; p3d = {NW.START[0]: NW.START[1]}; draw = []
    for lid, dn, frm, items in NW.LINES:
        p, p3, d = pos[frm], p3d[frm], dn
        for it in items:
            if isinstance(it, str):
                pos[it], p3d[it] = p, p3; continue
            dx, dy = iso_dir(it[0]); s = scale(it[1]); q = (p[0] + dx * s, p[1] + dy * s)
            v = NW.VEC[it[0]]; q3 = tuple(p3[i] + v[i] * it[1] for i in range(3))
            draw.append(dict(line=lid, dn=d, a=p, b=q, a3=p3, b3=q3, dir=it[0], len=it[1], fit=it[2] if len(it) > 2 else None))
            if len(it) > 2 and it[2] == "RED":
                d = NEXT_DN[d]
            p, p3 = q, q3
    return pos, draw


def render(out):
    pos, draw = layout()
    fig, ax = plt.subplots(figsize=(16, 12)); ax.set_aspect("equal"); ax.axis("off")
    for s in draw:
        (x0, y0), (x1, y1) = s["a"], s["b"]
        ax.plot([x0, x1], [y0, y1], color="k", lw=LW[s["dn"]], solid_capstyle="butt", zorder=2)
        nx, ny = -(y1 - y0), (x1 - x0); n = math.hypot(nx, ny) or 1
        ang = upright(math.degrees(math.atan2(y1 - y0, x1 - x0)))
        ax.text((x0 + x1) / 2 + nx / n * 7, (y0 + y1) / 2 + ny / n * 7, str(s["len"]), rotation=ang, ha="center", va="center",
                fontsize=8, zorder=4, bbox=dict(fc="white", ec="none", pad=0.3))
        if s["fit"]:
            ax.text(x1, y1, {"GV": "GV", "CK": "CHK", "GL": "GLB", "RED": "RED"}[s["fit"]], fontsize=7, color="white",
                    ha="center", va="center", zorder=5, bbox=dict(boxstyle="round,pad=0.2", fc="#444", ec="k"))
    crossings = []
    for i, s1 in enumerate(draw):
        for s2 in draw[i + 1:]:
            (ax1, ay1), (bx1, by1), (ax2, ay2), (bx2, by2) = s1["a"], s1["b"], s2["a"], s2["b"]
            den = (bx1 - ax1) * (by2 - ay2) - (by1 - ay1) * (bx2 - ax2)
            if abs(den) < 1e-9:
                continue
            t = ((ax2 - ax1) * (by2 - ay2) - (ay2 - ay1) * (bx2 - ax2)) / den
            u = ((ax2 - ax1) * (by1 - ay1) - (ay2 - ay1) * (bx1 - ax1)) / den
            if not (0.02 < t < 0.98 and 0.02 < u < 0.98):
                continue
            pt = lambda s, k: [s["a3"][j] + (s["b3"][j] - s["a3"][j]) * k for j in range(3)]
            back, tb, front = (s1, t, s2) if depth(pt(s1, t)) < depth(pt(s2, u)) else (s2, u, s1)
            (xa, ya), (xb, yb) = back["a"], back["b"]; g = 5 / math.hypot(xb - xa, yb - ya)
            ax.plot([xa + (xb - xa) * (tb - g), xa + (xb - xa) * (tb + g)], [ya + (yb - ya) * (tb - g), ya + (yb - ya) * (tb + g)],
                    color="white", lw=LW[back["dn"]] + 4, zorder=2.5, solid_capstyle="butt")
            ax.plot([front["a"][0], front["b"][0]], [front["a"][1], front["b"][1]], color="k", lw=LW[front["dn"]], zorder=2.6,
                    solid_capstyle="butt")
            crossings.append((back["line"], front["line"]))
    last = {d["b"]: d for d in draw}
    for k, (x, y) in pos.items():
        if k.startswith("T") and k != "T-1":
            ax.plot(x, y, "ko", ms=6, zorder=3)
            ox, oy = NODE_OFF.get(k, (3, -9))
            ax.text(x + ox, y + oy, k, fontsize=10, weight="bold", color="#0047ab", zorder=6, bbox=dict(fc="white", ec="none", pad=0.2))
        elif k == "T-1":
            ax.text(x + 4, y - 4, "T-1", fontsize=10, weight="bold", color="#0047ab", zorder=6)
        else:
            d = last[(x, y)]; dx, dy = iso_dir(d["dir"])
            ax.plot([x, x + dx * 3], [y, y + dy * 3], color="k", lw=4, zorder=3)
            ox, oy = NODE_OFF.get(k, (dx * 15, dy * 15))
            if k in NODE_OFF:
                ax.plot([x, x + ox * 0.8], [y, y + oy * 0.8], color="#0047ab", lw=0.8, zorder=5)
            ax.text(x + ox, y + oy, k, fontsize=11, weight="bold", color="#0047ab", ha="center", va="center", zorder=6,
                    bbox=dict(boxstyle="square,pad=0.25", fc="#e8f0ff", ec="#0047ab"))
    ax.text(pos["T-1"][0] - 6, pos["T-1"][1] + 4, "HEAD TANK T-1 OUTLET NOZZLE\nEL +20000  (E 0, N 0)", fontsize=9, ha="right")
    for lid, dn, frm, items in NW.LINES:
        s = [d for d in draw if d["line"] == lid][LINE_SEG.get(lid, 0)]
        (x0, y0), (x1, y1) = s["a"], s["b"]; mx, my = x0 * 0.45 + x1 * 0.55, y0 * 0.45 + y1 * 0.55
        nx, ny = (y1 - y0), -(x1 - x0); n = math.hypot(nx, ny) or 1
        ang = upright(math.degrees(math.atan2(y1 - y0, x1 - x0)))
        ax.text(mx + nx / n * 8, my + ny / n * 8, f"{lid} DN{dn}", rotation=ang, fontsize=7.5, color="#a00", ha="center",
                va="center", zorder=6, bbox=dict(fc="white", ec="none", pad=0.1))
    ax.annotate("", xy=(-30 + C30 * 20, 120 + S30 * 20), xytext=(-30, 120), arrowprops=dict(arrowstyle="-|>", lw=2))
    ax.text(-30 + C30 * 24, 120 + S30 * 24, "PLANT N", fontsize=10, weight="bold")
    ax.set_title("Cooling-water outfall and consumer supply - isometric (not to scale). Dimensions in mm along pipe centrelines.", fontsize=12)
    fig.savefig(out, dpi=130, bbox_inches="tight", facecolor="white")
    return crossings


if __name__ == "__main__":
    print("crossings (back, front):", render(sys.argv[1] if len(sys.argv) > 1 else "draft.png"))
