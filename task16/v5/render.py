"""To-scale isometric sheets for CW-200 (projected from the 3D model in plant.py/geom.py)."""
import math, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plant as P
from geom import build
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))
LW = {200: 3.4, 150: 2.6, 100: 1.9, 80: 1.5}
def iso(p): E, N, U = p; return ((E + N) * C30 / 1000.0, (N - E) * S30 / 1000.0 + U / 1000.0)
def upright(a): return a - 180 if a > 90 else (a + 180 if a < -90 else a)
SHEETS = {"1": ["CW-201", "CW-202", "CW-203", "CW-204", "CW-205", "CW-206", "CW-207"], "2": ["CW-208", "CW-209", "CW-210", "CW-211"]}
END_LABEL = {"D201": "DRAIN", "D202": "DRAIN", "D203": "DRAIN", "D204": "DRAIN", "D205": "DRAIN", "D206": "DRAIN",
             "TK1IN": "TK-1 (free-discharge inlet)", "POND": "RIVER POND (free outfall)"}
def render(sheet, out):
    nodes, lines = build()
    fig, ax = plt.subplots(figsize=(17, 12)); ax.set_aspect("equal"); ax.axis("off")
    segs = []
    for lid in SHEETS[sheet]:
        for pc in lines[lid]:
            p = nodes[pc["frm"]]
            for m in pc["moves"]:
                v = P.VEC[m[0]]; q = tuple(p[i] + v[i] * m[1] for i in range(3)); segs.append((lid, pc["dn"], p, q, m)); p = q
    for lid, dn, a, b, m in segs:
        (x0, y0), (x1, y1) = iso(a), iso(b)
        ax.plot([x0, x1], [y0, y1], color="k", lw=LW[dn], solid_capstyle="butt", zorder=2)
        ang = upright(math.degrees(math.atan2(y1 - y0, x1 - x0))); nx, ny = -(y1 - y0), (x1 - x0); n = math.hypot(nx, ny) or 1
        ax.text((x0 + x1) / 2 + nx / n * 1.6, (y0 + y1) / 2 + ny / n * 1.6, str(m[1]), rotation=ang, ha="center", va="center",
                fontsize=7.5, zorder=4, bbox=dict(fc="white", ec="none", pad=0.2))
        if len(m) > 2:
            tag = m[2]; txt = {"GV": "GV"}.get(tag, tag.replace("HX:", ""))
            fc = "#2b5d8a" if tag.startswith("HX") else "#444"
            ax.text(x1, y1, txt, fontsize=7, color="white", ha="center", va="center", zorder=5,
                    bbox=dict(boxstyle="square,pad=0.3" if tag.startswith("HX") else "round,pad=0.2", fc=fc, ec="k"))
    # crossings
    def depth(p): return p[0] - p[1] + p[2]
    for i, (l1, d1, a1, b1, _) in enumerate(segs):
        for (l2, d2, a2, b2, _) in segs[i + 1:]:
            (ax1, ay1), (bx1, by1), (ax2, ay2), (bx2, by2) = iso(a1), iso(b1), iso(a2), iso(b2)
            den = (bx1 - ax1) * (by2 - ay2) - (by1 - ay1) * (bx2 - ax2)
            if abs(den) < 1e-9: continue
            t = ((ax2 - ax1) * (by2 - ay2) - (ay2 - ay1) * (bx2 - ax2)) / den; u = ((ax2 - ax1) * (by1 - ay1) - (ay2 - ay1) * (bx1 - ax1)) / den
            if not (0.01 < t < 0.99 and 0.01 < u < 0.99): continue
            p1 = [a1[k] + (b1[k] - a1[k]) * t for k in range(3)]; p2 = [a2[k] + (b2[k] - a2[k]) * u for k in range(3)]
            (bx, by, tb, dn) = (ax1, ay1, t, d1) if depth(p1) < depth(p2) else (ax2, ay2, u, d2)
            (ex, ey) = (bx1, by1) if depth(p1) < depth(p2) else (bx2, by2)
            L = math.hypot(ex - bx, ey - by); g = 1.2 / L
            ax.plot([bx + (ex - bx) * (tb - g), bx + (ex - bx) * (tb + g)], [by + (ey - by) * (tb - g), by + (ey - by) * (tb + g)],
                    color="white", lw=LW[dn] + 4, zorder=2.5, solid_capstyle="butt")
    shown = set()
    for lid in SHEETS[sheet]:
        for pc in lines[lid]:
            for nm in (pc["frm"], pc["to"]):
                if nm in shown: continue
                shown.add(nm); x, y = iso(nodes[nm])
                if nm.startswith("T") and nm not in ("TK1", "TK1IN"):
                    ax.plot(x, y, "ko", ms=6, zorder=3); ax.text(x + 0.8, y - 2.2, nm, fontsize=10, weight="bold", color="#0047ab", zorder=6)
                elif nm in ("R1", "N5"):
                    ax.plot(x, y, "ko", ms=6, zorder=3); ax.text(x + 0.8, y - 2.2, nm, fontsize=10, weight="bold", color="#0047ab", zorder=6)
                elif nm in END_LABEL:
                    ax.text(x + 0.8, y + 0.8, END_LABEL[nm], fontsize=8, weight="bold", color="#0047ab", zorder=6,
                            bbox=dict(fc="#e8f0ff", ec="#0047ab", pad=0.2))
    for lid in SHEETS[sheet]:
        pc = lines[lid][0]; a = nodes[pc["frm"]]; m = pc["moves"][0]; v = P.VEC[m[0]]
        b = tuple(a[i] + v[i] * m[1] * 0.5 for i in range(3)); (x, y) = iso(b)
        ax.text(x - 1.2, y + 1.6, f"{lid} DN{pc['dn']}", fontsize=7.5, color="#a00", zorder=6, bbox=dict(fc="white", ec="none", pad=0.1))
    if sheet == "1":
        x, y = iso(nodes["M"]); ax.text(x - 1, y - 3.5, "PUMP DISCHARGE MANIFOLD OUTLET\nEL +1500 (E 0, N 0)\nP-201A/B/C/D below", fontsize=8, ha="right")
        ax.set_title("CW-200 isometric, sheet 1 of 2: pump manifold, DN200 ring main and its branches. To scale; dimensions in mm along centrelines. Plant north up-right.", fontsize=10)
    else:
        x, y = iso(nodes["TK1"]); ax.text(x + 1, y + 1, "TK-1 BOTTOM OUTLET NOZZLE\nEL +25000 (E 40000, N 60000)", fontsize=8)
        ax.set_title("CW-200 isometric, sheet 2 of 2: TK-1 gravity side. To scale; dimensions in mm along centrelines. Plant north up-right.", fontsize=10)
    xs, ys = zip(*[iso(p) for s in segs for p in (s[2], s[3])]); ax.set_xlim(min(xs) - 12, max(xs) + 12); ax.set_ylim(min(ys) - 8, max(ys) + 8)
    nx0, ny0 = min(xs) - 8, max(ys) + 2
    ax.annotate("", xy=(nx0 + C30 * 5, ny0 + S30 * 5), xytext=(nx0, ny0), arrowprops=dict(arrowstyle="-|>", lw=2))
    ax.text(nx0 + C30 * 6, ny0 + S30 * 6, "PLANT N", fontsize=9, weight="bold")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white"); plt.close(fig)
if __name__ == "__main__":
    render("1", sys.argv[1] + "_s1.png"); render("2", sys.argv[1] + "_s2.png")
