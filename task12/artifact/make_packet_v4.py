#!/usr/bin/env python3
"""Builds the COHERE-12 packet v2 (cohere12_v2.pdf): search over placement, line map, Q, B.

Link latencies, node layout and the baseline line map appear only in figures. Metadata stripped, figures
rasterized, ICC profile dropped, file ID removed.
"""
import io
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import fitz

REVISION = "cohere12_v4"
HERE = os.path.dirname(os.path.abspath(__file__))
DPI = 300
PAGE_W, PAGE_H = 612, 792

LINK_LAT = {(0, 1): 1, (1, 2): 2, (2, 3): 1, (4, 5): 2, (5, 6): 1, (6, 7): 3,
            (0, 4): 1, (1, 5): 3, (2, 6): 1, (3, 7): 2}
PLACEMENTS = {"P1": (0, 7), "P2": (1, 6), "P3": (3, 4), "P4": (2, 5)}


def png(fig):
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=DPI, metadata={"Software": ""})
    plt.close(fig)
    return b.getvalue()


def fig_floorplan():
    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    ax.set_xlim(-0.8, 3.8); ax.set_ylim(-0.4, 2.3); ax.axis("off"); ax.set_aspect("equal")
    pos = {}
    for n in range(8):
        r, c = divmod(n, 4)
        x, y = c * 1.0, (1 - r) * 1.15 + 0.5
        pos[n] = (x, y)
    for (a, b) in LINK_LAT:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        ax.plot([x1, x2], [y1, y2], color="#555", lw=2.2, zorder=1)
    for n, (x, y) in pos.items():
        ax.add_patch(FancyBboxPatch((x - 0.2, y - 0.17), 0.4, 0.34, boxstyle="round,pad=0.02",
                                    fc="#dbe8f5", ec="#1f4e79", lw=1.3, zorder=2))
        ax.text(x, y + 0.05, f"N{n}", ha="center", va="center", fontsize=11, weight="bold", zorder=3)
        ax.text(x, y - 0.08, f"core C{n}", ha="center", va="center", fontsize=7, zorder=3)
    ax.annotate("", xy=(3.55, 2.15), xytext=(3.05, 2.15), arrowprops=dict(arrowstyle="->"))
    ax.text(3.3, 2.22, "column +1", ha="center", fontsize=7)
    ax.annotate("", xy=(-0.55, 0.4), xytext=(-0.55, 1.6), arrowprops=dict(arrowstyle="->"))
    ax.text(-0.62, 1.0, "row +1", rotation=90, ha="right", va="center", fontsize=7)
    ax.text(-0.5, 2.15, "row 0", fontsize=7); ax.text(-0.5, 0.05, "row 1", fontsize=7)
    for c in range(4):
        ax.text(c, 2.1, f"col {c}", ha="center", fontsize=7)
    ax.set_title("Figure 1. Floorplan: 2 x 4 mesh. Each node has one core with its private cache;\n"
                 "a directory bank placed on a node shares that node's router. Lines are bidirectional links.", fontsize=9)
    return fig


def fig_links():
    names = [f"N{a}-N{b}" for (a, b) in LINK_LAT]
    vals = list(LINK_LAT.values())
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    ax.barh(range(len(names)), vals, color="#2b5d8a", height=0.55)
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 4); ax.set_xticks([0, 1, 2, 3, 4]); ax.set_xticks([x / 4 for x in range(17)], minor=True)
    ax.set_xticklabels([])
    ax.grid(axis="x", which="major", color="#888", lw=0.8); ax.grid(axis="x", which="minor", color="#ddd", lw=0.4)
    ax.set_axisbelow(True)
    ax.set_xlabel("link latency (axis starts at 0 cycles; major gridline = 1 cycle; same in both directions)", fontsize=8)
    ax.set_title("Figure 2. Link timing: cycles from leaving one router to arriving at the other.", fontsize=9)
    return fig


BASE_MAP = 0x4B2D  # bit L = bank of line L in the baseline


def fig_linemap():
    fig, ax = plt.subplots(figsize=(8.4, 2.6))
    ax.set_xlim(-0.5, 16.5); ax.set_ylim(-1.2, 1.6); ax.axis("off")
    for L in range(16):
        b = BASE_MAP >> L & 1
        ax.add_patch(plt.Rectangle((L, 0), 0.9, 0.9, fc="#f4c542" if b else "#5b8fd1", ec="black", lw=0.8))
        ax.text(L + 0.45, 1.05, f"L{L}", ha="center", fontsize=8)
    ax.add_patch(plt.Rectangle((2, -0.95), 0.6, 0.5, fc="#5b8fd1", ec="black", lw=0.8)); ax.text(2.8, -0.7, "home = D0", va="center", fontsize=8)
    ax.add_patch(plt.Rectangle((7, -0.95), 0.6, 0.5, fc="#f4c542", ec="black", lw=0.8)); ax.text(7.8, -0.7, "home = D1", va="center", fontsize=8)
    ax.set_title("Figure 5. Baseline line map: the home directory bank of each memory line L0..L15.", fontsize=9)
    return fig


CACHE_ROWS = [
    ("I (no way)", "miss: GetS to home; IS_D", "miss: GetM to home; IM_AD", "-", "-", "-", "-", "-", "-", "-"),
    ("IS_D", "stall", "stall", "-", "-", "stall", "-", "-> S; load done", "-> S; load done", "-"),
    ("IM_AD", "stall", "stall", "stall", "stall", "-", "-", "see note A", "-> M; store done", "counter -1"),
    ("IM_A", "stall", "stall", "stall", "stall", "-", "-", "-", "-", "see note B"),
    ("S", "hit", "GetM to home; SM_AD", "-", "-", "InvAck to requester; -> I (way freed)", "-", "-", "-", "-"),
    ("SM_AD", "hit", "stall", "stall", "stall", "InvAck to requester; -> IM_AD", "-", "see note A", "-> M; store done", "counter -1"),
    ("SM_A", "hit", "stall", "stall", "stall", "-", "-", "-", "-", "see note B"),
    ("M", "hit", "hit", "Data to requester, then Data to home; -> S", "Data to requester; -> I (way freed)", "-", "-", "-", "-", "-"),
    ("MI_A", "stall", "stall", "Data to requester, then Data to home; -> SI_A", "Data to requester; -> II_A", "-", "-> I (way freed)", "-", "-", "-"),
    ("SI_A", "stall", "stall", "-", "-", "InvAck to requester; -> II_A", "-> I (way freed)", "-", "-", "-"),
    ("II_A", "stall", "stall", "-", "-", "-", "-> I (way freed)", "-", "-", "-"),
]
CACHE_COLS = ["state", "Load", "Store", "FwdGetS", "FwdGetM", "Inv", "PutAck", "Data from home", "Data from a cache", "InvAck"]

DIR_ROWS = [
    ("I", "Data(ack=0) to req; add req to sharers; -> S", "Data(ack=0) to req; owner=req; -> M", "PutAck", "PutAck", "-"),
    ("S", "Data(ack=0) to req; add req to sharers", "Data(ack=n) to req, n = sharers other than req; then Inv to each such sharer in ascending core order; clear sharers; owner=req; -> M",
     "remove req from sharers; PutAck; if sharers now empty -> I", "remove req from sharers; PutAck; if sharers now empty -> I", "-"),
    ("M", "FwdGetS to owner; add req and owner to sharers; clear owner; -> S_D", "FwdGetM to owner; owner=req", "PutAck",
     "if req is owner: memory=data, clear owner, -> I; PutAck. Otherwise PutAck only", "-"),
    ("S_D", "stall", "stall", "remove req from sharers; PutAck", "remove req from sharers; PutAck", "memory=data; -> S"),
]
DIR_COLS = ["state", "GetS", "GetM", "PutS", "PutM", "Data (from a cache)"]


def fig_table(rows, cols, title, notes, widths, fs):
    import textwrap
    wrapped = [[textwrap.fill(str(c), w) for c, w in zip(r, widths)] for r in rows]
    nlines = [max(x.count("\n") + 1 for x in r) for r in wrapped]
    total = sum(nlines) + 2
    fig = plt.figure(figsize=(11, 0.17 * total + 0.9 + 0.22 * len(notes)))
    ax = fig.add_axes([0.02, 0.02 + 0.03 * len(notes), 0.96, 0.9 - 0.03 * len(notes)])
    ax.axis("off")
    hdr = [textwrap.fill(c, w) for c, w in zip(cols, widths)]
    tb = ax.table(cellText=wrapped, colLabels=hdr, cellLoc="left", colLoc="left",
                  colWidths=[w / sum(widths) for w in widths], bbox=[0, 0, 1, 1])
    tb.auto_set_font_size(False); tb.set_fontsize(fs)
    unit = 1.0 / total
    for (i, j), cell in tb.get_celld().items():
        cell.set_height(unit * (2 if i == 0 else nlines[i - 1]))
        if i == 0:
            cell.set_facecolor("#dbe8f5")
    fig.suptitle(title, fontsize=10, y=0.985)
    for k, n in enumerate(notes):
        fig.text(0.02, 0.012 + 0.03 * (len(notes) - 1 - k) * 1.0, n, fontsize=8)
    return fig


def spec_text():
    return """COHERE-12 ENGINEERING PACKET: DIRECTORY COHERENCE ON A 2 x 4 MESH

1. SCOPE AND DECISION
Eight cores (C0..C7) run fixed programs over sixteen shared memory lines (L0..L15). Each core has a private cache; two directory banks, D0 and D1, keep the caches coherent with an MSI protocol with transient states. Each memory line has one home bank, given by the line map. Each directory bank has a request queue of capacity Q (requests that arrive to a full queue are refused with Nack), and a refused cache retries after a backoff with base B.
A configuration is: the two nodes that host the directory banks (any two different nodes; D0 is always on the lower-numbered of the two), the line map (each of the 16 lines assigned to D0 or D1, written as the 16-bit number whose bit L is 1 when line L's home is D1), Q in {1, 2, 3, 4} and B in {1, 2, 4, 8}. That is 28 x 65,536 x 4 x 4 = 29,360,128 configurations.
Figure 1 gives each node's row and column, Figure 2 every link's latency, Figures 3 and 4 the cache and directory controllers, and Figure 5 the baseline line map. Everything below is normative.

2. NETWORK
Messages travel on three virtual networks: RESP (Data, InvAck, Nack), FWD (FwdGetS, FwdGetM, Inv, PutAck) and REQ (GetS, GetM, PutS, PutM). Routing is XY: a message first moves along its row until it reaches the destination's column, then along the column. A message between two entities on the same node does not use a link and is placed in the destination's input queue at the arrivals stage of the next cycle.
Each directed link sends at most one message per cycle (pipelined: a new message may leave every cycle). A message that entered a router (by arrival or by being sent there) in cycle t may leave on its next link in cycle t+1 or later. Among messages waiting at a router for the same outgoing link, the link sends the one on the highest-priority network (RESP before FWD before REQ), then the one that entered that router earliest, then the one with the lowest serial number. A message leaving in cycle d arrives at the next router in cycle d + latency of that link.
Every message receives a serial number when it is created: 1, 2, 3, ... in creation order across the whole system.

3. CYCLE STRUCTURE
Cycles are numbered from 1. In each cycle, in this order:
(1) Links: every directed link sends at most one waiting message (Section 2).
(2) Arrivals: messages whose arrival cycle is now are handled in increasing serial order. A message at its destination node goes to the end of the destination entity's input queue for its network, except that a REQ message arriving at a directory whose REQ queue already holds Q messages is refused (recorded for a Nack). Any other message is placed at the router to wait for its next link.
(3) Controllers, in the order D0, D1, C0, C1, ..., C7.
Messages created in a cycle are sent from the creator's router no earlier than the next cycle.

4. DIRECTORY STEP (each bank, each cycle)
(a) If its RESP queue is not empty, it removes and handles the first message (Figure 4, Data column).
(b) If its REQ queue is not empty, it handles the first message per Figure 4; if Figure 4 says stall, the message stays first in the queue and the bank does nothing more with REQ this cycle (later requests wait behind it).
(c) It sends a Nack (on RESP) to the sender of each request refused in this cycle's arrivals stage, in the order they were refused. The Nack names the refused request type.
A directory bank keeps, per line, a state (I, S, M, S_D), a sharer set, an owner and the memory value (initially 0). A Data message from the directory carries the memory value and an ack count.

5. CACHE AND CORE STEP (each core, each cycle)
(a) If the RESP queue is not empty, remove and handle its first message (Figure 3; Nack per Section 6).
(b) FWD queue: scan from the first message. If a message's line is blocked, skip it. Otherwise handle it per Figure 3: if Figure 3 says stall, leave it in place and mark its line blocked; if not, remove it, handle it, and stop scanning. At most one FWD message is handled per cycle.
(c) If any refused request has its retry cycle at or before now, resend the one with the earliest retry cycle (ties: lower line) on REQ to the line's home; a PutM carries the line's current data.
(d) Core: if the core is busy, waiting for a miss, or finished, nothing happens. Otherwise it takes its next operation:
WAIT n: the core is busy for this cycle and the next n-1 cycles; its next operation is taken n cycles later.
LD L / ST L with L present in the cache: follow the Load or Store column of Figure 3 for L's state. A hit completes now and the next operation is taken next cycle. "stall" means the operation is retried next cycle. A store in S starts an upgrade (the core waits).
LD L / ST L with L not present: if L's set has an empty way, put L in the lowest-numbered empty way in state IS_D (load) or IM_AD (store), send GetS or GetM to L's home, and wait. If the set is full, choose a victim among the set's ways in state S or M: the one with the smallest LRU stamp (ties: lower way index); send PutS (state S, way goes to SI_A) or PutM with its data (state M, way goes to MI_A) to the victim line's home. The operation is retried next cycle. If no way in the set is in S or M, the operation is retried next cycle.
A core with no operation left at step (d) is finished in that cycle.
Caches have 2 sets of 2 ways; line L uses set (L div 2) mod 2. A way leaves the cache (becomes empty) when Figure 3 says "way freed". The LRU stamp of a way is the cycle in which it was last used: a hit, the completion of a waiting load or store on it (including an upgrade), or its allocation, whichever is latest.
Miss completion: a waiting load completes when its line reaches S; it returns the line's data. A waiting store (miss or upgrade) completes when its line reaches M; the core then writes the value 1000 x (core number) + (number of stores this core has completed, counting this one). The core takes its next operation in the following cycle. A store hit writes the same way.
Data handling in IM_AD and SM_AD (note A): Data from home with ack count n adds n to the line's ack counter (which starts at 0 and may have been lowered by earlier InvAcks); if the counter is then 0 the line goes to M and the store completes, otherwise IM_AD goes to IM_A and SM_AD goes to SM_A. InvAck in IM_A or SM_A (note B) lowers the counter by 1; when it reaches 0 the line goes to M and the store completes. A cache sends Data and InvAck messages on RESP and its requests on REQ.

6. NACK AND RETRY
When a cache receives Nack for request type X on line L, it increments that request's refusal count k (k starts at 0 when the request is first sent) and schedules a resend of X on L at cycle now + min(B x 2^(k-1), 64). The line's state does not change. The refusal count is cleared when the request is answered (Data received for the line, or PutAck).

7. WORKLOAD
Each core runs 2400 operations generated by: x(next) = (1103515245 x + 12345) mod 2^31, starting from x = 101 + 7 x (core number). For each operation: advance x once, r = x div 256, kind = r mod 10; advance x again, s = x div 256; line = s mod 3 if ((s div 16) mod 10) < 6, otherwise s mod 16. kind 0..4: LD line; kind 5..7: ST line; kind 8..9: WAIT (1 + ((s div 8) mod 7)).

8. RUN END AND METRICS
A run ends at the end of the first cycle in which every core is finished, no message is in a queue, router or link, and no resend is scheduled. Makespan: the latest cycle in which a core became finished. Load-miss latency: completion cycle minus issue cycle, for every load that sent GetS (hits are excluded); the issue cycle is the cycle in which that load's GetS was first sent, not earlier cycles spent retrying the operation or evicting. p95: sort the latencies ascending and take the element at zero-based index min(n-1, floor(0.95 n)). Messages: the number of messages created (every serial number), all types. Nacks: the number of Nack messages created.

9. BASELINE AND OBJECTIVE
Baseline: D0 on N0, D1 on N7, Q = 2, B = 2, line map of Figure 5.
Objective: the optimal configuration has the smallest makespan over all 29,360,128 configurations; ties are broken by fewer messages, then lower D0 node, lower D1 node, smaller Q, smaller B, and smaller line-map number, in that order."""


def text_page(doc, text, fs=8.0):
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    rc = page.insert_textbox(fitz.Rect(44, 40, PAGE_W - 44, PAGE_H - 36), text, fontsize=fs, fontname="helv")
    if rc < 0:
        raise RuntimeError("overflow %s" % rc)


def image_page(doc, data, landscape=False):
    w, h = (PAGE_H, PAGE_W) if landscape else (PAGE_W, PAGE_H)
    page = doc.new_page(width=w, height=h)
    img = fitz.open("png", data)
    iw, ih = img[0].rect.width, img[0].rect.height
    s = min((w - 60) / iw, (h - 60) / ih)
    x0 = (w - iw * s) / 2
    page.insert_image(fitz.Rect(x0, 30, x0 + iw * s, 30 + ih * s), stream=data)


def main():
    doc = fitz.open()
    t = spec_text()
    cut = t.index("5. CACHE AND CORE STEP")
    text_page(doc, t[:cut]); text_page(doc, t[cut:])
    image_page(doc, png(fig_floorplan()))
    image_page(doc, png(fig_links()))
    image_page(doc, png(fig_linemap()))
    image_page(doc, png(fig_table(CACHE_ROWS, CACHE_COLS,
        "Figure 3. Cache controller (per line). '-' = cannot occur. 'stall' = leave the message (or retry the core operation) as Section 5 says.",
        ["Note A: Data from home in IM_AD / SM_AD: add the message's ack count to the line's ack counter; counter 0 -> M and the store completes; otherwise -> IM_A / SM_A.",
         "Note B: InvAck in IM_A / SM_A: counter -1; when it reaches 0 -> M and the store completes. Nack in any state: Section 6. Data from home or a cache sets the line's data."],
        [7, 9, 10, 14, 13, 13, 8, 10, 9, 7], 6.2)), landscape=True)
    image_page(doc, png(fig_table(DIR_ROWS, DIR_COLS,
        "Figure 4. Directory controller (per line). 'stall' = the request stays first in the REQ queue.",
        ["Data, FwdGetS, FwdGetM, Inv and PutAck name the original requester where relevant; Inv and Fwd* carry the requester so the cache can answer it.",
         "A cache answering FwdGetS sends Data to the requester first, then Data to the home directory."],
        [5, 22, 30, 20, 26, 12], 7.0)), landscape=True)
    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    for p in doc:
        for im in p.get_images(full=True):
            doc.xref_set_key(im[0], "ColorSpace", "/DeviceRGB")
    tmp = os.path.join(HERE, ".tmp.pdf")
    doc.save(tmp, garbage=4, deflate=True, clean=True); doc.close()
    doc = fitz.open(tmp)
    doc.xref_set_key(-1, "Info", "null"); doc.xref_set_key(-1, "ID", "null")
    cat = doc.pdf_catalog()
    pages_ref = doc.xref_get_key(cat, "Pages")[1]
    doc.update_object(cat, "<< /Type /Catalog /Pages %s >>" % pages_ref)
    out = os.path.join(HERE, f"{REVISION}.pdf")
    doc.save(out, garbage=4, deflate=True, clean=True, no_new_id=True); doc.close(); os.remove(tmp)
    raw = open(out, "rb").read()
    i = raw.find(b"% Written by")
    if i != -1:
        j = raw.find(b"\n", i)
        raw = raw[:i] + b"%" + b" " * (j - i - 1) + raw[j:]
        open(out, "wb").write(raw)
    print("wrote", out)


if __name__ == "__main__":
    main()
