# QMO and Community Guidance Carried Forward

## Status and provenance

This file records operational guidance supplied through community screenshots on 2026-09-21. It is useful authoring evidence, but it does not override the official project PDFs or handbook. Where guidance conflicts, follow official policy and ask a Quality Manager.

## 1. Assume no internet

The Quality Manager answer was explicit: target models have no internet access. Everything required to solve the task must therefore be present in the prompt and uploaded input artifact.

### Authoring rule

- Never require browsing, package downloads, remote documentation, APIs, or an unstated external standard.
- Include all bespoke rules, constants, schemas, schedules, and source hierarchy in the supplied materials.
- Prefer a standard-library or already-guaranteed runtime. If a named tool is optional, allow an equivalent local implementation.
- Audit the task in an offline environment before entry.

Task 03 satisfies this by defining TempestLog only through the attached packet and requiring a self-contained Python 3 program without network access or nonstandard packages.

## 2. “Use a tool” means substantive computational necessity

The Quality Manager advised treating tool use as a difficulty requirement: the requested deliverable should require software and should not be realistically producible by hand. A particular tool may be suggested, but the engineering need matters more than enforcing one brand or executable.

### Authoring rule

- Require an executable artifact, simulation, transformation, broad search, or structured output that cannot credibly be completed manually.
- Grade observable outputs and reproducibility, not whether the solver used one specific editor or library, unless that tool is itself essential and guaranteed.
- Reject “tool use” consisting only of a trivial calculator call or file-format conversion.

Task 03 requires a cycle simulator, 180-request workload generation, up to 3,888 schedule/configuration simulations, percentile and invariant computation, five generated files, and canonical SHA-256 traces.

## 3. The visual must be technically indispensable

Erik QMO’s advice is stricter than “attach an image”: the artifact must contain a real diagram, chart, plot, waveform, spectrum, or image that the model must inspect and interpret. A screenshot of prose, a typeset specification, or a table whose layout has no technical role does not qualify. If OCR alone yields the complete solution, the artifact is disqualified.

### Visual-ablation test

Before release, ask:

1. If all prose were OCR-extracted and reading order preserved, would at least one required value or relationship still be missing?
2. Does geometry, arrow direction, containment, scale, interval length, plotted shape, or spatial association change the computation?
3. Does the prompt explicitly tell the solver which visual relationships are normative?
4. Does a rubric/report criterion verify the visually derived result?

If the answer to the first question is no, redesign the artifact. Do not restate every measured visual result in adjacent prose.

Task 03 was hardened accordingly: `SERIAL=2` and `FIXED=6` must be measured from two separate local waveform axes; the packet prose uses the symbolic constants rather than printing their numeric spans.

## 4. Prefer deterministic, editable graphics

A fellow tasker recommended generating plots or diagrams through code—such as Matplotlib, Pillow, SVG, Graphviz, or equivalent—then inspecting and editing the result, instead of depending on opaque image generation that may introduce malformed text, inconsistent geometry, or unexplained artifacts.

### Authoring rule

- Keep the rendering source beside the artifact.
- Use deterministic coordinates, labels, fonts, axes, and colors.
- Manually inspect at full resolution and at the platform’s preview scale.
- Run OCR/glyph checks and verify every arrow, axis, tick, panel boundary, and footer.
- Regenerate from source after edits; do not paint over semantic content.
- Remove internal authoring metadata from the upload artifact while preserving any disclosure or attribution required by platform policy.

Task 03 follows this pattern through `artifact/make_packet.py`, which deterministically renders the PNG and is followed by full-resolution visual inspection and isolated packet-only audits.

## 5. Community tips on stumping Opus 5.5 (screenshots, 2026-10-08)

Two community posts, shared by the QMO, from authors who report real
sub-50 runs on the current Model A:

**Iterate on the model's own trajectory (via Erick_QMO_ES, tip from
@latam.coder2023).** Deep domain knowledge (DFIR in their case) plus many
iterations on the artifact bundle. After each run, read the trajectory: what
the model got right, which shortcuts it found, what made the task easier than
intended. Harden exactly those paths and remove the shortcuts until the
model must follow the intended reverse-engineering and attribution chain,
without making the task feel artificial.

**Put the fault one step past where the model looks (mubtasar).** When the
failure is in the part under suspicion, Opus finds it: it checks that part
and every standard check on it. When the failure sits one step further
along, in something the part rests on, feeds into or calls, it misses it.
The evidence only appears when two files are combined, such as a value in
one file and a position or reference point in another. If the model can
read or look it up directly, it finds it. Put the evidence in a file it
treats as background: it zooms into the files it thinks matter and skims
the rest. Keep that file legible at full size.

### Authoring rule

- Prefer diagnosis/attribution tasks over "simulate a complete spec"
  (every fully specified simulation in this project was transcribed, #74)
  and over compute-bound tasks (they pass only on timeouts, #73, #78).
- The decisive fact must come from combining two files: a value in one and
  a reference (datum, offset, ratio, orientation, revision, mapping) in
  another, where the second file looks like routine background.
- The obvious suspect must be checkable and must check out clean, so a
  model that stops there reaches a wrong root cause.
- Fairness is unchanged: the evidence is present, legible at full size,
  and determines one root cause; rival causes must be refutable from the
  supplied data, and the rubric grades the reference chain, not wording.
- Iterate: after every pilot, find the shortcut it used and harden it.

## Permanent gate

No future task proceeds to a pilot unless it passes all four checks:

- offline self-containment;
- substantive tool necessity;
- visual indispensability under the OCR-ablation test; and
- deterministic, inspected artifact generation.
