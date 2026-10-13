"""Pre-handover gate: mechanical checks for rubric, prompt, Ideal Flow and PDF artifact. Usage: gate.py <platform_dir> <artifact.pdf> [packet text files...]"""
import sys, os, re, json, glob
plat, pdf, texts = sys.argv[1], sys.argv[2], sys.argv[3:]
rows = []
def rep(name, ok, ev): rows.append((name, "PASS" if ok else "FAIL", ev))
R = json.load(open(os.path.join(plat, "rubric.json")))
L = max(len(t) for _, t in R); rep("A3 criteria <= 301 chars", L <= 301, f"longest {L}, {len(R)} criteria, +{sum(w for w, _ in R if w > 0)}")
comp = [(i, t[:70]) for i, (w, t) in enumerate(R, 1) if re.search(r"\band\b|\bbecause\b|;", t) and not t.startswith("Delivers")]
rep("B4 compound criteria (review each)", True, f"{len(comp)} flagged: " + "; ".join(f"#{i}" for i, _ in comp) if comp else "none")
pct = [i for i, (w, t) in enumerate(R, 1) if "%" in t and "accept" in t]
numrows = [i for i, (w, t) in enumerate(R, 1) if re.search(r"\d+\.\d+", t) and w > 0 and "Reports" in t]
norange = [i for i in numrows if "accept" not in R[i - 1][1]]
rep("B13 explicit ranges, no percentages", not pct and not norange, f"numeric rows {len(numrows)}, without range {norange}, with % {pct}")
dup = {t for _, t in R if [x for _, x in R].count(t) > 1}; rep("B11 duplicate criteria", not dup, f"{len(dup)} duplicates")
rub = " ".join(t for _, t in R); pk = " ".join(open(f).read() for f in texts)
for f in sorted(glob.glob(os.path.join(plat, "ideal-flow-*.txt"))):
    nums = set(re.findall(r"-?\d+\.\d+", open(f).read())); miss = sorted(n for n in nums if n not in rub and n not in pk)
    rep(f"B6 numbers in {os.path.basename(f)}", not miss, f"not in rubric/packet: {miss}" if miss else "all present")
pr = open(os.path.join(plat, "prompt.md")).read().lower()
rep("A1 prompt requires running code and files", ("running" in pr or "run " in pr or "execut" in pr) and ("file" in pr), "mentions run/execute and files")
try:
    import fitz
    d = fitz.open(pdf); md = {k: v for k, v in d.metadata.items() if v and k not in ("format", "encryption")}
    hits = []
    for x in range(1, d.xref_length()):
        try: st = d.xref_stream(x) or b""
        except Exception: st = b""
        obj = d.xref_object(x)
        for b in (b"Producer", b"Creator", b"Author", b"CreationDate", b"ModDate", b"matplotlib", b"Software", b"tEXt", b"iTXt", b"XMP", b"ICCBased", b"Artifex", b"Metadata"):
            if b in st[:400000] or b.decode() in obj: hits.append(b.decode())
    trailer = d.xref_get_key(-1, "Info")[0] != "null" or d.xref_get_key(-1, "ID")[0] != "null"
    rep("A2 PDF metadata (Info/ID/XMP/generator/ICC)", not md and not hits and not trailer, f"metadata {md}, stream hits {sorted(set(hits))}, trailer Info/ID {'present' if trailer else 'none'}")
    bad = [x for x in range(1, d.xref_length()) if d.xref_get_key(x, "Subtype")[1] == "/Image" and (d.xref_get_key(x, "SMask")[0] != "null" or (d.xref_get_key(x, "BitsPerComponent")[1] == "1" and d.xref_get_key(x, "ColorSpace")[1] == "/DeviceRGB"))]
    rep("B14 no soft mask / 1-bit RGB image", not bad, f"bad image objects {bad}")
    try:
        import pypdfium2 as p, numpy as np
        dk = [int((np.asarray(pg.render(scale=1).to_pil().convert('L')) < 128).sum()) for pg in p.PdfDocument(pdf)]
        rep("B14 second renderer (pdfium) draws every page", all(v > 500 for v in dk), f"dark pixels per page {dk}")
    except ImportError: rep("B14 second renderer", False, "pip install pypdfium2")
except ImportError: rep("A2 PDF checks", False, "pymupdf missing")
w = max(len(r[0]) for r in rows)
for n, s, e in rows: print(f"{n:{w}s}  {s}  {e}")
print("\nMANUAL (report with evidence): B1 legal values | B2 independent re-solve from packet text + drawing | B3 prompt-clause map | B5 every graded metric defined | B7/B9 no validity/presence-only | B10 false claims covered")
