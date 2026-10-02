#!/usr/bin/env python3
"""Builds typechain9_v1.pdf, the TYPECHAIN-9 engineering packet.

Playbook mistake #46: every content revision gets a unique filename.
REVISION below is the only thing to bump on a future content change; it
drives the output filename. That filename is also referenced by name in
platform/prompt.md's first sentence ("...specified in the attached
typechain9.pdf") -- actually referenced generically there without a
revision suffix on purpose (the prompt says "typechain9.pdf" as a
category name); if REVISION changes, re-check prompt.md still matches
the attached file's actual name on the platform.

Security/fairness discipline (same as every prior task's
make_packet.py): all diagrams are rendered to RASTER (PNG) images with
matplotlib's Agg backend and embedded as opaque image XObjects -- never
vector `savefig(..., format='pdf')` paths. None of the figures or
SPEC_TEXT contain any DERIVED value (no binding's final type, no
trace-integrity hash). The only "answer-adjacent" content is the
program's own SOURCE TEXT -- which is a stated INPUT (the problem to
solve), exactly like LEDGER-8's trial balances or QUORUM-7's protocol
constants, never the computation's own output.

After assembly, all document metadata (Info dictionary AND XMP) is
stripped.
"""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import fitz  # PyMuPDF

REVISION = "typechain9_v1"
DPI = 300
PAGE_W, PAGE_H = 612, 792

PROGRAM_TEXT = open("/home/user/cc/task09/reference/program.ty").read()


def render_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, metadata={"Software": ""})
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------
# Figure 1: grammar table.
# ---------------------------------------------------------------------
def diagram_grammar():
    fig, ax = plt.subplots(figsize=(8.2, 7.4))
    ax.axis("off")
    rows = [
        ("n", "integer literal, e.g. 42, -3"),
        ("true | false", "boolean literal"),
        ("x", "variable reference"),
        ("(fun x e)", "lambda; curry multi-arg via nested (fun x (fun y e))"),
        ("(e1 e2)", "application"),
        ("(let x e1 e2)", "let x = e1 in e2"),
        ("(if e1 e2 e3)", "conditional"),
        ("(+ e1 e2) (- e1 e2) (* e1 e2)", "Int -> Int -> Int"),
        ("(< e1 e2) (== e1 e2)", "Int -> Int -> Bool"),
        ("(pair e1 e2)", "pair construction"),
        ("(fst e) (snd e)", "pair projection"),
        ("nil", "empty list, polymorphic in element type"),
        ("(cons e1 e2)", "list construction"),
        ("(isnil e) (head e) (tail e)", "list operations"),
    ]
    y = 0.97
    ax.text(0.02, y, "Form", fontsize=11, fontweight="bold", transform=ax.transAxes)
    ax.text(0.46, y, "Meaning", fontsize=11, fontweight="bold", transform=ax.transAxes)
    y -= 0.045
    ax.plot([0, 1], [y + 0.015, y + 0.015], color="0.3", lw=1.0, transform=ax.transAxes)
    for form, meaning in rows:
        y -= 0.058
        ax.text(0.02, y, form, fontsize=9.5, family="monospace", transform=ax.transAxes)
        ax.text(0.46, y, meaning, fontsize=9, transform=ax.transAxes)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("Figure 1 -- Expression grammar (S-expression syntax)", fontsize=10)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Figure 2: type system.
# ---------------------------------------------------------------------
def diagram_types():
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ax.axis("off")
    rows = [
        ("Int, Bool", "base types"),
        ("T1 -> T2", "function type"),
        ("T1 * T2", "pair type"),
        ("List T", "homogeneous list type"),
        ("'a, 'b, 'c, ...", "type variables (inference-internal)"),
    ]
    y = 0.88
    for name, meaning in rows:
        ax.text(0.04, y, name, fontsize=12, fontweight="bold", color="#3f6f8f",
                family="monospace", transform=ax.transAxes)
        ax.text(0.42, y, meaning, fontsize=10, transform=ax.transAxes)
        y -= 0.16
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("Figure 2 -- The type system", fontsize=10)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Figure 3: generalization rule flowchart.
# ---------------------------------------------------------------------
def diagram_generalization_rule():
    fig, ax = plt.subplots(figsize=(8.0, 5.6))
    ax.axis("off")

    def box(x, y, w, h, text, color, fontsize=9.5):
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor="white", edgecolor=color,
                                     lw=2, zorder=2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize,
                color=color, zorder=3, wrap=True)

    box(0.33, 0.82, 0.34, 0.12, "let x = e1 in e2", "#3f6f8f", 11)
    box(0.33, 0.58, 0.34, 0.16,
        "Is e1 syntactically a lambda,\nor a bare reference to a name\n"
        "already bound to a polymorphic\nscheme?",
        "#5b9270")
    box(0.06, 0.34, 0.32, 0.14,
        "YES: generalize.\nQuantify ftv(t1) that are\nNOT free in the current\n"
        "environment.", "#5b9270")
    box(0.62, 0.34, 0.32, 0.14,
        "NO: do not generalize,\neven if e1 is a syntactic\nvalue under standard ML's\n"
        "value restriction.", "#a06b3f")
    box(0.06, 0.10, 0.32, 0.12, "x : forall (excluded vars). t1", "#5b9270")
    box(0.62, 0.10, 0.32, 0.12, "x : t1 (plain, unquantified)", "#a06b3f")

    ax.annotate("", xy=(0.5, 0.74), xytext=(0.5, 0.82), arrowprops=dict(arrowstyle="-|>"))
    ax.annotate("", xy=(0.22, 0.48), xytext=(0.42, 0.58), arrowprops=dict(arrowstyle="-|>"))
    ax.annotate("", xy=(0.78, 0.48), xytext=(0.58, 0.58), arrowprops=dict(arrowstyle="-|>"))
    ax.annotate("", xy=(0.22, 0.22), xytext=(0.22, 0.34), arrowprops=dict(arrowstyle="-|>"))
    ax.annotate("", xy=(0.78, 0.22), xytext=(0.78, 0.34), arrowprops=dict(arrowstyle="-|>"))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("Figure 3 -- This packet's generalization rule (stricter than\n"
                  "standard ML's value restriction)", fontsize=10)
    fig.tight_layout()
    return render_png(fig)


# ---------------------------------------------------------------------
# Figure 4: the program text (the task's input).
# ---------------------------------------------------------------------
def diagram_program():
    lines = PROGRAM_TEXT.splitlines()
    fig, ax = plt.subplots(figsize=(8.2, 9.6))
    ax.axis("off")
    y = 0.98
    for line in lines:
        ax.text(0.02, y, line, fontsize=8.6, family="monospace", transform=ax.transAxes)
        y -= 0.027
    ax.set_xlim(0, 1)
    ax.set_ylim(max(y - 0.02, 0), 1)
    ax.set_title("Figure 4 -- The fixed 27-binding program (this task's entire input)",
                  fontsize=10)
    fig.tight_layout()
    return render_png(fig)


SPEC_TEXT = """TYPECHAIN-9 -- Engineering Packet
Programming Languages / Compilers -- Hindley-Milner type inference
with let-polymorphism, one fixed 27-binding program, no sweep.

1. THE LANGUAGE (Figures 1-2)
A small, pure (no effects, no mutation) functional language in
S-expression syntax. Recover the full grammar from Figure 1 and the
type system from Figure 2: Int, Bool, function types, pair types, list
types, and type variables used internally during inference.

2. THE GENERALIZATION RULE (Figure 3)
At every let binding, this packet's own rule decides whether the bound
name gets a polymorphic (quantified) type scheme or a plain,
unquantified one -- and it is stricter than standard ML's value
restriction, not safe to assume from memory. Generalize only when the
bound expression is syntactically a lambda, or a bare reference to a
name already bound to a polymorphic scheme. For every other form --
integer or boolean literals, applications, if-expressions, pair or list
constructions or projections, anything else -- do not generalize, even
though standard ML's value restriction would allow it for several of
these forms: bind the name to its plain type instead. When generalizing,
quantify exactly the type variables free in the bound expression's type
that are not free in the current typing environment; quantifying one
that is still free in the environment is unsound and is this packet's
central correctness trap, since the resulting variable is actually tied
to an outer, not-yet-resolved lambda parameter, not independently
polymorphic.

3. UNIFICATION
Standard syntax-directed unification with an occurs-check: unifying a
type variable with a type that contains that same variable must fail
(it would require an infinite type), never silently succeed.

4. THE FIXED PROGRAM (Figure 4)
The entire input is the 27-binding program in Figure 4. It is a real
dependency chain, not 27 independent facts: most bindings call or
reference 2-4 earlier ones, often through a "capturing factory" pattern
(a lambda containing a nested let that closes over the outer, not yet
generalized parameter) -- getting the generalization rule wrong on one
binding corrupts the substitution threaded through everything built on
top of it. Every binding's final type is fully determined (ground or
validly polymorphic) by this program -- there is no ambiguity to
resolve beyond correctly applying the stated rules.

5. INDEPENDENT VERIFICATION
Build a separately-coded bidirectional type checker -- not a second
inferencer running the same algorithm, but one that verifies each
binding's claimed type by checking its body against that claim,
top-down -- sharing only immutable input constants (the grammar, the
program text) with the primary implementation, never importing its
substitution, environment, or any computed type. Run two required
adversarial mutations against the checker: a self-application
expression (fun x (x x)), which requires an infinite type and must be
rejected; and a claimed type scheme that over-generalizes (quantifies a
type variable that is actually still free in its own enclosing
environment), which must also be rejected even though it may look like
a plausible, internally-consistent type at first glance. The checker
must accept the true program's own correct types while rejecting both.

6. CERTIFICATION
Build the serialization as exactly these lines, in this exact order,
each line BindingName=Type, with no spaces, built from the type's
printed form: Int, Bool, (T1->T2),
(T1*T2), List(T), each function and pair former fully parenthesized
with no precedence elision. For a generalized binding whose scheme has
at least one quantified variable, prefix with "forall ", then the
quantified variables renamed to t0, t1, t2, ... in first-occurrence
order reading the type left to right, then " . ", then the type body
using those names; a binding that is generalization-eligible but ends
up with zero free type variables is printed as a plain type, with no
forall prefix. List the 27 binding lines in the SOURCE ORDER they
appear in Figure 4, not alphabetical, not dependency order. Join the
literal header line "TYPECHAIN9-CERT-V1" and the 27 binding lines with
a single newline character, UTF-8 encode, hash with SHA-256; report
the first 16 hex characters as the trace-integrity certificate.

Deliver: inference engine source; independent checker source; the full
typing output for all 27 bindings; a findings report; certification
evidence (both adversarial mutation rejection results plus the trace
hash); and an engineering memo explaining the causal chain from the
generalization rule through the program's actual dependency structure
to the final claimed types. Base every reported type on your own
executed implementation -- never hand-derive or embed a precomputed
type or hash as a substitute for running the delivered engine.
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

    build_image_page(doc, diagram_grammar(), "Figure 1 -- Expression grammar.")
    build_image_page(doc, diagram_types(), "Figure 2 -- The type system.")
    build_image_page(doc, diagram_generalization_rule(),
                      "Figure 3 -- This packet's generalization rule.")
    build_image_page(doc, diagram_program(),
                      "Figure 4 -- The fixed 27-binding program (this task's input).")
    build_text_pages(doc)

    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    doc.xref_set_key(doc.pdf_catalog(), "Info", "null")

    out_path = f"/home/user/cc/task09/artifact/{REVISION}.pdf"
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
