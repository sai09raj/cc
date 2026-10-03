#!/usr/bin/env python3
"""Builds cellguard10_v1.pdf, the CELLGUARD-10 engineering packet.

Playbook mistake #46: every content revision gets a unique filename.
REVISION below drives the output filename, from the first draft.

Security/fairness discipline (same as every prior task's
make_packet.py): all diagrams are rendered to RASTER (PNG) images with
matplotlib's Agg backend and embedded as opaque image XObjects -- never
vector `savefig(..., format='pdf')` paths. No figure or SPEC_TEXT
content contains any DERIVED value (no checkpoint state, no event tick,
no hash) -- Figure 3's worked certificate-format example uses fake
numbers that don't collide with any real computed value.

After assembly, all document metadata (Info dictionary AND XMP) is
stripped.
"""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import fitz  # PyMuPDF

REVISION = "cellguard10_v1"
DPI = 300
PAGE_W, PAGE_H = 612, 792


def render_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, metadata={"Software": ""})
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def diagram_constants():
    fig, ax = plt.subplots(figsize=(8.2, 8.0))
    ax.axis("off")
    rows = [
        ("CAPACITY", "6000", "charge units"),
        ("CC_CURRENT", "50", "constant-current phase current"),
        ("CV_VOLTAGE_THRESHOLD", "4150", "mV; CC->CV transition point"),
        ("CV_DECAY_STEP", "1.2", "per tick, CV regulation current"),
        ("TAPER_CURRENT_THRESHOLD", "8", "CV->TAPER transition point"),
        ("TAPER_CURRENT", "3", "fixed TAPER-mode current"),
        ("IR_DROP_PER_UNIT", "2.0", "mV per unit delivered current"),
        ("BASE_VOLTAGE", "3700", "mV, at soc=0"),
        ("VOLT_PER_SOC_PCT", "6.0", "mV per 1% state of charge"),
        ("AMBIENT", "250", "0.1 degC units, starting/ambient temp"),
        ("HEAT_FULL", "6", "0.1 degC/tick, full-rate charging"),
        ("HEAT_DERATED", "3", "0.1 degC/tick, derated charging"),
        ("HEAT_TAPER", "1", "0.1 degC/tick, TAPER mode (always)"),
        ("COOL_PER_TICK", "2", "0.1 degC/tick, passive cooling"),
        ("DERATE_TEMP", "450", "0.1 degC; derating engages at/above"),
        ("DERATE_FACTOR", "0.5", "multiplier on mode current"),
        ("FAULT_TEMP_HIGH", "575", "0.1 degC; fault latches at/above"),
        ("FAULT_TEMP_LOW", "520", "0.1 degC; release eligible at/below"),
        ("FAULT_RELEASE_TICKS", "4", "consecutive cool ticks to release"),
        ("OVERCURRENT_MAX", "45", "hard clamp, applied after derating"),
    ]
    tbl = ax.table(cellText=rows, colLabels=["Constant", "Value", "Meaning"],
                    loc="center", cellLoc="left", colLoc="left")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1, 1.35)
    tbl.auto_set_column_width([0, 1, 2])
    ax.set_title("Model constants (fixed packet input)", fontsize=12, pad=14)
    return fig


def diagram_rules():
    fig, ax = plt.subplots(figsize=(8.2, 8.6))
    ax.axis("off")
    steps = [
        "1. Mode transition: CC->CV if PREVIOUS tick's voltage >= CV_VOLTAGE_THRESHOLD.\n"
        "   CV->TAPER if CV regulation current <= TAPER_CURRENT_THRESHOLD. One-way only.",
        "2. Mode-commanded current: CC_CURRENT / CV regulation current / TAPER_CURRENT.",
        "3. CV taper-down: in CV mode only, after step 2, reduce CV regulation\n"
        "   current by CV_DECAY_STEP (floor 0), for next tick's step 1/2 check.",
        "4. Thermal derating and fault gating: if fault latched, current=0.\n"
        "   Else if INCOMING temperature >= DERATE_TEMP, current *= DERATE_FACTOR\n"
        "   (applies in every mode, TAPER included). Else current unmodified.",
        "5. Overcurrent clamp: cap current at OVERCURRENT_MAX. Applied AFTER\n"
        "   derating (step 4), never before.",
        "6. Heat generation: 0 if current is 0. Else, in TAPER mode: ALWAYS\n"
        "   HEAT_TAPER, regardless of temperature -- this packet's own\n"
        "   exception, not the derated-heat rule other modes follow when hot.\n"
        "   Else if incoming temp >= DERATE_TEMP: HEAT_DERATED. Else: HEAT_FULL.",
        "7. Temperature update: temp = incoming temp + heat - COOL_PER_TICK.",
        "8. Fault-latch hysteresis: latch if not already latched and NEW temp\n"
        "   >= FAULT_TEMP_HIGH. If latched: release only after\n"
        "   FAULT_RELEASE_TICKS CONSECUTIVE ticks at/below FAULT_TEMP_LOW --\n"
        "   a single tick back above FAULT_TEMP_LOW resets the counter to 0.",
        "9. State of charge: soc = min(100, soc_prev + current / CAPACITY * 100).",
        "10. Terminal voltage: voltage = BASE_VOLTAGE + soc*VOLT_PER_SOC_PCT\n"
        "    - current*IR_DROP_PER_UNIT. This tick's own voltage (step 1 of\n"
        "    the NEXT tick reads it as the previous tick's voltage).",
    ]
    y = 0.97
    for s in steps:
        ax.text(0.02, y, s, fontsize=9.2, va="top", ha="left",
                 transform=ax.transAxes, family="monospace")
        y -= 0.095
    ax.set_title("Per-tick update rules, in order (applied every tick, t=1..320)",
                 fontsize=11, pad=10)
    return fig


def diagram_certificate_example():
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    ax.axis("off")
    example = (
        "Certificate format (S03), worked example with FAKE numbers\n"
        "(these do not correspond to any real tick of this model):\n\n"
        "CELLGUARD10-CERT-V1\n"
        "t=1;mode=CC;soc=12.34;temp=317;current=50.0;voltage=3850.5;fault=False\n"
        "t=2;mode=CC;soc=12.67;temp=321;current=50.0;voltage=3852.5;fault=False\n"
        "...\n"
        "t=320;mode=TAPER;soc=77.10;temp=288;current=3.0;voltage=4150.9;fault=False\n\n"
        "Rules: one line per tick, t=1 through t=320, in order. soc/current/\n"
        "voltage rounded to exactly 2 decimal places. temp is an integer\n"
        "(0.1 degC units). fault is True or False (or a clearly equivalent\n"
        "boolean rendering). Certificate hash: SHA-256 of the full text\n"
        "(header through the t=320 line, newline-joined, trailing newline\n"
        "included), first 16 hex characters."
    )
    ax.text(0.03, 0.95, example, fontsize=9.3, va="top", ha="left",
             transform=ax.transAxes, family="monospace")
    ax.set_title("Figure 3 worked example (fake data)", fontsize=11, pad=10)
    return fig


SPEC_TEXT = """\
CELLGUARD-10 ENGINEERING PACKET

1. OVERVIEW

A single battery pack is simulated across 320 discrete ticks under a
charge and thermal controller. Every tick's state (charge mode, state
of charge, temperature, delivered current, terminal voltage, fault
latch status) is computed from the immediately preceding tick's state.
Figure 1 lists every fixed model constant. Figure 2 lists the ten
per-tick update rules, in their required order. Initial state, before
tick 1: state of charge 0, temperature AMBIENT, mode CC, fault not
latched, hysteresis counter 0, reference voltage BASE_VOLTAGE.

2. CHARGE MODE SEQUENCE

The charge mode is CC, then CV, then TAPER, strictly one-way (never
reverts). The CC to CV transition is evaluated against the PREVIOUS
tick's reported voltage, never the current tick's own just-computed
voltage. Once in CV mode, a regulation current value is tracked
separately from the delivered current; it starts at CC_CURRENT and
decays by CV_DECAY_STEP every tick (floored at zero, never negative).
The CV to TAPER transition triggers once that regulation current falls
to or below TAPER_CURRENT_THRESHOLD. In TAPER mode, delivered current
(before derating/clamping) is always the fixed TAPER_CURRENT.

3. THERMAL DERATING AND THE OVERCURRENT CLAMP

If the pack's incoming temperature for a tick (its temperature before
that tick's own heat/cool update) is at or above DERATE_TEMP, the
mode-commanded current for that tick is multiplied by DERATE_FACTOR --
in every mode, TAPER included. This derated (or undeprated) current is
then capped at OVERCURRENT_MAX. The clamp is applied AFTER derating,
never before: a tick whose mode-commanded current already exceeds
OVERCURRENT_MAX is clamped regardless of whether derating also applied,
and the clamp binds on every tick of the CC phase in this model, since
CC_CURRENT (50) exceeds OVERCURRENT_MAX (45) by a constant margin
independent of temperature.

4. HEAT GENERATION

If delivered current is zero (fault latched), no heat is generated that
tick. TAPER mode is an exception to the derating-sensitive heat rule
that every other mode follows: a TAPER-mode tick always generates
HEAT_TAPER, regardless of whether incoming temperature is at or above
DERATE_TEMP. Only CC and CV mode ticks follow the general rule: incoming
temperature at or above DERATE_TEMP generates HEAT_DERATED; otherwise
HEAT_FULL. Temperature is then updated by adding that tick's heat and
subtracting COOL_PER_TICK.

5. FAULT LATCH

If the pack is not currently fault-latched and the NEW temperature
(after this tick's own update) is at or above FAULT_TEMP_HIGH, the
fault latches immediately and the release-hysteresis counter resets to
zero. While latched, the pack delivers zero current every tick
(regardless of mode) until released. Release requires the temperature
to be at or below FAULT_TEMP_LOW for FAULT_RELEASE_TICKS CONSECUTIVE
ticks -- the counter increments only while temperature stays at or
below FAULT_TEMP_LOW every tick in a row; a single tick where
temperature rises back above FAULT_TEMP_LOW resets the counter to zero
immediately, even if the pack had been close to releasing.

6. STATE OF CHARGE AND VOLTAGE

State of charge increases each tick by delivered current divided by
CAPACITY, times 100, capped at 100. Terminal voltage is BASE_VOLTAGE
plus state of charge times VOLT_PER_SOC_PCT, minus delivered current
times IR_DROP_PER_UNIT -- this tick's own voltage, which becomes "the
previous tick's voltage" for the NEXT tick's mode-transition check
(section 2), never used for this same tick's own transition decision.

7. INDEPENDENT VERIFICATION

Deliver a separately coded verifier that re-implements these ten rules
itself, from scratch, in its own code -- never importing, calling, or
reading any state computed by the primary engine. It must check the
primary's claimed state at several checkpoint ticks by independently
replaying the simulation from tick 1 up to each checkpoint using only
its own logic. Run two required adversarial mutations against it: a
claimed fault release after only two consecutive cool ticks instead of
four, and a claimed delivered current above OVERCURRENT_MAX as if the
clamp were never applied. The verifier must reject both while still
accepting the true trace's own correct checkpoint states.

8. CERTIFICATION

See Figure 3 for the exact, fully mechanical certificate serialization
format and a worked example using fake numbers. Deliver six products as
files: the engine source; the independent verifier source; the full
320-tick state trace; a findings report; certification evidence (both
adversarial rejection results plus the SHA-256 trace-integrity hash);
and an engineering memo explaining, citing your own executed engine's
actual reported values: why TAPER mode never follows the derated-heat
rule even while hot; why the fault latch released at the specific tick
it did, citing the consecutive-tick hysteresis counter; and why the
overcurrent clamp is active on every tick of the CC phase. Base every
reported value on your own executed implementation -- never hand-derive
or embed a precomputed state, checkpoint value, or hash as a substitute
for running the delivered engine.
"""


def build_text_pages(doc):
    blocks = SPEC_TEXT.split("\n\n")
    margin = 44
    rect = fitz.Rect(margin, margin, PAGE_W - margin, PAGE_H - margin)
    fontsize = 8.0

    def fits(text, fs):
        tmp = fitz.open()
        p = tmp.new_page(width=PAGE_W, height=PAGE_H)
        rc = p.insert_textbox(rect, text, fontsize=fs, fontname="helv",
                               align=fitz.TEXT_ALIGN_LEFT)
        tmp.close()
        return rc >= 0

    pages_text, current = [], ""
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

    build_image_page(doc, render_png(diagram_constants()), "Figure 1 -- Model constants.")
    build_image_page(doc, render_png(diagram_rules()), "Figure 2 -- Per-tick update rules, in order.")
    build_image_page(doc, render_png(diagram_certificate_example()),
                      "Figure 3 -- Certificate format, worked example (fake data).")
    build_text_pages(doc)

    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    doc.xref_set_key(doc.pdf_catalog(), "Info", "null")

    out_path = f"/home/user/cc/task10/artifact/{REVISION}.pdf"
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
