#!/usr/bin/env python3
"""Deterministic renderer for the KILNWORKS R3 visual packet.

Pure matplotlib -> PDF, no image-generation model involved, so there is no
diffusion-style embedded watermark to strip in the first place. Metadata is
scrubbed explicitly below (Title/Author/Subject/Creator/Producer) so nothing
about the authoring environment leaks into the uploaded file.

Run: python3 make_packet.py
"""
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches


def wrapped(text, width=95):
    return "\n".join(textwrap.fill(line, width) if line.strip() else "" for line in text.split("\n"))

OUT = "KILNWORKS-T05-R3.pdf"

NODE_XY = {n: (n % 3, 2 - n // 3) for n in range(9)}  # node = 3y+x, y grows downward on page
BASE_EDGES = [(0, 3), (3, 6), (3, 4), (4, 7), (6, 7), (7, 8), (5, 8), (2, 5), (1, 4)]
OPEN_EDGE = (4, 5)
DOCKS = {3: "P", 5: "Q", 1: "K"}


def draw_graph(ax, show_open_edge, title):
    for a, b in BASE_EDGES:
        x1, y1 = NODE_XY[a]
        x2, y2 = NODE_XY[b]
        ax.plot([x1, x2], [y1, y2], color="0.25", lw=1.6, zorder=1)
    if show_open_edge:
        a, b = OPEN_EDGE
        x1, y1 = NODE_XY[a]
        x2, y2 = NODE_XY[b]
        ax.plot([x1, x2], [y1, y2], color="0.25", lw=1.6, ls=(0, (4, 3)), zorder=1)
    else:
        a, b = OPEN_EDGE
        x1, y1 = NODE_XY[a]
        x2, y2 = NODE_XY[b]
        ax.plot([x1, x2], [y1, y2], color="0.75", lw=1.2, ls=(0, (1, 2)), zorder=0)

    for n, (x, y) in NODE_XY.items():
        is_dock = n in DOCKS
        is_junction = n == 4
        face = "#f2c14e" if is_junction else ("#5b9bd5" if is_dock else "white")
        ax.add_patch(mpatches.Circle((x, y), 0.16, facecolor=face,
                                      edgecolor="black", lw=1.3, zorder=2))
        label = DOCKS.get(n, str(n))
        ax.text(x, y, label, ha="center", va="center", fontsize=9,
                fontweight="bold" if is_dock or is_junction else "normal", zorder=3)
        if is_dock:
            ax.text(x, y - 0.32, f"node {n}", ha="center", va="top", fontsize=7, color="0.3")

    ax.set_xlim(-0.6, 2.6)
    ax.set_ylim(-0.6, 2.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=11)


def page_1(pdf):
    fig = plt.figure(figsize=(8.5, 11))
    fig.suptitle("KILNWORKS — Retrofit Engineering Packet (Revision R3)", fontsize=14, y=0.975)
    fig.text(0.5, 0.945, "Section A — Plant aisle graph and docking bays", ha="center", fontsize=11)

    ax1 = fig.add_axes([0.08, 0.63, 0.4, 0.27])
    draw_graph(ax1, show_open_edge=False, title="Closed-aisle designs (D0, D1, D2, D4)")
    ax2 = fig.add_axes([0.52, 0.63, 0.4, 0.27])
    draw_graph(ax2, show_open_edge=True, title="Open-aisle designs (D3, D5)")

    fig.text(0.08, 0.585, wrapped(
        "Solid edges are permanent aisles. The dashed edge 4-5 exists only in the "
        "open-aisle retrofit (right). Filled blue nodes are docking bays (capacity 2 "
        "robots): P at node 3, Q at node 5, K at node 1. The amber node (4) is an "
        "interior node (capacity 1) shared by all traffic converging on K -- note "
        "that node 1 (K) has only one edge, to node 4, in BOTH layouts.", width=100),
        fontsize=9, va="top")

    fig.text(0.08, 0.44, "Section B — Six retrofit designs under evaluation", fontsize=11)
    ax_tab = fig.add_axes([0.08, 0.24, 0.84, 0.18])
    ax_tab.axis("off")
    rows = [
        ["Design", "F (fixtures)", "G (power)", "Aisle", "Capital"],
        ["D0", "2", "5", "closed", "0"],
        ["D1", "3", "5", "closed", "7"],
        ["D2", "2", "6", "closed", "9"],
        ["D3", "2", "5", "open", "6"],
        ["D4", "3", "6", "closed", "16"],
        ["D5", "3", "6", "open", "22"],
    ]
    tbl = ax_tab.table(cellText=rows, loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.4)

    fig.text(0.08, 0.16, wrapped(
        "F = plant-wide fixture ceiling (a lot holds one fixture continuously from the "
        "start of its own preparation through curing). G = plant-wide aggregate power "
        "ceiling per minute. Capital is an investment figure used only for the final "
        "retrofit decision, never inside the simulation itself.", width=100),
        fontsize=9, va="top")
    pdf.savefig(fig)
    plt.close(fig)


def page_2(pdf):
    fig = plt.figure(figsize=(8.5, 11))
    fig.text(0.5, 0.965, "Section C — Campaign workload and cadence", ha="center", fontsize=12)

    fig.text(0.08, 0.925, wrapped(
        "Four campaigns (s=0..3), five lots each (j=0..4), 20 lots per design run "
        "end-to-end on one shared clock -- the four campaigns are NOT four "
        "independent resets. For lot (j,s):", width=95), fontsize=9.5, va="top")
    formula_text = (
        "  family(j,s) = (j + s) mod 2\n"
        "  release local(j) = 2 * floor(j/2)\n"
        "  release abs(j,s) = 35*s + release local(j)      [cadence = 35 minutes]\n"
        "  Pbase(j,s) = 5 + ((j*j) + 2s) mod 4     (duration if processed on P)\n"
        "  Qbase(j,s) = 4 + (3j + s) mod 5     (duration if processed on Q)"
    )
    fig.text(0.10, 0.865, formula_text, fontsize=9.5, family="monospace", va="top")

    fig.text(0.08, 0.66, wrapped(
        "Campaign release windows share one clock and are spaced by a fixed cadence -- "
        "a campaign's own completion tail routinely extends past the next campaign's "
        "release window (see the full trace requirement in the prompt).", width=95),
        fontsize=9.5, va="top")

    ax = fig.add_axes([0.10, 0.30, 0.82, 0.28])
    for s in range(4):
        start = 35 * s
        end = start + 2 * (4 // 2)  # last lot's release offset within the campaign
        ax.barh(s, end - start + 1, left=start, height=0.5, color="#8fbfe0", edgecolor="black")
        ax.text(start, s, f" campaign {s}", va="center", ha="left", fontsize=8)
    ax.set_yticks(range(4))
    ax.set_yticklabels([f"s={s}" for s in range(4)])
    ax.set_xlabel("minute (t) — release window shown for each campaign's five lots")
    ax.set_xlim(-2, 118)
    ax.grid(axis="x", color="0.85")
    pdf.savefig(fig)
    plt.close(fig)

    fig = plt.figure(figsize=(8.5, 11))
    fig.text(0.5, 0.965, "Section D — Preparation, fixtures, and machine memory", ha="center", fontsize=12)
    body = (
        "Each lot is prepared exactly once, on P or Q, in one uninterrupted setup-plus-\n"
        "processing operation; the machine then frees and the prepared lot waits in an\n"
        "unlimited buffer at that machine's dock until a robot collects it.\n\n"
        "Each machine remembers the family of the last lot it processed — this memory\n"
        "is never reset between campaigns. Setup = 0 if this is the machine's first job\n"
        "ever, or the new job's family matches the remembered family; otherwise setup = 2.\n\n"
        "Assignment policy each minute (P evaluated before Q): a machine that is busy is\n"
        "skipped. Otherwise, from lots that are released and not yet assigned AND for\n"
        "which a fixture is currently available (held fixtures < F), pick the one\n"
        "minimizing (setup + processing duration on this machine); tie-break by lowest\n"
        "global index (global index = 5s + j). If a machine's pool is empty, or it\n"
        "cannot currently afford its power draw, it claims nothing this minute and does\n"
        "NOT remove anything from the other machine's pool. A fixture becomes held only\n"
        "at an actually-started preparation, releasing only when that lot's curing ends."
    )
    fig.text(0.08, 0.90, body, fontsize=9.5, family="monospace", va="top")
    pdf.savefig(fig)
    plt.close(fig)


def page_3(pdf):
    fig = plt.figure(figsize=(8.5, 11))
    fig.text(0.5, 0.965, "Section E — Robot dispatch and the node-4 disruption", ha="center", fontsize=12)

    body = (
        "Robot 0 starts empty at node 3 (P); Robot 1 starts empty at node 5 (Q); once,\n"
        "at t=0 for the whole run. Each minute each robot takes exactly one action:\n"
        "wait, move one adjacent edge, pickup, or unload. Cargo capacity is 1. An\n"
        "action chosen at minute t becomes visible starting at minute t+1. Each edge\n"
        "carries at most one robot traversal per minute (no swap, no shared direction).\n\n"
        "Robot 0's action for the minute is fully decided — including whether the\n"
        "plant's power budget actually admits it — before Robot 1's action is even\n"
        "computed. Priority order for each robot, first applicable wins:\n"
        "  1. inside its own forced-offline window -> no action at all;\n"
        "  2. carrying cargo and at K -> unload;\n"
        "  3. empty at a node with a waiting prepared lot -> pick up the earliest-\n"
        "     prepared one (tie-break lowest global index);\n"
        "  4. carrying cargo, not at K -> move one step on the shortest path to K\n"
        "     (tie-break lowest next-hop id), or wait if blocked/refused by power;\n"
        "  5. empty, no lot here -> move one step toward the NEAREST node holding a\n"
        "     waiting prepared lot (tie-break lowest target-node id, then lowest\n"
        "     next-hop id);\n"
        "  6. empty, no lot anywhere in the plant -> move one step toward its own\n"
        "     home dock (3 for Robot 0, 5 for Robot 1); wait if already home.\n\n"
        "Node 1 (K) has only the edge 1-4 in both aisle layouts (Section A), so every\n"
        "delivery to K passes through node 4 — the single shared junction — in every\n"
        "design regardless of the aisle retrofit."
    )
    fig.text(0.08, 0.94, body, fontsize=9.3, family="monospace", va="top")

    ax = fig.add_axes([0.12, 0.10, 0.76, 0.22])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xticks(range(0, 13))
    ax.grid(axis="x", color="0.85")
    A = 3  # illustrative arrival minute for THIS figure only; actual arrival varies by design
    W = 6
    ax.add_patch(mpatches.Rectangle((A, 0.25), W, 0.5, facecolor="#e08a8a",
                                     edgecolor="black"))
    ax.annotate("", xy=(A, 0.10), xytext=(A + W, 0.10),
                arrowprops=dict(arrowstyle="<->"))
    ax.text(A + W / 2, 0.04, "read the shaded span's width directly off the axis\n"
                              "(count grid lines) — that is Robot 0's forced-offline\n"
                              "duration once it first reaches node 4", ha="center", fontsize=8)
    ax.text(A, 0.85, "Robot 0 arrives\nat node 4", ha="left", fontsize=8)
    ax.set_title("Illustrative timeline — forced-offline window at first node-4 arrival\n"
                 "(the arrival minute itself is design-dependent; only the shaded span's length is normative)",
                 fontsize=9)
    pdf.savefig(fig)
    plt.close(fig)


def page_4(pdf):
    fig = plt.figure(figsize=(8.5, 11))
    fig.text(0.5, 0.965, "Section F — Oven batching, power admission, and tariff", ha="center", fontsize=12)

    body = (
        "The oven holds one batch at a time; membership is fixed the moment a batch\n"
        "starts and never changes. A batch cures for (4 + family) minutes. Batching is\n"
        "by family value alone — lots from different campaigns MAY be batched together.\n\n"
        "Bounded pairing timer (evaluated after both robots' actions, same minute\n"
        "eligible): when the oven is idle with no pending anchor, the earliest-arrived\n"
        "waiting uncured lot (tie-break lowest global index) becomes the pending\n"
        "anchor, with a deadline of its own arrival minute + 2. Every minute the anchor\n"
        "is pending and the oven is idle: if another arrived, uncured, same-family lot\n"
        "exists, start the batch now with the anchor plus the lowest-global-index such\n"
        "partner (size 2); else if the deadline has passed, start with the anchor alone\n"
        "(size 1); otherwise wait. A power refusal does not forfeit the anchor or its\n"
        "deadline — it simply retries next minute.\n\n"
        "Power admission is ONE ordered pass per minute, not two separate passes:\n"
        "machine P start, machine Q start, Robot 0's action, Robot 1's action, then a\n"
        "new oven start — each step drawing from whatever budget remains after the\n"
        "previous steps. Already-ongoing operations from an earlier minute are\n"
        "mandatory and keep their power. Draws: P=2, Q=3, oven=3, each robot\n"
        "move/pickup/unload=1, wait=0. Total draw must never exceed the design's G."
    )
    fig.text(0.08, 0.94, body, fontsize=9.3, family="monospace", va="top")

    ax = fig.add_axes([0.12, 0.10, 0.76, 0.24])
    ts = list(range(0, 42))
    mult = [1 + ((t // 7) % 3) for t in ts]
    ax.step(ts, mult, where="post", color="black")
    ax.set_xlabel("minute (t)")
    ax.set_ylabel("tariff multiplier")
    ax.set_yticks([1, 2, 3])
    ax.grid(color="0.9")
    ax.set_title("Tariff multiplier applied to that minute's total power draw:\n"
                 "multiplier(t) = 1 + (floor(t/7) mod 3). Bill = Σ power(t) × multiplier(t)\n"
                 "over t = 0 .. makespan−1, on the design's single continuous clock.", fontsize=9)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    with PdfPages(OUT, metadata={}) as pdf:
        page_1(pdf)
        page_2(pdf)
        page_3(pdf)
        page_4(pdf)
        info = pdf.infodict()
        for k in list(info.keys()):
            del info[k]
        info["Title"] = "KILNWORKS Retrofit Engineering Packet"
    print("wrote", OUT)


if __name__ == "__main__":
    main()
