#!/usr/bin/env python3
"""Evidence figures for the L1 event report (uses the replay engine in l1_replay.py).
Usage: python3 l1_plots.py <event directory> [--out DIR]"""
import argparse, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import l1_replay as L

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
a = ap.parse_args()
recA = L.read_comtrade(os.path.join(a.src, "SUBA_L1_RLY_20260914_142207.cfg"))
recB = L.read_comtrade(os.path.join(a.src, "SUBB_L1_RLY_20260914_142207.cfg"))
sA = L.read_settings(os.path.join(a.src, "SUBA_L1_RLY_settings.txt"))
sB = L.read_settings(os.path.join(a.src, "SUBB_L1_RLY_settings.txt"))
rA = L.Relay("A", sA, recA["ana"]); rB = L.Relay("B", sB, recB["ana"]); L.replay(rA, rB)
rA2 = L.Relay("A", sA, recA["ana"]); rB2 = L.Relay("B", sB, recB["ana"], current_scale=2000 / 1200); L.replay(rA2, rB2)
T = math.radians(sA["Z1ANG"])
th = np.linspace(0, 2 * np.pi, 400)

def circ(ax, R, sign, **kw):
    c = sign * (R / 2) * np.exp(1j * T)
    z = c + (R / 2) * np.exp(1j * th)
    ax.plot(z.real, z.imag, **kw)

fig, axs = plt.subplots(1, 2, figsize=(13, 6))
ks = np.arange(352, 462)
ax = axs[0]
circ(ax, sA["Z1P"], 1, color="0.4", lw=1.2, label="A Z1 (3.71)")
circ(ax, sA["Z2P"], 1, color="k", lw=1.5, ls="--", label="A Z2 (5.79)")
z = rA.Z["BC"][ks]
ax.plot(z.real, z.imag, ".", color="tab:blue", ms=3, label="A BC loop, k=352..461")
ax.plot(rA.Z["BC"][400].real, rA.Z["BC"][400].imag, "o", color="tab:red", label="k=400")
ax.set_title("Substation A relay, BC loop (secondary ohm)"); ax.set_aspect("equal"); ax.grid(alpha=.3)
ax.set_xlim(-3.5, 4.5); ax.set_ylim(-1, 7); ax.legend(fontsize=8, loc="lower right"); ax.set_xlabel("R"); ax.set_ylabel("X")
ax = axs[1]
circ(ax, sB["Z3P"], -1, color="k", lw=1.5, label="B Z3R (1.74)")
circ(ax, sB["Z1P"], 1, color="0.6", lw=1, label="B Z1 / Z2")
circ(ax, sB["Z2P"], 1, color="0.6", lw=1, ls="--")
z = rB.Z["BC"][ks]; z2 = rB2.Z["BC"][ks]
ax.plot(z.real, z.imag, ".", color="tab:red", ms=3, label="as found: CT on 2000:5, CTR=240")
ax.plot(z2.real, z2.imag, ".", color="tab:green", ms=3, label="design tap 1200:5 (x0.6)")
ax.plot(rB.Z["BC"][400].real, rB.Z["BC"][400].imag, "o", color="tab:red")
ax.plot(rB2.Z["BC"][400].real, rB2.Z["BC"][400].imag, "o", color="tab:green")
ax.set_title("Substation B relay, BC loop (secondary ohm), k=352..461"); ax.set_aspect("equal"); ax.grid(alpha=.3)
ax.set_xlim(-3, 2); ax.set_ylim(-3, 1.5); ax.legend(fontsize=8, loc="upper left"); ax.set_xlabel("R"); ax.set_ylabel("X")
fig.tight_layout(); fig.savefig(os.path.join(a.out, "fig_impedance_plane.png"), dpi=130)

fig, axs = plt.subplots(2, 1, figsize=(12, 7.5), sharex=True)
for ax, rel, names, title in ((axs[0], rA, ("Z1", "Z2", "RX", "KEY", "TRIP", "52A"), "Substation A (replay; identical to record)"),
                              (axs[1], rB, ("Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "52A"), "Substation B (replay; identical to record)")):
    for i, n in enumerate(names):
        y = rel.out[n] * 0.8 + i
        ax.step(np.arange(len(y)), y, where="post", lw=1.4)
    ax.set_yticks(np.arange(len(names)) + 0.4); ax.set_yticklabels(names)
    for kk, lab in ((320, "fault k=320"), (461, "L2 clears k=461")):
        ax.axvline(kk, color="tab:red", ls=":", lw=1); ax.text(kk + 2, len(names) - 0.2, lab, fontsize=8, color="tab:red")
    ax.set_title(title, fontsize=10); ax.grid(axis="x", alpha=.3)
axs[1].set_xlim(300, 560); axs[1].set_xlabel("relay sample k (1920 samples/s)")
fig.tight_layout(); fig.savefig(os.path.join(a.out, "fig_digital_sequence.png"), dpi=130)
print("figures written")
