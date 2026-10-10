"""Capability scan probes A (counting), B (wire tracing), C (noisy scan). Writes images + keys."""
import json, math, os, random, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageFilter
OUT = sys.argv[1]; R = random.Random(16); keys = {}

# ---- A: counting valve symbols on a cluttered sheet
os.makedirs(f"{OUT}/A", exist_ok=True)
fig, ax = plt.subplots(figsize=(18, 12)); ax.set_xlim(0, 180); ax.set_ylim(0, 120); ax.set_aspect("equal"); ax.axis("off")
for _ in range(70):                                   # clutter lines
    x, y = R.uniform(0, 180), R.uniform(0, 120)
    if R.random() < 0.5: ax.plot([x, x + R.uniform(-40, 40)], [y, y], color="k", lw=0.8)
    else: ax.plot([x, x], [y, y + R.uniform(-30, 30)], color="k", lw=0.8)
counts = {"gate": 0, "globe": 0, "check": 0, "ball": 0}; placed = []
def bow(x, y, rot):
    s = 1.3
    pts = [(-s, -s * 0.7), (s, s * 0.7), (s, -s * 0.7), (-s, s * 0.7), (-s, -s * 0.7)]
    if rot: pts = [(b, a) for a, b in pts]
    ax.fill([x + a for a, b in pts], [y + b for a, b in pts], fc="white", ec="k", lw=0.9, zorder=3)
while len(placed) < 150:
    x, y = R.uniform(4, 176), R.uniform(4, 116)
    if any(abs(x - a) < 4 and abs(y - b) < 4 for a, b in placed): continue
    placed.append((x, y)); kind = R.choice(list(counts)); counts[kind] += 1; rot = R.random() < 0.5
    bow(x, y, rot)
    if kind == "globe": ax.plot(x, y, "ko", ms=3.2, zorder=4)
    if kind == "check":
        if rot: ax.plot([x - 1.3, x + 1.3], [y, y], color="k", lw=1.6, zorder=4)
        else: ax.plot([x, x], [y - 1.3, y + 1.3], color="k", lw=1.6, zorder=4)
    if kind == "ball": ax.add_patch(plt.Circle((x, y), 0.55, fc="white", ec="k", lw=0.9, zorder=4))
ax.text(2, 118, "Legend: bow-tie = gate valve; bow-tie with filled dot = globe valve; bow-tie with bar across the middle = check valve; bow-tie with open circle = ball valve",
        fontsize=9, va="top")
fig.savefig(f"{OUT}/A/valves.png", dpi=150, bbox_inches="tight", facecolor="white"); plt.close(fig)
keys["A"] = counts

# ---- B: wire tracing
os.makedirs(f"{OUT}/B", exist_ok=True)
n = 24; perm = list(range(n)); R.shuffle(perm)
fig, ax = plt.subplots(figsize=(14, 14)); ax.set_xlim(-8, 108); ax.set_ylim(-2, 102); ax.axis("off")
for i in range(n):
    yl, yr = 2 + i * 4.2, 2 + perm[i] * 4.2
    c1 = (R.uniform(20, 45), R.uniform(0, 100)); c2 = (R.uniform(55, 80), R.uniform(0, 100))
    t = np.linspace(0, 1, 300)
    bx = (1 - t) ** 3 * 0 + 3 * (1 - t) ** 2 * t * c1[0] + 3 * (1 - t) * t ** 2 * c2[0] + t ** 3 * 100
    by = (1 - t) ** 3 * yl + 3 * (1 - t) ** 2 * t * c1[1] + 3 * (1 - t) * t ** 2 * c2[1] + t ** 3 * yr
    ax.plot(bx, by, color="k", lw=1.1)
    ax.text(-1.5, yl, f"L{i + 1}", ha="right", va="center", fontsize=9); ax.text(101.5, yr, f"R{perm[i] + 1}", ha="left", va="center", fontsize=9)
    ax.plot([0], [yl], "ks", ms=4); ax.plot([100], [yr], "ks", ms=4)
ax.set_title("Each wire runs from one left terminal to one right terminal. Wires cross but never join or branch.", fontsize=10)
fig.savefig(f"{OUT}/B/wires.png", dpi=150, bbox_inches="tight", facecolor="white"); plt.close(fig)
keys["B"] = {f"L{i + 1}": f"R{perm[i] + 1}" for i in range(n)}

# ---- C: noisy scanned table
os.makedirs(f"{OUT}/C", exist_ok=True)
rows, cols = 32, 9
vals = [[R.randint(10000, 99999) for _ in range(cols)] for _ in range(rows)]
fig, ax = plt.subplots(figsize=(13, 17)); ax.axis("off")
t = ax.table(cellText=[[f"{r + 1}"] + [str(v) for v in row] for r, row in enumerate(vals)],
             colLabels=["Row"] + [f"C{c + 1}" for c in range(cols)], loc="center", cellLoc="center")
t.auto_set_font_size(False); t.set_fontsize(9); t.scale(1, 1.35)
fig.savefig(f"{OUT}/C/clean.png", dpi=110, bbox_inches="tight", facecolor="white"); plt.close(fig)
im = Image.open(f"{OUT}/C/clean.png").convert("L").rotate(1.3, expand=True, fillcolor=255)
im = im.filter(ImageFilter.GaussianBlur(0.85)); a = np.asarray(im).astype(float)
a = 0.72 * a + 55 + np.random.default_rng(16).normal(0, 16, a.shape)
Image.fromarray(np.clip(a, 0, 255).astype("uint8")).save(f"{OUT}/C/scan.png"); os.remove(f"{OUT}/C/clean.png")
keys["C"] = {"sum_C3": sum(r[2] for r in vals), "sum_C7": sum(r[6] for r in vals),
             "cells": {"row5_C2": vals[4][1], "row17_C9": vals[16][8], "row23_C4": vals[22][3], "row30_C6": vals[29][5], "row12_C8": vals[11][7]}}
json.dump(keys, open(f"{OUT}/keys.json", "w"), indent=1); print(json.dumps(keys)[:400])
