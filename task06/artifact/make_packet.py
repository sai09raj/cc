#!/usr/bin/env python3
"""Builds atrium9.pdf, the ATRIUM-9 engineering packet.

Security/fairness requirement (explicit, non-negotiable): the three
engineering diagrams (shaft layout, door-timing waveform, power-draw
chart) are rendered to RASTER (PNG) images with matplotlib's Agg backend
and embedded into the PDF as opaque image XObjects -- never as vector
`savefig(..., format='pdf')` paths. A vector PDF page embeds the exact
plotted coordinates in its content stream, which a model could parse
programmatically to recover the underlying data (bar heights, gridline
positions) without ever performing the intended visual-measurement task.
Rasterizing at a fixed DPI removes that channel: the only way to recover
T_DOOR_OPEN/T_DWELL/T_DOOR_CLOSE/T_FLOOR and the power draw values is to
actually look at the image and count/measure, exactly like reading a
real engineering drawing.

After assembly, all document metadata (Info dictionary AND XMP) is
stripped so no authoring timestamps, tool paths, or producer strings ride
along with the shipped artifact.
"""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import fitz  # PyMuPDF

DPI = 300
PAGE_W, PAGE_H = 612, 792  # US letter, points


def render_png(fig):
    buf = io.BytesIO()
    # metadata={"Software": ""} suppresses matplotlib's default
    # "Software: Matplotlib version X, https://matplotlib.org/" tEXt chunk.
    # Belt-and-suspenders: PyMuPDF's insert_image() already re-encodes PNGs
    # into raw image XObjects and drops ancillary chunks on its own, but the
    # raw bytes shouldn't carry the tag even transiently.
    fig.savefig(buf, format="png", dpi=DPI, metadata={"Software": ""})
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------
# Diagram A: shaft / floor layout, 8 floors x 4 cars, capacity placard
# ---------------------------------------------------------------------
def diagram_shaft():
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    floors = 8
    cars = ["A", "B", "C", "D"]
    car_w = 1.4
    gap = 0.5
    shaft_x0 = 1.5

    for f in range(floors):
        y = f
        ax.plot([0, shaft_x0 + len(cars) * (car_w + gap)], [y, y],
                color="0.75", lw=0.8, zorder=1)
        ax.text(-0.3, y, f"L{f}", ha="right", va="center", fontsize=9)

    for ci, cname in enumerate(cars):
        x = shaft_x0 + ci * (car_w + gap)
        ax.add_patch(mpatches.Rectangle((x, -0.4), car_w, floors - 1 + 0.8,
                                         fill=False, edgecolor="0.4", lw=1.0))
        ax.text(x + car_w / 2, floors - 0.15, cname, ha="center", va="bottom",
                 fontsize=12, fontweight="bold")
        car_floor = 0
        ax.add_patch(mpatches.FancyBboxPatch(
            (x + 0.12, car_floor + 0.12), car_w - 0.24, 0.62,
            boxstyle="round,pad=0.02", edgecolor="0.2", facecolor="0.92", lw=1.0))
        if ci == 0:
            ax.text(x + car_w / 2, car_floor + 0.43, "MAX\nOCCUPANCY\n6",
                     ha="center", va="center", fontsize=7.5)

    ax.set_xlim(-1.0, shaft_x0 + len(cars) * (car_w + gap) + 0.3)
    ax.set_ylim(-0.8, floors + 0.6)
    ax.axis("off")
    ax.set_title("ATRIUM-9 shaft elevation -- cars A-D, floors L0 (ground) to L7 (top)",
                  fontsize=10)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Diagram B: door-timing waveform -- one full stop-and-go cycle.
# X-axis gridlines are unlabeled except the 0 anchor: spans must be
# measured by counting grid squares, not read off a printed number.
# ---------------------------------------------------------------------
def diagram_timing():
    fig, ax = plt.subplots(figsize=(8.5, 3.2))

    segments = [
        ("TRAVEL", 0, 4, "#8899aa"),
        ("DOOR OPENING", 4, 6, "#c9a34e"),
        ("DWELL", 6, 9, "#5b9270"),
        ("DOOR CLOSING", 9, 11, "#c9a34e"),
    ]
    for label, t0, t1, color in segments:
        ax.add_patch(mpatches.Rectangle((t0, 0.15), t1 - t0, 0.7,
                                         facecolor=color, edgecolor="0.2", lw=1.2))
        ax.text((t0 + t1) / 2, 0.5, label, ha="center", va="center",
                 fontsize=8.5, color="white", fontweight="bold")

    total = 13
    for t in range(total + 1):
        ax.axvline(t, color="0.85", lw=0.6, zorder=0)
    for t in range(0, total + 1, 5):
        ax.axvline(t, color="0.6", lw=0.9, zorder=0)

    ax.text(0, -0.18, "0", ha="center", va="top", fontsize=9)
    ax.plot([0, 0], [0.0, 1.0], color="0.3", lw=1.0)

    ax.set_xlim(-0.3, total)
    ax.set_ylim(-0.35, 1.15)
    ax.set_yticks([])
    ax.set_xticks([])
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_xlabel("elapsed time (grid = 1 tick; count squares to measure each span)",
                   fontsize=8)
    ax.set_title("Per-car door-timing waveform, one representative stop-and-go cycle",
                  fontsize=10)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Diagram C: power-draw chart. Y-axis IS labeled (the constraint is a
# tariff-style budget, meant to be read directly); X-axis gridlines are
# unlabeled except the 0 anchor, matching diagram B's convention.
# ---------------------------------------------------------------------
def diagram_power():
    fig, ax = plt.subplots(figsize=(8.5, 3.4))

    steps = [
        (0, 4, 2),
        (4, 6, 1),
        (6, 9, 0),
        (9, 11, 1),
        (11, 13, 0),
    ]
    for t0, t1, level in steps:
        ax.add_patch(mpatches.Rectangle((t0, 0), t1 - t0, level,
                                         facecolor="#3f6f8f", edgecolor="0.2", lw=1.0))

    total = 13
    for t in range(total + 1):
        ax.axvline(t, color="0.88", lw=0.5, zorder=0)
    for t in range(0, total + 1, 5):
        ax.axvline(t, color="0.6", lw=0.8, zorder=0)
    ax.text(0, -0.35, "0", ha="center", va="top", fontsize=9)

    ax.set_ylim(0, 3.4)
    ax.set_yticks([0, 1, 2, 3])
    ax.set_ylabel("power draw (units / tick)", fontsize=9)
    ax.set_xlim(-0.3, total)
    ax.set_xticks([])
    ax.set_xlabel("elapsed time (grid = 1 tick; count squares to align with waveform above)",
                   fontsize=8)
    ax.set_title("Single-car power draw over the same representative cycle",
                  fontsize=10)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return render_png(fig)


SPEC_TEXT = """ATRIUM-9 -- Engineering Packet
Building Systems / Vertical Transportation Engineering
Multi-car elevator bank dispatch -- controls specification

1. WORKLOAD GENERATION
Four campaigns s = 0..3, twenty calls each (k = 0..19), 80 calls total,
indexed gidx = 20*s + k. Calls form bursts of three sharing an origin
floor and direction: group = k // 3 (final group of a campaign has 2).

  origin(s,k)    = (3*group + 2*s) mod 8
  direction(s,k) = UP    if origin == 0
                 = DOWN  if origin == 7
                 = UP    if (group + s) is even, else DOWN   (otherwise)
  arrival(s,k)   = 200*s + 8*k
  span(s,k)      = 1 + ((5*k + 3*s) mod 7)
  dest(s,k)      = min(7, origin+span), or min(7, origin+1) if that
                   equals origin, when direction is UP
                 = max(0, origin-span), or max(0, origin-1) if that
                   equals origin, when direction is DOWN

A call's destination is revealed only at boarding, not at hall-call
assignment time.

2. DISPATCH POLICY (fully deterministic -- no free per-tick choice)
A car is eligible for a pending hall call (floor, direction) iff it is
idle (cost = distance in ticks), or it is currently scanning that same
direction AND the floor still lies ahead of its position in that
direction. A car scanning the opposite direction, or one that has
already passed the floor, is not eligible this tick -- no backtracking
mid-scan. Assign to the minimum-cost eligible car; ties break to the
lowest car ID. Each car tracks its committed stops SEPARATELY per scan
direction -- a floor needed while scanning UP is a different commitment
from the same floor needed while scanning DOWN. A car re-derives its
next action fresh every tick: continue the current scan direction while
a commitment remains ahead in it, else switch to the nearer remaining
commitment, else head to its home floor (zoning table below) and idle.

3. DOORS AND POWER (see the waveform and power-draw diagrams)
One full stop is: TRAVEL (per floor traversed) -> DOOR OPENING -> DWELL
-> DOOR CLOSING -> CLOSED. Boarding and alighting happen atomically at
the first DWELL tick, ascending call-index order, up to the fixed car
capacity shown on the shaft elevation. DWELL itself draws no power.
Building power is a SHARED cross-car budget (a sweep knob): a car
mid-travel or mid-door-cycle keeps the power it was already admitted;
starting a NEW travel hop, starting door OPENING, or the transition from
DWELL to CLOSING once dwell has elapsed are each their own power-gated
event, admitted each tick from whatever budget remains, in fixed car
priority A, B, C, D. The DWELL-to-CLOSING transition is NOT automatic:
a car that has finished dwelling stays in DWELL, drawing no power, until
its door-close is itself admitted that tick.

4. ZONING (idle parking policy -- a sweep knob)
   SPLIT:  A->L0  B->L2  C->L5  D->L7
   GROUND: A->L0  B->L0  C->L0  D->L0
   TOP:    A->L7  B->L7  C->L7  D->L7
Only the lowest-ID ACTIVE_CARS cars are in service (a sweep knob, 2, 3,
or 4); an inactive car never moves and is never eligible.

5. TIMEOUT REASSIGNMENT (non-combinable, cost-compared)
Every tick, for any still-unboarded call whose current assignment has
aged past WAIT_TIMEOUT ticks (a sweep knob: 50, 75, 100, or 125), find
the best alternative eligible car excluding the incumbent. Reassign only
if that alternative is strictly cheaper than the incumbent's own
recomputed cost -- never bounce a call between equally good cars. A call
reassigned away from a car is never later served by that same car.

6. ENERGY
Every tick a car is mid-travel: energy += 3 + load if moving up,
energy += 3 - load if moving down (regenerative credit for a loaded
descent). net_energy is the running total over the whole run.

7. THE SEARCH -- 144-configuration sweep
The legal configuration space is ACTIVE_CARS x ZONING x WAIT_TIMEOUT x
POWER_BUDGET = {2,3,4} x {SPLIT,GROUND,TOP} x {50,75,100,125} x
{6,8,10,12} = 144 configurations; capacity is fixed (see the shaft
elevation) and not swept. Run every configuration as one continuous
80-call simulation. Report three lexicographic selections:
  - wait-optimal: minimize avg_wait, tie-break net_energy
  - energy-optimal: minimize net_energy, tie-break avg_wait
  - budget-constrained: minimize avg_wait among configurations with
    net_energy <= 3800, tie-break net_energy
These three selections are not required to agree.

8. CERTIFICATION
For the baseline configuration (active_cars=3, zoning=TOP,
wait_timeout=50, power_budget=8) only: serialize the complete per-tick
trace as one line per tick "t,power,energy" in execution order (energy
is that tick's own signed contribution, not a running total), preceded
by one header line "CONFIG:{'active_cars': 3, 'zoning': 'TOP',
'wait_timeout': 50, 'capacity': <see shaft elevation>, 'power_budget':
8}" using Python dict.__str__ formatting and this exact key order, lines
joined by \\n, UTF-8 encoded, hashed with SHA-256; report the first 16
hex characters as the trace-integrity certificate.

Deliver: simulator source, an independently-coded verifier, the full
144-row sweep table, a decision file with all three selections, the
baseline trace plus its SHA-256 certificate and your adversarial-mutation
results, and an engineering memo. Base every reported number on your own
executed implementation.
"""


def build_text_pages(doc):
    # Split into per-section chunks (blank-line-separated blocks) and
    # paginate greedily, since insert_textbox renders nothing at all if
    # the full text doesn't fit in one box (no partial overflow).
    blocks = SPEC_TEXT.split("\n\n")
    margin = 48
    rect = fitz.Rect(margin, margin, PAGE_W - margin, PAGE_H - margin)
    fontsize = 9.0

    def fits(text, fs):
        tmp = fitz.open()
        p = tmp.new_page(width=PAGE_W, height=PAGE_H)
        rc = p.insert_textbox(rect, text, fontsize=fs, fontname="helv",
                               align=fitz.TEXT_ALIGN_LEFT)
        tmp.close()
        return rc >= 0

    pages_text = []
    current = ""
    for block in blocks:
        candidate = (current + "\n\n" + block) if current else block
        if fits(candidate, fontsize):
            current = candidate
        else:
            if current:
                pages_text.append(current)
            current = block
            if not fits(current, fontsize):
                raise RuntimeError(f"single block too large to fit page:\n{block[:80]}...")
    if current:
        pages_text.append(current)

    for text in pages_text:
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        page.insert_textbox(rect, text, fontsize=fontsize, fontname="helv",
                             align=fitz.TEXT_ALIGN_LEFT)


def build_image_page(doc, png_bytes, caption):
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    img = fitz.open("png", png_bytes)
    iw, ih = img[0].rect.width, img[0].rect.height
    margin = 40
    max_w = PAGE_W - 2 * margin
    max_h = PAGE_H - 2 * margin - 30
    scale = min(max_w / iw, max_h / ih)
    w, h = iw * scale, ih * scale
    x0 = (PAGE_W - w) / 2
    y0 = 40
    page.insert_image(fitz.Rect(x0, y0, x0 + w, y0 + h), stream=png_bytes)
    page.insert_textbox(fitz.Rect(margin, y0 + h + 6, PAGE_W - margin, y0 + h + 40),
                         caption, fontsize=9, fontname="helv",
                         align=fitz.TEXT_ALIGN_CENTER)


def main():
    doc = fitz.open()

    build_image_page(doc, diagram_shaft(),
                      "Figure 1 -- Shaft elevation. Read the occupancy placard for car capacity.")
    build_image_page(doc, diagram_timing(),
                      "Figure 2 -- Door-timing waveform. Count grid squares to measure each phase's duration.")
    build_image_page(doc, diagram_power(),
                      "Figure 3 -- Power draw over the same cycle. Bar height = draw in units/tick.")
    build_text_pages(doc)

    # --- strip all metadata (Info dictionary + XMP) ---
    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    # PyMuPDF also writes a self-referential /Info dict directly on the
    # Catalog object (distinct from the trailer-level Info doc.metadata
    # controls) stamped with its own Producer string -- clear that too.
    doc.xref_set_key(doc.pdf_catalog(), "Info", "null")

    out_path = "/home/user/cc/task06/artifact/atrium9.pdf"
    doc.save(out_path, garbage=4, deflate=True, clean=True)
    doc.close()

    # PyMuPDF unconditionally stamps a "% Written by MuPDF x.y.z" comment as
    # the third line of every file it writes, with no save() option to
    # suppress it. Blank it out in place -- same total byte length, so every
    # later object's byte offset in the xref table is unaffected -- rather
    # than deleting it, which would shift offsets and corrupt the file.
    raw = open(out_path, "rb").read()
    start = raw.find(b"% Written by")
    if start != -1:
        end = raw.find(b"\n", start)
        segment = raw[start:end]
        blanked = b"%" + b" " * (len(segment) - 1)
        raw = raw[:start] + blanked + raw[end:]
        open(out_path, "wb").write(raw)

    print("wrote", out_path)


if __name__ == "__main__":
    main()
