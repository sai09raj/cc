"""Mechanical audit of the HOLLOWAY-18 platform package."""
import json, re, sys, zlib, fitz
sys.path.insert(0, "../model")
C = json.load(open("rubric.json")); k = json.load(open("../model/key.json")); W = json.load(open("rubric_keys.json"))
P = open("prompt.md").read(); IF = {n: open(f"ideal-flow-{n}.txt").read() for n in ("analyze", "execute-generate", "synthesize")}
ok = True
def bad(msg):
    global ok; ok = False; print("FAIL", msg)
# 1 lengths, verbs, weights, count
for i, (w, t) in enumerate(C, 1):
    if len(t) > 301: bad(f"C{i} {len(t)} chars")
    if not re.match(r"(Reports|States|Delivers|The handover memo lists)\b", t): bad(f"C{i} verb")
    if not -10 <= w <= 10 or w == 0: bad(f"C{i} weight")
    if t.count(" and ") and "Reports" in t and "accept" in t and "kN" in t and t.count("as ") > 2: print("check conj", i)
if not 12 <= len(C) <= 50: bad("count")
# 2 every numeric row: its range contains the key value; one value per row
vals = {}
for i, (w, t) in enumerate(C, 1):
    m = re.search(r" as ([+-]?[\d.]+) (kN/m|kNm|mm|kN)\b", t)
    if t.startswith(("Reports", "States")) and w > 0:
        if not m: bad(f"C{i} no value"); continue
        v = float(m.group(1)); a = re.search(r"accept ([+-]?[\d.]+) to ([+-]?[\d.]+)", t)
        if not a or not (float(a.group(1)) <= v <= float(a.group(2))): bad(f"C{i} range does not contain stated value")
        vals[i] = v
# map rubric values to key values
kv = {round(x, 6) for x in k.values()}
for i, v in vals.items():
    if not any(abs(abs(v) - abs(x)) <= max(0.0006 * abs(x), 0.006) for x in k.values()): bad(f"C{i} value {v} not in key")
# 3 Ideal Flow numbers (decimal numbers) all appear in rubric values or are packet inputs
nums = re.findall(r"[+-]?\d+\.\d+", IF["execute-generate"] + IF["analyze"])
inputs = {"6.3", "0.9035", "69.81", "4.0", "5.0", "7.0", "7.5", "6.0", "168.3", "6.3"}
for n in nums:
    if n.lstrip("+") in inputs: continue
    if not any(abs(abs(float(n)) - abs(v)) < 1e-9 for v in vals.values()): bad(f"Ideal Flow number {n} not in rubric")
# 4 prompt coverage: every beam/column location in prompt has a rubric row
pb = re.findall(r"^(L\d|roof) bay (\d) to (\d) at grid (\d)", P, re.M)
for lvl, a, b, g in pb:
    if not any(f"the {lvl} beam of bay {a}-{b} at its grid {g} end" in t for _, t in C): bad(f"prompt beam {lvl} {a}-{b} g{g} uncovered")
for line in re.findall(r"^grid (\d) (.+?)[;.]$", P, re.M):
    g, rest = line
    for pos in re.split(r", | and ", rest):
        if not any(f"grid {g} column moment {pos} " in t for _, t in C): bad(f"prompt column grid {g} {pos} uncovered")
for need in ["L2 at", "L3 at", "the roof at", "self weight line load", "inside storage zone S", "maximum sagging"]:
    if not any(need in t for _, t in C): bad(f"prompt item '{need}' uncovered")
for need in ["BR1", "BR2", "L2 beam in bay 3-4", "L3 beam in bay 1-2", "TP-1", "storage zone S", "AHU-2"]:
    if not any(need in t and "memo" in t for _, t in C): bad(f"memo item {need} uncovered")
if not any(w < 0 and "does not compute" in t for w, t in C): bad("no penalty for 'own executed program'")
print("prompt words (hyphens as spaces):", len(P.replace("-", " ").split()), "| Ideal Flow chars:", {n: len(t) for n, t in IF.items()})
# 5 PDF metadata, deep: decompress every stream
d = fitz.open("../artifact/holloway_v2.pdf"); raw = open("../artifact/holloway_v2.pdf", "rb").read()
bl = [b"Producer", b"Creator", b"Author", b"CreationDate", b"ModDate", b"matplotlib", b"Software", b"tEXt", b"iTXt", b"xmp", b"XMP", b"Title", b"PyMuPDF", b"fitz"]
hits = [x for x in bl if x in raw]
for x in range(1, d.xref_length()):
    try:
        st = d.xref_stream(x)
    except Exception: st = None
    if st:
        hits += [f"xref{x}:{b.decode()}" for b in bl if b in st[:200000]]
    obj = d.xref_object(x)
    hits += [f"obj{x}:{b.decode()}" for b in bl if b.decode() in obj]
print("metadata", d.metadata, "Info", d.xref_get_key(-1, "Info"), "hits", hits)
if hits or any(d.metadata[f] for f in ("title", "author", "creator", "producer", "creationDate", "modDate")): bad("metadata")
if any(pg.get_drawings() for pg in d): bad("vector drawings")
txt = "".join(pg.get_text() for pg in d)
leak = [f"{abs(v):.4g}" for v in vals.values() if f"{abs(v):.4g}" in txt and abs(v) not in (0.9035,)]
print("answer values found in PDF text:", leak)
print("ALL CHECKS PASS" if ok else "AUDIT FAILED")
