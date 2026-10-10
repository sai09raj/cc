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
SHEETS = {"1": ["CW-201", "CW-202"], "2": ["CW-208", "CW-211"]}
STUBS = {"CW-203": "A", "CW-204": "B", "CW-205": "C", "CW-206": "D", "CW-207": "E"}
STUBS2 = {"CW-209": "F", "CW-210": "G"}
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
            x1, y1 = x1 - nx / n * 1.6, y1 - ny / n * 1.6
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
                    lm = pc["moves"][-1][0]; ddx, ddy = {"E": (C30, -S30), "W": (-C30, S30), "N": (C30, S30), "S": (-C30, -S30), "U": (0, 1), "D": (0, -1)}[lm]
                    ax.text(x + ddx * 2.5, y + ddy * 2.5, END_LABEL[nm], ha="center", fontsize=8, weight="bold", color="#0047ab", zorder=6,
                            bbox=dict(fc="#e8f0ff", ec="#0047ab", pad=0.2))
    for lid in SHEETS[sheet]:
        best = None
        for pc in lines[lid]:
            p = nodes[pc["frm"]]
            for m in pc["moves"]:
                v = P.VEC[m[0]]; q = tuple(p[i] + v[i] * m[1] for i in range(3))
                if best is None or m[1] > best[0]: best = (m[1], p, q, pc["dn"])
                p = q
        _, a, b, dn = best; (x0, y0), (x1, y1) = iso(a), iso(b)
        mx, my = x0 + (x1 - x0) * 0.3, y0 + (y1 - y0) * 0.3; nx, ny = (y1 - y0), -(x1 - x0); n = math.hypot(nx, ny) or 1
        ang = upright(math.degrees(math.atan2(y1 - y0, x1 - x0)))
        sgn = -1 if lid == "CW-201" else 1
        ax.text(mx + sgn * nx / n * 1.8, my + sgn * ny / n * 1.8, f"{lid} DN{dn}", rotation=ang, fontsize=7.5, color="#a00", zorder=6, ha="center",
                va="center", bbox=dict(fc="white", ec="none", pad=0.1))
    if True:
        for lid, det in (STUBS if sheet == "1" else STUBS2).items():
            pc = lines[lid][0]; a = nodes[pc["frm"]]; m = pc["moves"][0]; v = P.VEC[m[0]]
            b = tuple(a[i] + v[i] * 4000 for i in range(3)); (x0, y0), (x1, y1) = iso(a), iso(b)
            ax.plot([x0, x1], [y0, y1], color="k", lw=LW[pc["dn"]], zorder=2)
            ux, uy = (x1 - x0), (y1 - y0); n = math.hypot(ux, uy); ux, uy = ux / n, uy / n
            tx, ty = x1 + ux * 6, y1 + uy * 6
            ax.plot([x1, tx], [y1, ty], color="#a00", lw=0.7, ls=":", zorder=5)
            ax.text(tx, ty, f"{lid} DN{pc['dn']}\nsee sheet 3, detail {det}", fontsize=8, color="#a00", zorder=6, ha="center", va="center",
                    bbox=dict(fc="white", ec="#a00", pad=0.2))
    if sheet == "1":
        x, y = iso(nodes["M"]); ax.text(x - 3, y - 6, "PUMP DISCHARGE MANIFOLD OUTLET\nEL +1500 (E 0, N 0)\nP-201A/B/C/D below", fontsize=8, ha="right")
        ax.annotate("", xy=(x, y), xytext=(x - 3, y - 4.5), arrowprops=dict(arrowstyle="-", lw=0.7))
        ax.set_title("CW-200 isometric, sheet 1 of 3: pump manifold, DN200 ring main and its branches. To scale; dimensions in mm along centrelines. Plant north up-right.", fontsize=10)
    else:
        x, y = iso(nodes["TK1"]); ax.text(x + 1, y + 1, "TK-1 BOTTOM OUTLET NOZZLE\nEL +25000 (E 40000, N 60000)", fontsize=8)
        ax.set_title("CW-200 isometric, sheet 2 of 3: TK-1 gravity side. To scale; dimensions in mm along centrelines. Plant north up-right.", fontsize=10)
    xs, ys = zip(*[iso(p) for s in segs for p in (s[2], s[3])]); ax.set_xlim(min(xs) - 12, max(xs) + 12); ax.set_ylim(min(ys) - 8, max(ys) + 8)
    nx0, ny0 = min(xs) - 8, max(ys) + 2
    ax.annotate("", xy=(nx0 + C30 * 5, ny0 + S30 * 5), xytext=(nx0, ny0), arrowprops=dict(arrowstyle="-|>", lw=2))
    ax.text(nx0 + C30 * 6, ny0 + S30 * 6, "PLANT N", fontsize=9, weight="bold")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white"); plt.close(fig)
def render_details(out):
    """Sheet 3: each ring branch drawn on its own (not to scale), starting at its tee on the ring."""
    nodes, lines = build()
    fig, axs = plt.subplots(2, 4, figsize=(20, 10)); axs = axs.ravel()
    for k, (lid, det) in enumerate({**STUBS, **STUBS2}.items()):
        ax = axs[k]; ax.set_aspect("equal"); ax.axis("off"); pc = lines[lid][0]
        p = (0.0, 0.0); pts = [p]
        for m in pc["moves"]:
            dx, dy = {"E": (C30, -S30), "W": (-C30, S30), "N": (C30, S30), "S": (-C30, -S30), "U": (0, 1), "D": (0, -1)}[m[0]]
            s_ = 2.4 + 0.35 * math.log10(m[1] / 1000 + 1) * 6; q = (p[0] + dx * s_, p[1] + dy * s_)
            ax.plot([p[0], q[0]], [p[1], q[1]], color="k", lw=LW[pc["dn"]], zorder=2)
            ang = upright(math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))); nx, ny = -(q[1] - p[1]), (q[0] - p[0]); n = math.hypot(nx, ny) or 1
            ax.text((p[0] + q[0]) / 2 + nx / n * 0.35, (p[1] + q[1]) / 2 + ny / n * 0.35, str(m[1]), rotation=ang, ha="center", va="center",
                    fontsize=9, bbox=dict(fc="white", ec="none", pad=0.2), zorder=4)
            if len(m) > 2:
                tag = m[2]; fc = "#2b5d8a" if tag.startswith("HX") else "#444"
                ax_, ay_ = (q[0], q[1]) if tag.startswith("HX") else ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                ax.plot([ax_, ax_ - nx / n * 0.85], [ay_, ay_ - ny / n * 0.85], color="0.4", lw=0.8, zorder=4)
                ax.text(ax_ - nx / n * 1.1, ay_ - ny / n * 1.1, tag.replace("HX:", ""), fontsize=8.5, color="white", ha="center", va="center", zorder=5,
                        bbox=dict(boxstyle="square,pad=0.3" if tag.startswith("HX") else "round,pad=0.2", fc=fc, ec="k"))
            p = q; pts.append(p)
        fdx = {"E": C30, "W": -C30, "N": C30, "S": -C30, "U": 0, "D": 0}[pc["moves"][0][0]]
        ax.plot(0, 0, "ko", ms=7, zorder=3); ax.text(-0.3 if fdx >= 0 else 0.3, 0.6, ha="right" if fdx >= 0 else "left", s= f"{pc['frm']} (on ring main)" if pc["frm"] != "N5" else "N5 (sheet 2)", fontsize=9, weight="bold", color="#0047ab")
        lm = pc["moves"][-1][0]; ddx, ddy = {"E": (C30, -S30), "W": (-C30, S30), "N": (C30, S30), "S": (-C30, -S30), "U": (0, 1), "D": (0, -1)}[lm]
        ax.plot([p[0], p[0] + ddx * 0.6], [p[1], p[1] + ddy * 0.6], color="#0047ab", lw=1, ls=":")
        vert = lm in ("U", "D")
        ax.text(p[0] + (0.5 if vert else ddx * 1.6), p[1] + (ddy * 0.9 if vert else ddy * 1.6 - 0.2), END_LABEL[pc["to"]], fontsize=9, weight="bold",
                color="#0047ab", ha="left" if vert else "center",
                bbox=dict(fc="#e8f0ff", ec="#0047ab", pad=0.2)); pts.append((p[0] + ddx * 2.6, p[1] + ddy * 2.6))
        xs, ys = zip(*pts); ax.set_xlim(min(xs) - 2.5, max(xs) + 3.5); ax.set_ylim(min(ys) - 1.5, max(ys) + 1.5)
        ax.set_title(f"Detail {det}: {lid} DN{pc['dn']} (not to scale)", fontsize=10)
    axs[7].axis("off")
    ax = axs[7]; ax.annotate("", xy=(C30 * 2, S30 * 2), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", lw=2)); ax.set_xlim(-1, 4); ax.set_ylim(-1, 3)
    ax.text(C30 * 2.2, S30 * 2.2, "PLANT N", fontsize=10, weight="bold")
    fig.suptitle("CW-200 isometric, sheet 3 of 3: branch details. Dimensions in mm along centrelines.", fontsize=11)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white"); plt.close(fig)
if __name__ == "__main__":
    render("1", sys.argv[1] + "_s1.png"); render("2", sys.argv[1] + "_s2.png"); render_details(sys.argv[1] + "_s3.png")
