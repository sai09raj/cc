"""Shaded perspective renderer (painter's algorithm) for the ISO-16 v2 scene."""
import math, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import scene as S

def camera(eye, target, fov=38):
    eye, target = np.array(eye, float), np.array(target, float)
    f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1]); r /= np.linalg.norm(r); u = np.cross(r, f)
    k = 1 / math.tan(math.radians(fov) / 2)
    def proj(p):
        d = np.array(p, float) - eye
        z = d @ f
        return (d @ r) * k / z, (d @ u) * k / z, z
    return proj

def cyl_faces(a, b, rad, n=10):
    a, b = np.array(a, float), np.array(b, float); ax = b - a; ax /= np.linalg.norm(ax)
    t = np.array([1, 0, 0]) if abs(ax[0]) < 0.9 else np.array([0, 1, 0])
    e1 = np.cross(ax, t); e1 /= np.linalg.norm(e1); e2 = np.cross(ax, e1)
    out = []
    for i in range(n):
        t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        o0 = rad * (math.cos(t0) * e1 + math.sin(t0) * e2); o1 = rad * (math.cos(t1) * e1 + math.sin(t1) * e2)
        nrm = (o0 + o1) / 2; nrm /= np.linalg.norm(nrm)
        out.append(([a + o0, b + o0, b + o1, a + o1], nrm))
    return out

def box_faces(c, s):
    (x0, y0, z0), (x1, y1, z1) = c, (c[0] + s[0], c[1] + s[1], c[2] + s[2])
    V = lambda x, y, z: np.array([x, y, z], float)
    return [([V(x0, y0, z1), V(x1, y0, z1), V(x1, y1, z1), V(x0, y1, z1)], np.array([0, 0, 1.])),
            ([V(x0, y0, z0), V(x1, y0, z0), V(x1, y0, z1), V(x0, y0, z1)], np.array([0, -1, 0.])),
            ([V(x0, y1, z0), V(x1, y1, z0), V(x1, y1, z1), V(x0, y1, z1)], np.array([0, 1, 0.])),
            ([V(x0, y0, z0), V(x0, y1, z0), V(x0, y1, z1), V(x0, y0, z1)], np.array([-1, 0, 0.])),
            ([V(x1, y0, z0), V(x1, y1, z0), V(x1, y1, z1), V(x1, y0, z1)], np.array([1, 0, 0.]))]

LIGHT = np.array([0.4, -0.5, 0.75]); LIGHT /= np.linalg.norm(LIGHT)
PIPE_COL = {200: (0.15, 0.45, 0.85), 150: (0.2, 0.65, 0.4), 100: (0.85, 0.55, 0.15), 80: (0.75, 0.25, 0.6), 50: (0.35, 0.3, 0.3)}

def render(out, eye, target, title):
    proj = camera(eye, target)
    faces = []
    for E in S.COLS_E:
        for N in S.COLS_N:
            faces += [(f, n, (0.55, 0.55, 0.58)) for f, n in box_faces((E - 150, N - 150, 0), (300, 300, S.COL_H))]
        for L in S.LEVELS:
            faces += [(f, n, (0.6, 0.6, 0.62)) for f, n in box_faces((E - 100, S.COLS_N[0], L - 400), (200, S.COLS_N[1] - S.COLS_N[0], 250))]
    for N in S.COLS_N:
        faces += [(f, n, (0.62, 0.62, 0.64)) for f, n in box_faces((S.COLS_E[0], N - 100, 7000 - 400), (S.COLS_E[-1], 200, 250))]
    for tag, kind, (cx, cy), (dx, dy, h), noz in S.EQUIP:
        faces += [(f, n, (0.78, 0.76, 0.7)) for f, n in box_faces((cx - dx / 2, cy - dy / 2, 0), (dx, dy, h))]
    for lid, dn, vs in S.P:
        rad = dn * 0.9
        for a, b in zip(vs, vs[1:]):
            faces += [(f, n, PIPE_COL[dn]) for f, n in cyl_faces(a, b, rad)]
    polys = []
    for f, n, col in faces:
        pts = [proj(p) for p in f]
        if min(p[2] for p in pts) <= 0: continue
        cen = np.mean(f, axis=0); camz = proj(cen)[2]
        shade = 0.45 + 0.55 * max(0.0, float(n @ LIGHT))
        polys.append((camz, [(p[0], p[1]) for p in pts], tuple(min(1, c * shade) for c in col)))
    polys.sort(key=lambda t: -t[0])
    fig, ax = plt.subplots(figsize=(16, 11)); ax.set_aspect("equal"); ax.axis("off")
    # floor grid every 1500 with labels
    for x in range(-3000, 30001, 1500):
        a, b = proj((x, -3000, 0)), proj((x, 21000, 0))
        ax.plot([a[0], b[0]], [a[1], b[1]], color="0.82", lw=0.6, zorder=0)
        if x % 3000 == 0: ax.text(a[0], a[1], f"E{x}", fontsize=6.5, color="0.35", ha="center", va="top")
    for y in range(-3000, 21001, 1500):
        a, b = proj((-3000, y, 0)), proj((30000, y, 0))
        ax.plot([a[0], b[0]], [a[1], b[1]], color="0.82", lw=0.6, zorder=0)
        if y % 3000 == 0: ax.text(a[0], a[1], f"N{y}", fontsize=6.5, color="0.35", ha="right", va="center")
    for z, pts, col in polys:
        ax.add_patch(Polygon(pts, closed=True, fc=col, ec=(0, 0, 0, 0.15), lw=0.2, zorder=1))
    for tag, kind, (cx, cy), (dx, dy, h), noz in S.EQUIP:
        p = proj((cx, cy, h + 300)); ax.text(p[0], p[1], f"{tag}\nnozzle EL +{noz[2]}", fontsize=7, ha="center", va="bottom", zorder=5,
                                               bbox=dict(fc="white", ec="0.5", pad=0.2))
    for L in S.LEVELS:
        p = proj((S.COLS_E[0] - 300, S.COLS_N[0], L)); ax.text(p[0], p[1], f"TOS EL +{L}", fontsize=7, ha="right", zorder=5,
                                                                bbox=dict(fc="#ffffe0", ec="0.5", pad=0.2))
    for lid, dn, vs in S.P:
        a, b = vs[0], vs[1]; m = [(a[i] + b[i]) / 2 for i in range(3)]; m[2] += 350
        p = proj(m); ax.text(p[0], p[1], f"{lid} DN{dn}", fontsize=7, color="#900", ha="center", zorder=6,
                             bbox=dict(fc="white", ec="none", pad=0.1, alpha=0.85))
    ax.autoscale_view(); ax.set_title(title, fontsize=11)
    fig.savefig(out, dpi=140, bbox_inches="tight", facecolor="white"); plt.close(fig)

if __name__ == "__main__":
    o = sys.argv[1]
    render(o + "_v1.png", (36000, -14000, 16000), (12000, 9000, 2500), "View 1 - from south-east, looking north-west (perspective)")
    render(o + "_v2.png", (-12000, 28000, 15000), (13000, 8000, 2500), "View 2 - from north-west, looking south-east (perspective)")
