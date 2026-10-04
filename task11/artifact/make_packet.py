#!/usr/bin/env python3
"""Builds the TENURE-11 engineering packet PDF.

Every content revision gets a new REVISION (Playbook mistake #46).
All figures are rasterized (matplotlib Agg -> PNG -> image XObject); no vector
drawing objects. Decisive constants (HEADER, OLD_SIZE, base payloads, phase
boundaries) and the survivor-overflow promotion edge appear only in figures,
never in the prose (visual-ablation test). Document metadata is stripped.
"""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import fitz  # PyMuPDF

REVISION = "tenure11_v1"
DPI = 300
PAGE_W, PAGE_H = 612, 792


def render_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, metadata={"Software": ""})
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------- Figure 1
def fig_heap_map():
    fig, ax = plt.subplots(figsize=(8.4, 3.6))
    ax.set_xlim(-4096, 139264)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    # old generation bar, drawn to scale on the address axis
    ax.add_patch(Rectangle((0, 1.0), 131072, 0.8, facecolor="#d9e4f2", edgecolor="black", lw=1.2))
    ax.text(65536, 1.4, "OLD GENERATION (non-moving, free list)", ha="center", va="center", fontsize=10)
    # address axis
    y0 = 0.75
    ax.plot([0, 139264], [y0, y0], color="black", lw=1)
    for x in range(0, 139265, 8192):
        major = x % 49152 == 0
        ax.plot([x, x], [y0, y0 - (0.18 if major else 0.09)], color="black", lw=1)
        if major:
            ax.text(x, y0 - 0.32, f"{x // 1024} KiB", ha="center", va="top", fontsize=9)
    ax.text(69632, 0.05, "old-generation address (minor tick = 8 KiB)", ha="center", fontsize=9)
    # young generation, not to scale: sizes are sweep parameters
    ax.add_patch(Rectangle((0, 2.25), 52000, 0.6, facecolor="#f4e2c6", edgecolor="black", lw=1))
    ax.text(26000, 2.55, "EDEN  (size = EDEN, swept)", ha="center", va="center", fontsize=9)
    ax.add_patch(Rectangle((60000, 2.25), 30000, 0.6, facecolor="#e6f0d8", edgecolor="black", lw=1))
    ax.text(75000, 2.55, "SURVIVOR S0 (SURV)", ha="center", va="center", fontsize=9)
    ax.add_patch(Rectangle((96000, 2.25), 30000, 0.6, facecolor="#e6f0d8", edgecolor="black", lw=1))
    ax.text(111000, 2.55, "SURVIVOR S1 (SURV)", ha="center", va="center", fontsize=9)
    ax.text(133000, 2.55, "young: not\nto scale", ha="left", va="center", fontsize=8, style="italic")
    ax.set_title("Heap map. OLD_SIZE is the full span of the old-generation bar.", fontsize=11)
    return fig


# ---------------------------------------------------------------- Figure 2
def fig_object_layout():
    fig, ax = plt.subplots(figsize=(8.4, 2.6))
    ax.set_xlim(-2, 66)
    ax.set_ylim(0, 2.6)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 1.1), 16, 0.8, facecolor="#cfcfcf", edgecolor="black", lw=1.2))
    ax.text(8, 1.5, "HEADER", ha="center", va="center", fontsize=10)
    ax.add_patch(Rectangle((16, 1.1), 40, 0.8, facecolor="white", edgecolor="black", lw=1.2, hatch="//"))
    ax.text(36, 1.5, "payload (kind dependent)", ha="center", va="center", fontsize=9,
            bbox=dict(facecolor="white", edgecolor="none"))
    ax.add_patch(Rectangle((56, 1.1), 8, 0.8, facecolor="#eeeeee", edgecolor="black", lw=1, ls="--"))
    ax.text(60, 2.1, "padding to ALIGN", ha="center", fontsize=8)
    y0 = 0.85
    ax.plot([0, 64], [y0, y0], color="black", lw=1)
    for x in range(0, 65, 2):
        major = x % 10 == 0
        ax.plot([x, x], [y0, y0 - (0.2 if major else 0.1)], color="black", lw=1)
        if major:
            ax.text(x, y0 - 0.32, str(x), ha="center", va="top", fontsize=9)
    ax.text(32, 0.05, "byte offset within an object (tick = 2 bytes)", ha="center", fontsize=9)
    ax.set_title("Object layout. Every object starts with a HEADER of this length.", fontsize=11)
    return fig


# ---------------------------------------------------------------- Figure 3
KIND_BASE = [("TEMP", 24, 0), ("SESSION", 96, 1), ("BLOB", 96, 0),
             ("ENTRY", 56, 1), ("NODE", 40, 1), ("REG", 112, 4)]


def fig_kinds():
    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    names = [k for k, _, _ in KIND_BASE]
    vals = [v for _, v, _ in KIND_BASE]
    xs = range(len(names))
    ax.bar(xs, vals, width=0.55, color="#9db7d6", edgecolor="black")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylim(0, 160)
    ax.set_yticks(range(0, 161, 32))
    ax.set_yticks(range(0, 161, 8), minor=True)
    ax.grid(axis="y", which="minor", color="#dddddd", lw=0.6)
    ax.grid(axis="y", which="major", color="#999999", lw=0.9)
    ax.set_axisbelow(True)
    ax.set_ylabel("base payload (bytes); minor gridline = 8 bytes", fontsize=9)
    for x, (_, v, slots) in zip(xs, KIND_BASE):
        for s in range(slots):
            ax.plot(x - 0.18 + 0.12 * s, v + 9, marker="o", color="black", ms=5)
    ax.plot([], [], marker="o", color="black", ls="none", ms=5, label="one reference slot")
    ax.legend(loc="upper left", fontsize=9)
    notes = ("Size-varying kinds (i = index of the allocating operation):\n"
             "BLOB payload = base + 96 x (i mod 13)    ENTRY payload = base + 24 x (i mod 3)\n"
             "NODE payload = base + 8 x (i mod 5)      all other kinds: payload = base")
    fig.text(0.5, 0.015, notes, ha="center", fontsize=8.5, family="monospace")
    fig.subplots_adjust(bottom=0.24)
    ax.set_title("Object kinds: base payload (bar height) and reference slots (dots)", fontsize=11)
    return fig


# ---------------------------------------------------------------- Figure 4
MIXES = [
    ("warm", 0, 4000, "TEMP TEMP SESSION NODE TEMP ENTRY TEMP NODE TEMP SESSION"),
    ("steady", 4000, 16000, "TEMP SESSION TEMP ENTRY NODE TEMP ENTRY TEMP NODE TEMP"),
    ("burst", 16000, 22000, "SESSION TEMP SESSION ENTRY SESSION NODE SESSION TEMP ENTRY NODE"),
    ("drain", 22000, 26000, "TEMP TEMP ENTRY TEMP NODE TEMP TEMP TEMP ENTRY TEMP"),
]


def fig_timeline():
    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    ax.set_xlim(-600, 26600)
    ax.set_ylim(-6.2, 2.2)
    ax.axis("off")
    colors = ["#f6d7a7", "#bfd8b8", "#e8b4b8", "#c7cbe8"]
    for (name, a, b, _), c in zip(MIXES, colors):
        ax.add_patch(Rectangle((a, 0.6), b - a, 1.0, facecolor=c, edgecolor="black", lw=1))
        ax.text((a + b) / 2, 1.1, name, ha="center", va="center", fontsize=10)
    y0 = 0.45
    ax.plot([0, 26000], [y0, y0], color="black", lw=1)
    for x in range(0, 26001, 1000):
        major = x % 8000 == 0
        ax.plot([x, x], [y0, y0 - (0.3 if major else 0.15)], color="black", lw=1)
        if major:
            ax.text(x, y0 - 0.45, str(x), ha="center", va="top", fontsize=9)
    ax.plot([26000, 26000], [y0, 1.8], color="black", lw=1.5)
    ax.text(26000, 1.9, "end", ha="center", fontsize=8)
    ax.text(13000, -0.55, "operation index i (minor tick = 1000 operations)", ha="center", fontsize=9)
    ax.text(-500, -1.05, "Allocation kind for operation i = phase mix entry at position (i mod 10):",
            fontsize=9, ha="left")
    for r, (name, _, _, mix) in enumerate(MIXES):
        y = -2.1 - r * 1.0
        ax.text(-500, y, f"{name:>6}", fontsize=8.5, family="monospace", va="center")
        for p, k in enumerate(mix.split()):
            x = 2000 + p * 2400
            ax.add_patch(Rectangle((x, y - 0.35), 2300, 0.7, facecolor=colors[r], edgecolor="black", lw=0.6))
            ax.text(x + 1150, y, k, ha="center", va="center", fontsize=7.5)
    for p in range(10):
        ax.text(2000 + p * 2400 + 1150, -1.6, str(p), ha="center", va="center", fontsize=8,
                color="#444444")
    ax.set_title("Mutator workload phases (drawn to scale on the operation axis)", fontsize=11)
    return fig


# ---------------------------------------------------------------- Figure 5
def box(ax, x, y, w, h, text, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", facecolor=color,
                                edgecolor="black", lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10)


def arrow(ax, x1, y1, x2, y2, label, lx, ly, rad=0.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="black",
                                connectionstyle=f"arc3,rad={rad}"))
    ax.text(lx, ly, label, ha="center", va="center", fontsize=8,
            bbox=dict(facecolor="white", edgecolor="none", pad=1))


def fig_lifecycle():
    fig, ax = plt.subplots(figsize=(8.6, 7.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9)
    ax.axis("off")
    # boxes: (x, y, w, h)
    box(ax, 0.4, 7.6, 2.0, 0.7, "new object", "#ffffff")
    box(ax, 0.4, 4.0, 2.0, 0.9, "EDEN", "#f4e2c6")
    box(ax, 4.0, 4.0, 2.0, 0.9, "SURVIVOR", "#e6f0d8")
    box(ax, 7.6, 4.0, 2.0, 0.9, "OLD", "#d9e4f2")
    box(ax, 7.6, 0.9, 2.0, 0.7, "free block", "#eeeeee")
    # new object -> EDEN
    arrow(ax, 1.4, 7.6, 1.4, 4.9, "size < PT,\nor PT off", 0.55, 6.25)
    # new object -> OLD, routed across the top
    arrow(ax, 2.4, 7.95, 8.6, 4.9, "PT on and size >= PT", 6.4, 7.35, rad=-0.12)
    # EDEN -> SURVIVOR
    arrow(ax, 2.4, 4.45, 4.0, 4.45, "", 0, 0)
    ax.text(3.2, 5.25, "minor GC, reachable:\nage+1 < T and\nfits in to-space", ha="center",
            va="center", fontsize=8)
    # SURVIVOR self loop above the box
    arrow(ax, 4.4, 4.9, 5.6, 4.9, "", 0, 0, rad=-1.4)
    ax.text(5.0, 6.15, "next minor GC, reachable:\nage+1 < T and fits in to-space", ha="center",
            va="center", fontsize=8)
    # SURVIVOR -> OLD, two edges
    arrow(ax, 6.0, 4.7, 7.6, 4.7, "", 0, 0)
    ax.text(6.8, 5.05, "age+1 >= T", ha="center", fontsize=8)
    arrow(ax, 6.0, 4.2, 7.6, 4.2, "", 0, 0)
    ax.text(6.8, 3.55, "age+1 < T, but does\nnot fit in to-space", ha="center", va="center", fontsize=8)
    # EDEN -> OLD, routed below
    arrow(ax, 1.4, 4.0, 8.6, 4.0, "", 0, 0, rad=0.32)
    ax.text(5.0, 2.15, "minor GC, reachable: age+1 >= T, or\nage+1 < T but does not fit in to-space",
            ha="center", va="center", fontsize=8)
    # OLD -> free block
    arrow(ax, 9.3, 4.0, 9.3, 1.6, "", 0, 0)
    ax.text(8.55, 2.9, "major GC:\nnot reachable", ha="center", va="center", fontsize=8)
    ax.text(0.2, 0.35, "Reachable means reached by the minor collection's evacuation order. "
            "Unreachable young objects are\nabandoned when eden and the from-space are emptied.",
            fontsize=8)
    ax.set_title("Object lifecycle (T = tenuring threshold, PT = pretenure threshold)", fontsize=11)
    return fig


# ---------------------------------------------------------------- Figure 6
def fig_log_example():
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.axis("off")
    text = (
        "GC event log format, worked example with FAKE numbers. The values below\n"
        "do not come from this model and need not satisfy its rules; they show\n"
        "the TEXT FORMAT only.\n\n"
        "TENURE11-GCLOG-V1\n"
        "1;m;37;5104;912;0;0;0;912;151\n"
        "2;M;58;0;0;0;3320;7;2208;360\n"
        "3;m;58;4488;1376;3;0;0;3584;157\n"
        "...\n\n"
        "Fields: n;type;op;copied;promoted;remset;marked;freed;occupancy;pause\n"
        "One line per GC event in the order the events happen; integers in\n"
        "plain decimal, no padding, no spaces; type is m (minor) or M (major);\n"
        "fields that do not apply to the type are 0. Lines are joined with a\n"
        "single newline and the text ends with one trailing newline. The log\n"
        "hash is the first 16 lowercase hex characters of SHA-256 of that text."
    )
    ax.text(0.02, 0.97, text, va="top", ha="left", family="monospace", fontsize=9.2,
            transform=ax.transAxes)
    ax.set_title("Baseline GC event log (certificate) format", fontsize=11)
    return fig


SPEC_TEXT = """\
TENURE-11 ENGINEERING PACKET: GENERATIONAL COLLECTOR TUNING

1. PURPOSE AND SCOPE

A latency-bounded service runs one fixed allocation workload (Figure 4) on a generational garbage collector. The task is to simulate the collector exactly as described here for every candidate configuration, then choose settings. All quantities are bytes or integer pause units. All arithmetic is integer; every division rounds down. Nothing here depends on wall-clock time, randomness, or any external library.

2. OBJECTS AND SIZES

Every object has a kind (Figure 3). Its size is HEADER (Figure 2) plus its payload, rounded up to the next multiple of ALIGN = 8. Payload is the kind's base payload from Figure 3, plus, for BLOB, ENTRY and NODE, the variable term printed under Figure 3, where i is the index of the operation that allocates the object. Each kind has a fixed number of reference slots (dots in Figure 3), numbered from 0, each holding either null or a reference to one object.

3. ROOTS

The mutator holds references only in numbered root slots: slot 0 (scratch), slots 1 to 64 (session ring), slots 100 to 115 (registry), slot 120 (list head). All start null. Whenever roots are scanned, non-null root slots are visited in ascending slot number.

4. THE WORKLOAD

Before operation 0, the program allocates 16 REG objects one after another and puts the j-th (j = 0 to 15) into root slot 100 + j. Then operations run for every index i from 0 up to, but not including, the end mark of the timeline in Figure 4. Each phase covers the operation indexes from its left edge up to, but not including, its right edge. Operation i allocates one object of the kind given by its phase's mix at position (i mod 10), then acts on it:
TEMP: root slot 0 is set to the new object.
SESSION: if k sessions were created before this one, root slot 1 + (k mod 64) is set to the new session. The operation then allocates a BLOB (same i). After that allocation completes, it reads the session back from its root slot (a collection during the BLOB allocation may have relocated it) and stores the BLOB into the session's slot 0.
ENTRY: after the allocation, if any session exists, the entry's slot 0 is set to the object currently held in the ring slot of the most recently created session. If c entries were created before this one, the registry object in root slot 100 + (c mod 16) has its slot (c div 16) mod 4 set to the entry.
NODE: after the allocation, the node's slot 0 is set to whatever root slot 120 currently holds, and root slot 120 is set to the node.
After its actions, if i mod 1500 equals 1499, the operation sets root slot 120 to null.
Every read the mutator performs happens after the allocation it follows, so it always sees current locations.

5. HEAP REGIONS (FIGURE 1)

The young generation is an eden of EDEN bytes and two survivor spaces of SURV bytes each; both sizes are configuration parameters. Eden and the survivor spaces are bump allocated from offset 0. At any time one survivor space (the from-space) holds the objects that survived the previous minor collection and the other (the to-space) is empty. Every young object carries an age, 0 when allocated. The old generation is OLD_SIZE bytes (Figure 1). It never moves objects. It keeps a free list of blocks (address, length), initially one block covering the whole old generation.

6. ALLOCATION

If the configuration's pretenure threshold PT is enabled and the object's size is at least PT, the object is placed directly in the old generation (section 8). If that placement fails, one major collection runs (section 9) and placement is attempted once more; if it fails again the run ends in OOM. Otherwise the object goes to eden: if eden's used bytes plus the object's size would exceed EDEN, a minor collection runs first (section 7); the object is then bump allocated in eden with age 0.

7. MINOR COLLECTION

Before anything else, a minor collection checks a promotion guard: if the total number of free bytes in the old generation is smaller than eden's used bytes plus the from-space's used bytes, a major collection (section 9) runs first, and is logged first. The minor collection then records R, the current number of objects in the remembered set.
Live young objects are found and moved in a fixed order. First every non-null root, in ascending slot order. Then every remembered-set object, in ascending old-generation address, and within each such object its slots in slot order. Then a first-in first-out queue holding every object moved so far in this collection, in the order they were moved, whether they went to the to-space or to the old generation: for each queued object, its slots in slot order. Whenever this procedure reaches a reference to a young object that has not yet been moved in this collection, that object is moved now and appended to the queue; a young object already moved in this collection is not moved again, and the reference is simply updated to its new location. References to old objects are left alone.
Where a moved object goes is decided by its new age, which is its old age plus one, and by the to-space's remaining room, as drawn in Figure 5. An object moved to the to-space is bump allocated there with its new age, and its size counts toward bytes copied. An object moved to the old generation is placed by section 8, and its size counts toward bytes promoted. If any such placement fails, the run ends in OOM.
Afterwards eden and the old from-space are empty, and the to-space becomes the from-space. The remembered set is rebuilt as exactly the old objects holding at least one reference to an object now in the survivor space. The pause of the minor collection is 40 + (bytes copied div 64) + (bytes promoted div 32) + 2 x R.

8. OLD-GENERATION PLACEMENT

Placement of an object of size s takes the free block with the lowest address whose length is at least s. If the block's length minus s is at least 32, the object occupies the first s bytes and the rest stays a free block; otherwise the object occupies the entire block. Each old object remembers how many bytes it occupies. Placement never merges free blocks.

9. MAJOR COLLECTION

A major collection marks every object reachable from the non-null roots, following every reference in every region. It then frees every unmarked old object: its occupied block is returned to the free list and it leaves the remembered set. Finally the free list is sorted by address and blocks that are exactly adjacent are merged. Young objects are not moved. The pause is 150 + (total occupied bytes of the marked old objects div 32) + (number of old objects freed div 2).

10. WRITE BARRIER

When the mutator stores a non-null reference into a slot of an object that is in the old generation, and the referenced object is in eden or a survivor space, the old object is added to the remembered set. Adding an object already in the set has no effect. Stores that do not meet both conditions do not touch the set.

11. METRICS PER CONFIGURATION

oom (and the index of the operation during which it happened; registry setup counts as operation -1), number of minor collections, number of major collections, bytes copied, bytes promoted, bytes pretenured (sizes of objects placed directly by section 6), total pause (sum of all minor and major pauses), maximum pause, and peak old occupancy. Old occupancy is the sum of occupied bytes of all old objects; the peak is the largest value seen right after each minor collection and right after each pretenured placement. If a run ends in OOM, the configuration is infeasible.

12. CANDIDATE CONFIGURATIONS AND SELECTIONS

Every combination of EDEN in {16384, 24576, 32768, 49152}, SURV in {8192, 24576}, T in {1, 2, 3, 5} and PT in {off, 768, 1024} is a candidate, 96 in all, each simulated as a fresh, complete run of the workload. Configurations are ordered by EDEN, then SURV, then T, then PT (off before 768 before 1024). Over feasible configurations only:
Cost optimal: smallest total pause; ties by smallest maximum pause, then configuration order.
Latency optimal under budget: among configurations with total pause at most 220000, smallest maximum pause; ties by smallest total pause, then configuration order.
Footprint optimal under ceiling: among configurations with maximum pause at most 2400, smallest EDEN + 2 x SURV; ties by smallest total pause, then configuration order.

13. BASELINE AND ITS EVENT LOG

The service currently runs EDEN 24576, SURV 8192, T 2, PT off. For this baseline, produce the GC event log in the format of Figure 6, one line per minor or major collection in the order they happen. Field op is the index of the operation during which the collection happened (registry setup counts as -1). For a minor collection, remset is R, marked and freed are 0, and copied and promoted are its own bytes. For a major collection, copied, promoted and remset are 0, marked is the occupied bytes of the marked old objects, and freed is the number of old objects freed. Occupancy is old occupancy immediately after the event. Pause is that event's pause.
"""


def build_text_pages(doc):
    blocks = SPEC_TEXT.split("\n\n")
    margin = 44
    rect = fitz.Rect(margin, margin, PAGE_W - margin, PAGE_H - margin)
    fontsize = 7.8

    def fits(text):
        tmp = fitz.open()
        p = tmp.new_page(width=PAGE_W, height=PAGE_H)
        rc = p.insert_textbox(rect, text, fontsize=fontsize, fontname="helv", align=fitz.TEXT_ALIGN_LEFT)
        tmp.close()
        return rc >= 0

    pages, cur = [], ""
    for block in blocks:
        cand = (cur + "\n\n" + block) if cur else block
        if fits(cand):
            cur = cand
        else:
            if cur:
                pages.append(cur)
            cur = block
            if not fits(cur):
                raise RuntimeError("block too large: " + block[:60])
    if cur:
        pages.append(cur)
    for text in pages:
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        page.insert_textbox(rect, text, fontsize=fontsize, fontname="helv", align=fitz.TEXT_ALIGN_LEFT)


def build_image_page(doc, png, caption):
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    img = fitz.open("png", png)
    iw, ih = img[0].rect.width, img[0].rect.height
    margin = 40
    scale = min((PAGE_W - 2 * margin) / iw, (PAGE_H - 2 * margin - 30) / ih)
    w, h = iw * scale, ih * scale
    x0 = (PAGE_W - w) / 2
    y0 = 40
    page.insert_image(fitz.Rect(x0, y0, x0 + w, y0 + h), stream=png)
    page.insert_textbox(fitz.Rect(margin, y0 + h + 6, PAGE_W - margin, y0 + h + 40), caption,
                        fontsize=9, fontname="helv", align=fitz.TEXT_ALIGN_CENTER)


def main():
    doc = fitz.open()
    build_text_pages(doc)
    figs = [
        (fig_heap_map, "Figure 1 -- Heap map."),
        (fig_object_layout, "Figure 2 -- Object layout."),
        (fig_kinds, "Figure 3 -- Object kinds."),
        (fig_timeline, "Figure 4 -- Mutator workload."),
        (fig_lifecycle, "Figure 5 -- Object lifecycle."),
        (fig_log_example, "Figure 6 -- GC event log format (fake example)."),
    ]
    for fn, cap in figs:
        build_image_page(doc, render_png(fn()), cap)
    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    doc.xref_set_key(doc.pdf_catalog(), "Info", "null")
    out = f"/home/user/cc/task11/artifact/{REVISION}.pdf"
    doc.save(out, garbage=4, deflate=True, clean=True)
    doc.close()
    raw = open(out, "rb").read()
    start = raw.find(b"% Written by")
    if start != -1:
        end = raw.find(b"\n", start)
        raw = raw[:start] + b"%" + b" " * (end - start - 1) + raw[end:]
        open(out, "wb").write(raw)
    print("wrote", out)


if __name__ == "__main__":
    main()
