#!/usr/bin/env python3
"""Builds cistern7.pdf, the CISTERN-7 engineering packet.

Security/fairness requirement (explicit, non-negotiable): all four
engineering diagrams (wet-well cross-section, pump curve, inflow
hydrograph, TOU tariff chart) are rendered to RASTER (PNG) images with
matplotlib's Agg backend and embedded into the PDF as opaque image
XObjects -- never as vector `savefig(..., format='pdf')` paths. A vector
PDF page embeds the exact plotted coordinates in its content stream,
which a model could parse programmatically to recover the underlying
data without ever performing the intended visual-measurement task.
Rasterizing at a fixed DPI removes that channel.

After assembly, all document metadata (Info dictionary AND XMP) is
stripped so no authoring timestamps, tool paths, or producer strings ride
along with the shipped artifact.
"""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import fitz  # PyMuPDF

DPI = 300
PAGE_W, PAGE_H = 612, 792  # US letter, points

DRY_ANCHORS = [
    (0, 0.5), (180, 0.5), (330, 2.5), (480, 6.0), (600, 3.5),
    (780, 3.0), (1080, 5.5), (1200, 4.0), (1320, 1.5), (1439, 0.5),
]
STORM_START, STORM_PEAK, STORM_END, STORM_PEAK_Q = 300, 360, 420, 8.0
PUMP_CURVE = [(0.4, 3.0), (2.0, 4.0), (4.2, 5.0)]
PUMP_C_SCALE = 0.85
DEADBANDS = {
    "TIGHT":  {"LEAD": (1.2, 0.8), "LAG1": (1.8, 1.4), "LAG2": (2.4, 2.0)},
    "MEDIUM": {"LEAD": (1.5, 0.7), "LAG1": (2.2, 1.2), "LAG2": (3.0, 1.8)},
    "WIDE":   {"LEAD": (2.0, 0.6), "LAG1": (3.0, 1.0), "LAG2": (3.8, 1.6)},
}
TARIFF_BANDS = [(0, 7, 0.08), (7, 16, 0.14), (16, 21, 0.22), (21, 23, 0.14), (23, 24, 0.08)]


def render_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, metadata={"Software": ""})
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def interp(anchors, x):
    if x <= anchors[0][0]:
        return anchors[0][1]
    if x >= anchors[-1][0]:
        return anchors[-1][1]
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x0 <= x <= x1:
            frac = (x - x0) / (x1 - x0) if x1 != x0 else 0
            return y0 + frac * (y1 - y0)


# ---------------------------------------------------------------------
# Diagram 1: wet-well cross-section, tank bounds + the three deadband
# settings' role start/stop elevations. Y axis (elevation) is labeled at
# whole meters only (fine reading requires the 0.2 m gridlines).
# ---------------------------------------------------------------------
def diagram_cross_section():
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    tank_x0, tank_w = 1.0, 5.5

    ax.add_patch(plt.Rectangle((tank_x0, 0.4), tank_w, 3.8, fill=False,
                                 edgecolor="0.25", lw=1.4))
    for y in [x * 0.2 for x in range(2, 22)]:
        ax.axhline(y, color="0.9", lw=0.5, zorder=0, xmin=(tank_x0) / 8.5,
                   xmax=(tank_x0 + tank_w) / 8.5)
    for y in range(0, 5):
        ax.axhline(y, color="0.7", lw=0.8, zorder=0, xmin=tank_x0 / 8.5,
                   xmax=(tank_x0 + tank_w) / 8.5)
        ax.text(tank_x0 - 0.15, y, f"{y}", ha="right", va="center", fontsize=9)

    ax.axhline(0.4, color="#8b3a3a", lw=1.6)
    ax.text(tank_x0 + tank_w + 0.1, 0.4, "LOW CUTOFF", fontsize=8, va="center", color="#8b3a3a")
    ax.axhline(4.2, color="#8b3a3a", lw=1.6)
    ax.text(tank_x0 + tank_w + 0.1, 4.2, "HIGH-HIGH (overflow)", fontsize=8, va="center", color="#8b3a3a")

    colors = {"LEAD": "#3f6f8f", "LAG1": "#5b9270", "LAG2": "#a06b3f"}
    settings = list(DEADBANDS.keys())
    col_w = tank_w / len(settings)
    for si, setting in enumerate(settings):
        cx = tank_x0 + si * col_w + col_w / 2
        ax.text(cx, 4.45, setting, ha="center", fontsize=10, fontweight="bold")
        for role, (start, stop) in DEADBANDS[setting].items():
            c = colors[role]
            ax.plot([cx - col_w * 0.28, cx + col_w * 0.28], [start, start],
                     color=c, lw=2.2)
            ax.plot([cx - col_w * 0.28, cx + col_w * 0.28], [stop, stop],
                     color=c, lw=2.2, linestyle="--")

    handles = [plt.Line2D([0], [0], color=colors[r], lw=2.2, label=f"{r} start")
               for r in ("LEAD", "LAG1", "LAG2")]
    handles += [plt.Line2D([0], [0], color="0.3", lw=2.2, linestyle="--", label="(dashed = stop)")]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.02, 0.55), fontsize=8, frameon=False)

    ax.set_xlim(-0.3, tank_x0 + tank_w + 2.3)
    ax.set_ylim(-0.3, 4.9)
    ax.axis("off")
    ax.set_title("CISTERN-7 wet-well cross-section -- role start/stop elevations by deadband setting",
                 fontsize=10)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Diagram 2: pump curve -- discharge vs. wet-well level. Pump C's curve is
# plotted as a separate, visibly smaller line; its exact scale relative
# to A/B must be read off the chart, not printed as a ratio.
# ---------------------------------------------------------------------
def diagram_pump_curve():
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    xs = [p[0] for p in PUMP_CURVE]
    ys_ab = [p[1] for p in PUMP_CURVE]
    ys_c = [round(y * PUMP_C_SCALE, 4) for y in ys_ab]

    for x in [round(0.4 + 0.2 * i, 1) for i in range(21)]:
        ax.axvline(x, color="0.92", lw=0.5, zorder=0)
    for x in range(0, 5):
        ax.axvline(x, color="0.7", lw=0.8, zorder=0)
    for y in [round(0.5 * i, 1) for i in range(13)]:
        ax.axhline(y, color="0.92", lw=0.5, zorder=0)
    for y in range(0, 7):
        ax.axhline(y, color="0.7", lw=0.8, zorder=0)

    ax.plot(xs, ys_ab, marker="o", color="#3f6f8f", lw=2.0, label="Pumps A, B (primary units)")
    ax.plot(xs, ys_c, marker="s", color="#a06b3f", lw=2.0, label="Pump C (reserve unit)")

    ax.set_xlim(0, 4.6)
    ax.set_ylim(0, 6)
    ax.set_xticks(range(0, 5))
    ax.set_yticks(range(0, 7))
    ax.set_xlabel("wet-well level (m)", fontsize=9)
    ax.set_ylabel("pump discharge (m^3/min)", fontsize=9)
    ax.legend(loc="lower right", fontsize=9, frameon=False)
    ax.set_title("Pump curve: discharge vs. wet-well level (linear between marked points)",
                 fontsize=10)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Diagram 3: diurnal inflow hydrograph, DRY baseline + WET (with storm
# surcharge). X axis hour ticks only every 4h; intermediate anchor points
# must be read against the fine unlabeled gridlines.
# ---------------------------------------------------------------------
def diagram_hydrograph():
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ts = list(range(0, 1440, 2))
    dry = [interp(DRY_ANCHORS, t) for t in ts]
    wet = []
    for t in ts:
        q = interp(DRY_ANCHORS, t)
        if STORM_START <= t <= STORM_PEAK:
            q += (t - STORM_START) / (STORM_PEAK - STORM_START) * STORM_PEAK_Q
        elif STORM_PEAK < t <= STORM_END:
            q += (STORM_END - t) / (STORM_END - STORM_PEAK) * STORM_PEAK_Q
        wet.append(q)

    for m in range(0, 1441, 15):
        ax.axvline(m, color="0.93", lw=0.4, zorder=0)
    for h in range(25):
        ax.axvline(h * 60, color="0.8", lw=0.6, zorder=0)
    for h in range(0, 25, 4):
        ax.axvline(h * 60, color="0.55", lw=0.9, zorder=0)
    ax.set_xticks(range(0, 1441, 240))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 4)], fontsize=8)
    for y in range(0, 16, 2):
        ax.axhline(y, color="0.85", lw=0.5, zorder=0)

    ax.plot(ts, dry, color="#3f6f8f", lw=2.2, linestyle=(0, (4, 2)), label="DRY day")
    ax.plot(ts, wet, color="#8b3a3a", lw=1.6, label="WET day (DRY + storm)")

    ax.set_xlim(0, 1440)
    ax.set_ylim(0, 15)
    ax.set_yticks(range(0, 16, 2))
    ax.set_ylabel("inflow Q_in (m^3/min)", fontsize=9)
    ax.set_xlabel("time of day (fine gridlines every 15 min; labeled every 4 h)",
                  fontsize=8, labelpad=8)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    ax.set_title("Diurnal inflow hydrograph -- DRY baseline and WET (storm-surcharged) day",
                 fontsize=10)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Diagram 4: TOU tariff bands over the same 24h axis as the hydrograph.
# ---------------------------------------------------------------------
def diagram_tariff():
    fig, ax = plt.subplots(figsize=(8.5, 3.0))
    for t0, t1, rate in TARIFF_BANDS:
        ax.add_patch(plt.Rectangle((t0 * 60, 0), (t1 - t0) * 60, rate,
                                     facecolor="#c9a34e", edgecolor="0.2", lw=1.0))
    for h in range(25):
        ax.axvline(h * 60, color="0.9", lw=0.5, zorder=0)
    for h in range(0, 25, 4):
        ax.axvline(h * 60, color="0.65", lw=0.9, zorder=0)
    ax.set_xticks(range(0, 1441, 240))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 4)], fontsize=8)

    ax.set_xlim(0, 1440)
    ax.set_ylim(0, 0.26)
    ax.set_yticks([0.08, 0.14, 0.22])
    ax.set_ylabel("rate ($/kWh)", fontsize=9)
    ax.set_xlabel("time of day", fontsize=8, labelpad=8)
    ax.set_title("Time-of-use electricity tariff, aligned to the same 24h axis", fontsize=10)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return render_png(fig)


SPEC_TEXT = """CISTERN-7 -- Engineering Packet
Civil/Environmental Engineering -- Water Resources & Public Works
Wastewater lift-station wet-well level control -- controls specification

1. SIMULATION HORIZON
One simulated day is 1440 one-minute ticks, t=0 (00:00) through t=1439
(23:59), run to completion -- never a shortened or sampled run. The wet
well is a vertical tank of constant plan area 60.0 m^2. level(t) is a
single continuous state, updated each tick from that tick's own inflow
and pump discharge (see Figures 3, 2): level(t+1) = level(t) + (Q_in(t) -
Q_out(t)) / 60.0, clamped to [0.4, 4.2] m (Figure 1). Whenever the
unclamped update would exceed 4.2 m, the excess volume (times 60.0 m^2)
is a spill added to overflow_volume for that tick, and level is clamped
to exactly 4.2 m.

2. INFLOW (Figure 3)
Q_in(t) for a DRY day is the plotted DRY curve, linearly interpolated
between its marked anchor points. A WET day adds the plotted storm
surcharge on top of the same DRY curve; the surcharge is a triangle, zero
outside its marked window, linearly ramping to its labeled peak and back
to zero. Q_in is never a discrete arrival list -- it is this continuous
function, sampled once per tick.

3. PUMP CURVE AND STAGING (Figures 1, 2)
Three pumps A, B, C. Each running pump's discharge is interpolated from
Figure 2 against the current level(t); pump C's curve is scaled relative
to pumps A/B's (read the exact ratio from Figure 2 at any level). A
non-running pump discharges zero. Each pump fills one of three roles each
tick -- LEAD, LAG1, LAG2 -- assigned fresh each tick: LEAD holds whichever
pump is currently offered that role (rotation policy, item 5); the
remaining in-roster pumps fill LAG1 then LAG2 in ascending pump-ID order.
A role's pump starts when level(t) reaches that role's own start
elevation (Figure 1) and it is currently off; it stops when level(t)
falls to that role's own stop elevation and it is currently on, EXCEPT
that a stop is deferred while the pump is blocked by its minimum-run
timer (item 4). Only the lowest-ID duty_pump_count pumps (a sweep knob:
1, 2, or 3) are ever in service; pump C is the first excluded as the
roster shrinks. A pump outside the roster never runs.

4. PER-PUMP TIMERS
Minimum run time (a sweep knob: SHORT=8 or LONG=15 ticks): once a pump
starts, it cannot stop for that many ticks even if level has already
reached its stop elevation; it keeps running (and keeps discharging)
until the timer clears, then the stop condition is re-checked every
tick. Minimum off time (fixed, 4 ticks, not swept): once a pump stops, it
cannot restart for 4 ticks. A pump blocked from stopping by its
minimum-run timer still counts toward duty_pump_count for staging
additional pumps.

5. LEAD ROTATION POLICY (a sweep knob)
The lead role is offered to a pump only at the instant no pump currently
fills LEAD and level(t) reaches the would-be lead's own start elevation.
The rotation index advances by exactly one position IMMEDIATELY AFTER a
genuine LEAD-START transition completes -- never on a LAG start, never on
any stop event, and never merely because a tick elapsed. Three policies:
STRICT_ALTERNATE cycles the in-roster pumps in fixed ID order;
RUNTIME_BALANCED offers it to the in-roster pump with the lowest
cumulative running minutes so far (ties to lowest ID); FIXED_LEAD always
offers it to the lowest-ID in-roster pump (no rotation).

6. ENERGY AND TARIFF (Figure 4)
Each running pump draws a constant 15 kW, independent of level. Each
tick's energy cost is (running pump count) * 15 kW * (1/60 h) * the
tariff rate whose band (Figure 4) contains that tick's own start minute.
total_energy_cost is the sum over all 1440 ticks.

7. THE SEARCH -- 54-configuration sweep
day_type is weather, not a control setting -- it is never a free
dimension a selection optimizes over. The legal configuration space is
duty_pump_count x rotation_policy x deadband x min_run_time = {1,2,3} x
{STRICT_ALTERNATE, RUNTIME_BALANCED, FIXED_LEAD} x {TIGHT, MEDIUM, WIDE}
x {SHORT, LONG} = 54 configurations; deadband elevations are fixed per
setting (Figure 1) and not independently swept. Every configuration is
evaluated as a PAIR of full 1440-tick runs, one per day_type -- the sweep
table has 54 x 2 = 108 rows, but a selection is always over the 54
configurations, scored by both of a configuration's own two rows
together, never by picking whichever day happens to be cheaper. For
configuration k: E(k) = combined DRY+WET energy cost; P(k) = worse-day
peak level; imbalance(k) = worse-day (highest single pump's run-minutes /
that day's total fleet run-minutes); feasible iff overflow_volume is
zero on both days. Report three lexicographic selections:
  - energy-optimal: among feasible configurations, minimize E(k)
  - reliability-optimal: minimize P(k) over ALL configurations, tie-break
    lower E(k)
  - wear-balance-constrained: among feasible configurations with
    imbalance(k) <= 0.80, minimize E(k)
These three selections are not required to agree.

8. CERTIFICATION
For the baseline configuration (duty_pump_count=3,
rotation_policy=STRICT_ALTERNATE, deadband=TIGHT, min_run_time=LONG,
day_type=WET) only: serialize the complete per-tick trace as one line per
tick "t|level|q_in|q_out|running_pumps|lead" (level/q_in/q_out to exactly
6 decimal places; running_pumps as comma-separated 0-indexed pump numbers
in ascending order, A=0/B=1/C=2, empty string if none running; lead as
the 0-indexed pump number or the literal text None), preceded by one
header line "CISTERN7|(3, 'STRICT_ALTERNATE', 'TIGHT', 'LONG', 'WET')"
(Python tuple repr of the five config values in that order), lines joined
by \\n, UTF-8 encoded, hashed with SHA-256; report the first 16 hex
characters as the trace-integrity certificate.

Deliver: simulator source, an independently-coded verifier, the full
108-row sweep table, a decision file with all three selections, the
baseline trace plus its SHA-256 certificate and your adversarial-mutation
results, and an engineering memo. Base every reported number on your own
executed implementation.
"""


def build_text_pages(doc):
    blocks = SPEC_TEXT.split("\n\n")
    margin = 44
    rect = fitz.Rect(margin, margin, PAGE_W - margin, PAGE_H - margin)
    fontsize = 8.3

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

    build_image_page(doc, diagram_cross_section(),
                      "Figure 1 -- Wet-well cross-section. Role start/stop elevations by deadband setting.")
    build_image_page(doc, diagram_pump_curve(),
                      "Figure 2 -- Pump curve: discharge vs. level. Compare A/B's curve to C's to read C's scale.")
    build_image_page(doc, diagram_hydrograph(),
                      "Figure 3 -- Diurnal inflow hydrograph, DRY and WET days.")
    build_image_page(doc, diagram_tariff(),
                      "Figure 4 -- Time-of-use tariff, aligned to the same 24h axis as Figure 3.")
    build_text_pages(doc)

    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    doc.xref_set_key(doc.pdf_catalog(), "Info", "null")

    out_path = "/home/user/cc/task07/artifact/cistern7.pdf"
    doc.save(out_path, garbage=4, deflate=True, clean=True)
    doc.close()

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
