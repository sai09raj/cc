#!/usr/bin/env python3
"""Builds the ARRAY-11 engineering packet PDF.

Every content revision gets a new REVISION (Playbook mistake #46). Figures are
rasterized (matplotlib Agg -> PNG -> image XObject), no vector drawings. The
platform positions and the cable catalogue (capacities, prices) appear ONLY in
the figures (visual-ablation test); the prose refers to them by name. Turbine
coordinates are given exactly in the table. Metadata is stripped.
"""
import io
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import fitz  # PyMuPDF

REVISION = "array11_v1"
HERE = os.path.dirname(os.path.abspath(__file__))
FIELD = json.load(open(os.path.join(HERE, "..", "opt-prototype", "field64.json")))
DPI = 300
PAGE_W, PAGE_H = 612, 792

PRIMARY = tuple(FIELD["substation_primary"])
ALTERNATIVE = tuple(FIELD["substation_alternative"])
CATALOGUE = [("C1", 4, 100), ("C2", 8, 160), ("C3", 14, 245)]


def render_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, metadata={"Software": ""})
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def fig_site_plan():
    fig, ax = plt.subplots(figsize=(8.6, 8.2))
    ax.set_xlim(-1200, 6200)
    ax.set_ylim(-600, 6600)
    ax.set_aspect("equal")
    ax.set_xticks(range(-1000, 6001, 1000))
    ax.set_yticks(range(0, 6001, 1000))
    ax.set_xticks(range(-1200, 6201, 100), minor=True)
    ax.set_yticks(range(-600, 6601, 100), minor=True)
    ax.grid(which="major", color="#8c8c8c", lw=0.8)
    ax.grid(which="minor", color="#e3e3e3", lw=0.35)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=8)
    ax.set_xlabel("easting (m); major gridline 1000 m, minor gridline 100 m", fontsize=9)
    ax.set_ylabel("northing (m)", fontsize=9)
    for tid, (x, y) in sorted(FIELD["turbines"].items()):
        ax.plot(x, y, "o", color="#2b5d8a", ms=3.2)
        ax.text(x + 70, y + 70, tid, fontsize=4.6, color="#2b5d8a")
    for (px, py), name in ((PRIMARY, "P"), (ALTERNATIVE, "A")):
        ax.add_patch(Rectangle((px - 60, py - 60), 120, 120, facecolor="#c0392b", edgecolor="black",
                               lw=0.8, zorder=5))
        ax.plot([px - 220, px + 220], [py, py], color="#c0392b", lw=0.7, zorder=4)
        ax.plot([px, px], [py - 220, py + 220], color="#c0392b", lw=0.7, zorder=4)
        ax.text(px + 110, py - 260, name, fontsize=10, color="#c0392b", weight="bold", zorder=6)
    ax.set_title("Site plan. P = primary platform, A = alternative platform (square centre,\n"
                 "marked by the cross hair). Turbine dots are for orientation only: use the table.",
                 fontsize=9.5)
    return fig


def fig_catalogue():
    fig, ax = plt.subplots(figsize=(8.4, 5.4))
    xs, ys = [], []
    lo = 0
    for name, cap, price in CATALOGUE:
        ax.plot([lo, cap], [price, price], color="#1f4e79", lw=2.4)
        ax.plot([cap, cap], [price, price], "o", color="#1f4e79", ms=5)
        ax.plot([lo, lo], [price, price], "o", mfc="white", color="#1f4e79", ms=5)
        ax.text((lo + cap) / 2, price + 6, name, ha="center", fontsize=10, color="#1f4e79", weight="bold")
        lo = cap
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 300)
    ax.set_xticks(range(0, 17, 1))
    ax.set_yticks(range(0, 301, 20))
    ax.set_yticks(range(0, 301, 5), minor=True)
    ax.grid(which="major", color="#9a9a9a", lw=0.8)
    ax.grid(which="minor", color="#e6e6e6", lw=0.4)
    ax.set_axisbelow(True)
    ax.set_xlabel("cable load (turbines carried)", fontsize=9)
    ax.set_ylabel("price per metre; minor gridline = 5", fontsize=9)
    ax.set_title("Cable catalogue. Each type covers loads from just above the previous type's\n"
                 "capacity (open dot) up to and including its own capacity (filled dot).", fontsize=9.5)
    return fig


def spec_text():
    return """ARRAY-11 ENGINEERING PACKET: OFFSHORE INTER-ARRAY CABLE LAYOUT

1. SCOPE

A 64-turbine offshore wind farm must be connected to an offshore substation platform by inter-array cables. Turbine positions are given exactly in the table that follows (integer metres). The two candidate platform positions, P (primary) and A (alternative), are shown on the site plan (Figure 1) and must be read from its gridlines. The available cable types, with their capacities and prices per metre, are given only by the cable catalogue chart (Figure 2). All costs are whole numbers.

2. LAYOUT RULES

A layout gives every turbine exactly one outgoing cable, to another turbine or to the scenario's platform, such that following outgoing cables from any turbine always reaches the platform; the cables therefore form trees rooted at the platform.
The load of a cable is the number of turbines whose power flows through it: the turbine it leaves plus every turbine upstream of that turbine.
Every cable is a straight segment between the two points it joins. Its length is the Euclidean distance in metres, rounded to the nearest whole metre with exact halves rounded up.
A cable between two turbines may be at most 1300 metres long. A cable from a turbine to the platform has no length limit.
No two cables may cross: two cables cross if their segments share any point other than an endpoint they have in common; a cable that touches another cable's interior, or two collinear cables that overlap along a stretch, also count as crossing.
At most B cables may end at the platform, where B is the scenario's number of feeder bays.
Each cable is built from exactly one cable type. It must use a type whose capacity is at least its load, and it always uses the cheapest such type available in the scenario. A cable's cost is its rounded length multiplied by that type's price per metre, and a layout's cost is the sum of its cable costs.

3. SCENARIOS

S1: platform P, all cable types in the catalogue, B = 6.
S2: platform P, all cable types, B = 5.
S3: platform P, every type except the smallest-capacity type, B = 6.
S4: platform A, all cable types, B = 6.
S5: platform A, all cable types, B = 5.
In every scenario only that scenario's platform exists; the other position is empty sea."""


def table_text():
    rows = sorted(FIELD["turbines"].items())
    lines = ["4. TURBINE COORDINATES (metres, exact)", ""]
    half = (len(rows) + 1) // 2
    for k in range(half):
        a = rows[k]
        left = f"{a[0]}   x = {a[1][0]:>5}   y = {a[1][1]:>5}"
        if k + half < len(rows):
            b = rows[k + half]
            right = f"{b[0]}   x = {b[1][0]:>5}   y = {b[1][1]:>5}"
        else:
            right = ""
        lines.append(f"{left}          {right}")
    return "\n".join(lines)


def text_page(doc, text, fontname="helv", fontsize=8.6):
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    rect = fitz.Rect(48, 48, PAGE_W - 48, PAGE_H - 48)
    rc = page.insert_textbox(rect, text, fontsize=fontsize, fontname=fontname, align=fitz.TEXT_ALIGN_LEFT)
    if rc < 0:
        raise RuntimeError("text overflow")


def image_page(doc, png, caption):
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    img = fitz.open("png", png)
    iw, ih = img[0].rect.width, img[0].rect.height
    margin = 36
    scale = min((PAGE_W - 2 * margin) / iw, (PAGE_H - 2 * margin - 30) / ih)
    w, h = iw * scale, ih * scale
    x0 = (PAGE_W - w) / 2
    page.insert_image(fitz.Rect(x0, 36, x0 + w, 36 + h), stream=png)
    page.insert_textbox(fitz.Rect(margin, 36 + h + 6, PAGE_W - margin, 36 + h + 40), caption,
                        fontsize=9, fontname="helv", align=fitz.TEXT_ALIGN_CENTER)


def main():
    doc = fitz.open()
    text_page(doc, spec_text())
    text_page(doc, table_text(), fontname="cour", fontsize=8.4)
    image_page(doc, render_png(fig_site_plan()), "Figure 1 -- Site plan.")
    image_page(doc, render_png(fig_catalogue()), "Figure 2 -- Cable catalogue.")
    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    doc.xref_set_key(doc.pdf_catalog(), "Info", "null")
    out = os.path.join(HERE, f"{REVISION}.pdf")
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
