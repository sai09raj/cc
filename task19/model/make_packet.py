"""Build artifact/dh19_v2.pdf: data sheet, log, route plan; metadata stripped, leak check."""
import os, sys, json, fitz
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "artifact"); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE); os.chdir(HERE)
import render
NAME = "dh19_v2.pdf"; tmp = os.path.join(OUT, ".plan.png"); render.plan(tmp)
doc = fitz.open()
for f, fs in (("../packet/datasheet.txt", 8.6), ("../packet/log.txt", 9.0)):
    p = doc.new_page(width=612, height=792); rc = p.insert_textbox(fitz.Rect(36, 36, 576, 756), open(f).read(), fontsize=fs, fontname="helv"); assert rc >= 0, (f, rc)
from PIL import Image
import io; buf = io.BytesIO(); Image.open(tmp).convert("RGB").save(buf, "PNG"); data = buf.getvalue()   # flatten alpha: no SMask, no ICC
img = fitz.open("png", data); iw, ih = img[0].rect.width, img[0].rect.height
q = doc.new_page(width=792, height=612); sc = min(762 / iw, 582 / ih); q.insert_image(fitz.Rect(15, 15, 15 + iw * sc, 15 + ih * sc), stream=data); os.remove(tmp)
doc.set_metadata({})
try: doc.del_xml_metadata()
except Exception: pass
t = os.path.join(OUT, ".tmp.pdf"); doc.save(t, garbage=4, deflate=True, clean=True); doc.close()
d = fitz.open(t); d.xref_set_key(-1, "Info", "null"); d.xref_set_key(-1, "ID", "null")
for x in range(1, d.xref_length()):
    if d.xref_get_key(x, "Subtype")[1] == "/Image":
        assert d.xref_get_key(x, "SMask")[0] == "null", "image has a soft mask"
        if d.xref_get_key(x, "ColorSpace")[0] in ("array", "xref"): d.xref_set_key(x, "ColorSpace", "/DeviceRGB")   # ICCBased -> DeviceRGB (8-bit RGB only)
cat = d.pdf_catalog(); pages = d.xref_get_key(cat, "Pages")[1]; d.update_object(cat, "<< /Type /Catalog /Pages %s >>" % pages)
out = os.path.join(OUT, NAME); d.save(out, garbage=4, deflate=True, clean=True, no_new_id=True); d.close(); os.remove(t)
raw = open(out, "rb").read(); i = raw.find(b"% Written by")
if i != -1:
    j = raw.find(b"\n", i); raw = raw[:i] + b"%" + b" " * (j - i - 1) + raw[j:]; open(out, "wb").write(raw)
d = fitz.open(out); hits = []
for x in range(1, d.xref_length()):
    try: st = d.xref_stream(x) or b""
    except Exception: st = b""
    for b in (b"Producer", b"Creator", b"Author", b"CreationDate", b"ModDate", b"matplotlib", b"Software", b"tEXt", b"XMP", b"ICCBased", b"Artifex"):
        if b in st[:400000] or b.decode() in d.xref_object(x): hits.append((x, b))
assert not hits, hits
assert not any(pg.get_drawings() for pg in d)
txt = "".join(pg.get_text() for pg in d); k = json.load(open("key.json"))
vals = [f"{abs(v):#.4g}" for kk, v in k.items() if isinstance(v, float)]
leaks = [v for v in vals if v.rstrip(".") in txt]; assert not leaks, leaks
print(out, d.page_count, d.metadata, "clean, no leaks")
